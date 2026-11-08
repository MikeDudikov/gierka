"""Original C45E producer/routing/fleet callback hides graphics without changing its route."""
from pathlib import Path
import argparse
import json
import struct
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP
from tools import probe_ship_fleet_queued as queued


class ContextFleetOracle(queued.QueuedOracle):
    def __init__(self):
        self.context_ready = False
        self.visibility_messages = []
        super().__init__()
        self.context_app = self.allocate(0x2000)
        self.context_system = self.allocate(0x40)
        self.registry = self.allocate(0x40)
        self.registration = self.allocate(12)
        self.handlers = self.allocate(0x40)
        self.handler = self.allocate(8)
        self.context_message = self.allocate(32)
        self.w(self.context_system, 0x59b5e4)
        self.w(self.context_system + 0x18, self.context_app)
        self.w(self.context_system + 0x10, self.handlers)
        self.w(self.context_app + 0x10, self.registry)
        self.w(self.context_app + 0xd91, 1920)
        self.w(self.context_app + 0xd95, 1080)
        self.vector(self.registry, 12, 1, self.registration)
        self.w(self.registration, 1)
        self.w(self.registration + 4, self.context_system)
        self.vector(self.handlers, 8, 1, self.handler)
        self.w(self.handler + 4, queued.pointer.FLEET)
        self.w(queued.pointer.FLEET + 4, 0x100)
        self.context_ready = True

    def allocate(self, size):
        address = self.heap
        self.heap += (size + 15) & ~15
        assert self.heap < 0x72000000
        self.u.mem_write(address, bytes(size))
        return address

    def hook(self, engine, address, size, unused):
        if self.context_ready:
            sp = engine.reg_read(UC_X86_REG_ESP)
            if address == 0x49ab30:
                message = self.r(sp + 4)
                if self.r(message + 0x10) == 0xc45d:
                    self.visibility_messages.append(list(struct.unpack('<8I', engine.mem_read(message, 32))))
            if address == 0x540560 and self.r(self.r(sp + 12) + 0x10) == 0x17:
                self.ret(12, 0)
                return
            if address == 0x540540 and self.r(self.r(sp + 4) + 0x10) == 0x14a:
                self.ret(4, 0)
                return
        super().hook(engine, address, size, unused)

    def invoke_context(self, entry, receiver, args=()):
        motion = queued.pointer.motion
        sp = motion.S.STACK + motion.S.STACK_SIZE - 0x1000
        for i, value in enumerate((motion.S.END, *args)):
            self.w(sp + 4 * i, value)
        self.u.reg_write(UC_X86_REG_ESP, sp)
        self.u.reg_write(UC_X86_REG_ECX, receiver)
        self.u.emu_start(entry, motion.S.END, count=1000000)
        assert self.u.reg_read(UC_X86_REG_EIP) == motion.S.END

    def key(self, value):
        self.u.mem_write(self.context_message, struct.pack('<8I', 0, 0, 0, 0, 0xc45d, value, 0, 0))
        self.invoke_context(0x4eff00, self.context_system, (self.context_message,))

    def context(self, gate, registration):
        self.w(self.context_app + 0x20, gate)
        self.w(self.registration, registration)
        self.commands.clear()
        self.visibility_messages.clear()
        self.invoke_context(0x4ee900, self.context_app)
        state = self.snapshot_queued()
        return dict(gate=gate, registration=registration, stored=self.r(self.context_system + 0x20),
                    forwarded=list(self.visibility_messages), state=state)


def fixture():
    engine = ContextFleetOracle()
    engine.run(('select', 11, 12, 13))
    engine.run(('shift', 18, 6, 0))
    engine.run(('shift', 16, 4, 0))
    engine.key(1)
    rows = [engine.context(*pair) for pair in ((1, 1), (0, 0), (0, 1), (0, 1))]
    return dict(schema_version=1, original_exe_sha256=queued.pointer.gate.EXPECTED, rows=rows,
                scope=__doc__, source_entries=['4ee900', '540540', '540560', '4eff00', '541ee0', '541f00', '49ab30', '4a2050', '4cef10'],
                lower_graphics_constructor_and_destructor_are_boundaries=True,
                world_or_tick_executed=False, physical_os_input_executed=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = fixture()
    args.output.write_text(json.dumps(result, separators=(',', ':')) + '\n')
    print([(r['gate'], r['registration'], r['stored'], len(r['forwarded']),
            [p['marker'] is not None for p in r['state']['route']['points']]) for r in result['rows']])


if __name__ == '__main__':
    main()
