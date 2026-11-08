#!/usr/bin/env python3
"""Execute original4e06c0/5431d0/5575d0, without hooks, for ship mask queries."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct

try:
    from . import stage_ship_picking as staging
    from . import validate_mission_object_selection as source
except ImportError:
    import stage_ship_picking as staging
    import validate_mission_object_selection as source

ROOT = staging.ROOT
ENTRY = 0x4e06c0
SHIP, SPRITE, SEQUENCE, MASKS = 0x70000000, 0x70002000, 0x70004000, 0x70010000


def mask_inputs(source_root):
    payloads, metadata = staging.compose(source_root)
    blob = payloads['ShipHitMasks.bytes']
    result = []
    for family in metadata['families']:
        result.append({'family': family['family'], 'width': family['width'], 'height': family['height'],
                       'kind': 'original type18',
                       'planes': [blob[m['offset']:m['offset'] + m['length']] for m in family['masks']]})
    result.append({'family': 'PAD', 'width': 13, 'height': 5, 'kind': 'synthetic padding stress',
                   'planes': [bytes((frame * 37 + n * 19) & 255 for n in range(10)) for frame in range(24)]})
    return result, metadata


def original_cases(source_root=ROOT / 'reference/raw/ancient-conquest'):
    # Hash all original inputs before importing optional emulator dependencies.
    loaded = staging.checked_sources(source_root)
    families, metadata = mask_inputs(source_root)
    import pefile
    from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP
    pe = pefile.PE(data=loaded['installed/ancient.exe'])
    uc = source.new_engine(pe.get_memory_mapped_image(), pe.OPTIONAL_HEADER.SizeOfImage)
    put = lambda address, value: source.put(uc, address, value)
    put(SHIP + 0x8be, SPRITE); put(SHIP + 0x8e2, SEQUENCE)
    uc.mem_write(SEQUENCE + 0x23, struct.pack('<h', 24))
    top = source.STACK + source.STACK_SIZE - 0x1000
    for index, value in enumerate((source.END, 0, 0, 1, 0, 0)):
        put(top + index * 4, value)
    calls = 0

    def pose(frame, heading, ox=1028, oy=132):
        put(SPRITE + 0x45, frame); put(SPRITE + 0x59, ox); put(SPRITE + 0x5d, oy)
        uc.mem_write(SHIP + 0x5af, bytes([heading & 255]))

    def call(x, y, precise=1):
        nonlocal calls
        put(top + 4, x); put(top + 8, y); put(top + 12, precise)
        # Native4e06c0 reuses the output-argument stack byte for its mask index.
        # Each invocation supplies the declared null output pointer anew.
        put(top + 16, 0)
        uc.reg_write(UC_X86_REG_ECX, SHIP); uc.reg_write(UC_X86_REG_ESP, top)
        uc.emu_start(ENTRY, source.END, count=400)
        if uc.reg_read(UC_X86_REG_EIP) != source.END:
            raise AssertionError('Original ship hit query did not return')
        calls += 1
        return uc.reg_read(UC_X86_REG_EAX) & 255

    results = []
    for family in families:
        width, height = family['width'], family['height']
        put(SPRITE + 0x61, width); put(SPRITE + 0x65, height)
        offset = 0
        for index, raw in enumerate(family['planes']):
            uc.mem_write(MASKS + offset, raw); put(SEQUENCE + 0x30 + index * 4, MASKS + offset)
            offset += len(raw)
        planes = []
        for index in range(24):
            pose(32 + index, index % 8)
            coverage = bytes(call(1028 + x, 132 + y) for y in range(height) for x in range(width))
            planes.append({'index': index, 'coverage_sha256': hashlib.sha256(coverage).hexdigest(),
                           'covered': sum(coverage), 'pixels': len(coverage)})
        points = []
        frames = range(88) if family['family'] == 'A1' else (-2147483648, -1, 0, 20, 31, 32, 40, 55, 56, 87, 2147483647)
        positions = ((-1, 0), (0, 0), (width - 1, height - 1), (width, 0), (0, height),
                     (width // 2, height // 2), (width // 3, height // 4), (width * 3 // 4, height // 3))
        for frame in frames:
            for heading in range(8):
                pose(frame, heading)
                for x, y in positions:
                    points.append({'frame': frame, 'heading': heading, 'world': [1028 + x, 132 + y],
                                   'origin': [1028, 132], 'precise': True,
                                   'expected': call(1028 + x, 132 + y)})
        for ox, oy, x, y, precise, frame, heading in (
                (0, 0, -2147483648, 2147483647, 0, 0, -1),
                (2147483647, -2147483648, -2147483648, -2147483648, 1, 32, -1),
                (-2147483648, 2147483647, 2147483647, -2147483648, 1, 32, 127),
                (1028, 132, 1027, 132, 1, 0, -1)):
            pose(frame, heading, ox, oy)
            points.append({'frame': frame, 'heading': heading, 'world': [x, y], 'origin': [ox, oy],
                           'precise': bool(precise), 'expected': call(x, y, precise)})
        results.append({'family': family['family'], 'kind': family['kind'], 'width': width, 'height': height,
                        'plane_sha256': [hashlib.sha256(p).hexdigest() for p in family['planes']],
                        'planes': planes, 'points': points})
    return {'schema_version': 1, 'original_exe_sha256': staging.SOURCE_HASHES['installed/ancient.exe'],
            'sources': metadata['sources'], 'entry': '0x4e06c0', 'hooks': [],
            'native_calls': calls, 'family_count': len(results), 'families': results,
            'scope': 'Actual ship virtual hit, original sequence lookup and bit query; null output pointer',
            'excluded': ['world picking and neighbours', 'fog', 'ownership', 'selection and mouse events',
                         'other original object hit predicates', 'non-null object result output']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    result = original_cases()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'native_calls': result['native_calls'], 'families': result['family_count'],
                      'full_plane_pixels': sum(p['pixels'] for f in result['families'] for p in f['planes']),
                      'point_cases': sum(len(f['points']) for f in result['families'])}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
