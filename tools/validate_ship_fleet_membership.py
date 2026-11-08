"""Compare checked Unity membership code with the actual original fleet/consumer."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile

from tools import probe_ship_fleet_membership as native
from tools import validate_boss_ai_gate as gate

ROOT = gate.ROOT
FIXTURE_SHA = 'b937abe8f60d74abf1a166df9356f61b816f28324458d3d77af653bf5e96cfb0'
SOURCE = ROOT / 'Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipFleetMembership.cs'
PROBE = ROOT / 'tests/fixtures/ShipFleetMembershipProbe.cs'
# Compilation closure of the owned100/1 task;behavior remains checked against x86.
DEPENDENCIES = [SOURCE.parent / n for n in ('ShipFleetNormalTask.cs', 'ShipFleetMoveCommands.cs',
                'SourceFleetFormation.cs', 'SourceWaveField.cs', 'ShipMoveRequestInbox.cs')]


def load(path=None):
    path = Path(path or ROOT / 'tests/fixtures/ship_fleet_membership.json')
    raw = path.read_bytes()
    gate.require(hashlib.sha256(raw).hexdigest() == FIXTURE_SHA, 'Membership fixture SHA differs')
    return json.loads(raw)


def expected_row(state):
    groups = ';'.join(str(group['mode']) + ':' + str(group['serial']) + ':' +
                      ','.join(map(str, group['members'])) for group in state['groups'])
    actors = ';'.join(':'.join(str(actor[key]) for key in
                              ('id', 'ui_group', 'simulation_group', 'member_index')) for actor in state['actors'])
    commands = ';'.join(str(command['actor']) + ':' + str(command['action']) + ':' +
                        command['payload_hex'] for command in state['commands'])
    return '\t'.join(map(str, ['-' if state['result'] is None else state['result'],
                              state['current_group'], state['consumed'], groups, actors, commands]))


def compare_fixture(data, source=SOURCE, assembly=None):
    lines, expected = [], []
    for case in data['cases']:
        lines.append('CASE')
        for state in case['states']:
            lines.append('\t'.join(map(str, state['operation'])))
            expected.append(expected_row(state['after']))
    _, _, runtime, compiler = gate.prerequisites()
    with tempfile.TemporaryDirectory(prefix='fleet-membership-') as directory:
        executable = Path(directory) / 'Probe.exe'
        inputs = [str(source), str(PROBE), *map(str, DEPENDENCIES)] if assembly is None else [
            '/reference:' + str(assembly),
            '/reference:' + str(Path(assembly).parent / 'netstandard.dll'), str(PROBE)]
        compiled = subprocess.run(compiler + ['/nologo', '/checked+', '/warnaserror+', '/out:' + str(executable),
                                              *inputs], capture_output=True, text=True)
        gate.require(compiled.returncode == 0, compiled.stdout + compiled.stderr)
        if assembly is not None:
            # Execute the exact game assembly with the host Mono framework.
            # Adding all Windows Managed libraries to MONO_PATH incorrectly
            # loads their platform-specific System.Console implementation.
            shutil.copy2(assembly, executable.parent / 'Assembly-CSharp.dll')
        executed = subprocess.run([str(runtime), str(executable)], input='\n'.join(lines) + '\n',
                                  capture_output=True, text=True)
        gate.require(executed.returncode == 0, 'Membership execution failed: ' + executed.stderr)
        actual = executed.stdout.splitlines()
        gate.require(len(actual) == len(expected), 'Membership state count differs')
        for index, (observed, required) in enumerate(zip(actual, expected)):
            gate.require(observed == required, 'Membership mismatch row ' + str(index) +
                         '\nactual: ' + observed + '\nexpected: ' + required)
        controls = subprocess.run([str(runtime), str(executable), '--api'], capture_output=True, text=True)
        gate.require(controls.returncode == 0, controls.stdout + controls.stderr)
        gate.require(controls.stdout.strip() == 'API\t23', 'Membership API controls incomplete')
    return {'states': len(expected), 'api_controls': 23, 'checked': True, 'warnings_as_errors': True}


def validate():
    data = load()
    gate.require(data == native.fixture(), 'Fresh native membership differs')
    result = compare_fixture(data)
    return dict(result, passed=True, cases=len(data['cases']), fresh_native=True,
                fixture_sha256=FIXTURE_SHA,
                sources={str(path.relative_to(ROOT)): gate.digest(path) for path in (SOURCE, PROBE,
                          Path(native.__file__), Path(__file__))})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    result = validate()
    arguments.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'sources'}))


if __name__ == '__main__':
    main()
