"""Original4ee900 gate and4efd60 rectangle/C45E/14A producer;recipients are boundaries."""
from pathlib import Path
import argparse
import json
import struct
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_ECX, UC_X86_REG_EIP
from tools import probe_wp_move as marker


class ContextOracle(marker.MarkerOracle):
    def __init__(self, patches=()):
        self.context_ready = False
        self.messages = []
        super().__init__()
        self.context = self.heap
        self.heap += 0x2000
        self.u.mem_write(self.context, bytes(0x2000))
        self.context_ready = True
        for address, before, after in patches:
            assert bytes(self.u.mem_read(address, len(before))) == before
            assert len(before) == len(after)
            self.u.mem_write(address, after)

    def hook(self, engine, address, size, unused):
        if self.context_ready and address in (0x540540, 0x540560):
            sp = engine.reg_read(UC_X86_REG_ESP)
            if address == 0x540560:
                route = [self.r(sp + 4), self.r(sp + 8)]
                message = self.r(sp + 12)
                rectangle = list(struct.unpack('<4i', engine.mem_read(self.r(message + 0x14), 16)))
                words = list(struct.unpack('<8I', engine.mem_read(message, 32)))
                words[5] = None
                self.messages.append(dict(route=route, words=words, rectangle=rectangle))
                self.ret(12, 0)
            else:
                message = self.r(sp + 4)
                self.messages.append(dict(route=None, words=list(struct.unpack('<8I', engine.mem_read(message, 32)))))
                self.ret(4, 0)
            return
        super().hook(engine, address, size, unused)

    def run_context(self, gate, width, height):
        self.messages.clear()
        self.w(self.context + 0x20, gate)
        self.w(self.context + 0xd91, width)
        self.w(self.context + 0xd95, height)
        motion = marker.normal.pointer.motion
        sp = motion.S.STACK + motion.S.STACK_SIZE - 0x1000
        self.w(sp, motion.S.END)
        self.u.reg_write(UC_X86_REG_ESP, sp)
        self.u.reg_write(UC_X86_REG_ECX, self.context)
        self.u.emu_start(0x4ee900, motion.S.END, count=100000)
        assert self.u.reg_read(UC_X86_REG_EIP) == motion.S.END
        assert self.r(self.context + 0x20) == gate
        return dict(gate=gate, dimensions=[width, height], messages=list(self.messages))


def fixture(patches=()):
    oracle = ContextOracle(patches)
    return dict(schema_version=1, original_exe_sha256=marker.normal.pointer.gate.EXPECTED,
                rows=[oracle.run_context(gate, width, height)
                      for gate in (0, 1, 0xffffffff)
                      for width, height in ((800, 600), (1920, 1080), (0, 0), (-1, -1))],
                scope=__doc__, source_entries=['4ee900', '4efd60'],
                recipient_boundaries=['540540', '540560'], tick_or_world_executed=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = fixture()
    args.output.write_text(json.dumps(result, separators=(',', ':')) + '\n')
    print(dict(cases=len(result['rows']), messages=sum(len(row['messages']) for row in result['rows'])))


if __name__ == '__main__':
    main()
