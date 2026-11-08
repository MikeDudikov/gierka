"""Checked source/Unity-DLL comparison with original formation and full floods."""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import shutil
import struct
import subprocess
import tempfile

from tools import probe_source_fleet_formation as native
from tools import validate_boss_ai_gate as gate

ROOT = gate.ROOT
SIMULATION = ROOT / 'Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation'
SOURCE = SIMULATION / 'SourceFleetFormation.cs'
WAVE_SOURCE = SIMULATION / 'SourceWaveField.cs'
PROBE = ROOT / 'tests/fixtures/SourceFleetFormationProbe.cs'
HASHES = {'source_fleet_formation.json': '8f7ad44cd09ec6461d6674842ac11df614762f0e27bf7b0301a31b8965011846',
          'source_full_wave.json': 'f0b45fe8a94e6c51d67d6af2eba94394495001bfd75b69a73565ac9eafacd9fc'}


def load(name, path=None):
    path = Path(path or ROOT / 'tests/fixtures' / name)
    raw = path.read_bytes()
    gate.require(hashlib.sha256(raw).hexdigest() == HASHES[name], 'Formation fixture SHA differs: ' + name)
    return json.loads(raw)


def has_matching(case):
    return any(trace['entry'] == '0x55f800' for trace in case['after']['trace'])


def heading_guard(case):
    return has_matching(case) and 0 in case['after']['heading_updates']


def formation_row(case):
    after = case['after']
    return '\t'.join(map(str, [after['result'], int(has_matching(case)),
                              ';'.join(','.join(map(str, record[6:])) for record in after['records']),
                              after['reserved_base64'],
                              ';'.join(trace['field_base64'] for trace in after['trace'] if 'field_base64' in trace)]))


def compare(data, waves=None, source=SOURCE, assembly=None):
    _, _, runtime, compiler = gate.prerequisites()
    maps = data['maps']
    lines = ['MAP\t' + name + '\t' + entry['input_base64'] for name, entry in maps.items()]
    expected = []
    for case in data['cases']:
        entry = maps[case['map']]
        lines.append('\t'.join(map(str, ['C', case['map'], entry['width'], entry['height'], *case['goal'],
                                         *[value for cell in case['origins'] for value in cell]])))
        expected.append(None if heading_guard(case) else formation_row(case))
    if waves is not None:
        for index, case in enumerate(waves['cases']):
            name = 'wave-' + str(index)
            lines.append('MAP\t' + name + '\t' + case['input_base64'])
            lines.append('\t'.join(map(str, ['W', name, case['width'], case['height'], *case['seed']])))
            expected.append(str(case['result']) + '\t' + case['output_base64'])
    with tempfile.TemporaryDirectory(prefix='source-formation-') as directory:
        executable = Path(directory) / 'Probe.exe'
        inputs = [str(source), str(WAVE_SOURCE), str(PROBE)] if assembly is None else [
            '/reference:' + str(assembly), '/reference:' + str(Path(assembly).parent / 'netstandard.dll'), str(PROBE)]
        compiled = subprocess.run(compiler + ['/nologo', '/checked+', '/warnaserror+', '/out:' + str(executable), *inputs],
                                  capture_output=True, text=True)
        gate.require(compiled.returncode == 0, compiled.stdout + compiled.stderr)
        if assembly is not None:
            shutil.copy2(assembly, executable.parent / 'Assembly-CSharp.dll')
        result = subprocess.run([str(runtime), str(executable)], input='\n'.join(lines) + '\n', capture_output=True, text=True)
        gate.require(result.returncode == 0, 'Formation execution failed: ' + result.stderr)
        observed = result.stdout.splitlines()
        gate.require(len(observed) == len(expected), 'Formation output count differs')
        for index, (actual, required) in enumerate(zip(observed, expected)):
            if required is None:
                gate.require(actual.startswith('UNSUPPORTED\tOriginal55f800 did not select an approach heading'),
                             'Formation source-heading guard differs case' + str(index))
            else:
                gate.require(actual == required, 'Formation mismatch case' + str(index) +
                             '; columns=' + str([i for i, (a, b) in enumerate(zip(actual.split('\t'), required.split('\t'))) if a != b]))
        controls = subprocess.run([str(runtime), str(executable), '--api'], capture_output=True, text=True)
        gate.require(controls.returncode == 0, controls.stdout + controls.stderr)
        gate.require(controls.stdout.strip() == 'API\t19', 'Formation API controls incomplete')
    guarded = sum(heading_guard(case) for case in data['cases'])
    field_cells = sum(entry['width'] * entry['height'] *
                      (1 + sum('field_base64' in trace for trace in case['after']['trace']))
                      for case in data['cases'] if not heading_guard(case) for entry in (maps[case['map']],))
    mission_passable = 0
    for case in data['cases']:
        if case['group'] != 'mission-all-cells':
            continue
        entry = maps[case['map']]
        cells = struct.unpack('<' + 'h' * (entry['width'] * entry['height']), base64.b64decode(entry['input_base64']))
        x, y = case['goal']
        if cells[y * entry['width'] + x] == 0:
            gate.require(not heading_guard(case), 'Passable mission cell must not need a heading guard')
            mission_passable += 1
    return {'passed': True, 'formation_cases': len(data['cases']), 'formation_exact': len(data['cases']) - guarded,
            'heading_guards': guarded, 'mission_all_cell_cases': 2304, 'mission_passable_cases': mission_passable,
            'compared_formation_field_cells': field_cells, 'api_controls': 19, 'checked': True, 'warnings_as_errors': True,
            'full_wave_cases': len(waves['cases']) if waves else 0,
            'full_wave_field_cells': sum(case['width'] * case['height'] for case in waves['cases']) if waves else 0}


def validate():
    data, waves = load('source_fleet_formation.json'), load('source_full_wave.json')
    gate.require(data == native.fixture(), 'Fresh original formation differs')
    gate.require(waves == native.full_wave_fixture(), 'Fresh original full wave differs')
    result = compare(data, waves)
    return dict(result, fresh_native=True, fixture_hashes=HASHES,
                sources={str(path.relative_to(ROOT)): gate.digest(path) for path in (SOURCE, WAVE_SOURCE, PROBE,
                          Path(native.__file__), Path(__file__))})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = validate()
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'sources'}))


if __name__ == '__main__':
    main()
