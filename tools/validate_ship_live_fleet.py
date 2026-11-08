"""Exact normal idle20 receipt/promotion/live-planner/shared-motion comparison."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile

from tools import validate_ship_move_order as legacy
from tools import validate_ship_prepared_fleet_motion as motion
from tools import probe_ship_live_fleet as native

ROOT = legacy.ROOT
SOURCE = legacy.RUNTIME / 'Simulation/ShipMoveOrder.cs'
PLANNER = legacy.RUNTIME / 'Simulation/ShipReplanPlanner.cs'
PROBE = ROOT / 'tests/fixtures/ShipLiveFleetProbe.cs'
FIXTURE_SHA = '2d8bef03b7b31a033dac7c88e32537dbc8db760d9961ce1af8929c2d483646ed'
API_CONTROLS = 33


def load(path=None):
    raw = Path(path or ROOT / 'tests/fixtures/ship_live_fleet.json').read_bytes()
    legacy.gate.require(hashlib.sha256(raw).hexdigest() == FIXTURE_SHA, 'Live fleet fixture SHA differs')
    data = json.loads(raw)
    legacy.gate.require(data['original_exe_sha256'] == legacy.gate.EXPECTED, 'Original executable differs')
    return data


def expected(state):
    tail = [state['pending'], state['active'], state['deferred'], state['stop'], state['ready'], state['caps'],
            *state['requested'], *state['target'], state['first'], state['last_plan'], state['retry_interval'],
            state['radius'], state['retry_snapshot'], *state['target_snapshot'], *state['cell_snapshot'],
            state['route_hex'], ','.join(map(str, state['cache'])), state['pending_record'], state['simulation_group']]
    return motion.expected(state) + '\t' + '\t'.join(map(str, tail))


def compare(data, source=SOURCE, planner=PLANNER, assembly=None, probe=PROBE, api_controls=API_CONTROLS):
    _, _, runtime, compiler = legacy.gate.prerequisites()
    seed_lines = ['SEED\t' + i + '\t' + p for i, p in data['seed_payloads'].items()]
    lines = list(seed_lines)
    required = []
    for case in data['cases']:
        lines.append('START\t' + str(case['seed']))
        for state in case['initial']:
            lines.append('I\t' + str(state['id']))
            required.append(expected(state))
        for operation in case['operations']:
            if operation['kind'] == 'G':
                line = ['G', operation['id'], operation['group']]
            elif operation['kind'] == 'R':
                line = ['R', operation['id'], *operation['goal'], operation['argument']]
            else:
                legacy.gate.require(operation['kind'] == 'T', 'Unknown live fleet operation')
                line = ['T', operation['id'], operation['counter'], operation['pending']]
            lines.append('\t'.join(map(str, line)))
            #41 writes the external membership word. Its value is checked on
            #the next actor snapshot; unlike20/T it does not reset C# effects.
            if operation['kind'] != 'G':
                required.append(expected(operation['state']))
    for case in data.get('planning_cases', []):
        lines.append('\t'.join(map(str, ['P', case['peer'], case['group'], case['state'], case['class'],
                                        case['retry'], ','.join(map(str, case['cache']))])))
        required.append('\t'.join(map(str, ['P', case['path_hex'], case['planning_hex'], case['working_hex'],
                                           ','.join(map(str, case['cache_after'])), case['rng'], case['count'],
                                           case['nearest'], case['reached']])))
    with tempfile.TemporaryDirectory(prefix='live-fleet-') as directory:
        exe = Path(directory) / 'Probe.exe'
        replacements = {SOURCE: source, PLANNER: planner}
        inputs = [str(replacements.get(p, p)) for p in legacy.SOURCES] + [str(probe)]
        if assembly is not None:
            inputs = ['/reference:' + str(assembly),
                      '/reference:' + str(Path(assembly).parent / 'netstandard.dll'), str(probe)]
        result = subprocess.run(compiler + ['/nologo', '/checked+', '/warnaserror+', '/out:' + str(exe), *inputs],
                                capture_output=True, text=True, timeout=60)
        legacy.gate.require(result.returncode == 0, result.stdout + result.stderr)
        if assembly is not None:
            shutil.copy2(assembly, exe.parent / 'Assembly-CSharp.dll')
        result = subprocess.run([str(runtime), str(exe)], input='\n'.join(lines) + '\n',
                                capture_output=True, text=True, cwd=ROOT, timeout=90)
        legacy.gate.require(result.returncode == 0, 'Live fleet execution failed: ' + result.stderr)
        actual = result.stdout.splitlines()
        legacy.gate.require(len(actual) == len(required), 'Live fleet count differs')
        for index, (a, b) in enumerate(zip(actual, required)):
            if a != b:
                differences = [(i, x, y) for i, (x, y) in enumerate(zip(a.split('\t'), b.split('\t'))) if x != y]
                raise AssertionError('Live fleet mismatch row' + str(index) + ': ' + str(differences))
        controls = subprocess.run([str(runtime), str(exe), '--api'], input='\n'.join(seed_lines) + '\n',
                                  capture_output=True, text=True, cwd=ROOT, timeout=30)
        legacy.gate.require(controls.returncode == 0, controls.stdout + controls.stderr)
        legacy.gate.require(controls.stdout.strip() == 'API\t' + str(api_controls),
                            'Live fleet API controls incomplete: ' + controls.stdout)
    operations = [o for c in data['cases'] for o in c['operations']]
    return {'passed': True, 'cases': len(data['cases']), 'states': len(required) - len(data.get('planning_cases', [])),
            'planning_cases': len(data.get('planning_cases', [])),
            'planning_field_cells': len(data.get('planning_cases', [])) * 576 * 2,
            'tick_calls': sum(o['kind'] == 'T' for o in operations),
            'requests': sum(o['kind'] == 'R' for o in operations),
            'group_word_inputs': sum(o['kind'] == 'G' for o in operations),
            'publications': sum(len(o['state']['publications']) for o in operations if o['kind'] != 'G'),
            'grid_mutations': sum(len(o['state']['grid']) for o in operations if o['kind'] != 'G'),
            'checked': True, 'warnings_as_errors': True, 'api_controls': api_controls}


def validate():
    data = load()
    legacy.gate.require(data == native.fixture(), 'Fresh original live fleet differs')
    result = compare(data)
    return dict(result, fresh_native=True, fixture_sha256=FIXTURE_SHA,
                sources={str(p.relative_to(ROOT)): legacy.gate.digest(p)
                         for p in (SOURCE, PLANNER, PROBE, Path(native.__file__), Path(__file__))})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--assembly', type=Path)
    args = parser.parse_args()
    result = compare(load(), assembly=args.assembly) if args.assembly else validate()
    if args.assembly:
        result['dll_sha256'] = legacy.gate.digest(args.assembly)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'sources'}))


if __name__ == '__main__':
    main()
