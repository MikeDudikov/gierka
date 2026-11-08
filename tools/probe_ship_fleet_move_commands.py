"""Actual fleet41->formation->20 serialization and per-actor pending reception."""
from pathlib import Path
import argparse
import base64
import itertools
import json
import struct

from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP
from tools import probe_ship_fleet_membership as membership
from tools import probe_ship_pointer_commands as pointer
from tools import probe_source_fleet_formation as formation

ROOT = membership.ROOT


class MoveOracle(membership.MembershipOracle):
    def __init__(self, metadata):
        super().__init__(metadata)
        self.w(self.actors[13] + 0x261, 0xfffffeff)

    def pending_snapshot(self):
        rows = []
        for identifier in membership.LOCAL:
            actor = self.actors[identifier]
            ui, simulation = struct.unpack('<hh', self.u.mem_read(actor + 0x5c, 4))
            rows.append([identifier, ui, simulation, self.r(actor + 0x7d6),
                         bytes(self.u.mem_read(actor + 0x858, 26)).hex()])
        return rows

    def consume_packet(self, packet):
        motion = pointer.motion
        self.w(motion.MESSAGE + 16, 0x280f)
        self.w(motion.MESSAGE + 20, motion.ACTION)
        self.u.mem_write(motion.ACTION + 12, bytes([packet['action']]))
        self.w(motion.ACTION + 13, motion.DATA)
        self.u.mem_write(motion.DATA, bytes.fromhex(packet['payload_hex']))
        sp = motion.S.STACK + motion.S.STACK_SIZE - 0x1000
        self.w(sp, motion.S.END)
        self.w(sp + 4, motion.MESSAGE)
        self.u.reg_write(UC_X86_REG_ESP, sp)
        self.u.reg_write(UC_X86_REG_ECX, self.actors[packet['actor']])
        self.u.emu_start(0x4dc630, motion.S.END, count=100000)
        assert self.u.reg_read(UC_X86_REG_EIP) == motion.S.END
        assert self.r(0x5d1f90) == 0xabcdef01
        return self.pending_snapshot()


def fixture():
    cells = list(formation.mission_terrain())
    free = [index for index, value in enumerate(cells) if value == 0]
    goals = [[index % 24, index // 24] for index in free[::max(1, len(free) // 12)]]
    goals += [[18, 5], [19, 4]]
    metadata = membership.hover.source_metadata()
    cases = []
    for count in (1, 2, 3):
        for identifiers in itertools.permutations(membership.LOCAL, count):
            inputs = [('mission', goal) for goal in goals]
            if count > 1:
                inputs.append(('blocked', [18, 5]))
            for map_name, goal in inputs:
                oracle = MoveOracle(metadata)
                oracle.commit(identifiers)
                if map_name == 'blocked':
                    oracle.u.mem_write(oracle.r(0x5c93bc), b'\xff' * 1152)
                group = oracle.r(pointer.GROUPS + 28)
                request = pointer.BASE + 0x58000
                oracle.u.mem_write(request, struct.pack('<4i', *goal, 1, 0))
                oracle.invoke_fleet(0x4ccc30, (5, 0, group, request))
                commands = [dict(packet) for packet in oracle.commands]
                assert [packet['action'] for packet in commands] == [41] * count + [20] * count
                states = [oracle.pending_snapshot()]
                for packet in commands:
                    states.append(oracle.consume_packet(packet))
                cases.append({'map': map_name, 'members': list(identifiers), 'goal': goal,
                              'commands': commands, 'states': states})
    return {'schema_version': 1, 'original_exe_sha256': pointer.gate.EXPECTED,
            'terrain_base64': base64.b64encode(struct.pack('<576h', *cells)).decode(),
            'origins': [[16, 2], [21, 5], [19, 4]], 'local_ids': list(membership.LOCAL), 'cases': cases,
            'scope': 'Normal Mode10 first commit,task100/subtype1,all ordered local subsets;41 then20 then per-actor receipt;no promotion/Work',
            'entries': ['0x49ca60', '0x4ccc30', '0x4cc500', '0x4cc970', '0x560090', '0x4cc8c0',
                        '0x4cf070', '0x4cc650', '0x520c50', '0x5593a0', '0x4dc630', '0x4e2ba0', '0x50c970'],
            'boundaries': 'Existing MembershipOracle constructor/CRT/renderer/disabled-audio boundaries;no replaced formation/dispatch/serializer/consumer'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = fixture()
    args.output.write_text(json.dumps(data, separators=(',', ':')) + '\n')
    print({'cases': len(data['cases']), 'states': sum(len(case['states']) for case in data['cases'])})


if __name__ == '__main__':
    main()
