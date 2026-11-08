"""Coupled original MoveShip calls for actual constructed0b/0c/0d on one grid.

Routes and their normal initial installation state are explicit inputs.
No path planner, request promotion, AI, full Life or rendering claim is made.
"""
from pathlib import Path
import argparse
import json
import struct

from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_EAX
from tools import probe_ship_move_order as original

ROOT = original.ROOT
BASE = 0x72000000
LOCAL = (11, 12, 13)
SIZE = {11: 56, 12: 56, 13: 72}
ACTORS = {11: original.OBJ, 12: BASE + 0x1000, 13: BASE + 0x3000}
SPRITES = {11: original.SPRITE, 12: BASE + 0x5000, 13: BASE + 0x6000}


class FleetOracle(original.WorkOracle):
    def __init__(self, routes, session_seed=0):
        self.current_id = 11
        self.fleet_ready = False
        super().__init__(session_seed=session_seed)
        self.u.mem_map(BASE, 0x20000)
        self.phase = 'init'
        records = original.SS.source_records(self.sources)
        self.records = {int(entry['name'][4:], 16): raw for entry, raw in records}
        self.pointer_ids = {ACTORS[i]: i for i in LOCAL}
        for index, (entry, raw) in enumerate(records):
            identifier = int(entry['name'][4:], 16)
            if identifier not in LOCAL:
                self.pointer_ids[original.S.CONTEXT + 0xa0000 + index * 0x1000] = identifier
        for identifier in (12, 13):
            self.current_id = identifier
            actor = ACTORS[identifier]
            self.call_actor(0x4dc3f0)
            for offset, value in ((0xc, original.APP), (0x10, original.APP), (0x4c, identifier),
                                  (0x68, original.APP), (0x6c, original.SYSTEM), (0x70, original.SYSTEM)):
                self.w(actor + offset, value)
            self.u.mem_write(original.PAYLOAD, self.records[identifier])
            self.call_actor(0x4dfa90, (original.PAYLOAD,))
            self.call_actor(0x4bece0)
        self.recipes = []
        for identifier in LOCAL:
            actor, sprite, size = ACTORS[identifier], SPRITES[identifier], SIZE[identifier]
            raw = self.records[identifier]
            x, y = struct.unpack_from('<ii', raw, 36)
            self.current_id = identifier
            self.w(actor + 0x8be, sprite)
            for offset, value in ((0x61, size), (0x65, size), (0x59, x * 64 + (64 - size) // 2),
                                  (0x5d, y * 64 + (64 - size) // 2), (0x45, raw[44] * 4), (0x7d, 2), (0x81, 0)):
                self.w(sprite + offset, value)
            self.w(actor + 0x18, session_seed * identifier)
            self.u.mem_write(actor + 0x5c, struct.pack('<hh', 0, 0))
            # Replace WorkOracle's selection-only placeholder before the real
            # source claim;499830 correctly refuses an already occupied cell.
            self.w(original.GRID + 8 + (y * 24 + x) * 24 + 4, 0)
            self.call_actor(0x499830, (0, actor, y * 24 + x))
            self.recipes.append({'id': identifier, 'size': size, 'class': self.r(actor + 0x50),
                                 'maximum_speed': self.r(actor + 0x59f), 'base_speed': self.r(actor + 0x27c),
                                 'initial_acceleration': self.r(actor + 0x280),
                                 'reservation_acceleration': self.call_actor(0x4ac110, (raw[28], 8, 0x5bb510, 100)),
                                 'capabilities': self.r(actor + 0x261), 'equipment_a': raw[60], 'medium': self.b(actor + 0x592)})
        self.fleet_ready = True
        self.publications_by_id = {i: [] for i in LOCAL}
        self.depth_by_id = {i: 20000 - SIZE[i] - (struct.unpack_from('<i', self.records[i], 40)[0] * 64 + (64 - SIZE[i]) // 2) for i in LOCAL}
        self.tail_by_id = {i: False for i in LOCAL}
        self.drawn_by_id = {i: {'frame': self.r(SPRITES[i] + 0x45), 'world': [self.signed(SPRITES[i] + 0x59), self.signed(SPRITES[i] + 0x5d)]} for i in LOCAL}
        self.phase = 'work'
        for identifier, points in zip(LOCAL, routes):
            self.install(identifier, points)

    def call_actor(self, address, arguments=()):
        top = original.S.STACK + original.S.STACK_SIZE - 0x1000
        for index, value in enumerate((original.S.END, *arguments)):
            self.w(top + index * 4, value)
        self.u.reg_write(UC_X86_REG_ESP, top)
        self.u.reg_write(UC_X86_REG_ECX, ACTORS[self.current_id])
        self.u.emu_start(address, original.S.END, count=500000)
        assert self.u.reg_read(UC_X86_REG_EIP) == original.S.END
        assert self.r(0x5d1f90) == 0xabcdef01
        return self.u.reg_read(UC_X86_REG_EAX)

    def hook(self, engine, address, size, unused):
        if self.fleet_ready and self.phase == 'work':
            identifier = self.current_id
            if address == 0x4a4d49:
                self.tail_by_id[identifier] = True
            if address == 0x50d130:
                self.depth_by_id[identifier] = self.r(engine.reg_read(UC_X86_REG_ESP) + 8)
            if address == 0x50d5f0:
                top = engine.reg_read(UC_X86_REG_ESP)
                row = {'frame': self.r(top + 8), 'world': [self.signed(top + 12), self.signed(top + 16)],
                       'depth': self.depth_by_id[identifier]}
                self.publications_by_id[identifier].append(row)
                self.drawn_by_id[identifier] = {'frame': row['frame'], 'world': row['world'].copy()}
        super().hook(engine, address, size, unused)

    def install(self, identifier, points):
        if not points:
            return
        actor = ACTORS[identifier]
        pointer = BASE + 0x10000 + (identifier - 11) * 0x1000
        raw = b''.join(struct.pack('<hhB', *point) for point in points)
        self.u.mem_write(pointer, raw)
        self.w(actor + 0x5c2, pointer)
        self.w(actor + 0x5ba, len(points))
        self.w(actor + 0x5be, 1)
        self.w(actor + 0x5b2, points[-1][1] * 24 + points[-1][0])
        heading = points[1][2]
        self.u.mem_write(actor + 0x5b1, bytes([heading]))
        aligned = heading == self.b(actor + 0x5af)
        self.u.mem_write(actor + 0x58c, bytes([3 if aligned else 2]))
        self.u.mem_write(actor + 0x596, bytes([aligned]))
        self.u.mem_write(actor + 0x5b0, b'\0')

    def snapshot(self, identifier):
        actor, sprite = ACTORS[identifier], SPRITES[identifier]
        signed = lambda offset: self.signed(actor + offset)
        return {'id': identifier, 'cell': [signed(0x5a3), signed(0x5a7)],
                'world': [self.signed(sprite + 0x59), self.signed(sprite + 0x5d)],
                'state': self.b(actor + 0x58c), 'center': self.b(actor + 0x596),
                'heading': self.b(actor + 0x5af), 'target_heading': self.b(actor + 0x5b1),
                'turn_step': struct.unpack('b', self.u.mem_read(actor + 0x5b0, 1))[0],
                'speed': signed(0x59b), 'remainder': signed(0x597), 'deceleration': signed(0x284),
                'reserved': signed(0x5ab), 'next': signed(0x5b6), 'last': signed(0x5b2),
                'path_index': signed(0x5be), 'path_count': signed(0x5ba),
                'frame': self.r(sprite + 0x45), 'frame_tick': self.r(sprite + 0x81),
                'state_tick': self.r(actor + 0x58d), 'rng': self.r(actor + 0x18),
                'acceleration': signed(0x280), 'retry': self.b(actor + 0x591),
                'tail': self.tail_by_id[identifier], 'drawn': self.drawn_by_id[identifier],
                'publications': self.publications_by_id[identifier].copy()}

    def step(self, identifier, counter, pending):
        self.current_id = identifier
        self.tick = counter
        self.w(original.SYSTEM + 0xde, counter)
        self.w(original.APP + 0xe2, pending)
        self.publications_by_id[identifier] = []
        self.tail_by_id[identifier] = False
        self.grid_writes.clear()
        self.call_actor(0x4a3f40)
        state = self.snapshot(identifier)
        state['grid'] = [[row['cell_index'], self.pointer_ids.get(int(row['after'], 16), 0)] for row in self.grid_writes]
        state['claims'] = [[index, self.pointer_ids[self.r(original.GRID + 8 + index * 24 + 4)]] for index in range(576) if self.r(original.GRID + 8 + index * 24 + 4)]
        return state


def fixture():
    straight = [[[16, 2, 5], [15, 3, 5]], [[21, 5, 4], [20, 5, 4], [19, 5, 4], [18, 5, 4]],
                [[19, 4, 4], [18, 4, 4], [17, 4, 4], [16, 4, 4]]]
    turns = [[[16, 2, 0], [17, 2, 0], [18, 3, 7], [19, 3, 0]],
             [[21, 5, 6], [21, 6, 6], [20, 7, 5], [19, 7, 4]],
             [[19, 4, 2], [19, 3, 2], [18, 3, 4], [17, 3, 4]]]
    blocked = [[[16, 2, 7], [17, 3, 7], [18, 4, 7], [19, 4, 0]], [], []]
    specifications = []
    for pending in (1, 2, 3, 7):
        for order in (LOCAL, LOCAL[::-1]):
            specifications.append(('straight-' + str(pending) + '-' + str(order[0]), straight, [pending], order, 0))
    for pending in (1, 3, 7):
        specifications.append(('crossing-turns-' + str(pending), turns, [pending], LOCAL, 0x12345678))
    specifications += [('mixed-pending', turns, [1, 2, 3, 7], LOCAL[::-1], 7),
                       ('blocked-endpoint', blocked, [1], LOCAL, 0),
                       ('blocked-endpoint-fast', blocked, [7], LOCAL[::-1], 7),
                       ('idle-only', [[], [], []], [1], LOCAL, 0xffffffff)]
    cases = []
    for label, routes, sequence, order, seed in specifications:
        oracle = FleetOracle(routes, seed)
        initial = [oracle.snapshot(i) for i in LOCAL]
        rows = []
        for counter in range(1, 151):
            pending = sequence[(counter - 1) % len(sequence)]
            for identifier in order:
                rows.append({'counter': counter, 'pending': pending, 'state': oracle.step(identifier, counter, pending)})
        cases.append({'label': label, 'routes': routes, 'session_seed': seed, 'order': list(order),
                      'initial': initial, 'rows': rows})
    return {'schema_version': 1, 'original_exe_sha256': original.EXPECTED, 'recipes': oracle.recipes,
            'seed_payloads': {str(i): oracle.records[i].hex() for i in LOCAL}, 'cases': cases,
            'scope': 'Actual ctor/load/upgrade of3local actors;prepared routes;shared grid;MoveShip only;wind0/5;no planning/promotion/fullLife'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = fixture()
    args.output.write_text(json.dumps(result, separators=(',', ':')) + '\n')
    print({'recipes': result['recipes'], 'cases': len(result['cases']), 'rows': sum(len(c['rows'])for c in result['cases'])})


if __name__ == '__main__':
    main()
