#!/usr/bin/env python3
"""Compare actual original ship-mask queries with the actual checked C# helper."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

try:
    from . import probe_ship_pointer_mask as native
    from . import validate_boss_ai_gate as gate
except ImportError:
    import probe_ship_pointer_mask as native
    import validate_boss_ai_gate as gate

ROOT = gate.ROOT
MissingPrerequisite = gate.MissingPrerequisite
FIXTURE = ROOT / 'tests/fixtures/ship_pointer_mask.json'
FIXTURE_SHA256 = '8119cc2cb7e645edc671f2ba8daea5d1878a61ddeb0acca254e59a0c92163245'
SOURCE = ROOT / 'Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipPointerMask.cs'
PROBE = ROOT / 'tests/fixtures/ShipPointerMaskProbe.cs'
OUTPUT = ROOT / 'artifacts/world-input/picking/mask-csharp-validation.json'


def load_fixture(path=FIXTURE):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256:
        raise ValueError('Original ship-pointer mask fixture SHA256 differs')
    data = json.loads(raw)
    if data['original_exe_sha256'] != gate.EXPECTED:
        raise ValueError('Original ship-pointer executable differs')
    return data


def validate(mono_root=None):
    frozen = load_fixture()
    native.staging.checked_sources(ROOT / 'reference/raw/ancient-conquest')
    _, unicorn, runtime, compiler = gate.prerequisites(mono_root=mono_root)
    hashes = {str(p.relative_to(ROOT)): gate.digest(p) for p in
              (SOURCE, PROBE, Path(native.__file__), Path(native.staging.__file__))}
    actual = native.original_cases()
    gate.require(actual == frozen, 'Fresh original ship-mask execution differs from pinned fixture')
    families, _ = native.mask_inputs(ROOT / 'reference/raw/ancient-conquest')
    lines, expected = [], []
    for family, original in zip(families, frozen['families']):
        gate.require(family['family'] == original['family'], 'Source mask family order differs')
        gate.require([hashlib.sha256(p).hexdigest() for p in family['planes']] == original['plane_sha256'],
                     'Source mask planes differ')
        lines.append('\t'.join(map(str, ('F', family['family'], family['width'], family['height'],
                                        b''.join(family['planes']).hex()))))
        for plane in original['planes']:
            lines.append('M\t' + str(plane['index']))
            expected.append('\t'.join(map(str, ('PLANE', family['family'], plane['index'],
                                                plane['coverage_sha256'], plane['covered']))))
        for index, point in enumerate(original['points']):
            lines.append('\t'.join(map(str, ('P', point['frame'], point['heading'], *point['world'],
                                            *point['origin'], int(point['precise'])))))
            expected.append('\t'.join(map(str, ('POINT', family['family'], index, point['expected']))))
    with tempfile.TemporaryDirectory(prefix='ship-pointer-mask-') as directory:
        executable = Path(directory) / 'ShipPointerMaskProbe.exe'
        compiled = subprocess.run(compiler + ['/nologo', '/checked+', '/warnaserror+', '/target:exe',
                                             '/out:' + str(executable), str(SOURCE), str(PROBE)],
                                  capture_output=True, text=True, timeout=60)
        gate.require(compiled.returncode == 0, 'Mask C# compilation failed:\n' + compiled.stdout + compiled.stderr)
        run = subprocess.run([str(runtime), str(executable)], input='\n'.join(lines) + '\n',
                             capture_output=True, text=True, timeout=60)
        gate.require(run.returncode == 0, 'Mask C# execution failed:\n' + run.stdout[-1000:] + run.stderr)
    actual_rows = [line for line in run.stdout.splitlines() if line.startswith(('PLANE\t', 'POINT\t'))]
    gate.require(actual_rows == expected, 'C# mask plane coverage or point query differs from original')
    guards = [line.split('\t', 1)[1] for line in run.stdout.splitlines() if line.startswith('GUARD\t')]
    totals = [int(line.split('\t')[1]) for line in run.stdout.splitlines() if line.startswith('GUARDS\t')]
    gate.require(totals == [13] and len(guards) == len(set(guards)) == 13, 'Mask API guard count differs')
    gate.require(all(gate.digest(ROOT / p) == sha for p, sha in hashes.items()), 'Mask sources changed during validation')
    return {'passed': True, 'original_exe_sha256': gate.EXPECTED, 'fixture_sha256': FIXTURE_SHA256,
            'native_calls': frozen['native_calls'], 'original_mask_planes': 96, 'synthetic_padded_planes': 24,
            'full_plane_pixels': sum(p['pixels'] for f in frozen['families'] for p in f['planes']),
            'point_cases': sum(len(f['points']) for f in frozen['families']),
            'guard_count': len(guards), 'guards': guards, 'checked_compilation': True,
            'warnings_as_errors': True, 'source_sha256': hashes, 'validator_sha256': gate.digest(Path(__file__)),
            'mono_runtime': str(runtime), 'compiler_command': compiler, 'unicorn_version': unicorn.__version__,
            'native_hooks': [], 'scope': frozen['scope'], 'excluded': frozen['excluded']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--mono-root', type=Path)
    args = parser.parse_args(argv)
    result = validate(args.mono_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('passed', 'native_calls', 'full_plane_pixels', 'point_cases', 'guard_count')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
