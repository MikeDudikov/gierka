#!/usr/bin/env python3
"""Stage the original type18 ship hit masks, separately from rendered alpha."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import struct

try:
    from .stage_mission_objects import SOURCE_HASHES as ALL_HASHES, digest, write_payloads
    from .inspect_dkx import inspect_pair
    from .decode_sprite import resource_payload
except ImportError:
    from stage_mission_objects import SOURCE_HASHES as ALL_HASHES, digest, write_payloads
    from inspect_dkx import inspect_pair
    from decode_sprite import resource_payload

ROOT = Path(__file__).resolve().parents[1]
SOURCE_HASHES = {name: ALL_HASHES[name] for name in
                 ('installed/ancient.exe', 'files/DATA/OBJECTS.DKX', 'files/DATA/OBJECTS.DKD')}
FAMILIES = (('A1', 'SHIP_A1009', 'SHIP_A1110'), ('H1', 'SHIP_H1009', 'SHIP_H1110'),
            ('B4', 'SHIP_B4009', 'SHIP_B4400'), ('G4', 'SHIP_G4009', 'SHIP_G4400'))
MANIFEST_NAME = 'ShipPickingManifest.json'


def checked_sources(source_root):
    loaded = {}
    for name, expected in SOURCE_HASHES.items():
        path = Path(source_root) / name
        raw = path.read_bytes()
        if digest(raw) != expected:
            raise ValueError('Original source hash differs: ' + name)
        loaded[name] = raw
    return loaded


def compose(source_root):
    loaded = checked_sources(source_root)
    data = loaded['files/DATA/OBJECTS.DKD']
    entries = inspect_pair(loaded['files/DATA/OBJECTS.DKX'], data)
    resources = {(entry['type'], entry['name']): entry for entry in entries}
    if len(resources) != len(entries):
        raise ValueError('Duplicate source resource')
    payload = bytearray()
    families = []
    for family, descriptor_name, geometry_name in FAMILIES:
        descriptor = resource_payload(resources[11, descriptor_name], data)
        if len(descriptor) != 52:
            raise ValueError('Unexpected type11 mask descriptor length')
        prefix = descriptor[:32].split(b'\0', 1)[0].decode('ascii')
        digits, start, count = descriptor[32], *struct.unpack_from('<hh', descriptor, 33)
        if (digits, start, count) != (2, 0, 24) or prefix != 'MASK_' + family[1] + family[0]:
            raise ValueError('Unexpected source mask sequence')
        geometry = resources[8, geometry_name]
        _, _, width, height = struct.unpack_from('<4h', bytes.fromhex(geometry['metadata_hex']))
        if width < 1 or height < 1 or width > 2048 or height > 2048:
            raise ValueError('Unsupported source mask dimensions')
        length = ((width + 7) // 8) * height
        records = []
        for index in range(count):
            name = prefix + f'{start + index:0{digits}d}'
            raw = resource_payload(resources[18, name], data)
            if len(raw) != length:
                raise ValueError('Source mask length differs from logical sprite geometry')
            records.append({'index': index, 'name': name, 'offset': len(payload),
                            'length': len(raw), 'sha256': digest(raw)})
            payload.extend(raw)
        families.append({'family': family, 'descriptor': descriptor_name,
                         'descriptor_sha256': digest(descriptor), 'geometry_resource': geometry_name,
                         'geometry_metadata_hex': geometry['metadata_hex'],
                         'width': width, 'height': height, 'row_bytes': (width + 7) // 8,
                         'masks': records})
    metadata = {'schema_version': 1, 'native_canvas_width': 1920, 'native_canvas_height': 1080,
                'format': 'source type18, padded rows, most significant bit first, top to bottom',
                'family_count': len(families), 'mask_count': sum(len(f['masks']) for f in families),
                'families': families, 'sources': {name: {'bytes': len(raw), 'sha256': digest(raw)}
                                                 for name, raw in loaded.items()},
                'scope': 'Four source ship mask families; no world picking, ownership or input dispatch',
                'excluded': ['rendered alpha is not a hit mask', 'fog', 'other object slots',
                             'world neighbour ordering', 'selection state', 'mouse integration']}
    return {'ShipHitMasks.bytes': bytes(payload)}, metadata


def stage(source_root, project, *, replace_generated=False):
    payloads, metadata = compose(source_root)
    return write_payloads(Path(project) / 'Assets/Resources/ShipPickingGenerated', payloads, metadata,
                          replace_generated, manifest_name=MANIFEST_NAME)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=ROOT / 'reference/raw/ancient-conquest')
    parser.add_argument('--project', type=Path, default=ROOT / 'Unity/AncientConquest')
    parser.add_argument('--replace-generated', action='store_true')
    args = parser.parse_args(argv)
    result = stage(args.source_root, args.project, replace_generated=args.replace_generated)
    print(json.dumps({'family_count': result['family_count'], 'mask_count': result['mask_count'],
                      'payloads': result['payloads']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
