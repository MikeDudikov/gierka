"""Original560090: homogeneous normal-water formation, with full field evidence."""
from pathlib import Path
import argparse
import base64
import json
import struct
import itertools

from unicorn import UC_HOOK_CODE
from tools import validate_source_wave_field as wave

ROOT = wave.ROOT
RECORDS = wave.source.CONTEXT + 0x40000


class NativeFormation(wave.NativeWave):
    def __init__(self):
        super().__init__()
        self.uc.mem_map(0, 0x1000)  # Isolated original SEH chain head (FS:0).
        self.trace = []
        self.returns = {}
        for address in (0x589bc6, 0x560090, 0x55f800, 0x560f10, 0x5612f0, 0x5732e0, 0x5578a0,
                        0x55f9f0, 0x55fa6d):
            self.uc.hook_add(UC_HOOK_CODE, self.formation_hook, begin=address, end=address)
        # Return PCs for wave/component calls are observed, never replaced.
        self.uc.hook_add(UC_HOOK_CODE, self.return_hook, begin=0x560090, end=0x560f0f)

    def formation_hook(self, engine, address, size, unused):
        sp = engine.reg_read(self.ESP)
        if address == 0x589bc6:
            self._return(0)
            return
        if address in (0x55f9f0, 0x55fa6d):
            self.heading_updates[0 if address == 0x55f9f0 else 1] += 1
        if address in (0x5578a0, 0x5732e0):
            pointer, width = self.get(sp + 4), self.get(sp + 8)
            self.returns[self.get(sp)] = (address, pointer, width)
        if address in (0x55f800, 0x560f10):
            context = self.get(sp + 4)
            self.trace.append({'entry': hex(address), 'origin': [self.get(context + 60), self.get(context + 64)],
                               'goal': [self.get(context + 68), self.get(context + 72)]})

    def return_hook(self, engine, address, size, unused):
        pending = self.returns.pop(address, None)
        if pending is not None:
            entry, pointer, width = pending
            self.trace.append({'entry': hex(entry), 'field_base64': base64.b64encode(bytes(engine.mem_read(pointer, self.area * 2))).decode()})

    def plan(self, width, height, cells, goal, origins):
        self.services = []
        self.allocations = {}
        self.next_heap = self.heap
        self.trace = []
        self.returns = {}
        self.area = width * height
        self.heading_updates = [0, 0]
        self.uc.mem_write(self.map_address, struct.pack('<' + 'h' * self.area, *cells))
        rows = [[x, y, 0, 1, 0, 0, 0, 0, 0] for x, y in origins]
        self.uc.mem_write(RECORDS, b''.join(struct.pack('<9i', *row) for row in rows))
        result = self.invoke(0x560090, [0, self.map_address, 0, width, height, -1, -1,
                                      *goal, RECORDS, len(rows), 0])
        result = struct.unpack('<i', struct.pack('<I', result))[0]
        return {'result': result,
                'records': [list(struct.unpack('<9i', self.uc.mem_read(RECORDS + 36 * index, 36))) for index in range(len(rows))],
                'reserved_base64': base64.b64encode(bytes(self.uc.mem_read(self.map_address, self.area * 2))).decode(),
                'trace': self.trace, 'heading_updates': self.heading_updates}


def mission_terrain():
    from tools.probe_ship_move_order import WorkOracle
    original = WorkOracle()
    raw = bytes(original.u.mem_read(original.r(0x5c93bc), 1152))
    assert wave.hashlib.sha256(raw).hexdigest() == '3cc7c7ac49d9fd0512557cd909adad4c346db59705e0ff3ae047ff54b906843e'
    return struct.unpack('<576h', raw)


def specifications():
    maps = {'mission': {'width': 24, 'height': 24, 'cells': list(mission_terrain())}}
    cases = []
    positions = ([16, 2], [21, 5], [19, 4])
    def add(name, origins, goal, group):
        cases.append({'map': name, 'origins': list(origins), 'goal': list(goal), 'group': group})
    for count in (2, 3):
        for origins in itertools.combinations(positions, count):
            for y in range(24):
                for x in range(24):
                    add('mission', origins, [x, y], 'mission-all-cells')
    goals = [[i % 24, i // 24] for i in range(0, 576, 37)] + [[18, 5], [19, 4], [0, 0], [23, 23]]
    for count in (2, 3):
        for origins in itertools.permutations(positions, count):
            if tuple(origins) in tuple(itertools.combinations(positions, count)):
                continue
            for goal in goals:
                add('mission', origins, goal, 'ordered-members')
    rng = wave.Lcg(0x9b7c3a12)
    for width, height in ((3, 3), (5, 7), (9, 9), (24, 24)):
        name = 'open-' + str(width) + 'x' + str(height)
        maps[name] = {'width': width, 'height': height, 'cells': [0] * (width * height)}
        for count in (2, 3, 4, 8):
            origins = [[i % width, i // width] for i in range(count)]
            for index in range(width * height) if width * height <= 35 else range(0, width * height, max(1, width * height // 20)):
                add(name, origins, [index % width, index // width], 'open-even-odd-counts')
    for sample in range(24):
        width, height = 9, 9
        name = 'obstacles-' + str(sample)
        density = (sample % 4) * 20
        cells = [-1 if (rng.next() >> 16) % 100 < density else 0 for _ in range(width * height)]
        free = [i for i, cell in enumerate(cells) if cell == 0]
        origins = [[index % width, index // width] for index in free[::max(1, len(free) // 3)][:3]]
        maps[name] = {'width': width, 'height': height, 'cells': cells}
        for index in range(0, 81, 9):
            add(name, origins, [index % width, index // width], 'obstacles-and-blocked-median')
    for goal in ([-1, 0], [24, 0], [0, -1], [0, 24]):
        add('mission', positions, goal, 'source-invalid-goal')
    return maps, cases


def fixture():
    maps, cases = specifications()
    native = NativeFormation()
    for case in cases:
        data = maps[case['map']]
        case['after'] = native.plan(data['width'], data['height'], data['cells'], case['goal'], case['origins'])
    for data in maps.values():
        cells = data.pop('cells')
        data['input_base64'] = base64.b64encode(struct.pack('<' + 'h' * len(cells), *cells)).decode()
    return {'schema_version': 1, 'original_exe_sha256': wave.gate.EXPECTED, 'maps': maps, 'cases': cases,
            'scope': 'Category0 normal water ships,2..8 members,explicit current cells;original560090 and helpers;no action20/Work',
            'algorithm_intercepts': [], 'services': ['bounded allocation/reallocation/free', 'isolated FS:0 SEH head']}


def full_wave_fixture():
    native = wave.NativeWave()
    rows = []
    for width in (1, 2, 3):
        height = width
        for mask in range(1 << (width * height)):
            cells = [-1 if mask >> index & 1 else 0 for index in range(width * height)]
            raw = struct.pack('<' + 'h' * len(cells), *cells)
            for index in range(len(cells)):
                after = native.wave(width, height, [index % width, index // width], [-1, -1], cells)
                rows.append({'width': width, 'height': height, 'seed': [index % width, index // width],
                             'input_base64': base64.b64encode(raw).decode(),
                             'result': after['result'], 'output_base64': after['output_base64']})
    cells = mission_terrain()
    raw = base64.b64encode(struct.pack('<576h', *cells)).decode()
    for index in range(576):
        after = native.wave(24, 24, [index % 24, index // 24], [-1, -1], cells)
        rows.append({'width': 24, 'height': 24, 'seed': [index % 24, index // 24], 'input_base64': raw,
                     'result': after['result'], 'output_base64': after['output_base64']})
    return {'schema_version': 1, 'original_exe_sha256': wave.gate.EXPECTED, 'cases': rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    data = fixture()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(data, separators=(',', ':')) + '\n')
    print({'cases': len(data['cases']), 'maps': len(data['maps'])})


if __name__ == '__main__':
    main()
