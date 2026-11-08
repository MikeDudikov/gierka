"""Execute original BaseSystem vtable, recursive C45E and SystemClass routing.

The application/system registry and child-handler records are explicit inputs
with source offsets. The final child callback is an observation boundary;
no OS input, world tick or graphics callback is executed.
"""
from pathlib import Path
import argparse
import json
import struct
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP
from tools import probe_wp_move as marker


class BaseDispatchOracle(marker.MarkerOracle):
    def __init__(self, active=1, handler_flags=0, patches=()):
        self.dispatch_ready = False
        self.received = []
        self.entries = []
        self.context_messages = []
        super().__init__()
        self.system = self.allocate(0x40)
        self.application = self.allocate(0x2000)
        self.registry = self.allocate(0x40)
        self.registration = self.allocate(12)
        self.handlers = self.allocate(0x40)
        self.handler_records = self.allocate(16)
        self.callback_records = self.allocate(32)
        self.callback_table = self.allocate(4)
        self.callback = self.allocate(16)
        self.message = self.allocate(32)
        # 4ee4f8..4ee507: MSystemClass(parent, id0), then BaseSystem vptr.
        self.w(self.system, 0x59b5e4)
        self.w(self.system + 0x14, 0)
        self.w(self.system + 0x18, self.application)
        self.w(self.system + 0x10, self.handlers)
        self.w(self.application + 0x10, self.registry)
        self.vector(self.registry, 12, 1, self.registration)
        self.w(self.registration, active)
        self.w(self.registration + 4, self.system)
        self.vector(self.handlers, 8, 2, self.handler_records)
        for i in range(2):
            record = self.callback_records + i * 16
            self.w(self.handler_records + i * 8, handler_flags if i == 0 else 0)
            self.w(self.handler_records + i * 8 + 4, record)
            self.w(record, self.callback_table)
            self.w(record + 4, 0x100)
        self.u.mem_write(self.callback, b'\xc2\x04\0')
        self.w(self.callback_table, self.callback)
        assert self.r(0x59b5e4 + 0x18) == 0x541ee0
        assert self.r(0x59b5e4 + 0x20) == 0x4eff00
        for address, before, after in patches:
            assert bytes(self.u.mem_read(address, len(before))) == before
            assert len(before) == len(after)
            self.u.mem_write(address, after)
        self.dispatch_ready = True

    def allocate(self, size):
        address = self.heap
        self.heap += (size + 15) & ~15
        assert self.heap < 0x72000000
        self.u.mem_write(address, bytes(size))
        return address

    def hook(self, engine, address, size, unused):
        if self.dispatch_ready:
            if address in (0x4ee900, 0x4efd60, 0x540540, 0x540560,
                           0x4eff00, 0x541ee0, 0x541f00, 0x541390,
                           0x540d20, 0x540cc0, 0x542490):
                self.entries.append(f'{address:06x}')
            if address in (0x540540, 0x540560):
                sp = engine.reg_read(UC_X86_REG_ESP)
                message = self.r(sp + (12 if address == 0x540560 else 4))
                kind = self.r(message + 0x10)
                if (address, kind) == (0x540560, 0x17):
                    words = list(struct.unpack('<8I', engine.mem_read(message, 32)))
                    rectangle = list(struct.unpack('<4i', engine.mem_read(words[5], 16)))
                    words[5] = None
                    self.context_messages.append(dict(words=words, route=[self.r(sp + 4), self.r(sp + 8)], rectangle=rectangle))
                    self.ret(12, 0)
                    return
                if (address, kind) == (0x540540, 0x14a):
                    self.context_messages.append(dict(words=list(struct.unpack('<8I', engine.mem_read(message, 32)))))
                    self.ret(4, 0)
                    return
            if address == self.callback:
                sp = engine.reg_read(UC_X86_REG_ESP)
                message = self.r(sp + 4)
                index = (engine.reg_read(UC_X86_REG_ECX) - self.callback_records) // 16
                assert index in (0, 1)
                self.received.append(dict(handler=index, words=list(struct.unpack('<8I', engine.mem_read(message, 32)))))
                self.ret(4, 0)
                return
        super().hook(engine, address, size, unused)

    def send(self, kind, value=0):
        self.received.clear()
        self.entries.clear()
        self.u.mem_write(self.message, struct.pack('<8I', 0, 0, 0, 0, kind, value, 0, 0))
        motion = marker.normal.pointer.motion
        sp = motion.S.STACK + motion.S.STACK_SIZE - 0x1000
        self.w(sp, motion.S.END)
        self.w(sp + 4, self.message)
        self.u.reg_write(UC_X86_REG_ESP, sp)
        self.u.reg_write(UC_X86_REG_ECX, self.system)
        self.u.emu_start(0x4eff00, motion.S.END, count=500000)
        assert self.u.reg_read(UC_X86_REG_EIP) == motion.S.END
        return dict(message=kind, value=value, stored=self.r(self.system + 0x20),
                    received=list(self.received), entries=list(self.entries))

    def run_context(self, gate, held, width, height):
        self.received.clear()
        self.entries.clear()
        self.context_messages.clear()
        self.w(self.application + 0x20, gate)
        self.w(self.application + 0xd91, width)
        self.w(self.application + 0xd95, height)
        self.w(self.system + 0x20, held)
        motion = marker.normal.pointer.motion
        sp = motion.S.STACK + motion.S.STACK_SIZE - 0x1000
        self.w(sp, motion.S.END)
        self.u.reg_write(UC_X86_REG_ESP, sp)
        self.u.reg_write(UC_X86_REG_ECX, self.application)
        self.u.emu_start(0x4ee900, motion.S.END, count=500000)
        assert self.u.reg_read(UC_X86_REG_EIP) == motion.S.END
        return dict(gate=gate, held=held, dimensions=[width, height],
                    stored=self.r(self.system + 0x20), root_gate=self.r(self.application + 0x20),
                    received=list(self.received), messages=list(self.context_messages), entries=list(self.entries))


def fixture(patches=()):
    rows = []
    for active in (0, 1, 0xffffffff):
        for flags in (0, 1):
            engine = BaseDispatchOracle(active, flags, patches)
            operations = [(0xc45e, 0), (0xc45d, 1), (0xc45e, 0), (0xc45e, 0),
                          (0xc45d, 0xffffffff), (0xc45e, 0), (0xc45d, 0)]
            rows.append(dict(active=active, first_handler_flags=flags,
                             operations=[engine.send(*op) for op in operations]))
    context_rows = []
    for active in (0, 1, 0xffffffff):
        engine = BaseDispatchOracle(active, 0, patches)
        for gate in (0, 1, 0xffffffff):
            for held in (0, 1, 0xffffffff):
                for width, height in ((800, 600), (1920, 1080), (0, 0), (-1, -1)):
                    context_rows.append(dict(active=active, **engine.run_context(gate, held, width, height)))
    return dict(schema_version=1, original_exe_sha256=marker.normal.pointer.gate.EXPECTED,
                vtable='59b5e4', constructor_assignment='4ee501',
                scope=__doc__, rows=rows, context_rows=context_rows, os_or_world_executed=False,
                rectangle_and_14a_recipients_are_boundaries=True,
                child_callback_is_boundary=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = fixture()
    args.output.write_text(json.dumps(result, separators=(',', ':')) + '\n')
    print(dict(cases=len(result['rows']), operations=sum(len(r['operations']) for r in result['rows']),
               context_cases=len(result['context_rows'])))


if __name__ == '__main__':
    main()
