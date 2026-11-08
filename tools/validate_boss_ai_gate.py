#!/usr/bin/env python3
"""Compare original x86 dispatch instructions with the actual Unity C# rule.

The host OS never executes the original program. In the x86 emulator three
callees are intercepted: setjmp returns normally, the common base handler is a
no-op, and the AI decision routine records a call. Only the dispatch gate and
its direct writes are checked; the AI brain/base-handler effects are excluded.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021"
ORIGINAL = ROOT / "reference/raw/ancient-conquest/installed/ancient.exe"
SOURCE = ROOT / "Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/BossAiMessageGate.cs"
PROBE = ROOT / "tests/fixtures/GateCaseProbe.cs"
OUTPUT = ROOT / "artifacts/binary-analysis/boss-gate-validation.json"
FUNCTION, SETJMP, BASE, DECISION = 0x448d40, 0x587318, 0x542550, 0x448610
CONTEXT, PARENT, MESSAGE, END = 0x70000000, 0x70010000, 0x70020000, 0x700f0000
STACK, STACK_SIZE = 0x7ff00000, 0x100000
COUNTERS = (0, 1, 249, 250, 251, 500, 0xffffffff)
MESSAGES = (0, 0x0d8fd7, 2, 1, 0xffffffff)


class MissingPrerequisite(RuntimeError):
    """Optional reference data or the local analysis toolchain is unavailable."""


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def mono_tools(mono_root=None):
    """Find a Unity-bundled Mono pair or a conventional system Mono compiler."""
    configured = mono_root or os.environ.get("UNITY_MONO_ROOT")
    roots = []
    if configured:
        roots.append(Path(configured))
    else:
        version_file = ROOT / "Unity/AncientConquest/ProjectSettings/ProjectVersion.txt"
        if version_file.is_file():
            for line in version_file.read_text().splitlines():
                if line.startswith("m_EditorVersion:"):
                    version = line.partition(":")[2].strip()
                    roots.append(ROOT.parent / "toolchains/Unity" / version / "Editor/Data/MonoBleedingEdge")
                    break
    for root in roots:
        compiler = root / "lib/mono/4.5/csc.exe"
        for directory in ("bin-linux64", "bin"):
            runtime = root / directory / "mono"
            if runtime.is_file() and compiler.is_file():
                return runtime, [str(runtime), str(compiler)]
    if not configured:
        runtime, compiler = shutil.which("mono"), shutil.which("mcs")
        if runtime and compiler:
            return Path(runtime), [compiler]
    raise MissingPrerequisite("Mono runtime/C# compiler missing; set UNITY_MONO_ROOT to MonoBleedingEdge")


def prerequisites(original=ORIGINAL, mono_root=None):
    if not Path(original).is_file():
        raise MissingPrerequisite(f"Optional original executable missing: {original}")
    try:
        pefile = importlib.import_module("pefile")
        unicorn = importlib.import_module("unicorn")
    except ModuleNotFoundError as error:
        raise MissingPrerequisite("Install tools/requirements-analysis.txt for x86 differential validation") from error
    runtime, compiler = mono_tools(mono_root)
    return pefile, unicorn, runtime, compiler


def original_case(image, image_size, message, counter):
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_ECX, UC_X86_REG_EAX

    def u32(engine, address):
        return struct.unpack("<I", engine.mem_read(address, 4))[0]

    engine = Uc(UC_ARCH_X86, UC_MODE_32)
    engine.mem_map(0x400000, (image_size + 0xfff) & ~0xfff)
    engine.mem_write(0x400000, image)
    engine.mem_map(CONTEXT, 0x100000)
    engine.mem_map(STACK, STACK_SIZE)
    engine.mem_write(CONTEXT + 0xc, struct.pack("<I", PARENT))
    engine.mem_write(CONTEXT + 0x18, struct.pack("<I", 0x55555555))
    engine.mem_write(PARENT + 0xde, struct.pack("<I", counter))
    engine.mem_write(MESSAGE + 0x10, struct.pack("<I", message))
    engine.mem_write(0x5c7468, b"\x7b")
    engine.mem_write(0x5d1f90, struct.pack("<I", 0xabcdef01))
    top = STACK + STACK_SIZE - 0x100
    engine.mem_write(top, struct.pack("<II", END, MESSAGE))
    engine.reg_write(UC_X86_REG_ESP, top)
    engine.reg_write(UC_X86_REG_ECX, CONTEXT)
    calls = {"base": 0, "decision": 0, "setjmp": 0}

    def code_hook(uc, address, size, unused):
        if address not in (SETJMP, BASE, DECISION):
            return
        key = {SETJMP: "setjmp", BASE: "base", DECISION: "decision"}[address]
        calls[key] += 1
        stack = uc.reg_read(UC_X86_REG_ESP)
        ret = u32(uc, stack)
        uc.reg_write(UC_X86_REG_EAX, 0)
        uc.reg_write(UC_X86_REG_ESP, stack + (8 if address == BASE else 4))
        uc.reg_write(UC_X86_REG_EIP, ret)

    engine.hook_add(UC_HOOK_CODE, code_hook)
    engine.emu_start(FUNCTION, END, count=10000)
    require(engine.reg_read(UC_X86_REG_EIP) == END, "Original did not return")
    require(calls["base"] == calls["setjmp"] == 1, "Unexpected intercepted callee count")
    require(engine.reg_read(UC_X86_REG_EAX) == 0, "Original return value changed")
    require(u32(engine, CONTEXT + 0x18) == counter, "Original did not copy the counter")
    require(u32(engine, 0x5d1f90) == 0xabcdef01, "Original did not restore its exception chain")
    flag = bytes(engine.mem_read(0x5c7468, 1))[0]
    require(flag in (0, 0x7b), "Unexpected original shared flag write")
    return {"message": message, "counter": counter, "decision_calls": calls["decision"],
            "shared_flag": flag, "counter_copied": True, "return_value": 0,
            "exception_chain_restored": True}


def validate(original=ORIGINAL, mono_root=None):
    if not Path(original).is_file():
        raise MissingPrerequisite(f"Optional original executable missing: {original}")
    raw = Path(original).read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise ValueError("Original executable SHA-256 differs from the verified function contract")
    pefile, unicorn, runtime, compiler = prerequisites(original, mono_root)
    pe = pefile.PE(data=raw)
    if pe.OPTIONAL_HEADER.ImageBase != 0x400000:
        raise ValueError("Unexpected original image base")
    image = pe.get_memory_mapped_image()
    cases = [original_case(image, pe.OPTIONAL_HEADER.SizeOfImage, message, counter)
             for counter in COUNTERS for message in MESSAGES]

    with tempfile.TemporaryDirectory(prefix="boss-gate-csharp-") as temporary:
        executable = Path(temporary) / "GateCaseProbe.exe"
        compiled = subprocess.run(compiler + ["/nologo", "/target:exe", "/out:" + str(executable),
                                  str(SOURCE), str(PROBE)], capture_output=True, text=True, timeout=60)
        if compiled.returncode:
            raise RuntimeError("C# probe compilation failed:\n" + compiled.stdout + compiled.stderr)
        output = subprocess.run([str(runtime), str(executable)], check=True,
                                capture_output=True, text=True, timeout=60)
    rows = [[int(value) for value in line.split("\t")] for line in output.stdout.splitlines()]
    require(len(rows) == len(cases), "C# probe returned an unexpected case count")
    for case, row in zip(cases, rows):
        message, counter, request, clear = row
        require((message, counter) == (case["message"], case["counter"]), "C# case identifiers differ")
        require(request == case["decision_calls"], f"Decision mismatch: {case} / {row}")
        require(clear == int(case["shared_flag"] == 0), f"Flag mismatch: {case} / {row}")
    return {"original_sha256": EXPECTED, "entry_point": hex(FUNCTION),
            "kind": "Isolated original x86 emulation vs actual Unity C# dispatcher",
            "counter_unit": "not assumed by this rule",
            "csharp_source": str(SOURCE.relative_to(ROOT)), "csharp_sha256": digest(SOURCE),
            "probe_sha256": digest(PROBE), "mono_runtime": str(runtime),
            "compiler_command": compiler, "unicorn_version": unicorn.__version__,
            "case_count": len(cases), "passed": len(cases),
            "csharp_comparison": ["decision request", "shared flag clearing request"],
            "original_only_checks": ["counter copy", "zero return", "exception chain restoration"],
            "hooked_callees": {hex(SETJMP): "normal setjmp return", hex(BASE): "no-op base handler",
                               hex(DECISION): "record decision call; no AI brain execution"},
            "cases": cases}


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
    print(f"{result['passed']} original x86 / actual C# dispatch comparisons passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
