"""Execute original4ee970 WM_ACTIVATEAPP and real C45E producer/recipient chain.

Window cursor imports and scene restoration are observation boundaries. Empty
OS-message decoders and disabled audio/DirectDraw configuration are explicit
inputs;source decoding,activation flags,render flags and key routing execute.
"""
from pathlib import Path
import argparse
import json
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP
from tools import probe_source_base_dispatch as source


class ActivationOracle(source.BaseDispatchOracle):
    def allocate(self, size):
        return super().allocate(0x4000 if size == 0x2000 else size)

    def __init__(self, active=1, graphics=True, scene=False, patches=()):
        self.activation_ready = False
        self.services = []
        super().__init__(active, 0, patches)
        self.graphics = self.allocate(0x20) if graphics else 0
        self.load_cursor = self.allocate(16)
        self.set_cursor = self.allocate(16)
        self.w(self.application + 0xd9d, self.graphics)
        self.w(self.application + 0x15b5, 1 if scene else 0)
        self.w(0x5c9e58, self.application)
        self.w(0x5c9e5c, 1)
        self.w(0x5d0204, 0x400000)
        self.u.mem_write(0x5ca55e, b'\0')
        self.w(0x594258, self.load_cursor)
        self.w(0x594270, self.set_cursor)
        self.u.mem_write(self.load_cursor, b'\xc2\x08\0')
        self.u.mem_write(self.set_cursor, b'\xc2\x04\0')
        self.activation_ready = True

    def hook(self, engine, address, size, unused):
        if self.activation_ready:
            if address in (0x4ee970, 0x540b00, 0x567800, 0x567810, 0x501160, 0x5246a0):
                self.entries.append(f'{address:06x}')
            sp = engine.reg_read(UC_X86_REG_ESP)
            if address == self.load_cursor:
                self.services.append(dict(kind='LoadCursorA', resource=self.r(sp + 8), instance=self.r(sp + 4)))
                self.ret(8, 0x12345678)
                return
            if address == self.set_cursor:
                self.services.append(dict(kind='SetCursor', cursor=self.r(sp + 4),
                                          active=self.r(self.application + 0x329d), held=self.r(self.system + 0x20)))
                self.ret(4, 0)
                return
            if address == 0x524150:
                self.services.append(dict(kind='scene-restore', window=self.r(sp + 4),
                                          rectangle_is_app=self.r(sp + 8) == self.application + 0x35c,
                                          mode=self.r(sp + 12) & 255))
                self.ret(12, 0)
                return
        super().hook(engine, address, size, unused)

    def activate(self, activity, gate, held):
        self.received.clear()
        self.entries.clear()
        self.services.clear()
        self.context_messages.clear()
        self.w(self.application + 0x20, gate)
        self.w(self.application + 0x329d, 0xabcdef01)
        self.w(self.application + 0xd91, 1920)
        self.w(self.application + 0xd95, 1080)
        self.w(self.system + 0x20, held)
        if self.graphics:
            self.w(self.graphics + 0xc, 0xa5a5ffff)
        motion = source.marker.normal.pointer.motion
        sp = motion.S.STACK + motion.S.STACK_SIZE - 0x1000
        for i, value in enumerate((motion.S.END, 0x10203040, 0x1c, activity, 0x99)):
            self.w(sp + i * 4, value)
        self.u.reg_write(UC_X86_REG_ESP, sp)
        self.u.reg_write(UC_X86_REG_ECX, self.application)
        self.u.emu_start(0x4ee970, motion.S.END, count=1000000)
        assert self.u.reg_read(UC_X86_REG_EIP) == motion.S.END
        return dict(activity=activity, gate=gate, held=held,
                    stored=self.r(self.system + 0x20), root_gate=self.r(self.application + 0x20),
                    active=self.r(self.application + 0x329d),
                    graphics_flags=self.r(self.graphics + 0xc) if self.graphics else None,
                    result=self.u.reg_read(UC_X86_REG_EAX), entries=list(self.entries),
                    services=list(self.services), received=list(self.received), messages=list(self.context_messages))


def fixture(patches=()):
    rows = []
    for registration in (0, 1):
        for graphics in (False, True):
            for scene in (False, True):
                engine = ActivationOracle(registration, graphics, scene, patches)
                for activity in (0, 1, 0xffffffff):
                    for gate in (0, 1):
                        for held in (0, 1):
                            rows.append(dict(registration=registration, graphics=graphics, scene=scene,
                                             **engine.activate(activity, gate, held)))
    return dict(schema_version=1, original_exe_sha256=source.marker.normal.pointer.gate.EXPECTED,
                source_entry='4ee970', message='WM_ACTIVATEAPP/1C', scope=__doc__, rows=rows,
                os_cursor_and_scene_restore_are_boundaries=True,
                physical_os_events_executed=False, unity_integration=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = fixture()
    args.output.write_text(json.dumps(result, separators=(',', ':')) + '\n')
    print(dict(cases=len(result['rows'])))


if __name__ == '__main__':
    main()
