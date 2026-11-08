"""Exact shared-grid local-body motion, publications and claim mutations."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import tempfile

from tools import validate_ship_move_order as legacy
from tools import probe_ship_prepared_fleet_motion as native

ROOT = legacy.ROOT
SOURCE = legacy.RUNTIME / 'Simulation/ShipMoveOrder.cs'
PROBE = ROOT / 'tests/fixtures/ShipPreparedFleetMotionProbe.cs'
FIXTURE_SHA = 'cbb6e4307dde096b121644bb34d1119a83405bc7017d02e9716bbc9574a159d5'


def load(path=None):
    path = Path(path or ROOT / 'tests/fixtures/ship_prepared_fleet_motion.json')
    raw = path.read_bytes()
    legacy.gate.require(hashlib.sha256(raw).hexdigest() == FIXTURE_SHA, 'Prepared fleet fixture SHA differs')
    return json.loads(raw)


def expected(state):
    values = [state['id'], *state['cell'], *state['world'], state['state'], state['center'],
              state['heading'], state['target_heading'], state['turn_step'], state['speed'], state['remainder'],
              state['deceleration'], state['reserved'], state['next'], state['last'], state['path_index'], state['path_count'],
              state['frame'], state['frame_tick'], state['state_tick'], state['rng'], state['acceleration'], state['retry'],
              int(state['tail']), state['drawn']['frame'], *state['drawn']['world'],
              ';'.join(','.join(map(str, [p['frame'], *p['world'], p['depth']])) for p in state['publications']),
              ';'.join(','.join(map(str, p)) for p in state.get('grid', [])),
              ';'.join(','.join(map(str, p)) for p in state.get('claims',
                         [[64, 11], [115, 13], [141, 12], [318, 41], [342, 42], [443, 16], [513, 39], [538, 40]]))]
    return '\t'.join(map(str, values))


def compare(data, source=SOURCE, assembly=None):
    _, _, runtime, compiler = legacy.gate.prerequisites()
    lines = ['SEED\t' + identifier + '\t' + payload for identifier, payload in data['seed_payloads'].items()]
    required = []
    for case in data['cases']:
        lines.append('START\t' + str(case['session_seed']))
        for identifier, route in zip(native.LOCAL, case['routes']):
            if route:
                raw = b''.join(struct.pack('<hhB', *point) for point in route)
                lines.append('ROUTE\t' + str(identifier) + '\t' + raw.hex())
        lines += ['I\t' + str(i) for i in native.LOCAL]
        required.extend(expected(state) for state in case['initial'])
        for row in case['rows']:
            lines.append('\t'.join(map(str, ['T', row['state']['id'], row['counter'], row['pending']])))
            required.append(expected(row['state']))
    with tempfile.TemporaryDirectory(prefix='prepared-fleet-') as directory:
        executable = Path(directory) / 'Probe.exe'
        inputs = [str(source) if p == SOURCE else str(p) for p in legacy.SOURCES] + [str(PROBE)]
        if assembly is not None:
            inputs = ['/reference:' + str(assembly), '/reference:' + str(Path(assembly).parent / 'netstandard.dll'), str(PROBE)]
        result = subprocess.run(compiler + ['/nologo', '/checked+', '/warnaserror+', '/out:' + str(executable), *inputs], capture_output=True, text=True)
        legacy.gate.require(result.returncode == 0, result.stdout + result.stderr)
        if assembly is not None:
            shutil.copy2(assembly, executable.parent / 'Assembly-CSharp.dll')
        result = subprocess.run([str(runtime), str(executable)], input='\n'.join(lines) + '\n', capture_output=True, text=True, cwd=ROOT)
        legacy.gate.require(result.returncode == 0, 'Prepared fleet execution failed: ' + result.stderr)
        actual = result.stdout.splitlines()
        legacy.gate.require(len(actual) == len(required), 'Prepared fleet state count differs')
        for index, (a, b) in enumerate(zip(actual, required)):
            if a != b:
                difference = [(i, x, y) for i, (x, y) in enumerate(zip(a.split('\t'), b.split('\t'))) if x != y]
                raise AssertionError('Prepared fleet mismatch row' + str(index) + ': ' + str(difference))
        seed_lines=['SEED\t'+identifier+'\t'+payload for identifier,payload in data['seed_payloads'].items()]
        controls=subprocess.run([str(runtime),str(executable),'--api'],input='\n'.join(seed_lines)+'\n',capture_output=True,text=True,cwd=ROOT)
        legacy.gate.require(controls.returncode==0,controls.stdout+controls.stderr)
        legacy.gate.require(controls.stdout.strip()=='API\t22','Prepared fleet API controls incomplete: '+controls.stdout)
    return {'passed': True, 'cases': len(data['cases']), 'states': len(required),
            'tick_calls': sum(len(case['rows']) for case in data['cases']),
            'publications': sum(len(row['state']['publications']) for case in data['cases'] for row in case['rows']),
            'grid_mutations': sum(len(row['state']['grid']) for case in data['cases'] for row in case['rows']),
            'checked': True, 'warnings_as_errors': True,'api_controls':22}


def validate():
    data = load()
    legacy.gate.require(data == native.fixture(), 'Fresh original prepared fleet differs')
    result = compare(data)
    return dict(result, fresh_native=True, fixture_sha256=FIXTURE_SHA,
                sources={str(p.relative_to(ROOT)): legacy.gate.digest(p) for p in (SOURCE, PROBE, Path(native.__file__), Path(__file__))})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = validate()
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'sources'}))


if __name__ == '__main__':
    main()
