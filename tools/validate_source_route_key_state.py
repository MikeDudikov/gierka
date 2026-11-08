"""Compare the actual pure C# route-key state with pinned original x86 observations."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from tools import validate_boss_ai_gate as gate
from tools import validate_source_base_dispatch as reference

ROOT = gate.ROOT
SOURCE = ROOT / 'Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/SourceRouteKeyVisibility.cs'
PROBE = ROOT / 'tests/fixtures/SourceRouteKeyProbe.cs'


def compare(assembly=None, source_text=None):
    raw = reference.FIXTURE.read_bytes()
    gate.require(hashlib.sha256(raw).hexdigest() == reference.SHA, 'Source base corpus differs')
    data = json.loads(raw)
    lines, expected = [], []
    for case in data['rows']:
        lines.append('R')
        for row in case['operations']:
            lines.append(f'M\t{row["message"]}\t{row["value"]}')
            forwarded = '541ee0' in row['entries']
            expected.append([row['stored'], int(forwarded), row['stored'] if forwarded else 0])
    for row in data['context_rows']:
        lines += ['R', f'I\t{row["held"]}', f'C\t{row["gate"]}\t{row["active"]}']
        expected.append([row['stored'], int('541ee0' in row['entries']), 0])
    _, _, runtime, compiler = gate.prerequisites()
    with tempfile.TemporaryDirectory(prefix='source-route-key-state-') as directory:
        directory = Path(directory)
        inputs, executable = directory / 'inputs.tsv', directory / 'probe.exe'
        inputs.write_text('\n'.join(lines) + '\n')
        files = [str(PROBE)]
        if assembly is not None:
            assembly = Path(assembly).resolve()
            files += ['/r:' + str(assembly), '/r:' + str(assembly.parent / 'netstandard.dll')]
        else:
            source = SOURCE
            if source_text is not None:
                source = directory / SOURCE.name
                source.write_text(source_text)
            files.append(str(source))
        build = subprocess.run(compiler + ['/nologo', '/checked+', '/warnaserror+', '/out:' + str(executable), *files],
                               capture_output=True, text=True, timeout=60)
        gate.require(build.returncode == 0, 'Route-key C# compilation failed:\n' + build.stdout + build.stderr)
        if assembly is not None:
            shutil.copy2(assembly, directory / 'Assembly-CSharp.dll')
        run = subprocess.run([str(runtime), str(executable), str(inputs)], capture_output=True, text=True,
                             timeout=60, cwd=ROOT)
        gate.require(run.returncode == 0, 'Route-key C# execution failed:\n' + run.stdout + run.stderr)
        actual = [[int(value) for value in row.split('\t')] for row in run.stdout.splitlines()]
        gate.require(actual == expected, 'C# route-key state differs from original x86 observations')
    return dict(passed=True, states=len(expected), direct_operations=42, context_cases=108,
                checked_csharp=True, assembly=str(assembly) if assembly else None,
                source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(), fixture_sha256=reference.SHA)


def validate(assembly=None, negative_controls=True):
    result = compare(assembly)
    detected = []
    if negative_controls:
        text = SOURCE.read_text()
        mutations = {
            'boolean_normalization': ('Stored = value;', 'Stored = value == 0 ? 0u : 1u;'),
            'lost_recursive_reset': ('Receive(0);', 'Receive(Stored);'),
            'wrong_registration_truthiness': ('registrationState == 1', 'registrationState != 0'),
            'inverted_application_gate': ('applicationGate == 0', 'applicationGate != 0'),
            'duplicate_zero_reset': ('if (Stored == 0) return false;', 'if (Stored == 0) return true;'),
        }
        for name, (before, after) in mutations.items():
            gate.require(text.count(before) == 1, 'Mutant anchor differs: ' + name)
            try:
                compare(source_text=text.replace(before, after))
            except AssertionError as error:
                gate.require(str(error).startswith('C# route-key state differs'), 'Mutant failed for unrelated reason: ' + str(error))
                detected.append(name)
            else:
                raise AssertionError('Undetected C# route-key mutation: ' + name)
    return dict(result, negative_controls=detected, raw_uint_preserved=True,
                no_unity_dependency=True, world_or_tick_executed=False,
                application_lifecycle_integrated=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--assembly', type=Path)
    parser.add_argument('--no-negative-controls', action='store_true')
    args = parser.parse_args()
    result = validate(args.assembly, not args.no_negative_controls)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(result)


if __name__ == '__main__':
    main()
