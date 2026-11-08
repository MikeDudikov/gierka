"""Execute the original normal100/1 task and its real32-byte group events.

This is a fleet-level oracle, not a whole-world clock. Actor cells and physical
states are explicit inputs; actor Work, packet delivery and rendering are not
executed. Actual membership, event vectors, formation, task Work and serializer
execute x86. Only normal water ships, local owner5, patrol off, no interrupted
task/report or linked orders are represented.
"""
from pathlib import Path
import argparse
import base64
import itertools
import json
import struct

from unicorn.x86_const import UC_X86_REG_ESP
from tools import probe_ship_fleet_move_commands as source

ROOT = source.ROOT
pointer = source.pointer
LOCAL = source.membership.LOCAL


class TaskOracle(source.MoveOracle):
    def hook(self, engine, address, size, unused):
        if self.pointer_ready and address == 0x520c50:
            stack = engine.reg_read(UC_X86_REG_ESP)
            action = self.r(stack + 12) & 255
            if action == 35:
                # Real520c50 specifies22 bytes for35. Observe, do not replace it.
                self.commands.append({'actor': self.r(stack + 4), 'action': action,
                                      'payload_hex': bytes(engine.mem_read(self.r(stack + 16), 22)).hex()})
                return
        super().hook(engine, address, size, unused)

    def group(self):
        return self.r(pointer.GROUPS + 28)

    def snapshot_task(self):
        group = self.group()
        task = self.r(group + 0x25) if self.r(pointer.GROUPS + 12) else 0
        assignments = []
        if task and self.r(task + 0x24):
            vector = self.r(task + 0x24)
            assert self.r(vector + 8) == 20
            for i in range(self.r(vector + 12)):
                identifier, actor, x, y, reserved = struct.unpack('<IIiiI', self.u.mem_read(self.r(vector + 28) + i * 20, 20))
                assert self.r(actor + 0x4c) == identifier and reserved == 0
                assignments.append([identifier, x, y])
        events = []
        vector = self.r(group + 0x2d) if task else 0
        if vector:
            assert self.r(vector + 8) == 32
            events = [bytes(self.u.mem_read(self.r(vector + 28) + i * 32, 32)).hex()
                      for i in range(self.r(vector + 12))]
        slots = []
        if self.r(pointer.GROUPS + 12):
            members = self.r(group + 0x31)
            needed = max([self.r(members + 12)] + [struct.unpack_from('<I', bytes.fromhex(e), 8)[0] + 1
                                                for e in events if e.startswith('2c010000')])
            assert needed <= self.r(members + 16)
            for i in range(needed):
                ordinal = self.r(self.r(members + 28) + i * 4)
                slots.append(LOCAL[ordinal] if ordinal < len(LOCAL) else 0)
        membership = self.snapshot_membership()
        return {'age': self.r(group + 8), 'task': list(struct.unpack('<7I', self.u.mem_read(task, 28))) if task else None,
                'assignments': assignments, 'events': events, 'event_slots': slots,
                'groups': [g['members'] for g in membership['groups']], 'actors': membership['actors'],
                'commands': [dict(p) for p in self.commands]}

    def perform(self, op):
        self.commands.clear()
        if op[0] == 'C':
            self.commit(op[1:])
        elif op[0] == 'R':
            _, map_name, x, y, counter = op
            cells = source.formation.mission_terrain() if map_name == 'mission' else [-1] * 576
            self.u.mem_write(self.r(0x5c93bc), struct.pack('<576h', *cells))
            request = pointer.BASE + 0x58000
            self.u.mem_write(request, struct.pack('<4i', x, y, 1, 0))
            self.w(pointer.motion.SYSTEM + 0xde, counter)
            self.invoke_fleet(0x4ccc30, (5, 0, self.group(), request))
        elif op[0] == 'T':
            _, pending, counter = op
            self.w(pointer.motion.SYSTEM + 0xde, counter)
            self.w(pointer.motion.SYSTEM + 0xe2, pending)
            self.invoke_fleet(0x4c4f40, (5, 0, self.group()))
        elif op[0] == 'S':
            _, identifier, counter = op
            self.w(pointer.motion.SYSTEM + 0xde, counter)
            self.release(5, identifier, flags=4)
        elif op[0] == 'P':
            _, identifier, x, y, state = op
            self.w(self.actors[identifier] + 0x5a3, x)
            self.w(self.actors[identifier] + 0x5a7, y)
            self.u.mem_write(self.actors[identifier] + 0x58c, bytes([state]))
        elif op[0] == 'A':
            self.w(self.group() + 8, op[1])
        elif op[0] == 'X':
            self.invoke_fleet(0x4a1c60, (5, self.group()))
        else:
            raise AssertionError(op)
        return self.snapshot_task()


def specifications():
    for count in (1, 2, 3):
        for members in itertools.permutations(LOCAL, count):
            for map_name in ('mission', 'blocked'):
                yield {'label': f'initial-{members}-{map_name}', 'operations': [
                    ['C', *members], ['R', map_name, 18, 5, 123], ['T', 100, 124],
                    ['T', 1, 125], ['T', 7, 126], ['T', 1, 127]]}
    # The test inputs deliberately isolate >100, pre-increment, unsigned wrap,
    # idle-only and Chebyshev-distance >1. No actor physics is claimed here.
    for age in (0, 99, 100, 101, 102, 0xffffffff):
        for pending in (0, 1, 2, 3, 7, 0xffffffff):
            yield {'label': f'clock-{age}-{pending}', 'operations': [
                ['C', 11], ['R', 'mission', 18, 5, 0xffffffff], ['A', age],
                ['T', pending, 0], ['T', 1, 1]]}
    for state in range(7):
        for dx, dy in ((0, 0), (1, 1), (-1, -1), (2, 0), (0, -2), (-2, 2)):
            yield {'label': f'idle-distance-{state}-{dx}-{dy}', 'operations': [
                ['C', 13], ['R', 'mission', 18, 5, 25], ['P', 13, 18 + dx, 5 + dy, state],
                ['A', 101], ['T', 3, 26]]}
    yield {'label': 'same-task-replacements-and-clear-preserve-group-age', 'operations': [
        ['C', 11, 12, 13], ['R', 'mission', 18, 5, 5], ['T', 100, 6],
        ['R', 'mission', 20, 4, 7], ['T', 1, 8], ['R', 'blocked', 0, 0, 9], ['T', 1, 10],
        ['X'], ['T', 7, 11], ['R', 'mission', 18, 5, 12], ['T', 1, 13]]}
    for start in ((11,), (11, 12), (11, 12, 13), (13, 12, 11)):
        for map_name in ('mission', 'blocked'):
            others = [i for i in LOCAL if i not in start]
            edits = [*others, *start, *LOCAL, *LOCAL[::-1]]
            operations = [['C', *start], ['R', map_name, 18, 5, 10], ['A', 101]]
            for index, identifier in enumerate(edits):
                operations.append(['S', identifier, 20 + index])
                if index % 3 == 2:
                    operations.append(['T', 1, 50 + index])
            operations += [['T', 7, 90], ['T', 1, 91], ['X']]
            yield {'label': f'live-edits-{start}-{map_name}', 'operations': operations}
    yield {'label': 'all-members-removed-task-and-stale-assignments-remain', 'operations': [
        ['C', 11, 12, 13], ['R', 'mission', 18, 5, 0], ['S', 11, 1], ['S', 12, 2], ['S', 13, 3],
        ['A', 101], ['T', 1, 4], ['T', 7, 5], ['S', 13, 6], ['T', 1, 7]]}
    yield {'label': 'stale-add-index-resolved-by-id-after-removal', 'operations': [
        ['C', 11], ['R', 'mission', 18, 5, 0], ['S', 12, 1], ['S', 13, 2], ['S', 11, 3],
        ['A', 101], ['T', 1, 4], ['S', 12, 5], ['S', 13, 6], ['T', 1, 7]]}
    for map_name in ('mission', 'blocked'):
        yield {'label': f'retained-tail-can-resolve-removed-actor-{map_name}', 'operations': [
            ['C', 11], ['R', map_name, 18, 5, 0], ['S', 12, 1], ['S', 13, 2], ['S', 13, 3],
            ['T', 1, 4], ['S', 12, 5], ['S', 11, 6], ['T', 1, 7]]}
    for x, y in ((-2147483630, 5), (18, -2147483643), (2147483647, -2147483648)):
        yield {'label': f'int32-distance-{x}-{y}', 'operations': [
            ['C', 11], ['R', 'mission', 18, 5, 0], ['P', 11, x, y, 0], ['A', 101], ['T', 1, 1]]}


def fixture():
    metadata = source.membership.hover.source_metadata()
    rows = []
    for specification in specifications():
        oracle = TaskOracle(metadata)
        states = [{'operation': op, 'after': oracle.perform(op)} for op in specification['operations']]
        rows.append({'label': specification['label'], 'states': states})
    return {'schema_version': 1, 'original_exe_sha256': pointer.gate.EXPECTED,
            'terrain_base64': base64.b64encode(struct.pack('<576h', *source.formation.mission_terrain())).decode(),
            'cases': rows, 'scope': __doc__,
            'entries': ['0x4ccc30', '0x4c4f40', '0x4ccd80', '0x4cc6a0', '0x4cc590',
                        '0x4cc970', '0x4cc760', '0x4cc7d0', '0x49e850', '0x4a1340', '0x4a1770', '0x4dc600', '0x4a1c60'],
            'boundaries': ['MoveOracle constructor/CRT/selection-render/disabled-audio boundaries unchanged',
                           'Real source32-byte events and20-byte assignment vectors, with pointers normalized by actor ID',
                           'Explicit cell/state/clock inputs; no actor Work, packet delivery or app/fleet/world scheduling claim',
                           'Patrol disabled and interrupted-task flag0 for all actors; queued subtype2 and AI excluded']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = fixture()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, separators=(',', ':')) + '\n')
    print({'cases': len(data['cases']), 'states': sum(len(c['states']) for c in data['cases'])})


if __name__ == '__main__':
    main()
