#!/usr/bin/env python3
"""Compare actual C# reef reference recipes to bounded original x86 evidence.

Five frozen source-seed cases came from actual ctor/message2/SetState/LoadImages
execution with documented service hooks and empty collision cells. Stress cases
execute two original instruction ranges without hooks for field extraction and
32-bit cell-to-world shifts. This is not a complete mission/state/renderer test.
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
    from .validate_boss_ai_gate import ROOT, EXPECTED, MissingPrerequisite, digest, prerequisites, require
else:
    from validate_boss_ai_gate import ROOT, EXPECTED, MissingPrerequisite, digest, prerequisites, require

SEED_SOURCE = ROOT / "Unity/AncientConquest/Assets/AncientConquest/Runtime/MissionObjectSeed.cs"
SOURCE = ROOT / "Unity/AncientConquest/Assets/AncientConquest/Runtime/MissionReefSeed.cs"
PROBE = ROOT / "tests/fixtures/MissionReefSeedProbe.cs"
FIXTURE = ROOT / "tests/fixtures/mission_reef_seed.json"
FIXTURE_SHA256 = "8acc201d1bc05885684a1982f5ecd8f7dab9ea3bc4046251cb5787f3d9cdfdff"
OUTPUT = ROOT / "artifacts/objects/position/reef-seed-csharp-validation.json"
FIELD_START, FIELD_END = 0x430773, 0x43079a
ANCHOR_START, ANCHOR_END = 0x43016e, 0x43018c
CONTEXT, PAYLOAD, SPRITE = 0x70000000, 0x70010000, 0x70020000
STACK, STACK_SIZE = 0x7ff00000, 0x100000
GUARDS = {"null_seed", "unsupported_class"} | {f"length_{n}" for n in (16, 20, 28, 31, 33, 36)} | {f"mode_{m}" for m in (1, 2, 0xffffffff)}


def load_fixture(path=FIXTURE):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256:
        raise ValueError("Frozen reef initialization fixture hash differs")
    fixture = json.loads(raw)
    if fixture["schema_version"] != 1 or fixture["original_exe_sha256"] != EXPECTED or len(fixture["records"]) != 5:
        raise ValueError("Unexpected reef initialization fixture")
    for row in fixture["records"]:
        payload = bytes.fromhex(row["payload_hex"])
        if len(payload) != 32 or hashlib.sha256(payload).hexdigest() != row["payload_sha256"]:
            raise ValueError("Invalid frozen reef payload")
    return fixture


def stress_cases():
    pairs = [(0, 0), (23, 23), (-1, 1), (-0x80000000, 0x7fffffff),
             (0x7fffffff, -0x80000000), (33554431, 33554432),
             (33554432, -33554433), (67108863, -67108864), (123456789, -987654321)]
    variants = [0, 1, 2, 3, 127, 128, 255, 256, 0xffffffff, 0x12345678, 0x80000000]
    result = []
    for x, y in pairs:
        for variant in variants:
            payload = struct.pack("<8I", 601, 2, 0, 0, 0, x & 0xffffffff, y & 0xffffffff, variant)
            result.append({"name": f"OBJ_{0x1000 + len(result):08x}", "payload_hex": payload.hex()})
    return result


def original_fields_and_anchor(image, image_size, payload):
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
    from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_EDI,
                                   UC_X86_REG_ESI, UC_X86_REG_ESP, UC_X86_REG_EIP)
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    uc.mem_map(0x400000, (image_size + 0xfff) & ~0xfff)
    uc.mem_write(0x400000, image)
    uc.mem_map(CONTEXT, 0x30000)
    uc.mem_map(STACK, STACK_SIZE)
    uc.mem_write(PAYLOAD, payload)
    uc.mem_write(CONTEXT + 0x82, struct.pack("<I", SPRITE))
    uc.reg_write(UC_X86_REG_EAX, PAYLOAD)
    uc.reg_write(UC_X86_REG_EBX, CONTEXT)
    uc.reg_write(UC_X86_REG_EDI, 0)
    uc.reg_write(UC_X86_REG_ESP, STACK + STACK_SIZE - 0x100)
    uc.emu_start(FIELD_START, FIELD_END, count=100)
    require(uc.reg_read(UC_X86_REG_EIP) == FIELD_END, "Original reef field-copy range did not stop")
    uc.reg_write(UC_X86_REG_ESI, CONTEXT)
    uc.emu_start(ANCHOR_START, ANCHOR_END, count=100)
    require(uc.reg_read(UC_X86_REG_EIP) == ANCHOR_END, "Original reef anchor range did not stop")
    read_int = lambda offset: struct.unpack("<i", uc.mem_read(CONTEXT + offset, 4))[0]
    pixel_int = lambda offset: struct.unpack("<i", uc.mem_read(SPRITE + offset, 4))[0]
    require(read_int(0x50) == 601, "Original field range did not retain reef class")
    return (read_int(0x7a), read_int(0x7e), uc.mem_read(CONTEXT + 0x75, 1)[0], pixel_int(0x59), pixel_int(0x5d))


def validate(mono_root=None, fixture_path=FIXTURE):
    fixture = load_fixture(fixture_path)
    pefile, _unicorn, runtime, compiler = prerequisites(mono_root=mono_root)
    original = ROOT / "reference/raw/ancient-conquest/installed/ancient.exe"
    raw = original.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == EXPECTED, "Original executable hash differs")
    pe = pefile.PE(data=raw)
    image = pe.get_memory_mapped_image()
    cases = list(fixture["records"]) + stress_cases()
    expected = []
    for row in cases:
        actual = original_fields_and_anchor(image, pe.OPTIONAL_HEADER.SizeOfImage, bytes.fromhex(row["payload_hex"]))
        if "cell" in row:
            require(actual == (*row["cell"], row["variant"], *row["world_pixel"]),
                    "Frozen full initialization disagrees with original instruction ranges")
            require((row["reference_state"], row["reference_frame_index"]) == (1, 0), "Frozen reference state changed")
        x, y, variant, world_x, world_y = actual
        expected.append((row["name"], int(row["name"][4:], 16), x, y, variant, 1, 0, world_x, world_y, f"BREEF{variant}SPR_1"))
    sources = {p: digest(p) for p in (SEED_SOURCE, SOURCE, PROBE)}
    with tempfile.TemporaryDirectory(prefix="mission-reef-csharp-") as temporary:
        executable = Path(temporary) / "MissionReefSeedProbe.exe"
        command = compiler + ["/nologo", "/checked+", "/target:exe", "/out:" + str(executable), str(SEED_SOURCE), str(SOURCE), str(PROBE)]
        compiled = subprocess.run(command, capture_output=True, text=True, timeout=60)
        require(compiled.returncode == 0, "C# reef probe compilation failed:\n" + compiled.stdout + compiled.stderr)
        result = subprocess.run([str(runtime), str(executable)],
                                input="".join(row["name"] + "\t" + row["payload_hex"] + "\n" for row in cases),
                                capture_output=True, text=True, timeout=60)
        require(result.returncode == 0, "C# reef probe failed:\n" + result.stdout + result.stderr)
    for path, before in sources.items():
        require(digest(path) == before, "Reef source/probe changed during validation")
    rows, guards = [], []
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) == 2 and fields[0] == "CHECK": guards.append(fields[1])
        elif len(fields) == 11 and fields[0] == "ROW":
            rows.append((fields[1], *(int(value) for value in fields[2:10]), fields[10]))
        else: raise ValueError("Unexpected C# reef probe output: " + line)
    require(len(guards) == len(GUARDS) and set(guards) == GUARDS, "Missing or duplicated reef C# contract guards")
    require(len(rows) == len(expected), "Unexpected C# reef row count")
    for wanted, actual in zip(expected, rows):
        require(wanted == actual, f"Reef reference mismatch: original {wanted}; C# {actual}")
    return {"kind": "Frozen source initialization plus original x86 field/anchor ranges vs actual C# reference recipe",
            "original_sha256": EXPECTED, "fixture_sha256": FIXTURE_SHA256,
            "fixture_source_cases": len(fixture["records"]), "stress_cases": len(cases) - len(fixture["records"]),
            "case_count": len(cases), "passed": len(rows), "original_instruction_ranges": [[hex(FIELD_START), hex(FIELD_END)], [hex(ANCHOR_START), hex(ANCHOR_END)]],
            "range_intercepted_functions": [], "checked_compilation": True,
            "csharp_guard_count": len(guards), "csharp_guards": guards,
            "source_sha256": {str(p.relative_to(ROOT)): digest for p, digest in sources.items()},
            "validator_sha256": digest(Path(__file__)),
            "conditions": fixture["conditions"], "frozen_initialization_services_hooked": fixture["intercepted_services"],
            "excluded": ["The C# struct does not run ctor, SetState, collision grid, spawning or simulation",
                         "State1/frame0 are a frozen reference recipe with an empty collision cell, not full mission state",
                         "Stress vectors prove extraction/truncation/wrapping; no corresponding game assets or playable positions claimed",
                         "Frame rendering, sprite pivots, animation, timing, AI and full original game are not validated here"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mono-root", type=Path)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    arguments = parser.parse_args(argv)
    if arguments.output.exists(): parser.error("Select a fresh output report")
    report = validate(arguments.mono_root)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    with arguments.output.open("x") as stream: stream.write(json.dumps(report, indent=2) + "\n")
    print(f"{report['passed']} C#/original reef reference cases, {report['csharp_guard_count']} C# guards passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
