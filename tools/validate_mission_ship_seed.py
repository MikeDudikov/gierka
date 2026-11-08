#!/usr/bin/env python3
"""Validate the bounded ShipClassTy source recipe, not a simulated ship.

The original ctor/LoadDateBase/damage-state code execute with explicit service
boundaries. A separate graphics-position instruction range has no hooks.
Class/world creation, command execution, combat, sprite loading and AI are not
implemented or validated by this recipe.
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
    from . import validate_mission_object_selection as selection
else:
    import validate_boss_ai_gate as gate
    import validate_mission_object_selection as selection

ROOT = gate.ROOT
MissingPrerequisite = gate.MissingPrerequisite
SOURCES = [ROOT / "Unity/AncientConquest/Assets/AncientConquest/Runtime" / name
           for name in ("MissionObjectSeed.cs", "MissionShipSeed.cs")]
PROBE = ROOT / "tests/fixtures/MissionShipSeedProbe.cs"
FIXTURE = ROOT / "tests/fixtures/mission_ship_seed.json"
FIXTURE_SHA256 = "1ae221249bf8812b5a033c769134b22d6266e85d232d18a53e8473fa0cfcdab9"
OUTPUT = ROOT / "artifacts/units/initialization/ship-seed-csharp-validation.json"
OBJ, APP, SYSTEM, PAYLOAD, SPRITE = (selection.CONTEXT, selection.CONTEXT + 0x10000,
                                  selection.CONTEXT + 0x20000, selection.CONTEXT + 0x30000,
                                  selection.CONTEXT + 0x40000)
END = selection.END
CTOR, LOAD, DAMAGE_STATE = 0x4dc3f0, 0x4dfa90, 0x4be030
ANCHOR_START, ANCHOR_STOP = 0x4e0160, 0x4e01d6


def original_projection(image, image_size, payload, instance):
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_ECX
    engine = selection.new_engine(image, image_size)
    put, get = lambda a, v: selection.put(engine, a, v), lambda a: selection.get(engine, a)
    byte = lambda a: bytes(engine.mem_read(a, 1))[0]
    signed = lambda a: struct.unpack("<i", engine.mem_read(a, 4))[0]
    calls, requested_health = [], []
    phase = ["ctor"]

    def ret(clean=0, eax=0):
        stack = engine.reg_read(UC_X86_REG_ESP)
        engine.reg_write(UC_X86_REG_EIP, get(stack))
        engine.reg_write(UC_X86_REG_ESP, stack + 4 + clean)
        engine.reg_write(UC_X86_REG_EAX, eax)

    def hook(uc, address, size, unused):
        if address == 0x587318:
            ret()
            return
        if address == 0x4ac110 and phase[0] == "load":
            # Observe the actual health-percentage argument, without replacing
            # the original static table lookup/multiply/divide instructions.
            stack = uc.reg_read(UC_X86_REG_ESP)
            gate.require(get(stack + 8) == 650 and get(stack + 12) == 0x5bb4b0,
                         "Unexpected source health scaling call")
            requested_health.append(struct.unpack("<i", uc.mem_read(stack + 16, 4))[0])
        boundaries = {0x4e7220: (0, "initial command dispatch"),
                      0x4bee60: (0, "derived combat/navigation initialization"),
                      0x50e640: (4, "object system-message dispatch"),
                      0x4e1bb0: (4, "damage-state graphics request"),
                      0x4b97d0: (16, "initial order queue")}
        if address in boundaries:
            clean, label = boundaries[address]
            stack = uc.reg_read(UC_X86_REG_ESP)
            calls.append({"entry": hex(address), "service": label,
                          "arguments": [get(stack + 4 + index * 4) for index in range(clean // 4)],
                          "damage_state": byte(OBJ + 0x74)})
            ret(clean)
        if address in (0x556610, 0x556880):
            raise AssertionError("Unexpected original error path: " + hex(address))

    engine.hook_add(UC_HOOK_CODE, hook)

    def invoke(address, arguments=()):
        top = selection.STACK + selection.STACK_SIZE - 0x1000
        for index, value in enumerate((END, *arguments)):
            put(top + 4 * index, value)
        engine.reg_write(UC_X86_REG_ESP, top)
        engine.reg_write(UC_X86_REG_ECX, OBJ)
        engine.emu_start(address, END, count=100000)
        gate.require(engine.reg_read(UC_X86_REG_EIP) == END, "Original ship projection did not return")

    put(0x5d1f90, 0xabcdef01)
    invoke(CTOR)
    gate.require(get(OBJ) == 0x59b48c, "Original ctor installed another vtable")
    for offset, value in ((0x10, APP), (0x4c, instance), (0x68, APP), (0x6c, SYSTEM), (0x70, SYSTEM)):
        put(OBJ + offset, value)
    engine.mem_write(PAYLOAD, payload)
    phase[0] = "load"
    invoke(LOAD, (PAYLOAD,))
    gate.require(requested_health and len(requested_health) == 1, "Original health argument was not observed once")
    gate.require(get(0x5d1f90) == 0xabcdef01, "LoadDateBase did not restore the exception chain")
    phase[0] = "damage-state"
    invoke(DAMAGE_STATE)
    gate.require(get(0x5d1f90) == 0xabcdef01, "Damage-state projection changed the exception chain")
    return {"instance_id": get(OBJ + 0x4c), "runtime_class_tag": get(OBJ + 0x50),
            "owner_side": byte(OBJ + 0x54), "owner_player": byte(OBJ + 0x55),
            "origin_side": byte(OBJ + 0x250), "source_player_slot": byte(OBJ + 0x24f),
            "model_value": struct.unpack_from("<I", payload, 28)[0], "model_variant": byte(OBJ + 0x25a),
            "cell_x": signed(OBJ + 0x5a3), "cell_y": signed(OBJ + 0x5a7),
            "heading": struct.unpack("b", engine.mem_read(OBJ + 0x5af, 1))[0],
            "requested_health_percent": requested_health[0],
            "source_equipment_a": byte(OBJ + 0x27a),
            "source_equipment_b": struct.unpack("b", engine.mem_read(OBJ + 0x27b, 1))[0],
            "source_order_count": struct.unpack_from("<I", payload, 512)[0],
            "observed_raw_health": signed(OBJ + 0x271),
            "observed_raw_max_health": signed(0x5c76b0 + byte(OBJ + 0x25a) * 4),
            "observed_damage_state": byte(OBJ + 0x74), "masked_flags": get(OBJ + 0x261),
            "calls": calls}


def original_anchor(image, image_size, x, y, heading, width, height):
    from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_ECX
    engine = selection.new_engine(image, image_size)
    for address, value in ((OBJ + 0x8be, SPRITE), (OBJ + 0x5a3, x), (OBJ + 0x5a7, y),
                           (SPRITE + 0x61, width), (SPRITE + 0x65, height)):
        selection.put(engine, address, value)
    engine.mem_write(OBJ + 0x5af, bytes([heading & 255]))
    top = selection.STACK + selection.STACK_SIZE - 0x1000
    selection.put(engine, top, END)
    engine.reg_write(UC_X86_REG_ESP, top)
    engine.reg_write(UC_X86_REG_ECX, OBJ)
    engine.emu_start(ANCHOR_START, ANCHOR_STOP, count=100)
    gate.require(engine.reg_read(UC_X86_REG_EIP) == ANCHOR_STOP, "Original position range did not reach the sound boundary")
    gate.require(selection.get(engine, SPRITE + 0x7d) == 2, "Original sprite frame mode changed")
    return tuple(struct.unpack("<i", engine.mem_read(SPRITE + offset, 4))[0] for offset in (0x59, 0x5d, 0x45))


def source_records(sources):
    records = [(entry, payload) for entry, payload in selection.source_records(sources)
               if struct.unpack_from("<I", payload)[0] == 200]
    gate.require(len(records) == 8 and all(len(payload) == 616 for _, payload in records),
                 "Source ship layout/count changed")
    return records


def input_cases(records):
    cases = [("source", entry["name"], entry["name"], payload, 64, 64) for entry, payload in records]
    base = records[0][1]

    def add(group, label, changes, width=64, height=64):
        payload = bytearray(base)
        for offset, value in changes.items():
            struct.pack_into("<I", payload, offset, value & 0xffffffff)
        cases.append((group, label, "OBJ_80000000", bytes(payload), width, height))

    for variant in range(12):
        for heading in range(8):
            add("variant-heading", f"{variant}:{heading}", {28: variant, 44: heading})
    for value in (0, 1, 2, 3, 127, 128, 255, 0x12340001, 0x80000000, 0xffffffff):
        add("byte-fields", str(value), {20: value, 24: value ^ 1, 56: value, 60: value})
    for value in (0, 1, 6, 7, 11, 0x12340000, 0x12340006, 0x80000007, 0xffffff00, 0xffffff06):
        add("full-model", str(value), {28: value})
    for value in (-0x80000000, -100, -1, 0, 1, 35, 36, 70, 71, 100, 101, 0x7fffffff):
        add("health-input", str(value), {48: value})
    for count in (0, 1, 2, 5, 0x80000000, 0xffffffff):
        payload = bytearray(base)
        payload[516:] = bytes(len(payload) - 516)
        struct.pack_into("<I", payload, 512, count)
        cases.append(("order-metadata", str(count), "OBJ_00000001", bytes(payload), 64, 64))
    coordinates = ((0, 0), (-1, 23), (23, -1), (-0x80000000, 0x7fffffff),
                   (0x7fffffff, -0x80000000), (0x40000000, -0x40000000))
    dimensions = ((64, 64), (63, 65), (96, 128), (1, 2), (8192, 8191),
                  (0x7fffffff, -0x80000000), (-1, 0))
    for number, (x, y) in enumerate(coordinates):
        for width, height in dimensions:
            add("anchor-arithmetic", f"{x},{y}:{width},{height}",
                {36: x, 40: y, 44: (0, 1, 127, 128, 255, 0x12340004)[number]}, width, height)
    return cases


def validate(source_root=selection.SOURCE_ROOT, mono_root=None):
    sources = selection.checked_sources(source_root)
    pefile, unicorn, runtime, compiler = gate.prerequisites(Path(source_root) / "installed/ancient.exe", mono_root)
    pe = pefile.PE(data=sources["installed/ancient.exe"])
    gate.require(pe.OPTIONAL_HEADER.ImageBase == 0x400000, "Unexpected original image base")
    image, image_size = pe.get_memory_mapped_image(), pe.OPTIONAL_HEADER.SizeOfImage
    records = source_records(sources)
    cases = input_cases(records)
    projections, anchors = [], []
    for _, _, name, payload, width, height in cases:
        projection = original_projection(image, image_size, payload, int(name[4:], 16))
        projections.append(projection)
        anchors.append(original_anchor(image, image_size, projection["cell_x"], projection["cell_y"],
                                       projection["heading"], width, height))
    with tempfile.TemporaryDirectory(prefix="mission-ship-seed-") as temporary:
        executable = Path(temporary) / "MissionShipSeedProbe.exe"
        compiled = subprocess.run(compiler + ["/nologo", "/checked+", "/target:exe", "/out:" + str(executable),
                                              *map(str, SOURCES), str(PROBE)], capture_output=True, text=True, timeout=60)
        if compiled.returncode:
            raise RuntimeError("C# ship recipe probe compilation failed:\n" + compiled.stdout + compiled.stderr)
        output = subprocess.run([str(runtime), str(executable)],
            input="\n".join(name + "\t" + payload.hex() + "\t" + str(width) + "\t" + str(height)
                            for _, _, name, payload, width, height in cases) + "\n",
            capture_output=True, text=True, timeout=60, check=True)
    lines = output.stdout.splitlines()
    gate.require(lines and lines[-1].startswith("GUARDS\t"), "C# ship contract checks did not finish")
    guards = int(lines.pop().split("\t")[1])
    rows = [[int(value) for value in line.split("\t")] for line in lines]
    gate.require(len(rows) == len(cases), "C# ship recipe returned a different case count")
    for case, projection, anchor, row in zip(cases, projections, anchors, rows):
        x, y, frame = anchor
        expected = [projection[key] for key in ("instance_id", "owner_side", "owner_player", "model_value",
                    "model_variant", "runtime_class_tag", "cell_x", "cell_y", "heading")]
        expected += [frame, projection["requested_health_percent"], projection["source_equipment_a"],
                     projection["source_equipment_b"], projection["source_order_count"], x, y]
        gate.require(row == expected, f"Ship projection mismatch {case[:3]}: x86 {expected} / C# {row}")
    counts = {kind: sum(case[0] == kind for case in cases) for kind in sorted({case[0] for case in cases})}
    source_rows = [{"resource_name": entry["name"], "payload_hex": payload.hex(),
                    "payload_sha256": hashlib.sha256(payload).hexdigest(), **projection}
                   for (entry, payload), projection in zip(records, projections[:len(records)])]
    gate.require(gate.digest(FIXTURE) == FIXTURE_SHA256, "Pinned ship initialization fixture changed")
    fixture = json.loads(FIXTURE.read_text())
    gate.require(fixture["records"] == source_rows and
                 fixture["mission_source_hashes"] == selection.SOURCE_HASHES,
                 "Current original execution differs from source ship fixture")
    return {"original_sha256": gate.EXPECTED, "mission_source_hashes": selection.SOURCE_HASHES,
            "scope": "Bounded ShipClassTy ctor/LoadDateBase field projection and no-hook graphics-position range vs actual C# recipe",
            "case_count": len(cases), "passed": len(cases), "case_groups": counts,
            "source_count": len(records), "csharp_contract_checks": guards, "checked_compilation": True,
            "source_sha256": {str(path.relative_to(ROOT)): gate.digest(path) for path in SOURCES},
            "probe_sha256": gate.digest(PROBE), "fixture_sha256": FIXTURE_SHA256,
            "compiler_command": compiler, "mono_runtime": str(runtime), "unicorn_version": unicorn.__version__,
            "original_source_records": source_rows,
            "original_projection_hooks": {"0x587318": "normal setjmp return", "0x4e7220": "skip initial command dispatch",
                "0x4bee60": "skip derived combat/navigation initialization", "0x50e640": "skip object system-message dispatch",
                "0x4e1bb0": "record damage-state graphics request", "0x4b97d0": "skip initial order queue (stress cases only)"},
            "anchor_instruction_range": {"start": hex(ANCHOR_START), "stop_before": hex(ANCHOR_STOP), "hooks": {}},
            "limits": ["This is a source recipe, not complete ShipClassTy creation or initial world simulation",
                       "Original LoadDateBase's own direct field writes and static health arithmetic execute; listed service boundaries do not",
                       "SourceOrderCount and ModelValue preserve exact raw source words; no command behavior is implemented",
                       "Damage-state observation is conditional on the omitted derived combat setup; source eight healthy references select state1",
                       "Anchor stress dimensions are arithmetic inputs, not claims about actual source frame sizes",
                       "Negative headings, overflow values and malformed world coordinates are bounded arithmetic stress, not playable states",
                       "No original sprite loading, compositing, palette mapping, collision validation, navigation or AI is executed here"],
            "cases": [{"group": group, "label": label, "name": name, "frame_dimensions": [width, height],
                       "original": projection, "anchor": anchor}
                      for (group, label, name, _, width, height), projection, anchor in zip(cases, projections, anchors)]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=selection.SOURCE_ROOT)
    parser.add_argument("--mono-root", type=Path)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("Select a fresh output path; previous evidence is preserved")
    try:
        report = validate(args.source_root, args.mono_root)
    except MissingPrerequisite as error:
        parser.exit(2, str(error) + "\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(f"{report['passed']} original x86 / C# ship recipe cases passed; {report['csharp_contract_checks']} C# guards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
