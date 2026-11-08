#!/usr/bin/env python3
"""Compare original x86 release/fleet/membership transactions with checked C#."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

try:
    from . import probe_ship_pointer_commands as native
    from . import validate_boss_ai_gate as gate
except ImportError:
    import probe_ship_pointer_commands as native
    import validate_boss_ai_gate as gate

ROOT = gate.ROOT
MissingPrerequisite = gate.MissingPrerequisite
FIXTURE = ROOT / 'tests/fixtures/ship_pointer_commands.json'
FIXTURE_SHA256 = '6d88a2300b7a7619f5379aec8192963ac3cf8cebd07fedb7e2a714381b0592cd'
SOURCE = ROOT / 'Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipPointerCommands.cs'
PROBE = ROOT / 'tests/fixtures/ShipPointerCommandsProbe.cs'
OUTPUT = ROOT / 'artifacts/world-input/commands/pointer-csharp-validation.json'


def load_fixture(path=FIXTURE):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256:
        raise ValueError('Original pointer-command fixture SHA256 differs')
    data = json.loads(raw)
    if data['original_exe_sha256'] != gate.EXPECTED:
        raise ValueError('Original pointer-command executable differs')
    return data


def rows(frozen):
    lines, expected = [], []
    for case in frozen['cases']:
        lines.append('CASE\t' + case['label'])
        for index, (op, state) in enumerate(zip(case['operations'], case['rows'])):
            if op['operation'] == 'release':
                i = op['input']
                lines.append('\t'.join(map(str, ('R', i['cursor_type'], int(i['hover_self']), *i['cell'],
                                                i['mask'], i['bit'], int(i['blocked']), int(i['enabled']),
                                                op['message'], op['flags']))))
            else:
                lines.append('C\t' + str(op['group']))
            packets = ','.join(str(p['actor']) + ':' + str(p['action']) + ':' + p['payload_hex']
                               for p in state['commands'])
            fields = ('ROW', case['label'], index, state['group_count'], int(state['selected']),
                      int(state['pending']), state['current_group'], state['ui_group'], state['sim_group'],
                      state['visual'], state['cursor_type'], state['mask'], state['bit'], int(state['blocked']),
                      state['clear_count'], state['select_count'], state['confirm_count'], packets)
            expected.append('\t'.join(map(str, fields)))
    return lines, expected


def validate(mono_root=None):
    frozen = load_fixture()
    _, unicorn, runtime, compiler = gate.prerequisites(mono_root=mono_root)
    sources = (SOURCE, PROBE, Path(native.__file__), Path(native.motion.__file__))
    hashes = {str(p.relative_to(ROOT)): gate.digest(p) for p in sources}
    actual = native.original_cases()
    gate.require(actual == frozen, 'Fresh original pointer-command execution differs from pinned fixture')
    lines, expected = rows(frozen)
    with tempfile.TemporaryDirectory(prefix='ship-pointer-commands-') as directory:
        executable = Path(directory) / 'ShipPointerCommandsProbe.exe'
        compiled = subprocess.run(compiler + ['/nologo', '/checked+', '/warnaserror+', '/target:exe',
                                             '/out:' + str(executable), str(SOURCE), str(PROBE)],
                                  capture_output=True, text=True, timeout=60)
        gate.require(compiled.returncode == 0, 'Pointer C# compilation failed:\n' + compiled.stdout + compiled.stderr)
        run = subprocess.run([str(runtime), str(executable)], input='\n'.join(lines) + '\n',
                             capture_output=True, text=True, timeout=60)
        gate.require(run.returncode == 0, 'Pointer C# execution failed:\n' + run.stdout[-1000:] + run.stderr)
    actual_rows = [line for line in run.stdout.splitlines() if line.startswith('ROW\t')]
    differences = [(i, a, b) for i, (a, b) in enumerate(zip(actual_rows, expected)) if a != b]
    gate.require(actual_rows == expected, 'C# pointer transactions differ from original: ' + repr(differences[:4]))
    guards = [line.split('\t', 1)[1] for line in run.stdout.splitlines() if line.startswith('GUARD\t')]
    totals = [int(line.split('\t')[1]) for line in run.stdout.splitlines() if line.startswith('GUARDS\t')]
    gate.require(totals == [19] and len(guards) == len(set(guards)) == 19, 'Pointer API guard count differs')
    states = [s for c in frozen['cases'] for s in c['rows']]
    gate.require(all(s['rng'] == 0 and not s['rng_writes'] and not s['sound_backend_enabled'] for s in states),
                 'Actual disabled-audio pointer transaction changed ship RNG footprint')
    gate.require(all(gate.digest(ROOT / p) == sha for p, sha in hashes.items()), 'Pointer sources changed during validation')
    return {'passed': True, 'original_exe_sha256': gate.EXPECTED, 'fixture_sha256': FIXTURE_SHA256,
            'cases': len(frozen['cases']), 'snapshots': len(states), 'guard_count': len(guards), 'guards': guards,
            'checked_compilation': True, 'warnings_as_errors': True, 'source_sha256': hashes,
            'validator_sha256': gate.digest(Path(__file__)), 'mono_runtime': str(runtime),
            'compiler_command': compiler, 'unicorn_version': unicorn.__version__,
            'rng_footprint': 'No writes to actual Ship+18 during55 snapshots; actual50e500/525300 with audio backend disabled; explicit renderer boundaries.',
            'selection_removal': 'Separate actual4e0d00 confirms1→2→0/delete; host acknowledges only deletion.',
            'native_entries': frozen['native_entries'], 'scope': frozen['scope'],
            'boundaries': frozen['boundaries'], 'excluded': frozen['excluded']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--mono-root', type=Path)
    args = parser.parse_args(argv)
    result = validate(args.mono_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('passed', 'cases', 'snapshots', 'guard_count')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
