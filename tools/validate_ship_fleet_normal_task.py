"""Compare the bounded Unity100/1 task with real original fleet Work/events."""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import shutil
import subprocess
import tempfile
from tools import probe_ship_fleet_normal_task as native
from tools import validate_boss_ai_gate as gate

ROOT = gate.ROOT
SIMULATION = ROOT / 'Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation'
SOURCE = SIMULATION / 'ShipFleetNormalTask.cs'
PROBE = ROOT / 'tests/fixtures/ShipFleetNormalTaskProbe.cs'
FIXTURE_SHA = 'f85cc3a6aa1a26304faaa5f9f746c239ee6ddb3930936d083e37185a1a849873'


def load(path=None):
    path = Path(path or ROOT / 'tests/fixtures/ship_fleet_normal_task.json')
    raw = path.read_bytes()
    gate.require(hashlib.sha256(raw).hexdigest() == FIXTURE_SHA, 'Normal task fixture SHA differs')
    return json.loads(raw)


def expected(state):
    packets = [p for p in state['commands'] if p['action'] != 41]
    return '\t'.join([str(state['age']), ','.join(map(str, state['task'])) if state['task'] else '-',
                      ';'.join(':'.join(map(str, a)) for a in state['assignments']), ';'.join(state['events']),
                      ';'.join(f"{p['actor']}:{p['action']}:{p['payload_hex']}" for p in packets)])


def compare(data, source=SOURCE, assembly=None):
    lines = ['MAP\tmission\t' + data['terrain_base64'], 'MAP\tblocked\t' + base64.b64encode(b'\xff' * 1152).decode()]
    required = []
    for case in data['cases']:
        lines.append('CASE'); previous = None; map_name = 'mission'
        poses = {11: [16, 2, 0], 12: [21, 5, 0], 13: [19, 4, 0]}
        for row in case['states']:
            op, state = row['operation'], row['after']
            members = ';'.join(','.join(map(str, [ordinal + 11, *poses[ordinal + 11]]))
                               for ordinal in state['groups'][0]) or '-'
            if op[0] == 'R':
                map_name = op[1]; line = [*op, members]
            elif op[0] == 'T':
                line = ['T', map_name, op[1], members, ','.join(map(str, previous['event_slots'])) or '-']
            elif op[0] == 'S':
                identifier, counter = op[1:]
                old = next(a for a in previous['actors'] if a['id'] == identifier)
                new = next(a for a in state['actors'] if a['id'] == identifier)
                if old['ui_group'] == 0:
                    line = ['E', 311, counter, old['member_index'], identifier, *poses[identifier][:2]]
                else:
                    line = ['E', 300, counter, new['member_index'], identifier, 0, 0]
            elif op[0] == 'P':
                poses[op[1]] = op[2:]; line = ['N']
            else:
                line = op if op[0] in ('A', 'X') else ['N']
            lines.append('\t'.join(map(str, line))); required.append(expected(state)); previous = state
    _, _, runtime, compiler = gate.prerequisites()
    with tempfile.TemporaryDirectory(prefix='fleet-normal-task-') as directory:
        executable = Path(directory) / 'Probe.exe'
        inputs = [str(source), str(PROBE)] + [str(SIMULATION / n) for n in
                  ('ShipFleetMoveCommands.cs', 'SourceFleetFormation.cs', 'SourceWaveField.cs', 'ShipMoveRequestInbox.cs')]
        if assembly is not None:
            inputs = ['/reference:' + str(assembly), '/reference:' + str(Path(assembly).parent / 'netstandard.dll'), str(PROBE)]
        compiled = subprocess.run(compiler + ['/nologo', '/checked+', '/warnaserror+', '/out:' + str(executable), *inputs], capture_output=True, text=True)
        gate.require(compiled.returncode == 0, compiled.stdout + compiled.stderr)
        if assembly is not None:
            shutil.copy2(assembly, executable.parent / 'Assembly-CSharp.dll')
        executed = subprocess.run([str(runtime), str(executable)], input='\n'.join(lines) + '\n', capture_output=True, text=True)
        gate.require(executed.returncode == 0, 'Normal task execution failed: ' + executed.stderr)
        actual = executed.stdout.splitlines()
        gate.require(len(actual) == len(required), 'Normal task output count differs')
        for index, (observed, wanted) in enumerate(zip(actual, required)):
            gate.require(observed == wanted, f'Normal task mismatch row {index}\nactual: {observed}\nexpected: {wanted}')
        controls = subprocess.run([str(runtime), str(executable), '--api'], capture_output=True, text=True)
        gate.require(controls.returncode == 0, controls.stdout + controls.stderr)
        gate.require(controls.stdout.strip() == 'API\t20', 'Normal task API controls incomplete: ' + controls.stdout)
    packets = [p for c in data['cases'] for s in c['states'] for p in s['after']['commands'] if p['action'] != 41]
    return {'passed': True, 'cases': len(data['cases']), 'states': len(required), 'task_packets': len(packets),
            'watch35_packets': sum(p['action'] == 35 for p in packets), 'api_controls': 20,
            'checked': True, 'warnings_as_errors': True}


def validate():
    data = load()
    gate.require(data == native.fixture(), 'Fresh original normal task differs')
    return dict(compare(data), fresh_native=True, fixture_sha256=FIXTURE_SHA,
                sources={str(p.relative_to(ROOT)): gate.digest(p) for p in (SOURCE, PROBE, Path(native.__file__), Path(__file__))})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True); args = parser.parse_args()
    result = validate(); args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'sources'}))


if __name__ == '__main__':
    main()
