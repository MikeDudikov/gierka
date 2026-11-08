#!/usr/bin/env python3
"""Compare bounded original x86 geometry instruction ranges with Unity C#.

Unicorn executes the clamp after DrawMapaXY's early-return/setjmp handling and
stops before redraw. It separately executes DrawCellBig's coordinate prelude,
stopping before setjmp and bitmap lookup. No original game, input loop, camera
cadence, renderer, entity or mission setup is executed. No callees are hooked.
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

SOURCE = ROOT / "Unity/AncientConquest/Assets/AncientConquest/Runtime/TerrainViewport.cs"
PROBE = ROOT / "tests/fixtures/TerrainViewportProbe.cs"
OUTPUT = ROOT / "artifacts/binary-analysis/terrain-camera/geometry-validation.json"
CLAMP_START, CLAMP_END = 0x519f3d, 0x519f92
POSITION_START, POSITION_END = 0x5196e0, 0x51972c
CONTEXT, GAME, HEADER = 0x70000000, 0x70010000, 0x70020000
STACK, STACK_SIZE = 0x7ff00000, 0x100000


def input_cases():
    # Header dimensions are signed 16-bit in the original. Nonpositive headers
    # and oversized views are arithmetic stress vectors, not playable maps.
    axes = [(request, cells, view)
            for cells in (-32768, -1, 0, 1, 24, 32767)
            for view in (-0x80000000, -1, 0, 1, 8, 9, 24, 25, 0x7fffffff)
            for request in (-0x80000000, -100, -1, 0, 1, 8, 15, 16, 23, 24, 25, 100, 0x7fffffff)]
    clamp = [{"kind": "clamp", "x": axis, "y": axes[(index + 137) % len(axes)]}
             for index, axis in enumerate(axes)]
    positions = []
    pairs = ((0, 0), (1, 0), (23, 15), (-1, 0), (0, 23),
             (0x7fffffff, -0x80000000), (-0x80000000, 0x7fffffff),
             (0x7fffffff, -1), (-0x80000000, 1))
    for index, (cell, origin) in enumerate(pairs):
        for tile in (0, 1, 64, -64, 32767, 0x7fffffff, -0x80000000):
            for sub_x, frame_x in ((0, 8), (0, 16), (-63, 216),
                                   (63, -8), (0x7fffffff, 1), (-0x80000000, -1)):
                other_cell, other_origin = pairs[(index + 2) % len(pairs)]
                positions.append({"kind": "position", "cell_x": cell, "cell_y": other_cell,
                                  "origin_x": origin, "origin_y": other_origin, "tile": tile,
                                  "sub_x": sub_x, "sub_y": frame_x,
                                  "frame_x": frame_x, "frame_y": sub_x})
    return clamp + positions


def original_case(image, image_size, case):
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
    from unicorn.x86_const import (UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_EBP,
                                   UC_X86_REG_ECX)

    engine = Uc(UC_ARCH_X86, UC_MODE_32)
    engine.mem_map(0x400000, (image_size + 0xfff) & ~0xfff)
    engine.mem_write(0x400000, image)
    engine.mem_map(CONTEXT, 0x30000)
    engine.mem_map(STACK, STACK_SIZE)

    def write32(address, value):
        engine.mem_write(address, struct.pack("<I", value & 0xffffffff))

    def read32(address):
        return struct.unpack("<i", engine.mem_read(address, 4))[0]

    frame = STACK + STACK_SIZE - 0x100
    if case["kind"] == "clamp":
        request_x, cells_x, view_x = case["x"]
        request_y, cells_y, view_y = case["y"]
        write32(CONTEXT + 0x485, GAME)
        write32(GAME + 0x17b2, HEADER)
        engine.mem_write(HEADER, struct.pack("<hh", cells_x, cells_y))
        write32(CONTEXT + 0x3c, view_x)
        write32(CONTEXT + 0x40, view_y)
        write32(frame - 4, CONTEXT)
        write32(frame + 8, request_x)
        write32(frame + 12, request_y)
        engine.reg_write(UC_X86_REG_EBP, frame)
        engine.reg_write(UC_X86_REG_ESP, frame - 0x100)
        start, end = CLAMP_START, CLAMP_END
        engine.emu_start(start, end, count=100)
        require(engine.reg_read(UC_X86_REG_EIP) == end, "Original clamp did not reach redraw boundary")
        x, y = read32(CONTEXT + 0x2c), read32(CONTEXT + 0x30)
        require((x, y) == (read32(GAME + 0x17b6), read32(GAME + 0x17ba)),
                "Original map/game origins differ")
        return (x, y)

    for offset, key in ((0x2c, "origin_x"), (0x30, "origin_y"), (0x54, "tile"),
                        (0x4c, "sub_x"), (0x50, "sub_y"), (0x24, "frame_x"), (0x28, "frame_y")):
        write32(CONTEXT + offset, case[key])
    write32(frame, 0x7002f000)
    write32(frame + 4, case["cell_x"])
    write32(frame + 8, case["cell_y"])
    engine.reg_write(UC_X86_REG_ESP, frame)
    engine.reg_write(UC_X86_REG_ECX, CONTEXT)
    engine.emu_start(POSITION_START, POSITION_END, count=100)
    require(engine.reg_read(UC_X86_REG_EIP) == POSITION_END,
            "Original position prelude did not reach setjmp boundary")
    actual_frame = engine.reg_read(UC_X86_REG_EBP)
    return (read32(actual_frame - 0xc), read32(actual_frame - 4))


def probe_line(case):
    if case["kind"] == "clamp":
        return "C\t" + "\t".join(str(value) for value in (*case["x"], *case["y"]))
    return "P\t" + "\t".join(str(case[key]) for key in
               ("cell_x", "cell_y", "origin_x", "origin_y", "tile", "sub_x", "sub_y", "frame_x", "frame_y"))


def validate(original=ORIGINAL, mono_root=None):
    original = Path(original)
    if not original.is_file():
        raise MissingPrerequisite(f"Optional original executable missing: {original}")
    raw = original.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise ValueError("Original executable SHA-256 differs from the verified geometry")
    pefile, unicorn, runtime, compiler = prerequisites(original, mono_root)
    pe = pefile.PE(data=raw)
    require(pe.OPTIONAL_HEADER.ImageBase == 0x400000, "Unexpected original image base")
    image = pe.get_memory_mapped_image()
    cases = input_cases()
    results = [original_case(image, pe.OPTIONAL_HEADER.SizeOfImage, case) for case in cases]
    with tempfile.TemporaryDirectory(prefix="terrain-viewport-csharp-") as temporary:
        executable = Path(temporary) / "TerrainViewportProbe.exe"
        compiled = subprocess.run(compiler + ["/nologo", "/checked+", "/target:exe", "/out:" + str(executable),
                                  str(SOURCE), str(PROBE)], capture_output=True, text=True, timeout=60)
        if compiled.returncode:
            raise RuntimeError("C# terrain geometry probe compilation failed:\n" + compiled.stdout + compiled.stderr)
        output = subprocess.run([str(runtime), str(executable)],
                                input="\n".join(probe_line(case) for case in cases) + "\n",
                                check=True, capture_output=True, text=True, timeout=60)
    rows = [[int(value) for value in line.split("\t")] for line in output.stdout.splitlines()]
    require(len(rows) == len(cases), "C# geometry probe returned an unexpected case count")
    for case, result, row in zip(cases, results, rows):
        require(tuple(row) == result, f"Geometry mismatch: {case} / x86 {result} / C# {row}")
    clamp_count = sum(case["kind"] == "clamp" for case in cases)
    return {"original_sha256": EXPECTED,
            "kind": "Bounded original x86 clamp / position ranges vs actual Unity C#",
            "ranges": {"clamp": {"start": hex(CLAMP_START), "stop_before": hex(CLAMP_END)},
                       "position": {"start": hex(POSITION_START), "stop_before": hex(POSITION_END)}},
            "csharp_source": str(SOURCE.relative_to(ROOT)), "csharp_sha256": digest(SOURCE),
            "probe_sha256": digest(PROBE), "mono_runtime": str(runtime), "compiler_command": compiler,
            "checked_compilation": True, "unicorn_version": unicorn.__version__,
            "case_count": len(cases), "passed": len(cases), "clamp_cases": clamp_count,
            "position_cases": len(cases) - clamp_count, "axis_comparisons": 2 * len(cases),
            "original_only_checks": ["clamp writes matching Mapa / GameSystem origins"],
            "hooked_callees": {},
            "limits": ["not the complete DrawMapaXY / DrawCellBig routines",
                       "clamp range excludes unchanged-position early return and setjmp handling",
                       "redraw, bitmap lookup and renderer are excluded",
                       "map dimensions are raw sign-extended signed-16-bit header values",
                       "invalid dimensions and oversized views are arithmetic stress vectors",
                       "no initial mission camera, target field of view, input cadence or display scale validated"],
            "cases": [{"input": case, "x86": result} for case, result in zip(cases, results)]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, default=ORIGINAL)
    parser.add_argument("--mono-root", type=Path)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    arguments = parser.parse_args(argv)
    if arguments.output.exists():
        parser.error("Refusing to replace an existing report; select a fresh --output")
    try:
        result = validate(arguments.original, arguments.mono_root)
    except MissingPrerequisite as error:
        parser.exit(2, str(error) + "\n")
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    with arguments.output.open("x") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print(f"{result['passed']} original x86 / actual C# geometry cases passed ({result['axis_comparisons']} axes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
