#!/usr/bin/env python3
"""Compare complete original turn routine/helper with the actual C# adapter.

Only normal setjmp return and the final DrawSprite boundary are intercepted.
The original frame selection, direction helper, timing, completion fields and
return value execute unchanged. This does not execute movement or rendering.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile

try:
    from .validate_boss_ai_gate import ROOT, EXPECTED, ORIGINAL, MissingPrerequisite, digest, prerequisites, require
except ImportError:
    from validate_boss_ai_gate import ROOT, EXPECTED, ORIGINAL, MissingPrerequisite, digest, prerequisites, require

SOURCE = ROOT / "Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipTurnProgression.cs"
PROBE = ROOT / "tests/fixtures/ShipTurnProgressionProbe.cs"
FIXTURE = ROOT / "tests/fixtures/ship_turn_traces.json"
FIXTURE_SHA256 = "298be52cb4d4cd867b6060bf84cb6a2eb7ee65d9e91b1edfd98830a387a488dd"
OUTPUT = ROOT / "artifacts/movement/adjacent-evidence/animation/turn-csharp-validation.json"
SHIP, SPRITE, GAME = 0x70000000, 0x70002000, 0x70004000
STACK, STACK_SIZE, END = 0x71000000, 0x20000, 0x72000000
INPUT_FIELDS = ("frame", "heading", "target_heading", "turn_step", "now", "last_tick", "interval",
                "has_path", "state", "changed_marker")
RESULT_FIELDS = ("frame", "heading", "turn_step", "last_tick", "state", "changed_marker", "publishes_pose")


def stress_cases():
    cases = []
    for heading in range(8):
        for target in range(8):
            for frame in (4 * heading, 32 + 3 * heading, 56 + 4 * heading):
                for now, last in ((0, 0), (2, 0), (3, 0), (100, 0), (1, 0xfffffffe)):
                    cases.append({"scope": "initial_and_idle_pose", "input": {
                        "frame": frame, "heading": heading, "target_heading": target, "turn_step": 0,
                        "now": now, "last_tick": last, "interval": 2, "has_path": True,
                        "state": 2, "changed_marker": 0}})
    for frame in range(32, 56):
        for target in range(8):
            cases.append({"scope": "mid_turn_direction", "input": {
                "frame": frame, "heading": (frame - 32) // 3, "target_heading": target,
                "turn_step": 0, "now": 3, "last_tick": 0, "interval": 2,
                "has_path": False, "state": 2, "changed_marker": 0}})
    for frame in (-0x80000000, 0x7fffffff, -1, 31, 56, 87):
        for heading, target in ((-128, 127), (-1, 0), (127, -128), (-1, -1)):
            for step in (0, -128, 127):
                for now, last, interval in ((3, 0, 2), (0, 1, 0xffffffff)):
                    cases.append({"scope": "raw_arithmetic_stress", "input": {
                        "frame": frame, "heading": heading, "target_heading": target, "turn_step": step,
                        "now": now, "last_tick": last, "interval": interval,
                        "has_path": True, "state": 17, "changed_marker": 165}})
    return cases


class OriginalTurn:
    def __init__(self, image, image_size):
        from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
        from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EIP, UC_X86_REG_ESP
        self.engine = Uc(UC_ARCH_X86, UC_MODE_32)
        self.engine.mem_map(0x400000, (image_size + 4095) & ~4095)
        self.engine.mem_write(0x400000, image)
        self.engine.mem_map(SHIP, 0x10000)
        self.engine.mem_map(STACK, STACK_SIZE)
        self.engine.mem_map(END, 0x1000)
        self.draws, self.setjmps = [], 0

        def hook(engine, address, _size, _unused):
            if address in self.visits:
                self.visits[address] += 1
            if address in (0x556610, 0x556880):
                raise AssertionError("Original turn error path")
            if address not in (0x587318, 0x4df6e0):
                return
            if address == 0x587318:
                self.setjmps += 1
            else:
                self.draws.append(self.read_state())
            stack = engine.reg_read(UC_X86_REG_ESP)
            engine.reg_write(UC_X86_REG_EAX, 0)
            engine.reg_write(UC_X86_REG_EIP, self.get(stack))
            engine.reg_write(UC_X86_REG_ESP, stack + 4)

        self.engine.hook_add(UC_HOOK_CODE, hook)

    def put(self, address, value):
        self.engine.mem_write(address, struct.pack("<I", value & 0xffffffff))

    def get(self, address):
        return struct.unpack("<I", self.engine.mem_read(address, 4))[0]

    def signed_byte(self, address):
        return struct.unpack("<b", self.engine.mem_read(address, 1))[0]

    def read_state(self):
        return {"frame": struct.unpack("<i", self.engine.mem_read(SPRITE + 0x45, 4))[0],
                "heading": self.signed_byte(SHIP + 0x5af), "turn_step": self.signed_byte(SHIP + 0x5b0),
                "last_tick": self.get(SPRITE + 0x81),
                "state": self.engine.mem_read(SHIP + 0x58c, 1)[0],
                "changed_marker": self.engine.mem_read(SHIP + 0x596, 1)[0]}

    def case(self, case, *, whole_move=False):
        from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP
        self.engine.mem_write(SHIP, b"\0" * 0x6000)
        for address, value in ((SHIP + 0x8be, SPRITE), (SHIP + 0x70, GAME),
                               (SHIP + 0x5c2, int(case["has_path"])), (SPRITE + 0x45, case["frame"]),
                               (SPRITE + 0x7d, case["interval"]), (SPRITE + 0x81, case["last_tick"]),
                               (GAME + 0xde, case["now"]), (0x5d1f90, 0xabcdef01)):
            self.put(address, value)
        for offset, key in ((0x5af, "heading"), (0x5b0, "turn_step"), (0x5b1, "target_heading"),
                            (0x58c, "state"), (0x596, "changed_marker")):
            self.engine.mem_write(SHIP + offset, bytes((case[key] & 255,)))
        stack = STACK + STACK_SIZE - 0x100
        self.put(stack, END)
        self.engine.reg_write(UC_X86_REG_ESP, stack)
        self.engine.reg_write(UC_X86_REG_ECX, SHIP)
        self.draws, self.setjmps = [], 0
        self.visits = {address: 0 for address in (0x4a3320, 0x4a3560, 0x4a4d49)}
        self.engine.emu_start(0x4a3f40 if whole_move else 0x4a3320, END, count=3000)
        require(self.engine.reg_read(UC_X86_REG_EIP) == END, "Original turn did not return")
        require(self.engine.reg_read(UC_X86_REG_EAX) == (1 if whole_move else 0),
                "Unexpected original turn/caller normal return")
        require(self.setjmps == (2 if whole_move else 1) and len(self.draws) <= 1,
                "Unexpected turn boundary calls")
        require(self.visits == {0x4a3320: 1, 0x4a3560: 0, 0x4a4d49: 0},
                "Original turn unexpectedly continued into state3 movement or forward phase")
        if whole_move:
            require(self.get(SHIP + 0x58d) == case["now"], "MoveShip did not write the pre-turn movement stamp")
        require(self.get(0x5d1f90) == 0xabcdef01, "Original turn did not restore its exception chain")
        result = self.read_state()
        if self.draws:
            require(self.draws[0] == result, "Turn publishes a different pose from its final state")
        return dict(result, publishes_pose=bool(self.draws))


def trace_cases(fixture):
    cases = []
    for trace_index, trace in enumerate(fixture["turn_traces"]):
        heading = trace["initial_heading"]
        current = {"frame": heading * 4, "heading": heading, "target_heading": trace["target_heading"],
                   "turn_step": 0, "now": 0, "last_tick": 0, "interval": 2,
                   "has_path": trace["path_present"], "state": 2, "changed_marker": 0}
        for row in trace["trace"]:
            current = dict(current, now=row["tick"])
            expected = {"frame": row["frame"], "heading": row["heading"], "turn_step": row["frame_step"],
                        "last_tick": row["last_stamp"], "state": row["move_state"],
                        "changed_marker": row["changed_marker"], "publishes_pose": bool(row["draw_calls"])}
            cases.append({"scope": "source_turn_trace", "trace_index": trace_index,
                          "input": current, "fixture_expected": expected})
            current = dict(current, **{key: expected[key] for key in
                                      ("frame", "heading", "turn_step", "last_tick", "state", "changed_marker")})
    return cases


def validate(original=ORIGINAL, mono_root=None):
    original = Path(original)
    if not original.is_file():
        raise MissingPrerequisite(f"Optional original executable missing: {original}")
    raw = original.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise ValueError("Original executable SHA-256 differs from the verified turn routine")
    require(digest(FIXTURE) == FIXTURE_SHA256, "Original turn fixture changed")
    fixture = json.loads(FIXTURE.read_text())
    pefile, unicorn, runtime, compiler = prerequisites(original, mono_root)
    pe = pefile.PE(data=raw)
    require(pe.OPTIONAL_HEADER.ImageBase == 0x400000, "Unexpected original image base")
    before = {str(path): digest(path) for path in (original, SOURCE, PROBE, FIXTURE)}
    source_cases = trace_cases(fixture)
    require(len(source_cases) == 2480 and len(fixture["turn_traces"]) == 128, "Unexpected original turn fixture scope")
    cases = source_cases + stress_cases()
    oracle = OriginalTurn(pe.get_memory_mapped_image(), pe.OPTIONAL_HEADER.SizeOfImage)
    results = []
    for case in cases:
        result = oracle.case(case["input"])
        if "fixture_expected" in case:
            require(result == case["fixture_expected"], f"Original turn no longer matches pinned trace: {case}")
        results.append(result)
    # Execute the whole original caller as well: each trace's initial and
    # completing state2 calls must return before state3/forward processing.
    caller_cases = [case for index, case in enumerate(source_cases)
                    if case["input"]["now"] == 0 or case["fixture_expected"]["state"] != 2]
    require(len(caller_cases) == 256, "Unexpected source turn-caller selection")
    for case in caller_cases:
        require(oracle.case(case["input"], whole_move=True) == case["fixture_expected"],
                "Whole MoveShip turn branch differs from its isolated turn result")
    with tempfile.TemporaryDirectory(prefix="ship-turn-csharp-") as temporary:
        executable = Path(temporary) / "ShipTurnProgressionProbe.exe"
        compiled = subprocess.run(compiler + ["/nologo", "/checked+", "/target:exe", "/out:" + str(executable),
                                  str(SOURCE), str(PROBE)], capture_output=True, text=True, timeout=60)
        if compiled.returncode:
            raise RuntimeError("C# ship turn probe compilation failed:\n" + compiled.stdout + compiled.stderr)
        lines = ["\t".join(str(int(case["input"][key])) for key in INPUT_FIELDS) for case in cases]
        output = subprocess.run([str(runtime), str(executable)], input="\n".join(lines) + "\n",
                                check=True, capture_output=True, text=True, timeout=60)
    rows = [[int(value) for value in line.split("\t")] for line in output.stdout.splitlines()]
    require(len(rows) == len(cases), "C# ship turn probe returned an unexpected case count")
    for case, result, row in zip(cases, results, rows):
        require(tuple(row) == tuple(int(result[key]) for key in RESULT_FIELDS),
                f"Turn mismatch: {case['input']} / x86 {result} / C# {row}")
    require(before == {str(path): digest(path) for path in (original, SOURCE, PROBE, FIXTURE)},
            "Original or C# evidence inputs changed during validation")
    return {"original_sha256": EXPECTED, "entry_point": "0x4a3320", "direction_helper": "0x4b5390",
            "csharp_source": str(SOURCE.relative_to(ROOT)), "csharp_sha256": digest(SOURCE),
            "probe_sha256": digest(PROBE), "fixture_sha256": FIXTURE_SHA256,
            "mono_runtime": str(runtime), "compiler_command": compiler, "checked_compilation": True,
            "unicorn_version": unicorn.__version__, "source_trace_count": 128, "source_step_count": 2480,
            "stress_case_count": len(cases) - len(source_cases), "case_count": len(cases), "passed": len(cases),
            "normal_zero_return_count": len(cases),
            "whole_move_caller_cases": len(caller_cases), "whole_move_normal_return": 1,
            "whole_move_source_calls_per_case": {"0x4a3320": 1, "0x4a3560": 0, "0x4a4d49": 0},
            "hooked_callees": {"0x587318": "normal setjmp return", "0x4df6e0": "capture final publication request; no renderer"},
            "limits": ["whole turn routine/helper plus whole MoveShip state2 branch; moving-state branches and rendering excluded",
                       "raw arithmetic stress cases do not represent valid asset poses",
                       "normal zero return requires MoveShip to end this call even when turn completes",
                       "tick-to-wall-time conversion and initial global stamp are separate"],
            "cases": [{"scope": case["scope"], "input": case["input"], "x86": result}
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
        report = validate(args.original, args.mono_root)
    except MissingPrerequisite as error:
        parser.exit(2, str(error) + "\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(f"{report['passed']} original x86 / actual C# turn cases passed")


if __name__ == "__main__":
    main()
