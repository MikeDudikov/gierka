#!/usr/bin/env python3
"""Compare the original type-5 TabClass pointer path with actual Unity C#.

Only selection is compared. Paint and parent dispatch are recorded, while the
original base stub executes. Keyboard, OS input, lifecycle and rendering are
outside this bounded contract. The original executable is never run by the OS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile

if __package__:
    from . import validate_boss_ai_gate as gate
else:
    import validate_boss_ai_gate as gate

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Unity/AncientConquest/Assets/AncientConquest/Runtime/BriefingDifficultySelection.cs"
PROBE = ROOT / "tests/fixtures/BriefingDifficultyProbe.cs"
CONTEXT, MESSAGE, VTABLE, RECORDS, END = (0x70000000, 0x70001000, 0x70002000,
                                         0x70003000, 0x700f0000)
PAINT, SETJMP, DISPATCH = END + 0x100, 0x587318, 0x5425a0
ENTRY = 0x550ba0
MissingPrerequisite = gate.MissingPrerequisite
LAYOUTS = (
    ((660, 440, 23, 23), (660, 470, 23, 23), (660, 500, 23, 23)),
    ((1591, 792, 41, 41), (1591, 846, 41, 41), (1591, 900, 41, 41)),
)


def traces(rectangles):
    result = []
    for index, (x, y, width, height) in enumerate(rectangles):
        center = (x + width // 2, y + height // 2)
        result.append((f"icon-{index}-click-repeat", [(0x60, *center), (0x61, *center),
                                                      (0x62, *center), (0x61, *center)]))
        points = ((x - 1, y), (x, y), (x + width - 1, y + height - 1),
                  (x + width, y), (x, y + height), (x + width, y + height),
                  (x + width + 8, y + height // 2), (0, 0), (65535, 65535))
        for number, point in enumerate(points):
            result.append((f"icon-{index}-boundary-{number}", [(0x61, *point), (0x62, *point)]))
        result.append((f"icon-{index}-down-then-leave", [(0x61, *center), (0x60, 0, 0), (0x62, 0, 0)]))
        result.append((f"icon-{index}-hover-release-right", [(0x60, *center), (0x62, *center),
                                                             (0x63, *center), (0x64, *center)]))
    centers = [(x + w // 2, y + h // 2) for x, y, w, h in rectangles]
    result.append(("all-levels-in-order", [(0x61, *center) for center in centers + centers[::-1]]))
    return result


def original_trace(image, image_size, selected, rectangles, events):
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_ECX, UC_X86_REG_EAX

    engine = Uc(UC_ARCH_X86, UC_MODE_32)
    engine.mem_map(0x400000, (image_size + 0xfff) & ~0xfff)
    engine.mem_write(0x400000, image)
    engine.mem_map(CONTEXT, 0x100000)
    engine.mem_map(gate.STACK, gate.STACK_SIZE)

    def put(address, value):
        engine.mem_write(address, struct.pack("<I", value & 0xffffffff))

    def get(address):
        return struct.unpack("<I", engine.mem_read(address, 4))[0]

    put(CONTEXT, VTABLE)
    put(VTABLE + 4, PAINT)
    put(CONTEXT + 0x64, RECORDS)
    put(CONTEXT + 0x68, selected + 1)
    put(CONTEXT + 0x70, 0)  # Briefing descriptor's hover flag is zero.
    put(CONTEXT + 0x74, 1)  # Active TabClass flag.
    put(CONTEXT + 0x34, 0x210)
    put(0x5d1f90, 0xabcdef01)
    for index, (x, y, width, height) in enumerate(rectangles):
        base = RECORDS + index * 0x70
        for offset, value in ((0, index + 1), (4, int(index == selected)),
                              (0xc, x), (0x10, y), (0x14, width), (0x18, height)):
            put(base + offset, value)
    dispatched, painted = [], []

    def hook(uc, address, size, unused):
        if address not in (SETJMP, DISPATCH, PAINT):
            return
        stack = uc.reg_read(UC_X86_REG_ESP)
        if address == DISPATCH:
            message = get(stack + 4)
            gate.require(get(message + 0x10) == 0x210, "Unexpected original dispatch message")
            record = get(message + 0x14)
            dispatched.append(get(record))
            gate.require(get(record + 4) == 1, "Dispatched record is not selected")
        if address == PAINT:
            painted.append(get(get(stack + 4)))
        uc.reg_write(UC_X86_REG_EAX, 0)
        uc.reg_write(UC_X86_REG_ESP, stack + (4 if address == SETJMP else 8))
        uc.reg_write(UC_X86_REG_EIP, get(stack))

    engine.hook_add(UC_HOOK_CODE, hook)
    rows = []
    for message, x, y in events:
        gate.require(0 <= x <= 65535 and 0 <= y <= 65535, "Original coordinates use unsigned16 packing")
        dispatched.clear()
        painted.clear()
        put(MESSAGE + 0x10, message)
        put(MESSAGE + 0x18, x | y << 16)
        top = gate.STACK + gate.STACK_SIZE - 0x100
        put(top, END)
        put(top + 4, MESSAGE)
        engine.reg_write(UC_X86_REG_ESP, top)
        engine.reg_write(UC_X86_REG_ECX, CONTEXT)
        engine.emu_start(ENTRY, END, count=10000)
        gate.require(engine.reg_read(UC_X86_REG_EIP) == END, "Original TabClass did not return")
        gate.require(engine.reg_read(UC_X86_REG_EAX) == 0, "Original TabClass returned an error")
        gate.require(get(0x5d1f90) == 0xabcdef01, "Original exception chain not restored")
        gate.require(len(dispatched) <= 1, "Unexpected repeated difficulty dispatch")
        identifier = get(CONTEXT + 0x68)
        states = [get(RECORDS + index * 0x70 + 4) for index in range(3)]
        gate.require(states == [int(index + 1 == identifier) for index in range(3)],
                     "Original selection/record states disagree")
        gate.require(not dispatched or dispatched == [identifier], "Original dispatched a different record ID")
        rows.append({"selected": identifier - 1, "changed": bool(dispatched),
                     "record_states": states, "paint_ids": list(painted)})
    return rows


def validate(original=gate.ORIGINAL, mono_root=None):
    original = Path(original)
    if not original.is_file():
        raise MissingPrerequisite(f"Optional original executable missing: {original}")
    raw = original.read_bytes()
    if hashlib.sha256(raw).hexdigest() != gate.EXPECTED:
        raise ValueError("Original executable SHA-256 differs from the verified briefing contract")
    pefile, unicorn, runtime, compiler = gate.prerequisites(original, mono_root)
    pe = pefile.PE(data=raw)
    gate.require(pe.OPTIONAL_HEADER.ImageBase == 0x400000, "Unexpected original image base")
    cases, probe_rows = [], []
    image = pe.get_memory_mapped_image()
    trace_count = 0
    for layout_index, rectangles in enumerate(LAYOUTS):
        flat = [value for rect in rectangles for value in rect]
        for selected in range(3):
            for name, events in traces(rectangles):
                trace_count += 1
                rows = original_trace(image, pe.OPTIONAL_HEADER.SizeOfImage, selected, rectangles, events)
                for step, ((message, x, y), result) in enumerate(zip(events, rows)):
                    cases.append({"layout": layout_index, "initial_selected": selected,
                                  "trace": name, "step": step, "message": message,
                                  "point": [x, y], "original": result})
                    probe_rows.append("\t".join(str(value) for value in
                                      [int(step == 0), selected, *flat, message, x, y]))
    with tempfile.TemporaryDirectory(prefix="briefing-difficulty-csharp-") as temporary:
        executable = Path(temporary) / "BriefingDifficultyProbe.exe"
        compiled = subprocess.run(compiler + ["/nologo", "/checked+", "/target:exe", "/out:" + str(executable),
                                              str(SOURCE), str(PROBE)], capture_output=True, text=True, timeout=60)
        if compiled.returncode:
            raise RuntimeError("Difficulty C# compilation failed:\n" + compiled.stdout + compiled.stderr)
        output = subprocess.run([str(runtime), str(executable)], input="\n".join(probe_rows) + "\n",
                                capture_output=True, text=True, check=True, timeout=60)
    gate.require("10 C# configuration-boundary checks passed" in output.stderr,
                 "C# configuration checks did not complete")
    rows = [[int(value) for value in line.split("\t")] for line in output.stdout.splitlines()]
    gate.require(len(rows) == len(cases), "Unexpected C# difficulty probe row count")
    for case, actual in zip(cases, rows):
        expected = case["original"]
        gate.require(actual == [expected["selected"], int(expected["changed"])],
                     f"Difficulty mismatch: {case} / C# {actual}")
    return {"kind": "Original x86 type-5 TabClass pointer selection vs actual Unity C#",
            "entry_point": hex(ENTRY), "original_sha256": gate.EXPECTED,
            "unicorn_version": unicorn.__version__, "case_count": len(cases), "passed": len(cases),
            "trace_count": trace_count, "layouts": LAYOUTS, "initial_choices": [0, 1, 2],
            "csharp_source": str(SOURCE.relative_to(ROOT)), "csharp_sha256": gate.digest(SOURCE),
            "probe_sha256": gate.digest(PROBE), "configuration_csharp_checks": 10,
            "mono_runtime": str(runtime), "compiler_command": compiler,
            "compared": ["selected difficulty0..2", "changed/selection dispatch"],
            "original_only_checks": ["selected record states", "zero return", "exception-chain restoration",
                                     "dispatch payload selectedID", "at most one dispatch"],
            "hooked_callees": {hex(SETJMP): "normal setjmp return", hex(DISPATCH): "record parent request",
                               hex(PAINT): "virtual renderer records only"},
            "limits": ["active TabClass with valid selection and hoverflag0 only",
                       "keyboard/lifecycle/OS input/rendering not compared",
                       "original pointer coordinates packed unsigned16",
                       "global difficulty persistence and gameplay effects excluded"],
            "cases": cases}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, default=gate.ORIGINAL)
    parser.add_argument("--mono-root", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/binary-analysis/briefing-controls/difficulty-validation.json")
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("Refusing to overwrite an existing report; select a fresh output")
    try:
        report = validate(args.original, args.mono_root)
    except MissingPrerequisite as error:
        parser.exit(2, str(error) + "\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(f"{report['passed']} original x86 / actual C# difficulty steps passed in {report['trace_count']} traces")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
