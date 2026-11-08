#!/usr/bin/env python3
"""Compare actual Unity C# campaign setup against bounded original x86 code.

Executes original player-selection instructions without hooks, then its saved
WIN_VIEW message-argument lookup without hooks. No mission objects, full game,
source camera redraw or modern viewport/FOV is executed by this validator.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile

if __package__:
    from .validate_boss_ai_gate import ROOT, EXPECTED, ORIGINAL, MissingPrerequisite, digest, prerequisites, require
    from .inspect_dkx import inspect_pair
    from .decode_sprite import resource_payload
else:
    from validate_boss_ai_gate import ROOT, EXPECTED, ORIGINAL, MissingPrerequisite, digest, prerequisites, require
    from inspect_dkx import inspect_pair
    from decode_sprite import resource_payload

SOURCE = ROOT / "Unity/AncientConquest/Assets/AncientConquest/Runtime/MissionInitialSetup.cs"
PROBE = ROOT / "tests/fixtures/MissionInitialSetupProbe.cs"
MISSION = ROOT / "reference/raw/ancient-conquest/installed/missions/miss000"
OUTPUT = ROOT / "artifacts/objects/camera/mission-initial-setup-validation.json"
MISSION_DKX_SHA256 = "b4b2fda60bb38e837b6d0548caa86229e1fbebf8cb9fd806c4f39c9bd75835ce"
MISSION_DKD_SHA256 = "a77e801a93baafd6942db9087d7541f8c85ed2f3c88d440b9f9e81b45ba9a0d1"
DESCRIPTOR_SHA256 = "458dac3b5942c5dff55d0640cb354a3761be9c824074cb99c29a939856a03ded"
SAVED_VIEWS_SHA256 = "b8a17a6b40efc364c44dc2a1470a1ace8188de20e6cf057edd6865eff04800f8"
SELECT_START, SELECT_END = 0x5380d7, 0x538195
VIEW_START, VIEW_END = 0x5100d8, 0x510123
APP, DESCRIPTOR = 0x70000000, 0x70010000
STACK, STACK_SIZE = 0x7ff00000, 0x100000
EXPECTED_GUARDS = {
    "descriptor_null", "descriptor_short", "views_null", "views_short", "views_long",
    "missing_selected_pair", "sources_unchanged", "unsigned_saved_origin", "source_extent",
    "copy_isolation", "input_lifetime_isolation",
} | {"descriptor_count_" + str(n) for n in (-1, 0, 0x7fffffff, 2)} | {
    "side_" + str(n) for n in (-1, 5, 0x7fffffff)
} | {"player_" + str(n) for n in (-1, 4, 0x7fffffff)} | {
    "campaign_" + str(n) for n in (-1, 4, -0x80000000, 0x7fffffff)
}


def guarded(raw, expected, message):
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(message)


def load_reference(mission=MISSION):
    mission = Path(mission)
    dkx, dkd = mission.with_suffix(".dkx"), mission.with_suffix(".dkd")
    if not dkx.is_file() or not dkd.is_file():
        raise MissingPrerequisite("Original miss000 inputs missing")
    index, data = dkx.read_bytes(), dkd.read_bytes()
    guarded(index, MISSION_DKX_SHA256, "Original miss000 index hash differs")
    guarded(data, MISSION_DKD_SHA256, "Original miss000 payload hash differs")
    entries = inspect_pair(index, data)
    result = []
    for kind, name, expected in ((0, "DESCRIPTOR", DESCRIPTOR_SHA256),
                                 (12, "WIN_VIEW", SAVED_VIEWS_SHA256)):
        selected = [entry for entry in entries if (entry["type"], entry["name"]) == (kind, name)]
        if len(selected) != 1:
            raise ValueError("Original source resource is missing or ambiguous: " + name)
        raw = resource_payload(selected[0], data)
        guarded(raw, expected, "Original resource hash differs: " + name)
        result.append(raw)
    return tuple(result)


def synthetic_descriptor(pairs, trailer=0):
    # Opaque fields carry noise; only the source selection fields are assigned.
    raw = bytearray((index * 37 + 13) & 255 for index in range(20 + len(pairs) * 104 + trailer))
    struct.pack_into("<i", raw, 16, len(pairs))
    for index, (side, player) in enumerate(pairs):
        struct.pack_into("<ii", raw, 20 + index * 104 + 8, side, player)
    return bytes(raw)


def synthetic_views(seed):
    coordinates = (0, 1, 15, 24, 255, 256, 32767, 32768, 65534, 65535)
    return b"".join(struct.pack("<HH", coordinates[(index + seed) % len(coordinates)],
                               coordinates[(index * 3 + seed + 1) % len(coordinates)])
                    for index in range(20))


def input_cases(descriptor, saved_views):
    cases = [{"name": "source-miss000-campaign0", "descriptor": descriptor,
              "saved_views": saved_views, "campaign": 0, "source": True}]
    pairs = [(side, player) for side in range(5) for player in range(4)]
    for campaign, selected in enumerate(((1, 1), (0, 0), (2, 2), (3, 3))):
        for index, other in enumerate(pairs):
            for order, records in enumerate(((selected, other), (other, selected))):
                cases.append({"name": f"campaign{campaign}-pair{index}-order{order}",
                              "descriptor": synthetic_descriptor(records, trailer=index % 5),
                              "saved_views": synthetic_views(index + order), "campaign": campaign,
                              "source": False})
        for ordering, records in enumerate((pairs, pairs[::-1], [selected] * 3, [selected])):
            cases.append({"name": f"campaign{campaign}-table-order{ordering}",
                          "descriptor": synthetic_descriptor(records),
                          "saved_views": synthetic_views(campaign + ordering), "campaign": campaign,
                          "source": False})
    return cases


def original_case(image, image_size, case):
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
    from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_EBP, UC_X86_REG_EBX

    engine = Uc(UC_ARCH_X86, UC_MODE_32)
    engine.mem_map(0x400000, (image_size + 0xfff) & ~0xfff)
    engine.mem_write(0x400000, image)
    engine.mem_map(APP, 0x100000)
    engine.mem_map(STACK, STACK_SIZE)
    def write32(address, value):
        engine.mem_write(address, struct.pack("<I", value & 0xffffffff))
    engine.mem_write(DESCRIPTOR, case["descriptor"])
    write32(APP + 0x19ed, DESCRIPTOR)
    engine.mem_write(APP + 0x3212, b"\xff\xaa")
    frame = STACK + STACK_SIZE - 0x1000
    write32(frame + 12, case["campaign"])
    engine.reg_write(UC_X86_REG_ESP, frame - 0x100)
    engine.reg_write(UC_X86_REG_EBP, frame)
    engine.reg_write(UC_X86_REG_EBX, APP)
    engine.emu_start(SELECT_START, SELECT_END, count=10000)
    require(engine.reg_read(UC_X86_REG_EIP) == SELECT_END, "Original selection did not reach the bounded end")
    side, player = engine.mem_read(APP + 0x3212, 2)
    require(side != 255, "A differential case has no selected player; unknown previous-slot state is outside this API")
    players = bytes(engine.mem_read(APP + 0x1a1d, 20))
    engine.mem_write(APP + 0x2ef5, case["saved_views"])
    engine.emu_start(VIEW_START, VIEW_END, count=1000)
    require(engine.reg_read(UC_X86_REG_EIP) == VIEW_END, "Original view lookup did not reach the dispatch boundary")
    packed = struct.unpack("<I", engine.mem_read(frame - 0x1c, 4))[0]
    message = struct.unpack("<III", engine.mem_read(frame - 0x28, 12))
    require(message == (0x2f4, 3, 0xcba), "Original view lookup prepared a different message")
    return (side, player, packed & 65535, packed >> 16, 9, 8, players)


def validate(original=ORIGINAL, mission=MISSION, mono_root=None):
    descriptor, saved_views = load_reference(mission)
    pefile, _unicorn, runtime, compiler = prerequisites(original, mono_root)
    guarded(Path(original).read_bytes(), EXPECTED, "Original executable hash differs")
    pe = pefile.PE(str(original))
    image, image_size = pe.get_memory_mapped_image(), pe.OPTIONAL_HEADER.SizeOfImage
    cases = input_cases(descriptor, saved_views)
    expected = [original_case(image, image_size, case) for case in cases]
    source_sha, probe_sha = digest(SOURCE), digest(PROBE)
    lines = ["\t".join((base64.b64encode(case["descriptor"]).decode(),
                         base64.b64encode(case["saved_views"]).decode(), str(case["campaign"])))
             for case in cases]
    with tempfile.TemporaryDirectory(prefix="mission-setup-csharp-") as temporary:
        executable = Path(temporary) / "MissionInitialSetupProbe.exe"
        compiled = subprocess.run(compiler + ["/nologo", "/checked+", "/target:exe", "/out:" + str(executable),
                                              str(SOURCE), str(PROBE)], capture_output=True, text=True, timeout=60)
        if compiled.returncode:
            raise RuntimeError("C# initial-setup probe compilation failed:\n" + compiled.stdout + compiled.stderr)
        output = subprocess.run([str(runtime), str(executable)], input="\n".join(lines) + "\n",
                                check=True, capture_output=True, text=True, timeout=60)
    require(digest(SOURCE) == source_sha and digest(PROBE) == probe_sha, "Source changed during validation")
    rows, guards = [], []
    for line in output.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) == 2 and fields[0] == "CHECK":
            guards.append(fields[1])
        elif len(fields) == 8 and fields[0] == "ROW":
            rows.append(tuple(int(value) for value in fields[1:7]) + (base64.b64decode(fields[7], validate=True),))
        else:
            raise ValueError("Unexpected C# setup output: " + line)
    require(len(guards) == len(EXPECTED_GUARDS) and set(guards) == EXPECTED_GUARDS,
            "C# initial-setup guards are missing, duplicated or unexpected")
    require(len(rows) == len(expected), "Actual C# returned an unexpected row count")
    evidence = []
    for case, native, actual in zip(cases, expected, rows):
        require(actual == native, f"Initial setup mismatch at {case['name']}: x86{native!r}/C#{actual!r}")
        evidence.append({"name": case["name"], "campaign_index": case["campaign"], "source_miss000": case["source"],
                         "selected_side": native[0], "selected_player": native[1], "saved_origin": list(native[2:4]),
                         "players_descriptor_hex": native[6].hex()})
    return {"kind": "Bounded original campaign-selection and saved-view lookup vs actual Unity C#",
            "original_sha256": EXPECTED, "mission_dkx_sha256": MISSION_DKX_SHA256,
            "mission_dkd_sha256": MISSION_DKD_SHA256, "descriptor_sha256": DESCRIPTOR_SHA256,
            "saved_views_sha256": SAVED_VIEWS_SHA256,
            "original_ranges": [[hex(SELECT_START), hex(SELECT_END)], [hex(VIEW_START), hex(VIEW_END)]],
            "intercepted_functions": [], "csharp_source": str(SOURCE.relative_to(ROOT)),
            "csharp_sha256": source_sha, "probe_sha256": probe_sha, "validator_sha256": digest(Path(__file__)),
            "mono_runtime": str(runtime), "compiler_command": compiler, "checked_compilation": True,
            "case_count": len(rows), "passed": len(rows), "source_case_count": 1,
            "synthetic_case_count": len(rows) - 1, "cases": evidence,
            "csharp_guard_count": len(guards), "csharp_guard_checks": guards,
            "scope": "Pure immutable player setup; source9x8 extent is a constructor constant proved separately; no simulation or modern FOV",
            "excluded": ["Complete StartGame, source redraw, world objects and game loop not executed",
                         "Synthetic descriptors for campaigns1..3 test the selection rule, not those campaigns' actual mission data",
                         "Absent selected player is explicitly rejected: original keeps an unknown previous application's slot byte",
                         "C# length/bounds/immutability checks are defensive contracts, not original malformed-input equivalence",
                         "Saved views must be a supplied80byte payload; optional-loader fallback is covered only by the separate evidence"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, default=ORIGINAL)
    parser.add_argument("--mission", type=Path, default=MISSION)
    parser.add_argument("--mono-root", type=Path)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("Refusing to replace an existing report; select a fresh --output")
    try:
        report = validate(args.original, args.mission, args.mono_root)
    except MissingPrerequisite as error:
        parser.exit(2, str(error) + "\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(f"{report['passed']} actual C#/original x86 setup cases and {report['csharp_guard_count']} C# guard checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
