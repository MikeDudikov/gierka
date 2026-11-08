#!/usr/bin/env python3
"""Compare original MoveShip's bounded forward-animation tail with actual C#.

Original x86 instructions execute without hooks. Movement, rendering, turn and
idle animation, and tick-to-wall-time conversion are outside this range.
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
    from .validate_boss_ai_gate import ROOT, EXPECTED, ORIGINAL, MissingPrerequisite, digest, prerequisites, require
else:
    from validate_boss_ai_gate import ROOT, EXPECTED, ORIGINAL, MissingPrerequisite, digest, prerequisites, require

SOURCE = ROOT / "Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipFrameProgression.cs"
PROBE = ROOT / "tests/fixtures/ShipFrameProgressionProbe.cs"
OUTPUT = ROOT / "artifacts/movement/animation/ship-frame-progression-csharp-validation.json"
START, END = 0x4a4d49, 0x4a4da0
SHIP, SPRITE, GAME = 0x70000000, 0x70002000, 0x70004000
STACK, STACK_SIZE = 0x71000000, 0x20000


def input_cases():
    source = [{"frame": heading * 4 + phase, "heading": heading,
               "now": now, "last_tick": last, "interval": 2, "scope": "source_forward_phases"}
              for heading in range(8) for phase in range(4)
              for now, last in ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (100, 0), (1, 0xfffffffe))]
    # Stress inputs check the raw signed/unsigned instruction contract, rather
    # than claiming these malformed frames/headings are playable ship poses.
    stress = [{"frame": frame, "heading": heading, "now": now, "last_tick": last,
               "interval": interval, "scope": "raw_arithmetic_stress"}
              for frame in (-0x80000000, -1, 0, 0x7fffffff)
              for heading in (-128, -1, 0, 127)
              for now, last, interval in ((3, 0, 2), (0, 0xffffffff, 0),
                                          (0, 1, 0xfffffffe), (0, 1, 0xffffffff))]
    return source + stress


def original_case(image, image_size, case):
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
    from unicorn.x86_const import UC_X86_REG_EBP, UC_X86_REG_ESI, UC_X86_REG_ESP, UC_X86_REG_EIP
    engine = Uc(UC_ARCH_X86, UC_MODE_32)
    engine.mem_map(0x400000, (image_size + 0xfff) & ~0xfff)
    engine.mem_write(0x400000, image)
    engine.mem_map(SHIP, 0x10000)
    engine.mem_map(STACK, STACK_SIZE)

    def write(address, value):
        engine.mem_write(address, struct.pack("<I", value & 0xffffffff))

    frame = STACK + STACK_SIZE - 0x100
    for address, value in ((SHIP + 0x8be, SPRITE), (SHIP + 0x70, GAME),
                           (SPRITE + 0x45, case["frame"]), (SPRITE + 0x81, case["last_tick"]),
                           (SPRITE + 0x7d, case["interval"]), (GAME + 0xde, case["now"]),
                           (frame - 0x48, case["heading"])):
        write(address, value)
    engine.reg_write(UC_X86_REG_EBP, frame)
    engine.reg_write(UC_X86_REG_ESI, SHIP)
    engine.reg_write(UC_X86_REG_ESP, frame - 0x200)
    engine.emu_start(START, END, count=100)
    require(engine.reg_read(UC_X86_REG_EIP) == END, "Original forward tail did not reach its boundary")
    return (struct.unpack("<i", engine.mem_read(SPRITE + 0x45, 4))[0],
            struct.unpack("<I", engine.mem_read(SPRITE + 0x81, 4))[0])


def validate(original=ORIGINAL, mono_root=None):
    original = Path(original)
    if not original.is_file():
        raise MissingPrerequisite(f"Optional original executable missing: {original}")
    raw = original.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise ValueError("Original executable SHA-256 differs from the verified forward tail")
    pefile, unicorn, runtime, compiler = prerequisites(original, mono_root)
    pe = pefile.PE(data=raw)
    require(pe.OPTIONAL_HEADER.ImageBase == 0x400000, "Unexpected original image base")
    image = pe.get_memory_mapped_image()
    before = {str(path): digest(path) for path in (original, SOURCE, PROBE)}
    cases = input_cases()
    results = [original_case(image, pe.OPTIONAL_HEADER.SizeOfImage, case) for case in cases]
    with tempfile.TemporaryDirectory(prefix="ship-forward-csharp-") as temporary:
        executable = Path(temporary) / "ShipFrameProgressionProbe.exe"
        compiled = subprocess.run(compiler + ["/nologo", "/checked+", "/target:exe", "/out:" + str(executable),
                                  str(SOURCE), str(PROBE)], capture_output=True, text=True, timeout=60)
        if compiled.returncode:
            raise RuntimeError("C# ship frame probe compilation failed:\n" + compiled.stdout + compiled.stderr)
        lines = ["\t".join(str(case[key]) for key in ("frame", "heading", "now", "last_tick", "interval"))
                 for case in cases]
        output = subprocess.run([str(runtime), str(executable)], input="\n".join(lines) + "\n",
                                check=True, capture_output=True, text=True, timeout=60)
    rows = [[int(value) for value in line.split("\t")] for line in output.stdout.splitlines()]
    require(len(rows) == len(cases), "C# ship frame probe returned an unexpected case count")
    for case, result, row in zip(cases, results, rows):
        require(tuple(row) == result, f"Forward frame mismatch: {case} / x86 {result} / C# {row}")
    require(before == {str(path): digest(path) for path in (original, SOURCE, PROBE)},
            "Original or C# inputs changed during validation")
    return {"original_sha256": EXPECTED, "kind": "Bounded original forward-frame x86 vs actual Unity C#",
            "range": {"start": hex(START), "stop_before": hex(END)}, "hooked_callees": {},
            "csharp_source": str(SOURCE.relative_to(ROOT)), "csharp_sha256": digest(SOURCE),
            "probe_sha256": digest(PROBE), "mono_runtime": str(runtime), "compiler_command": compiler,
            "checked_compilation": True, "unicorn_version": unicorn.__version__,
            "source_phase_cases": 224, "arithmetic_stress_cases": len(cases) - 224,
            "case_count": len(cases), "passed": len(cases),
            "limits": ["bounded forward-animation tail only; no movement, turn, idle or renderer",
                       "raw arithmetic stress cases do not represent supported asset poses",
                       "now is a source tick counter; no wall-clock unit is assumed"],
            "cases": [{"input": case, "x86_frame": result[0], "x86_last_tick": result[1]}
                      for case, result in zip(cases, results)]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, default=ORIGINAL)
    parser.add_argument("--mono-root", type=Path)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("Refusing to replace an existing report; select a fresh --output")
    try:
        result = validate(args.original, args.mono_root)
    except MissingPrerequisite as error:
        parser.exit(2, str(error) + "\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print(f"{result['passed']} original x86 / actual C# ship frame cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
