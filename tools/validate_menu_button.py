#!/usr/bin/env python3
"""Compare pointer traces in original type-1 x86 button with Unity C#.

Only the button state machine executes. The renderer, base handler and command
transport are intercepted, so this does not test full original UI integration,
keyboard shortcuts, sound, focus policy, network or the action's application code.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import validate_boss_ai_gate as gate

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Unity/AncientConquest/Assets/AncientConquest/Runtime/MainMenuButton.cs"
PROBE = ROOT / "tests/fixtures/MenuButtonProbe.cs"
FUNCTION = 0x54aab0
CONTEXT, MESSAGE, VTABLE, END = 0x70000000, 0x70001000, 0x70002000, 0x700f0000
PAINT = END + 0x100
SETJMP, BASE, DISPATCH = 0x587318, 0x555b80, 0x5425a0
GEOMETRY = (112, 398, 278, 64)
MOVE, DOWN, UP = 0x60, 0x61, 0x62
MissingPrerequisite = gate.MissingPrerequisite


def traces():
    """Human interaction sequences, boundaries and disabled-state controls."""
    inside, outside = (120, 410), (500, 600)
    event = lambda message, point: (message, *point)
    result = [
        ("hover-click", True, [event(MOVE, inside), event(DOWN, inside), event(UP, inside)]),
        ("direct-click", True, [event(DOWN, inside), event(UP, inside)]),
        ("release-without-down", True, [event(MOVE, inside), event(UP, inside)]),
        ("drag-out-return", True, [event(MOVE, inside), event(DOWN, inside), event(MOVE, outside), event(MOVE, inside), event(UP, inside)]),
        ("release-outside-without-motion", True, [event(DOWN, inside), event(UP, outside), event(MOVE, inside), event(UP, inside)]),
        ("down-outside-drag-in", True, [event(DOWN, outside), event(MOVE, inside), event(UP, inside)]),
        ("repeat-down-up", True, [event(MOVE, inside), event(DOWN, inside), event(DOWN, inside), event(UP, inside), event(UP, inside)]),
        ("motion-while-held", True, [event(DOWN, inside), event(MOVE, inside), event(UP, inside)]),
        ("hover-exit-return", True, [event(MOVE, inside), event(MOVE, outside), event(MOVE, outside), event(MOVE, inside)]),
        ("two-clicks", True, [event(MOVE, inside), event(DOWN, inside), event(UP, inside), event(DOWN, inside), event(UP, inside)]),
        ("disabled", False, [event(MOVE, inside), event(DOWN, inside), event(UP, inside), event(MOVE, outside)]),
    ]
    x, y, width, height = GEOMETRY
    points = [(x-1,y), (x,y), (x+width-1,y), (x+width,y), (x,y-1),
              (x,y+height-1), (x,y+height), (x+width,y+height),
              (x+width+1,y+height), (0,0), (65535,65535)]
    for i, point in enumerate(points):
        result.append((f"boundary-direct-{i}", True, [event(MOVE, point), event(DOWN, point), event(UP, point)]))
        result.append((f"boundary-release-{i}", True, [event(MOVE, inside), event(DOWN, inside), event(UP, point)]))
        result.append((f"boundary-motion-{i}", True, [event(MOVE, inside), event(DOWN, inside), event(MOVE, point), event(UP, point)]))
    return result


def original_trace(image, image_size, enabled, events):
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_ECX, UC_X86_REG_EAX
    engine = Uc(UC_ARCH_X86, UC_MODE_32)
    engine.mem_map(0x400000, (image_size + 0xfff) & ~0xfff)
    engine.mem_write(0x400000, image)
    engine.mem_map(CONTEXT, 0x100000)
    engine.mem_map(gate.STACK, gate.STACK_SIZE)

    def put(address, value): engine.mem_write(address, struct.pack("<I", value))
    def get(address): return struct.unpack("<I", engine.mem_read(address, 4))[0]

    put(CONTEXT, VTABLE)
    put(VTABLE + 4, PAINT)
    put(CONTEXT + 0x1c, int(enabled))
    put(CONTEXT + 0x20, 1)  # Main-menu descriptors select button type 1.
    for offset, value in zip((0x24,0x28,0x2c,0x30), GEOMETRY): put(CONTEXT + offset, value)
    put(CONTEXT + 0x142, 0x164)  # Message ID of Quit; transport is intercepted.
    put(0x5d1f90, 0xabcdef01)
    calls = []

    def hook(uc, address, size, unused):
        if address not in (SETJMP, BASE, DISPATCH, PAINT): return
        stack = uc.reg_read(UC_X86_REG_ESP)
        calls.append(address)
        if address == DISPATCH:
            gate.require(get(get(stack + 4) + 0x10) == 0x164, "Unexpected command message")
        uc.reg_write(UC_X86_REG_EAX, 0)
        uc.reg_write(UC_X86_REG_ESP, stack + (8 if address in (BASE, DISPATCH) else 4))
        uc.reg_write(UC_X86_REG_EIP, get(stack))

    engine.hook_add(UC_HOOK_CODE, hook)
    rows = []
    for message, x, y in events:
        gate.require(0 <= x <= 65535 and 0 <= y <= 65535, "Original input uses packed unsigned16 coordinates")
        calls.clear()
        put(MESSAGE + 0x10, message)
        put(MESSAGE + 0x18, x | y << 16)
        top = gate.STACK + gate.STACK_SIZE - 0x100
        engine.mem_write(top, struct.pack("<II", END, MESSAGE))
        engine.reg_write(UC_X86_REG_ESP, top)
        engine.reg_write(UC_X86_REG_ECX, CONTEXT)
        engine.emu_start(FUNCTION, END, count=10000)
        gate.require(engine.reg_read(UC_X86_REG_EIP) == END, "Original did not return")
        gate.require(engine.reg_read(UC_X86_REG_EAX) == 0, "Original returned an error")
        gate.require(get(0x5d1f90) == 0xabcdef01, "Original exception chain not restored")
        gate.require(calls.count(SETJMP) == calls.count(BASE) == 1, "Unexpected original base/setjmp count")
        gate.require(calls.count(PAINT) <= 1 and calls.count(DISPATCH) <= 1, "Unexpected renderer/command call count")
        rows.append([get(CONTEXT + offset) for offset in (0x1c,0x196,0x19a,0x1c6)] + [calls.count(DISPATCH)])
    return rows


def validate(original=gate.ORIGINAL, mono_root=None):
    original = Path(original)
    if not original.is_file(): raise MissingPrerequisite(f"Optional original executable missing: {original}")
    raw = original.read_bytes()
    if hashlib.sha256(raw).hexdigest() != gate.EXPECTED:
        raise ValueError("Original executable SHA-256 differs from verified button contract")
    pefile, unicorn, runtime, compiler = gate.prerequisites(original, mono_root)
    pe = pefile.PE(data=raw)
    if pe.OPTIONAL_HEADER.ImageBase != 0x400000: raise ValueError("Unexpected image base")
    cases = []
    input_lines = []
    for name, enabled, events in traces():
        rows = original_trace(pe.get_memory_mapped_image(), pe.OPTIONAL_HEADER.SizeOfImage, enabled, events)
        for index, ((message, x, y), row) in enumerate(zip(events, rows)):
            cases.append({"trace":name,"step":index,"enabled":enabled,"message":message,"x":x,"y":y,
                          "state":row[0],"pressed":row[1],"hovered":row[2],"inside":row[3],"emitted":row[4]})
            input_lines.append(f"{int(index == 0)}\t{int(enabled)}\t{message}\t{x}\t{y}")
    with tempfile.TemporaryDirectory(prefix="menu-button-csharp-") as temporary:
        executable = Path(temporary) / "MenuButtonProbe.exe"
        compiled = subprocess.run(compiler + ["/nologo","/target:exe","/out:"+str(executable),str(SOURCE),str(PROBE)],capture_output=True,text=True,timeout=60)
        if compiled.returncode: raise RuntimeError("C# probe compilation failed:\n"+compiled.stdout+compiled.stderr)
        output = subprocess.run([str(runtime),str(executable)],input="\n".join(input_lines)+"\n",capture_output=True,text=True,check=True,timeout=60)
    rows = [[int(value) for value in line.split("\t")] for line in output.stdout.splitlines()]
    gate.require(len(rows) == len(cases), "C# returned unexpected row count")
    for case, row in zip(cases, rows):
        expected = [case[key] for key in ("state","pressed","hovered","inside","emitted")]
        gate.require(row == expected, f"Button mismatch: {case} / C# {row}")
    return {"original_sha256":gate.EXPECTED,"entry_point":hex(FUNCTION),"unicorn_version":unicorn.__version__,
            "kind":"Isolated original x86 type-1 pointer traces vs actual Unity C#",
            "geometry":list(GEOMETRY),"trace_count":len(traces()),"case_count":len(cases),"passed":len(cases),
            "csharp_source":str(SOURCE.relative_to(ROOT)),"csharp_sha256":gate.digest(SOURCE),"probe_sha256":gate.digest(PROBE),
            "mono_runtime":str(runtime),"compiler_command":compiler,
            "compared":["state","pressed","hovered","inside","emitted command"],
            "original_only_checks":["zero return","exception-chain restoration","base/setjmp/render/dispatch call bounds"],
            "hooked_callees":{hex(SETJMP):"normal setjmp return",hex(BASE):"no-op base handler",hex(DISPATCH):"record transport request",hex(PAINT):"no-op virtual renderer"},
            "excluded":["renderer pixels","parent action code","keyboard/right-click modes","sound","host focus-loss adapter policy"],
            "cases":cases}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original",type=Path,default=gate.ORIGINAL)
    parser.add_argument("--mono-root",type=Path)
    parser.add_argument("--output",type=Path,default=ROOT/"artifacts/binary-analysis/menu-interaction/button-validation.json")
    args = parser.parse_args(argv)
    if args.output.exists(): parser.error("Refusing to replace an existing report; select fresh --output")
    try: result = validate(args.original,args.mono_root)
    except MissingPrerequisite as error: parser.exit(2,str(error)+"\n")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x") as stream: stream.write(json.dumps(result,indent=2)+"\n")
    print(f"{result['passed']} original x86 / actual C# button comparisons passed in {result['trace_count']} traces")
    return 0

if __name__ == "__main__":
    # Allow both python -m tools.validate_menu_button and direct script invocation.
    raise SystemExit(main())
