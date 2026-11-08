"""Verify RightShift actual-control evidence and unchanged deterministic project inputs."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / 'docs/evidence/milestone-20261104-source-route-keys.json'
OUTPUT = ROOT / 'docs/evidence/milestone-20261104-right-shift-input.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seal():
    old = json.loads(PREVIOUS.read_text())
    changed = []
    for name, meta in old['files'].items():
        path = ROOT / name
        assert path.is_file(), name
        if digest(path) != meta['sha256']:
            changed.append(name)
    expected = {
        'README.md',
        *('docs/' + name for name in ('SHIP_POINTER_RESUME.md', 'UnityProjectContext.md',
           'VALIDATION.md', 'UNITY_ENVIRONMENT.md', 'REMAKE_PLAN.md')),
        *('Unity/AncientConquest/Assets/AncientConquest/Runtime/' + name + '.cs'
          for name in ('ShipFleetMoveInputReplay', 'WorldPointerInput')),
        *('artifacts/unity-reference/Windows/' + name for name in (
            'AncientConquestReference_Data/Managed/Assembly-CSharp.dll',
            'AncientConquestReference_Data/boot.config', 'AncientConquestReference_Data/globalgamemanagers',
            'AncientConquestReference_Data/resources.assets', 'build-report.json')),
        'tools/smoke_pending_queued_input.py', 'tools/smoke_queued_input.py',
    }
    assert set(changed) == expected, (set(changed) - expected, expected - set(changed))
    project = json.loads((ROOT / 'artifacts/right-shift-input/project-frozen.json').read_text())
    for name, meta in project.items():
        assert digest(ROOT / name) == meta['sha256']
    for name, sha in old['original_source_hashes_verified'].items():
        assert digest(ROOT / 'reference/raw/ancient-conquest' / name) == sha
    for filename, count in (('artifacts/right-shift-input/prior-profile-checkers.log', 6),
                            ('artifacts/right-shift-input/runtime-tests.log', 2),
                            ('artifacts/source-key-context/tests.log', 1)):
        log = (ROOT / filename).read_text()
        assert re.search('Ran ' + str(count) + r' tests? in ', log) and log.rstrip().endswith('OK'), filename
    players = {}
    for name, right in (('right-committed-first', True), ('right-pending-last', True),
                        ('left-pending-first', False)):
        report = json.loads((ROOT / 'artifacts/right-shift-input' / name / 'report.json').read_text())
        assert report['passed'] and report['exit_code'] == 0
        assert report['right_shift_replay'] == right
        assert report['key_control_events'] == report['key_envelopes'] == 4
        assert 'wrong_shift_control' in report['negative_controls']
        players[name] = {key: report[key] for key in (
            'passed', 'checkpoints', 'actor_rows', 'component_rows', 'actual_queue_reads',
            'publications', 'marker_checkpoint_reads', 'key_envelopes', 'key_control_events',
            'right_shift_replay', 'negative_controls', 'exit_code')}
    build = json.loads((ROOT / 'artifacts/unity-reference/Windows/build-report.json').read_text())
    assert build['result'] == 'Succeeded' and build['warnings'] == build['errors'] == 0
    shipping = json.loads((ROOT / 'artifacts/right-shift-input/shipping.json').read_text())
    dll = ROOT / 'artifacts/unity-reference/Windows/AncientConquestReference_Data/Managed/Assembly-CSharp.dll'
    assert digest(dll) == shipping['assembly_sha256']
    assert all(value['passed'] for value in shipping.values() if isinstance(value, dict))
    context = json.loads((ROOT / 'artifacts/source-key-context/validation.json').read_text())
    assert context['passed'] and context['fresh_x86'] and not context['csharp_integration']
    names = set(old['files']) | set(project)
    for folder in ('artifacts/right-shift-input', 'artifacts/source-key-context',
                   'artifacts/queued-key-visibility', 'artifacts/unity-reference/Windows'):
        names.update(str(path.relative_to(ROOT)) for path in (ROOT / folder).rglob('*')
                     if path.is_file() and path.name not in (
                         'seal.log', 'config-draft-verified.json', 'previous-start-skill.txt', 'next-start-skill.txt'))
    names.update({
        'tools/seal_right_shift_input.py', 'tools/probe_source_key_context.py',
        'tools/validate_source_key_context.py', 'tests/test_source_key_context.py',
        'tests/fixtures/source_key_context.json', 'tests/test_right_shift_runtime.py',
        'docs/RIGHT_SHIFT_INPUT.md',
    })
    names.update(str(path.relative_to(ROOT)) for path in (ROOT / 'tests/fixtures').glob('right_shift_*_player.log'))
    names.discard(str(OUTPUT.relative_to(ROOT)))
    files = {name: dict(bytes=(ROOT / name).stat().st_size, sha256=digest(ROOT / name))
             for name in sorted(names)}
    result = dict(
        date='2026-11-04', passed=True, status='Ready with limitations',
        previous_milestone=dict(path=str(PREVIOUS.relative_to(ROOT)), sha256=digest(PREVIOUS)),
        previous_files_checked=len(old['files']), changed_previous_files=sorted(changed),
        base_commit=old['base_commit'], csharp=73, meta=132, frozen_project_files=len(project),
        changed_existing_csharp=['ShipFleetMoveInputReplay', 'WorldPointerInput'],
        unchanged_existing_csharp=71, new_csharp=[], staged_resource_files_unchanged=80,
        original_source_hashes_verified=old['original_source_hashes_verified'],
        build=build, shipping=shipping, players=players, selected_unit_tests=9,
        discovery=343, full_suite_run=False, tick_class='SingleStepClock',
        deterministic_core_unchanged=True, receiver_unchanged=True,
        actual_right_shift_input_replay=True, default_left_shift_regression=True,
        actual_key_controls_observed=True, wrong_control_checker_rejects_unchanged_boolean_messages=True,
        source_wave_memory_explicit=True, context_producer_evidence=context,
        c45e_input_producer_integrated=False, original_os_keyboard_polling_executed=False,
        target='Windows11,1920x1080,16:9,ExclusiveFullScreen',
        published=False, applied=False, new_png=False, new_zip=False, full_remake_complete=False,
        limitations=['Original global key registry/virtual recipients remain source boundaries',
                     'C45E producer evidence is complete;recipient and lifecycle still require evidence',
                     'No physicalOS/nativeWin11/laptop/performance/fullApp/Life/AI/Start/final2026art claim'],
        next_step='Resolve original C45E recipient/lifecycle without guessing focus or tick;consider native VM vtable capture',
        files=files)
    OUTPUT.write_text(json.dumps(result, indent=2) + '\n')
    for name, meta in files.items():
        assert digest(ROOT / name) == meta['sha256']
    print(json.dumps(dict(passed=True, milestone=str(OUTPUT.relative_to(ROOT)), sha256=digest(OUTPUT),
                          files=len(files), selected_unit_tests=9, players=len(players))))


if __name__ == '__main__':
    seal()
