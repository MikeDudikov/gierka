#!/usr/bin/env python3
"""Execute original SpriteEngine publication/selection for a pinned move trace.

The full setter and bounded renderer pointer-selection prelude run without
hooks. The synthetic active composite node omits immediate-draw flags. This
checks the engine-selected pose, not a complete original framebuffer.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import struct

try:
    from .stage_mission_objects import SOURCE_HASHES
    from .validate_boss_ai_gate import ROOT, MissingPrerequisite, require
except ImportError:
    from stage_mission_objects import SOURCE_HASHES
    from validate_boss_ai_gate import ROOT, MissingPrerequisite, require

SOURCE_ROOT = ROOT / "reference/raw/ancient-conquest"
MOVEMENT_FIXTURE = ROOT / "tests/fixtures/prepared_ship_movement.json"
MOVEMENT_SHA256 = "28931c2849e05f46c7fd005c0f7b923f1d19bf26c045148a1a2388191cf2d374"
PUBLICATION_FIXTURE = ROOT / "tests/fixtures/ship_forward_publication.json"
PUBLICATION_SHA256 = "9567c1a18cd894892af9a97841ff5c73399a0b0030847a7a562a064b2f42b666"
OUTPUT = ROOT / "artifacts/movement/animation/ship-forward-publication-tracked-validation.json"
CONTEXT, NODE, ARRAY, DATA = 0x70000000, 0x70001000, 0x70002000, 0x70003000
STACK, END = 0x71000000, 0x72000000


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def validate(source_root=SOURCE_ROOT):
    checked = {}
    for name, expected in SOURCE_HASHES.items():
        path = Path(source_root) / name
        if not path.is_file():
            raise MissingPrerequisite("Original source missing: " + str(path))
        raw = path.read_bytes()
        if digest(raw) != expected:
            raise ValueError("Original source hash differs: " + name)
        checked[name] = raw
    movement_raw = MOVEMENT_FIXTURE.read_bytes()
    publication_raw = PUBLICATION_FIXTURE.read_bytes()
    require(digest(movement_raw) == MOVEMENT_SHA256, "Pinned original movement fixture changed")
    require(digest(publication_raw) == PUBLICATION_SHA256, "Pinned original publication fixture changed")
    movement, expected = json.loads(movement_raw), json.loads(publication_raw)
    case = next(case for case in movement["cases"] if case["label"] == "southwest_pending1")
    require(len(case["trace"]) == 45, "Unexpected original route trace length")
    try:
        pefile = importlib.import_module("pefile")
        unicorn = importlib.import_module("unicorn")
    except ModuleNotFoundError as error:
        raise MissingPrerequisite("Install tools/requirements-analysis.txt for x86 publication validation") from error
    from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EIP, UC_X86_REG_ESP
    pe = pefile.PE(data=checked["installed/ancient.exe"])
    require(pe.OPTIONAL_HEADER.ImageBase == 0x400000, "Unexpected original image base")
    engine = unicorn.Uc(unicorn.UC_ARCH_X86, unicorn.UC_MODE_32)
    engine.mem_map(0x400000, (pe.OPTIONAL_HEADER.SizeOfImage + 4095) & ~4095)
    engine.mem_write(0x400000, pe.get_memory_mapped_image())
    engine.mem_map(CONTEXT, 0x10000)
    engine.mem_map(STACK, 0x10000)
    engine.mem_map(END, 0x1000)

    def put(address, value):
        engine.mem_write(address, struct.pack("<I", value & 0xffffffff))

    def get(address):
        return struct.unpack("<I", engine.mem_read(address, 4))[0]

    for address, value in ((CONTEXT + 0x1a0, 1), (CONTEXT + 0x1b0, ARRAY), (ARRAY, NODE),
                           (NODE, 0x04008000), (NODE + 0xc0, 3), (NODE + 0xc4, 20),
                           (NODE + 0xc8, 152), (NODE + 0xcc, DATA),
                           (NODE + 0x18, 1028), (NODE + 0x1c, 132)):
        put(address, value)
    publications = {row["tick"]: row["arguments"] for row in case["service_boundaries"]
                    if row["entry"] == "0x50d5f0"}
    require(len(publications) == sum(row["entry"] == "0x50d5f0" for row in case["service_boundaries"]),
            "Duplicate source frame publication in a single call")
    rows = []
    for trace in case["trace"]:
        arguments = publications.get(trace["tick"])
        if arguments is not None:
            slot, frame, x, y, mask, cell_x, cell_y = arguments
            require(slot == 0 and mask == cell_x == cell_y == 0xffffffff, "Unsupported native publication arguments")
            require(frame == trace["frame"] and [x, y] == trace["world"], "DrawSprite must publish after MoveShip's phase tail")
            sp = STACK + 0xf000
            for index, value in enumerate((END, CONTEXT, 0, frame, x, y)):
                put(sp + index * 4, value)
            engine.reg_write(UC_X86_REG_ESP, sp)
            engine.emu_start(0x55ec00, END, count=200)
            require(engine.reg_read(UC_X86_REG_EIP) == END, "Original frame setter did not return")
            require(get(NODE + 0xc4) == frame, "Original frame publication differs")
            require([get(NODE + 0x18), get(NODE + 0x1c)] == [x, y], "Original position publication differs")
        # The original renderer indexes the published engine field, not the
        # independent AnimObj frame that movement may have advanced this tick.
        engine.reg_write(UC_X86_REG_EAX, NODE)
        engine.emu_start(0x565686, 0x5656c4, count=40)
        require(engine.reg_read(UC_X86_REG_EIP) == 0x5656c4, "Original renderer selection did not reach pixelcall boundary")
        frame = get(NODE + 0xc4)
        require(get(0x5d0888) == 3, "Original renderer component count differs")
        require(get(0x5d08bc) == DATA + frame * 3 * 10, "Original renderer selected another composite pose")
        rows.append({"call": trace["tick"], "stamp": trace["stamp"], "stored_frame": trace["frame"],
                     "drawn_frame": frame, "published": arguments is not None,
                     "render_world_x": get(NODE + 0x18), "render_world_y": get(NODE + 0x1c)})
    require(rows == expected["rows"], "Original publication/selection differs from its pinned fixture")
    require(digest(MOVEMENT_FIXTURE.read_bytes()) == MOVEMENT_SHA256 and
            digest(PUBLICATION_FIXTURE.read_bytes()) == PUBLICATION_SHA256, "Evidence fixture changed during validation")
    return {"original_exe_sha256": SOURCE_HASHES["installed/ancient.exe"], "source_hashes": SOURCE_HASHES,
            "movement_fixture_sha256": MOVEMENT_SHA256, "publication_fixture_sha256": PUBLICATION_SHA256,
            "setter_va": "0x55ec00", "renderer_selection_range": ["0x565686", "0x5656c4"],
            "hooked_callees": {}, "case_count": len(rows), "passed": len(rows), "rows": rows,
            "limits": expected["limits"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=SOURCE_ROOT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("Refusing to replace an existing report; select a fresh --output")
    try:
        report = validate(args.source_root)
    except MissingPrerequisite as error:
        parser.exit(2, str(error) + "\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(f"{report['passed']} original no-hook setter/renderer-selection cases passed")


if __name__ == "__main__":
    main()
