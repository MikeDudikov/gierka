#!/usr/bin/env python3
"""Compare original mission-object eligibility/dispatch with the actual Unity C#.

CreateSystemObjects and its unsigned hexadecimal parser execute in Unicorn.
Only normal setjmp return and the constructor boundary are intercepted.
The original B-tree iterator and OBJ_ filter separately execute without hooks.
No class constructor, object Init, AI or playable mission is executed.
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
    from .inspect_dkx import inspect_pair
    from .decode_sprite import resource_payload
else:
    import validate_boss_ai_gate as gate
    from inspect_dkx import inspect_pair
    from decode_sprite import resource_payload

ROOT = gate.ROOT
MissingPrerequisite = gate.MissingPrerequisite
SOURCE_ROOT = ROOT / "reference/raw/ancient-conquest"
SOURCE_HASHES = {
    "installed/ancient.exe": gate.EXPECTED,
    "installed/missions/miss000.dkx": "b4b2fda60bb38e837b6d0548caa86229e1fbebf8cb9fd806c4f39c9bd75835ce",
    "installed/missions/miss000.dkd": "a77e801a93baafd6942db9087d7541f8c85ed2f3c88d440b9f9e81b45ba9a0d1",
}
SOURCES = [ROOT / "Unity/AncientConquest/Assets/AncientConquest/Runtime" / name
           for name in ("MissionObjectSeed.cs", "MissionObjectSelection.cs")]
PROBE = ROOT / "tests/fixtures/MissionObjectSelectionProbe.cs"
FIXTURE = ROOT / "tests/fixtures/mission_miss000_object_selection.json"
FIXTURE_SHA256 = "8502df484e066fd80a75872583fe01fbc46ff3031f75942e375f020fffc9c812"
OUTPUT = ROOT / "artifacts/objects/loader/selection-validation.json"
CONTEXT, APP, PAYLOAD, NAME, END = (0x70000000, 0x70010000, 0x70020000,
                                  0x70030000, 0x700f0000)
STACK, STACK_SIZE = 0x7ff00000, 0x100000
ENTRY, SETJMP, CREATE = 0x51e7a0, 0x587318, 0x51f0e0


def checked_sources(source_root):
    result = {}
    for name, expected in SOURCE_HASHES.items():
        path = Path(source_root) / name
        if not path.is_file():
            raise MissingPrerequisite("Optional original mission input missing: " + str(path))
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("Original source SHA-256 differs: " + name)
        result[name] = raw
    return result


def source_records(sources):
    data = sources["installed/missions/miss000.dkd"]
    entries = inspect_pair(sources["installed/missions/miss000.dkx"], data)
    records = [(entry, resource_payload(entry, data)) for entry in entries
               if entry["type"] == 12 and entry["name"].startswith("OBJ_")]
    gate.require(len(records) == 45, "Source mission object count changed")
    return records


def new_engine(image, image_size):
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
    engine = Uc(UC_ARCH_X86, UC_MODE_32)
    engine.mem_map(0x400000, (image_size + 0xfff) & ~0xfff)
    engine.mem_write(0x400000, image)
    engine.mem_map(CONTEXT, 0x100000)
    engine.mem_map(STACK, STACK_SIZE)
    return engine


def put(engine, address, value):
    engine.mem_write(address, struct.pack("<I", value & 0xffffffff))


def get(engine, address):
    return struct.unpack("<I", engine.mem_read(address, 4))[0]


def original_selection(image, image_size, payload, name, players):
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_ECX
    engine = new_engine(image, image_size)
    put(engine, CONTEXT + 0x18, APP)
    put(engine, APP + 0xd7c, 1)  # Local/offline branch, no network recorder.
    engine.mem_write(APP + 0xd80, b"\x01")
    engine.mem_write(APP + 0x1a1d, players)
    engine.mem_write(PAYLOAD, payload)
    engine.mem_write(NAME, name.encode("ascii") + b"\0")
    put(engine, 0x5d1f90, 0xabcdef01)
    calls, setjmp_count = [], [0]

    def hook(uc, address, size, unused):
        if address not in (SETJMP, CREATE):
            return
        stack = uc.reg_read(UC_X86_REG_ESP)
        if address == SETJMP:
            setjmp_count[0] += 1
        else:
            args = [get(uc, stack + 4 + 4 * index) for index in range(6)]
            gate.require(uc.reg_read(UC_X86_REG_ECX) == CONTEXT, "Unexpected constructor owner")
            gate.require(args[2:] == [0, 0, PAYLOAD, 0],
                         "Unexpected constructor-boundary arguments")
            calls.append({"factory_type": args[0], "instance_id": args[1]})
        uc.reg_write(UC_X86_REG_EAX, 0)
        uc.reg_write(UC_X86_REG_EIP, get(uc, stack))
        uc.reg_write(UC_X86_REG_ESP, stack + (28 if address == CREATE else 4))

    engine.hook_add(UC_HOOK_CODE, hook)
    top = STACK + STACK_SIZE - 0x1000
    for index, value in enumerate((END, PAYLOAD, len(payload), 0, NAME, CONTEXT)):
        put(engine, top + 4 * index, value)
    engine.reg_write(UC_X86_REG_ESP, top)
    engine.emu_start(ENTRY, END, count=100000)
    gate.require(engine.reg_read(UC_X86_REG_EIP) == END, "Original object selector did not return")
    gate.require(engine.reg_read(UC_X86_REG_EAX) == 0, "Original object selector returned an error")
    gate.require(get(engine, 0x5d1f90) == 0xabcdef01, "Original exception chain not restored")
    gate.require(len(calls) <= 1, "Original selected multiple constructors")
    return {"selected": bool(calls), "factory_type": calls[0]["factory_type"] if calls else 0,
            "instance_id": calls[0]["instance_id"] if calls else None,
            "setjmp_calls": setjmp_count[0]}


def original_enumeration(image, image_size, index, filtered=True):
    from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EIP, UC_X86_REG_ESP
    engine = new_engine(image, image_size)
    header, iterator, raw_index = CONTEXT + 0x1000, CONTEXT + 0x2000, CONTEXT + 0x10000
    buffer, offset_out, filter_arg = CONTEXT + 0x20000, CONTEXT + 0x30000, CONTEXT + 0x40000
    put(engine, CONTEXT + 8, header)
    put(engine, header + 0x30, raw_index)
    put(engine, header + 0x40, iterator)
    put(engine, iterator + 0x24, struct.unpack_from("<I", index, 36)[0])
    put(engine, iterator + 8, 0x543440)  # Original variable-key size callback.
    engine.mem_write(raw_index, index)
    engine.mem_write(filter_arg, b"\x0cOBJ_\0")

    def call(address, arguments):
        top = STACK + STACK_SIZE - 0x1000
        for number, value in enumerate((END, *arguments)):
            put(engine, top + 4 * number, value)
        engine.reg_write(UC_X86_REG_ESP, top)
        engine.emu_start(address, END, count=100000)
        gate.require(engine.reg_read(UC_X86_REG_EIP) == END, "Original B-tree function did not return")
        return engine.reg_read(UC_X86_REG_EAX)

    call(0x570ea0, (CONTEXT, 0x5444c0 if filtered else 0, filter_arg))
    records = []
    while True:
        result = call(0x57af80, (CONTEXT, buffer, offset_out))
        if result == 0xfffffffc:
            return records
        gate.require(result == 0 and len(records) < 1000, "Invalid B-tree enumeration result")
        length = struct.unpack("<h", engine.mem_read(buffer + 0x16, 2))[0]
        records.append({"type": bytes(engine.mem_read(buffer, 1))[0],
                        "name": bytes(engine.mem_read(buffer + 24, length)).decode("ascii"),
                        "data_offset": get(engine, offset_out)})


def input_cases(records):
    start = bytearray(20)
    start[5], start[16] = 1, 3
    masks = [("start-scenario", bytes(start)), ("all-disabled", bytes(20)),
             ("all-one", bytes([1] * 20)), ("all-three", bytes([3] * 20)),
             ("all-255", bytes([255] * 20)),
             ("side-one-only", bytes([1 if 4 <= n < 8 else 0 for n in range(20)])),
             ("side-four-only", bytes([3 if 16 <= n < 20 else 0 for n in range(20)]))]
    cases = []
    for label, players in masks:
        for entry, payload in records:
            cases.append(("source", label, entry["name"], payload, players))
    for tag in [*range(1001), 0x7fffffff, 0xffffffff]:
        cases.append(("tag-stress", str(tag), "OBJ_80000000", struct.pack("<4I", tag, 2, 0, 0), bytes(20)))
    for slot in range(20):
        for value in (0, 1, 2, 3, 128, 255):
            players = bytearray(20)
            players[slot] = value
            cases.append(("slot-stress", f"{slot}:{value}", "OBJ_00000001",
                          struct.pack("<4I", 401, 1, slot // 4, slot % 4), bytes(players)))
    for kind in (0, 2, 3, 0xffffffff):
        cases.append(("kind-bypass", str(kind), "OBJ_00000001",
                      struct.pack("<4I", 401, kind, 0xffffffff, 0xffffffff), bytes(20)))
    for suffix in ("00000000", "00000001", "0000000f", "0000000F",
                   "7fffffff", "80000000", "ffffffff", "FFFFFFFF"):
        cases.append(("id-boundary", suffix, "OBJ_" + suffix, struct.pack("<4I", 401, 2, 0, 0), bytes(20)))
    return cases


def validate(source_root=SOURCE_ROOT, mono_root=None):
    sources = checked_sources(source_root)
    pefile, unicorn, runtime, compiler = gate.prerequisites(Path(source_root) / "installed/ancient.exe", mono_root)
    pe = pefile.PE(data=sources["installed/ancient.exe"])
    gate.require(pe.OPTIONAL_HEADER.ImageBase == 0x400000, "Unexpected image base")
    image, image_size = pe.get_memory_mapped_image(), pe.OPTIONAL_HEADER.SizeOfImage
    records = source_records(sources)
    full_order = original_enumeration(image, image_size, sources["installed/missions/miss000.dkx"], False)
    order = original_enumeration(image, image_size, sources["installed/missions/miss000.dkx"])
    expected = [{"type": e["type"], "name": e["name"], "data_offset": e["offset"]} for e, _ in records]
    gate.require(order == expected and len(full_order) == 63, "Original OBJ enumeration differs from canonical name order")
    cases = input_cases(records)
    results = [original_selection(image, image_size, payload, name, players)
               for _, _, name, payload, players in cases]
    with tempfile.TemporaryDirectory(prefix="mission-object-selection-") as temporary:
        executable = Path(temporary) / "MissionObjectSelectionProbe.exe"
        compiled = subprocess.run(compiler + ["/nologo", "/checked+", "/target:exe", "/out:" + str(executable),
                                              *map(str, SOURCES), str(PROBE)], capture_output=True, text=True, timeout=60)
        if compiled.returncode:
            raise RuntimeError("C# mission selector probe compilation failed:\n" + compiled.stdout + compiled.stderr)
        output = subprocess.run([str(runtime), str(executable)],
                                input="\n".join(name + "\t" + payload.hex() + "\t" + players.hex()
                                                for _, _, name, payload, players in cases) + "\n",
                                capture_output=True, text=True, timeout=60, check=True)
    lines = output.stdout.splitlines()
    gate.require(lines and lines[-1].startswith("GUARDS\t"), "C# contract guards did not complete")
    guards = int(lines.pop().split("\t")[1])
    rows = [[int(value) for value in line.split("\t")] for line in lines]
    gate.require(len(rows) == len(cases), "C# selector returned a different number of cases")
    for case, actual, row in zip(cases, results, rows):
        selected, factory, identifier = row
        gate.require((selected, factory) == (int(actual["selected"]), actual["factory_type"]),
                     f"Mission selection mismatch: {case[:3]}: {actual} / {row}")
        if selected:
            gate.require(identifier == actual["instance_id"], "Unsigned object ID differs from original hex parser")
    counts = {kind: sum(case[0] == kind for case in cases) for kind in sorted({case[0] for case in cases})}
    start_rows = [{"name": name, "class_tag": struct.unpack_from("<I", payload)[0],
                   "kind": struct.unpack_from("<I", payload, 4)[0],
                   "side_index": struct.unpack_from("<I", payload, 8)[0],
                   "player_index": struct.unpack_from("<I", payload, 12)[0],
                   "byte_length": len(payload), "payload_sha256": hashlib.sha256(payload).hexdigest(),
                   **result} for case, result in zip(cases, results)
                  for kind, label, name, payload, _ in [case] if kind == "source" and label == "start-scenario"]
    gate.require(gate.digest(FIXTURE) == FIXTURE_SHA256, "Pinned mission-selection fixture changed")
    fixture = json.loads(FIXTURE.read_text())
    gate.require(fixture["source_start_scenario"] == start_rows and
                 fixture["original_enumeration"]["records"] == order and
                 fixture["mission_source_hashes"] == SOURCE_HASHES,
                 "Current original execution differs from the persisted mission-selection fixture")
    return {"original_sha256": gate.EXPECTED, "mission_source_hashes": SOURCE_HASHES,
            "scope": "Original local/offline object eligibility, factory code, canonical uint32 ID and DB iteration only",
            "entry_point": hex(ENTRY), "case_count": len(cases), "passed": len(cases),
            "case_groups": counts, "configuration_csharp_checks": guards, "checked_compilation": True,
            "original_enumeration": {"all_record_count": len(full_order), "object_count": len(order),
                                      "records": order, "hooks": {}},
            "source_start_scenario": start_rows,
            "source_sha256": {str(path.relative_to(ROOT)): gate.digest(path) for path in SOURCES},
            "probe_sha256": gate.digest(PROBE), "compiler_command": compiler,
            "fixture_sha256": FIXTURE_SHA256,
            "mono_runtime": str(runtime), "unicorn_version": unicorn.__version__,
            "hooked_callees": {hex(SETJMP): "normal return 0", hex(CREATE): "record factory/ID; no constructor or Init"},
            "limits": ["No constructor, class Init, object state, graphics, simulation or AI is executed",
                       "Local offline branch only; network/replay recording and DB allocation are excluded",
                       "Original DB traversal uses raw mapped verified index, not original OS file opening",
                       "Canonical OBJ_8hex names only; noncanonical parser/error behavior is excluded",
                       "C# rejects malformed kind1 slots; original uses raw unchecked memory indexing",
                       "General DB key order is type, signed16 name length, raw name bytes; canonical OBJ names all have length12"],
            "cases": [{"group": group, "label": label, "name": name,
                       "header_words": list(struct.unpack_from("<4I", payload)), "players_hex": players.hex(),
                       "original": result} for (group, label, name, payload, players), result in zip(cases, results)]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=SOURCE_ROOT)
    parser.add_argument("--mono-root", type=Path)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    arguments = parser.parse_args(argv)
    if arguments.output.exists():
        parser.error("Select a fresh report path; previous evidence is preserved")
    try:
        report = validate(arguments.source_root, arguments.mono_root)
    except MissingPrerequisite as error:
        parser.exit(2, str(error) + "\n")
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    with arguments.output.open("x") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(f"{report['passed']} original x86 / C# mission selection cases passed; {report['configuration_csharp_checks']} C# guards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
