"""Validate fleet41/20 packets and all three exact pending26-byte receivers."""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import shutil
import subprocess
import tempfile

from tools import probe_ship_fleet_move_commands as native
from tools import validate_boss_ai_gate as gate

ROOT = gate.ROOT
SIMULATION = ROOT / 'Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation'
SOURCE = SIMULATION / 'ShipFleetMoveCommands.cs'
PROBE = ROOT / 'tests/fixtures/ShipFleetMoveCommandsProbe.cs'
FIXTURE_SHA = 'd7e4c6a1f158a8654919cf4684c8745757728eab1b69c7a1505d57297685b537'


def load(path=None):
    path = Path(path or ROOT / 'tests/fixtures/ship_fleet_move_commands.json')
    raw = path.read_bytes()
    gate.require(hashlib.sha256(raw).hexdigest() == FIXTURE_SHA, 'Fleet move fixture SHA differs')
    return json.loads(raw)


def compare(data, source=SOURCE, assembly=None):
    lines = ['MAP\tmission\t' + data['terrain_base64'], 'MAP\tblocked\t' + base64.b64encode(b'\xff' * 1152).decode()]
    expected = []
    for case in data['cases']:
        lines.append('\t'.join(map(str, ['C', case['map'], ','.join(map(str, case['members'])), *case['goal']])))
        commands = ';'.join(str(packet['actor']) + ':' + str(packet['action']) + ':' + packet['payload_hex'] for packet in case['commands'])
        states = '|'.join(';'.join(','.join(map(str, actor)) for actor in state) for state in case['states'])
        expected.append(commands + '\t' + states)
    _, _, runtime, compiler = gate.prerequisites()
    with tempfile.TemporaryDirectory(prefix='fleet-move-commands-') as directory:
        executable = Path(directory) / 'Probe.exe'
        inputs = [str(source), str(PROBE)] + [str(SIMULATION / name) for name in
                  ('SourceFleetFormation.cs', 'SourceWaveField.cs', 'ShipFleetMembership.cs', 'ShipMoveRequestInbox.cs','ShipFleetNormalTask.cs')]
        if assembly is not None:
            inputs = ['/reference:' + str(assembly), '/reference:' + str(Path(assembly).parent / 'netstandard.dll'), str(PROBE)]
        compiled = subprocess.run(compiler + ['/nologo', '/checked+', '/warnaserror+', '/out:' + str(executable), *inputs], capture_output=True, text=True)
        gate.require(compiled.returncode == 0, compiled.stdout + compiled.stderr)
        if assembly is not None:
            shutil.copy2(assembly, executable.parent / 'Assembly-CSharp.dll')
        result = subprocess.run([str(runtime), str(executable)], input='\n'.join(lines) + '\n', capture_output=True, text=True)
        gate.require(result.returncode == 0, 'Fleet move execution failed: ' + result.stderr)
        observed = result.stdout.splitlines()
        gate.require(len(observed) == len(expected), 'Fleet move output count differs')
        for index, (actual, required) in enumerate(zip(observed, expected)):
            gate.require(actual == required, 'Fleet move mismatch case' + str(index))
        result = subprocess.run([str(runtime), str(executable), '--api'], capture_output=True, text=True)
        gate.require(result.returncode == 0, result.stdout + result.stderr)
        gate.require(result.stdout.strip() == 'API\t13', 'Fleet move API controls incomplete')
    return {'passed': True, 'cases': len(data['cases']), 'receiver_states': sum(len(case['states']) for case in data['cases']),
            'packets': sum(len(case['commands']) for case in data['cases']),
            'fallback_cases': sum(case['map'] == 'blocked' for case in data['cases']),
            'api_controls': 13, 'checked': True, 'warnings_as_errors': True}


def validate():
    data = load()
    gate.require(data == native.fixture(), 'Fresh original fleet move commands differ')
    result = compare(data)
    return dict(result, fresh_native=True, fixture_sha256=FIXTURE_SHA,
                sources={str(path.relative_to(ROOT)): gate.digest(path) for path in (SOURCE, PROBE, Path(native.__file__), Path(__file__))})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = validate()
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'sources'}))


if __name__ == '__main__':
    main()
