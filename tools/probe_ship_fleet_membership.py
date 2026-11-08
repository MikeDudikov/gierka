"""Execute normal Mode10 fleet conversion, reassignment and action41 reception.

No formation/Work step is executed. The temporary vector is an explicit input;
49ca60,49b990,49bd60,49bef0,520c50,5593a0 and actor GetMessage run original x86.
"""
from pathlib import Path
import argparse
import itertools
import json
import struct
import sys
from unittest.mock import patch

from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP
from tools import probe_ship_pending_selection as pending
from tools import probe_ship_pointer_commands as pointer
from tools import probe_ship_pointer_hover as hover

ROOT = pending.ROOT
LOCAL = pending.LOCAL


class MembershipOracle(pending.PendingOracle):
    def __init__(self, metadata=None):
        metadata = hover.source_metadata() if metadata is None else metadata
        # Cache only immutable upstream actor metadata within one fixture run.
        # Every case still initializes and executes a fresh original x86 engine.
        # BoxOracle otherwise decodes/hashes the same sprite catalogue twice.
        with patch.object(pending.box, 'source_metadata', return_value=metadata):
            super().__init__()
        # Actor registry ordinal is not an actor instance ID. BoxOracle's cloned
        # selection actors did not require unique ordinals or current cells.
        for index, identifier in enumerate(LOCAL):
            self.w(self.actors[identifier] + 0x58, index)
        for actor in metadata:
            self.w(self.actors[actor['id']] + 0x5a3, actor['cell'][0])
            self.w(self.actors[actor['id']] + 0x5a7, actor['cell'][1])
        # Fixed owned backing store has room for64 source61-byte group records.
        self.w(pointer.GROUPS + 16, 64)
        self.w(pointer.GROUPS + 20, 64)
        self.consumed = 0
        assert self.r(pointer.FLEET + 0x112 + 5 * 4) == 0

    def commit(self, identifiers):
        self.w(pointer.SELECTED + 12, len(identifiers))
        for index, identifier in enumerate(identifiers):
            self.w(pointer.SELECTED_DATA + 4 * index, self.actors[identifier])
        self.invoke_fleet(0x49ca60, (5,))
        result = struct.unpack('<i', struct.pack('<I', self.u.reg_read(UC_X86_REG_EAX)))[0]
        return self.snapshot_membership(result)

    def consume(self):
        packet = self.commands[self.consumed]
        assert packet['action'] == 41
        self.consumed += 1
        motion = pointer.motion
        self.w(motion.MESSAGE + 0x10, 0x280f)
        self.w(motion.MESSAGE + 0x14, motion.ACTION)
        self.u.mem_write(motion.ACTION + 0xc, b'\x29')
        self.w(motion.ACTION + 0xd, motion.DATA)
        self.u.mem_write(motion.DATA, bytes.fromhex(packet['payload_hex']))
        sp = motion.S.STACK + motion.S.STACK_SIZE - 0x1000
        self.w(sp, motion.S.END)
        self.w(sp + 4, motion.MESSAGE)
        self.u.reg_write(UC_X86_REG_ESP, sp)
        self.u.reg_write(UC_X86_REG_ECX, self.actors[packet['actor']])
        self.u.emu_start(0x4dc630, motion.S.END, count=100000)
        assert self.u.reg_read(UC_X86_REG_EIP) == motion.S.END
        assert self.r(0x5d1f90) == 0xabcdef01
        return self.snapshot_membership()

    def snapshot_membership(self, result=None):
        groups = []
        for index in range(self.r(pointer.GROUPS + 12)):
            group = self.r(pointer.GROUPS + 28) + index * 61
            vector = self.r(group + 0x31)
            members = [self.r(self.r(vector + 28) + 4 * n) for n in range(self.r(vector + 12))]
            groups.append({'mode': self.r(group), 'serial': self.r(group + 12), 'members': members})
        actors = []
        for identifier in LOCAL:
            actor = self.actors[identifier]
            ui, sim = struct.unpack('<hh', self.u.mem_read(actor + 0x5c, 4))
            actors.append({'id': identifier, 'ui_group': ui, 'simulation_group': sim,
                           'member_index': self.r(actor + 0x60)})
        return {'result': result, 'current_group': self.signed(pointer.FLEET + 0xc2 + 5 * 4),
                'groups': groups, 'actors': actors, 'consumed': self.consumed,
                'commands': [dict(command) for command in self.commands]}


def cases():
    orders = [list(order) for count in range(4) for order in itertools.permutations(LOCAL, count)]
    for first in orders:
        for second in orders:
            yield {'label': 'two-commits-' + '-'.join(map(str, first)) + '--' + '-'.join(map(str, second)),
                   'operations': [['C', *first], ['N'], ['C', *second], ['A']]}
    # Source keeps emptied groups in this normal local-owner configuration.
    yield {'label': 'repeated-reordering-and-empty-groups',
           'operations': [operation for index in range(32) for operation in
                          (['C', *orders[1 + index % 15]], ['N'] if index % 3 == 0 else ['Z'])] + [['A']]}
    yield {'label': 'all-ui-reassignments-before-any-reception',
           'operations': [['C', *order] for order in orders] + [['A']]}


def fixture():
    rows = []
    metadata = hover.source_metadata()
    for case in cases():
        oracle = MembershipOracle(metadata)
        states = []
        for operation in case['operations']:
            if operation[0] == 'C':
                states.append({'operation': operation, 'after': oracle.commit(operation[1:])})
            elif operation[0] == 'N':
                if oracle.consumed < len(oracle.commands):
                    states.append({'operation': ['D'], 'after': oracle.consume()})
            elif operation[0] == 'A':
                while oracle.consumed < len(oracle.commands):
                    states.append({'operation': ['D'], 'after': oracle.consume()})
        rows.append({'label': case['label'], 'states': states})
        if len(rows) % 64 == 0:
            print('Native fleet membership cases completed: ' + str(len(rows)), file=sys.stderr, flush=True)
    return {'schema_version': 1, 'original_exe_sha256': pointer.gate.EXPECTED,
            'local_ids': list(LOCAL), 'registry_indices': [0, 1, 2], 'cases': rows,
            'entries': ['0x49ca60', '0x49b990', '0x49bd60', '0x49bef0', '0x520c50',
                        '0x5593a0', '0x4dc630', '0x50c970'],
            'scope': 'Normal local ships; Mode10; no active group task; auto-delete-empty off; explicit temporary-vector input; action41 only',
            'boundaries': ['PendingOracle constructor/CRT/render/audio boundaries unchanged',
                           'Unique source actor-registry ordinals and real source cells assigned before dispatch',
                           'No simulated membership writes or replaced fleet/serializer/consumer functions',
                           'No formation, action20, Work, rendering or OS-input claim']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    data = fixture()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(data, indent=2) + '\n')
    print({'cases': len(data['cases']), 'states': sum(len(case['states']) for case in data['cases'])})


if __name__ == '__main__':
    main()
