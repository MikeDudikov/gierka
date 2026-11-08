#!/usr/bin/env python3
"""Execute the original x86 time-quantum branch and compare actual Unity C#.

The OS never executes ancient.exe. Unicorn starts at VA 0x520352 and stops at
the branch join 0x5209e2. Only the three world/base callbacks are intercepted;
their bodies are excluded. Some cases deliberately change the phase and speed
inside the first callback to verify the original's post-callback reread.
This does not validate branch selection, pause/network modes, or the game loop.
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

SOURCE = ROOT / "Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/SingleStepClock.cs"
PROBE = ROOT / "tests/fixtures/SingleStepClockProbe.cs"
OUTPUT = ROOT / "artifacts/binary-analysis/single-step-clock-validation.json"
START, END = 0x520352, 0x5209e2
CALLBACKS = (0x521500, 0x522850, 0x542320)
SPEED_INDEX, SPEED_TABLE = 0x5ca556, 0x5bed74
CONTEXT, APP = 0x70000000, 0x70010000
STACK, STACK_SIZE = 0x7ff00000, 0x100000
QUANTA = (13, 17, 20, 33, 40, 50, 60, 70, 80)
APP_COUNTER = 0xfffffffe


def signed32(value):
    """Generate raw 32-bit input patterns; never used to predict an output."""
    return struct.unpack("<i", struct.pack("<I", value & 0xffffffff))[0]


def input_cases():
    cases = []
    for speed_index, quantum in enumerate(QUANTA, 1):
        differences = (-2 * quantum - 1, -2 * quantum, -quantum - 1, -quantum,
                       -quantum + 1, -1, 0, 1, quantum - 1, quantum, quantum + 1,
                       2 * quantum - 1, 2 * quantum, 2 * quantum + 1, 5000,
                       0x7fffffff, -0x80000000)
        for phase in (0, 0x7fffffee, -0x7fffffee, -1):
            for difference in differences:
                for counter in (0, 0xffffffff):
                    cases.append({"now": signed32(phase + difference), "phase": phase,
                                  "counter": counter, "speed_index": speed_index,
                                  "callback_phase": phase, "callback_speed_index": speed_index,
                                  "kind": "unchanged callbacks"})
    # The original rereads both values after the three callbacks. Expose that
    # split instead of treating the whole branch as one immutable calculation.
    for callback_speed_index in range(1, 10):
        for callback_phase in (10000, 10001, 10039, 10040, 9999, -0x80000000, 0x7fffffff):
            cases.append({"now": 10000, "phase": 9900, "counter": 0xffffffff,
                          "speed_index": 5, "callback_phase": callback_phase,
                          "callback_speed_index": callback_speed_index,
                          "kind": "callback changes phase and/or speed"})
    return cases


def original_case(image, image_size, case):
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
    from unicorn.x86_const import (UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_EBP,
                                   UC_X86_REG_ESI, UC_X86_REG_EBX, UC_X86_REG_ECX)

    engine = Uc(UC_ARCH_X86, UC_MODE_32)
    engine.mem_map(0x400000, (image_size + 0xfff) & ~0xfff)
    engine.mem_write(0x400000, image)
    engine.mem_map(CONTEXT, 0x20000)
    engine.mem_map(STACK, STACK_SIZE)

    def write32(address, value):
        engine.mem_write(address, struct.pack("<I", value & 0xffffffff))

    def read32(address, signed=False):
        return struct.unpack("<i" if signed else "<I", engine.mem_read(address, 4))[0]

    frame = STACK + STACK_SIZE - 0x100
    write32(frame - 0x20, case["now"])
    write32(CONTEXT + 0xde, case["counter"])
    write32(CONTEXT + 0xe2, 0x55555555)
    write32(CONTEXT + 0xe6, case["phase"])
    write32(APP + 0x344e, APP_COUNTER)
    write32(SPEED_INDEX, case["speed_index"])
    engine.reg_write(UC_X86_REG_EBP, frame)
    engine.reg_write(UC_X86_REG_ESP, frame - 0x100)
    engine.reg_write(UC_X86_REG_ESI, CONTEXT)
    engine.reg_write(UC_X86_REG_EBX, APP)
    calls = []

    def code_hook(uc, address, size, unused):
        if address not in CALLBACKS:
            return
        require(uc.reg_read(UC_X86_REG_ECX) == CONTEXT, "Unexpected original callback this pointer")
        calls.append({"address": hex(address), "pending_step": read32(CONTEXT + 0xe2),
                      "counter": read32(CONTEXT + 0xde)})
        if address == CALLBACKS[0]:
            write32(CONTEXT + 0xe6, case["callback_phase"])
            write32(SPEED_INDEX, case["callback_speed_index"])
        stack = uc.reg_read(UC_X86_REG_ESP)
        return_address = read32(stack)
        uc.reg_write(UC_X86_REG_ESP, stack + 4)
        uc.reg_write(UC_X86_REG_EIP, return_address)

    engine.hook_add(UC_HOOK_CODE, code_hook)
    engine.emu_start(START, END, count=500)
    require(engine.reg_read(UC_X86_REG_EIP) == END, "Original branch did not reach its join")
    require([item["address"] for item in calls] in ([], [hex(address) for address in CALLBACKS]),
            "Unexpected original callback order")
    require(all(item["pending_step"] == 1 for item in calls), "Original callback did not receive one step")
    require(read32(CONTEXT + 0xe2) == 0, "Original did not clear its pending-step field")
    require(read32(APP + 0x344e) == APP_COUNTER + bool(calls),
            "Unexpected original application step-counter change")
    counter = read32(CONTEXT + 0xde)
    require(all(item["counter"] == counter for item in calls), "Original counter changed across no-op callbacks")
    return {"step_requested": bool(calls), "counter": counter,
            "phase": read32(CONTEXT + 0xe6, signed=True), "calls": calls,
            "pending_step_cleared": True, "application_counter_checked": True}


def validate(original=ORIGINAL, mono_root=None):
    original = Path(original)
    if not original.is_file():
        raise MissingPrerequisite(f"Optional original executable missing: {original}")
    raw = original.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise ValueError("Original executable SHA-256 differs from the verified clock branch")
    pefile, unicorn, runtime, compiler = prerequisites(original, mono_root)
    pe = pefile.PE(data=raw)
    require(pe.OPTIONAL_HEADER.ImageBase == 0x400000, "Unexpected original image base")
    image = pe.get_memory_mapped_image()
    for index, expected in enumerate(QUANTA, 1):
        address = SPEED_TABLE + index * 24
        actual = struct.unpack_from("<i", image, address - 0x400000)[0]
        require(actual == expected, f"Original time quantum at speed {index} differs")
    cases = input_cases()
    original_results = [original_case(image, pe.OPTIONAL_HEADER.SizeOfImage, case) for case in cases]
    probe_input = "".join("\t".join(str(value) for value in
                          (case["now"], case["phase"], case["counter"], QUANTA[case["speed_index"] - 1],
                           case["callback_phase"], QUANTA[case["callback_speed_index"] - 1])) + "\n"
                          for case in cases)
    with tempfile.TemporaryDirectory(prefix="single-step-clock-csharp-") as temporary:
        executable = Path(temporary) / "SingleStepClockProbe.exe"
        # Force a checked caller/assembly so wrapping must be explicit in the
        # actual Unity source, rather than an accidental compiler default.
        compiled = subprocess.run(compiler + ["/nologo", "/checked+", "/target:exe", "/out:" + str(executable),
                                  str(SOURCE), str(PROBE)], capture_output=True, text=True, timeout=60)
        if compiled.returncode:
            raise RuntimeError("C# clock probe compilation failed:\n" + compiled.stdout + compiled.stderr)
        output = subprocess.run([str(runtime), str(executable)], input=probe_input, check=True,
                                capture_output=True, text=True, timeout=60)
    rows = [[int(value) for value in line.split("\t")] for line in output.stdout.splitlines()]
    require(len(rows) == len(cases), "C# clock probe returned an unexpected case count")
    for case, expected, row in zip(cases, original_results, rows):
        require(row == [int(expected["step_requested"]), expected["counter"], expected["phase"]],
                f"Clock branch mismatch: {case} / x86 {expected} / C# {row}")
    return {"original_sha256": EXPECTED, "entry_point": hex(START), "stop_before": hex(END),
            "kind": "Isolated original x86 time-quantum branch vs actual Unity C# Begin/Complete",
            "csharp_source": str(SOURCE.relative_to(ROOT)), "csharp_sha256": digest(SOURCE),
            "probe_sha256": digest(PROBE), "mono_runtime": str(runtime), "compiler_command": compiler,
            "checked_compilation": True, "unicorn_version": unicorn.__version__,
            "case_count": len(cases), "passed": len(cases), "speed_quanta": list(QUANTA),
            "callback_mutation_cases": sum(case["kind"] != "unchanged callbacks" for case in cases),
            "invalid_quantum_csharp_checks": 4,
            "csharp_comparison": ["step requested", "32-bit step counter", "post-callback phase"],
            "original_only_checks": ["callback order and this pointer", "one pending step during callbacks",
                                     "pending-step reset", "application step-counter increment"],
            "hooked_callees": {hex(address): "body excluded; record invocation; first may mutate phase/speed"
                               for address in CALLBACKS},
            "limits": ["mode conditions selecting this branch are not emulated",
                       "no Unity time-source or scene integration",
                       "world, base-handler, pause, replay and networking effects are excluded"],
            "cases": [{"input": case, "x86": result} for case, result in zip(cases, original_results)]}


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
    print(f"{result['passed']} original x86 / actual C# clock branch comparisons passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
