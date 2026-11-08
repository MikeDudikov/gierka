#!/usr/bin/env python3
"""Compare actual Unity C# map references with the original x86 lookup fixture.

The checked-in oracle was produced by executing original 0x545190 and its
lookup callees without hooks, using reconstructed runtime library/DArray inputs.
This validator checks that frozen oracle's provenance and payload hashes, then
compiles the actual Unity C# source. It does not execute the original game,
rebuild libraries, select bitmap types in C#, or validate rendering/gameplay.
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
    from .validate_boss_ai_gate import ROOT, EXPECTED, MissingPrerequisite, digest, mono_tools, require
else:
    from validate_boss_ai_gate import ROOT, EXPECTED, MissingPrerequisite, digest, mono_tools, require

SOURCE = ROOT / "Unity/AncientConquest/Assets/AncientConquest/Runtime/TerrainMapData.cs"
PROBE = ROOT / "tests/fixtures/TerrainMapDataProbe.cs"
RAW_MAP = ROOT / "Unity/AncientConquest/Assets/Resources/TerrainGenerated/MapPlanar.bytes"
FIXTURE = ROOT / "tests/fixtures/terrain_miss000_lookup.bin"
PROVENANCE = FIXTURE.with_suffix(".json")
OUTPUT = ROOT / "artifacts/binary-analysis/terrain-render/map-data-validation.json"
RAW_MAP_SHA256 = "931138965e7ff49641ff28e389a48104f113d66666badf6de027c8d6e716cfe3"
FIXTURE_SHA256 = "2c26432812ce2c1a4862c0b36f4d5716da972bb5d78e64298469b057ab0d018d"
PROVENANCE_SHA256 = "a7f6558d7ff68f01dad5e096fab5ae53999f298432fa2c1ee2be8f37d3774f44"
WIDTH, HEIGHT, LAYERS, TILE_WIDTH, TILE_HEIGHT = 24, 24, 8, 64, 64
EXPECTED_GUARDS = {
    "geometry_properties", "layer_count", "input_immutability", "ctor_length_null",
    "ctor_length_empty", "ctor_length_short", "ctor_length_long", "ctor_large_length",
    "bounds_x_negative", "bounds_x_end", "bounds_y_negative", "bounds_y_end",
    "bounds_layer_negative", "bounds_layer_end", "bounds_x_min", "bounds_x_max",
    "bounds_y_min", "bounds_y_max", "bounds_layer_min", "bounds_layer_max",
} | {f"ctor_dimension_{axis}_{value}" for axis in range(4) for value in range(4)} | {
    f"selector_bytes_{index}" for index in range(8)
}


def checked_hash(raw, expected, message):
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(message)


def load_reference(raw_map=RAW_MAP, fixture=FIXTURE, provenance=PROVENANCE):
    """Read the fixed native oracle and independently hash-guarded raw map.

    The oracle rows are ordered x/y/layer; the map bytes are planar layer/y/x.
    Verifying every word joins those representations before any C# comparison.
    """
    fixture_raw = Path(fixture).read_bytes()
    provenance_raw = Path(provenance).read_bytes()
    checked_hash(fixture_raw, FIXTURE_SHA256, "Native lookup fixture hash differs")
    checked_hash(provenance_raw, PROVENANCE_SHA256, "Native lookup provenance hash differs")
    evidence = json.loads(provenance_raw)
    expected_provenance = {
        "schema_version": 1, "original_exe_sha256": EXPECTED,
        "map_sha256": RAW_MAP_SHA256, "rows_sha256": FIXTURE_SHA256,
        "entry_va": "0x00545190", "cases": WIDTH * HEIGHT * LAYERS,
        "active_cases": 1007, "bounds_cases": 6,
        "row_format": "<HhB: word, frame_index(-1 null), drawing_type(255 null)",
        "row_order": "x outer, y inner, layer0..7", "intercepted_functions": [],
        "scope": "Original accessor code and callees; reconstructed runtime libraries/DArray inputs, loader excluded",
    }
    if evidence != expected_provenance:
        raise ValueError("Native lookup provenance contract differs")
    raw_map = Path(raw_map)
    if not raw_map.is_file():
        raise MissingPrerequisite(f"Staged source map missing; run tools/stage_terrain.py: {raw_map}")
    raw = raw_map.read_bytes()
    checked_hash(raw, RAW_MAP_SHA256, "Planar map hash differs from native lookup provenance")
    if len(raw) != WIDTH * HEIGHT * LAYERS * 2 or len(fixture_raw) != evidence["cases"] * 5:
        raise ValueError("Native lookup or map length differs")
    rows = list(struct.iter_unpack("<HhB", fixture_raw))
    active = 0
    for index, (word, frame_index, drawing_type) in enumerate(rows):
        x, remainder = divmod(index, HEIGHT * LAYERS)
        y, layer = divmod(remainder, LAYERS)
        source_word = struct.unpack_from("<H", raw, 2 * ((layer * HEIGHT + y) * WIDTH + x))[0]
        if source_word != word:
            raise ValueError(f"Native lookup word differs from raw map at {x},{y},{layer}")
        if frame_index >= 0:
            if not (word & 255) or frame_index != (word & 255) - 1 or drawing_type not in (1, 6):
                raise ValueError("Native lookup contains an invalid active reference")
            active += 1
        elif frame_index != -1 or drawing_type != 255 or word & 255:
            raise ValueError("Native lookup contains an invalid empty reference")
    if active != evidence["active_cases"]:
        raise ValueError("Native lookup active count differs")
    return raw, rows, evidence


def validate(raw_map=RAW_MAP, mono_root=None, fixture=FIXTURE, provenance=PROVENANCE):
    raw, native_rows, evidence = load_reference(raw_map, fixture, provenance)
    runtime, compiler = mono_tools(mono_root)
    source_sha, probe_sha = digest(SOURCE), digest(PROBE)
    with tempfile.TemporaryDirectory(prefix="terrain-map-csharp-") as temporary:
        executable = Path(temporary) / "TerrainMapDataProbe.exe"
        # A local copy removes races with generated-resource replacement while
        # retaining the independently checked payload bytes as the C# input.
        payload = Path(temporary) / "MapPlanar.bytes"
        payload.write_bytes(raw)
        compiled = subprocess.run(compiler + ["/nologo", "/checked+", "/target:exe",
                                  "/out:" + str(executable), str(SOURCE), str(PROBE)],
                                  capture_output=True, text=True, timeout=60)
        if compiled.returncode:
            raise RuntimeError("C# map-data probe compilation failed:\n" + compiled.stdout + compiled.stderr)
        output = subprocess.run([str(runtime), str(executable), str(payload)],
                                check=True, capture_output=True, text=True, timeout=60)
    require(digest(SOURCE) == source_sha and digest(PROBE) == probe_sha,
            "C# source or probe changed during validation")
    rows, guards = [], []
    for line in output.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) == 2 and fields[0] == "CHECK":
            guards.append(fields[1])
        elif len(fields) == 9 and fields[0] == "ROW":
            rows.append(tuple(int(value) for value in fields[1:]))
        else:
            raise ValueError("Unexpected map-data probe output: " + line)
    require(len(guards) == len(EXPECTED_GUARDS) and set(guards) == EXPECTED_GUARDS,
            "C# map guard checks are missing, duplicated or unexpected")
    require(len(rows) == len(native_rows), "C# map-data probe returned an unexpected row count")
    for index, (native, actual) in enumerate(zip(native_rows, rows)):
        x, remainder = divmod(index, HEIGHT * LAYERS)
        y, layer = divmod(remainder, LAYERS)
        word, frame_index, _original_drawing_type = native
        expected = (x, y, layer, word, frame_index, int(frame_index >= 0), word >> 8, word & 255)
        require(actual == expected, f"Map reference mismatch at {x},{y},{layer}: native {expected} / C# {actual}")
    return {
        "kind": "Frozen executed original x86 lookup fixture vs actual Unity C# reference decoder",
        "original_sha256": EXPECTED, "original_entry_point": evidence["entry_va"],
        "native_fixture_sha256": FIXTURE_SHA256, "native_provenance_sha256": PROVENANCE_SHA256,
        "raw_map_sha256": RAW_MAP_SHA256, "native_provenance": evidence,
        "csharp_source": str(SOURCE.relative_to(ROOT)), "csharp_sha256": source_sha,
        "probe_sha256": probe_sha, "validator_sha256": digest(Path(__file__)),
        "mono_runtime": str(runtime), "compiler_command": compiler, "checked_compilation": True,
        "case_count": len(rows), "passed": len(rows), "active_cases": evidence["active_cases"],
        "inactive_cases": len(rows) - evidence["active_cases"],
        "compared": ["raw word", "zero-based frame index", "reference present", "library ID byte", "selector byte"],
        "csharp_guard_checks": guards, "csharp_guard_count": len(guards),
        "original_only": ["bitmap drawing type retained only in native fixture; C# does not resolve bitmaps",
                          "six native bounds cases belong to the fixture's generation evidence"],
        "excluded": ["native oracle generation is not rerun by this validator",
                     "mfALibLoad, bitmap pointer/type resolution in C#, renderer and palette",
                     "gameplay, entities, original full game, camera or screen presentation",
                     "C# guard checks are defensive API contracts, not original binary equivalence claims"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-map", type=Path, default=RAW_MAP)
    parser.add_argument("--mono-root", type=Path)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    arguments = parser.parse_args(argv)
    if arguments.output.exists():
        parser.error("Refusing to replace an existing report; select a fresh --output")
    try:
        report = validate(arguments.raw_map, arguments.mono_root)
    except MissingPrerequisite as error:
        parser.exit(2, str(error) + "\n")
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    with arguments.output.open("x") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(f"{report['passed']} actual C# / native fixture map references and {report['csharp_guard_count']} C# guard checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
