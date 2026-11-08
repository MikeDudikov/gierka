"""Seal x86 activation, C# key projection and player evidence;reject unrelated project drift."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / 'docs/evidence/milestone-20261104-base-dispatch.json'
OUTPUT = ROOT / 'docs/evidence/milestone-20261104-source-app-activation.json'
PHASE = ROOT / 'artifacts/source-app-activation'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seal():
    assert not OUTPUT.exists(), 'Do not overwrite a sealed milestone'
    old = json.loads(PREVIOUS.read_text())
    changed = []
    for name, meta in old['files'].items():
        assert (ROOT / name).is_file(), name
        if digest(ROOT / name) != meta['sha256']:
            changed.append(name)
    expected = {'README.md', 'docs/REFERENCE_MATRIX.csv',
        *('docs/' + n for n in ('SHIP_POINTER_RESUME.md', 'UnityProjectContext.md',
           'VALIDATION.md', 'UNITY_ENVIRONMENT.md', 'REMAKE_PLAN.md')),
        *('Unity/AncientConquest/Assets/AncientConquest/Runtime/' + n + '.cs'
          for n in ('ShipPointerReference', 'ShipFleetMoveInputReplay')),
        *('artifacts/unity-reference/Windows/' + n for n in (
            'AncientConquestReference_Data/Managed/Assembly-CSharp.dll',
            'AncientConquestReference_Data/boot.config', 'AncientConquestReference_Data/globalgamemanagers',
            'AncientConquestReference_Data/globalgamemanagers.assets',
            'AncientConquestReference_Data/resources.assets', 'build-report.json'))}
    assert set(changed) == expected, (set(changed) - expected, expected - set(changed))
    project = json.loads((PHASE / 'project-frozen.json').read_text())
    for name, meta in project.items():
        assert digest(ROOT / name) == meta['sha256'], name
    assert len(project) == 279
    assert sum(n.endswith('.cs') for n in project) == 74
    assert sum(n.endswith('.meta') for n in project) == 133
    for name, sha in old['original_source_hashes_verified'].items():
        assert digest(ROOT / 'reference/raw/ancient-conquest' / name) == sha
    build = json.loads((ROOT / 'artifacts/unity-reference/Windows/build-report.json').read_text())
    assert build['result'] == 'Succeeded' and build['warnings'] == build['errors'] == 0
    assert build['bytes'] == 153601435 and build['resolution'] == '1920x1080'
    shipping = json.loads((PHASE / 'shipping-world.json').read_text())
    dll = ROOT / 'artifacts/unity-reference/Windows/AncientConquestReference_Data/Managed/Assembly-CSharp.dll'
    assert digest(dll) == shipping['assembly_sha256']
    assert all(v['passed'] for v in shipping.values() if isinstance(v, dict))
    assert sum(v.get('actor_states', 0) for v in shipping.values() if isinstance(v, dict)) == 33624
    proofs = {name: json.loads((PHASE / filename).read_text()) for name, filename in (
        ('x86_activation', 'validation.json'), ('csharp_state', 'csharp-state.json'),
        ('shipping_state', 'shipping-route-key.json'))}
    assert all(p['passed'] for p in proofs.values())
    assert proofs['x86_activation']['cases'] == 96 and len(proofs['x86_activation']['negative_controls']) == 4
    assert proofs['csharp_state']['states'] == proofs['shipping_state']['states'] == 150
    assert len(proofs['csharp_state']['negative_controls']) == 5
    tests = (PHASE / 'runtime-tests.log').read_text()
    assert re.search(r'Ran 12 tests in ', tests) and tests.rstrip().endswith('OK')
    corrected = (PHASE / 'source-context-marker-test.log').read_text()
    assert re.search(r'Ran 1 test in ', corrected) and corrected.rstrip().endswith('OK')
    players = {}
    for name, count in (('left-context-first', 39), ('right-context-last', 39), ('default-pending-last', 35)):
        report = json.loads((PHASE / name / 'report.json').read_text())
        assert report['passed'] and report['exit_code'] == 0 and report['checkpoints'] == count
        assert report['publications'] == 291
        if count == 39:
            assert report['context_events'] == 4 and report['key_envelopes'] == 5
            assert len(report['negative_controls']) == 13
            assert report['actual_queue_reads'] == 1326 and report['marker_checkpoint_reads'] == 26
        players[name] = {k: report[k] for k in ('passed', 'checkpoints', 'actor_rows', 'component_rows',
            'actual_queue_reads', 'publications', 'marker_checkpoint_reads', 'negative_controls', 'exit_code')}
    names = set(old['files']) | set(project)
    excluded = {'seal.log', 'config-draft-verified.json', 'previous-start-skill.txt', 'next-start-skill.txt'}
    names.update(str(p.relative_to(ROOT)) for p in PHASE.rglob('*') if p.is_file() and p.name not in excluded)
    names.update({'tools/seal_source_app_activation.py', 'tools/probe_source_app_activation.py',
        'tools/validate_source_app_activation.py', 'tools/probe_context_marker_lifecycle.py',
        'tools/validate_source_route_key_state.py', 'tools/smoke_source_context_input.py',
        'tests/test_source_app_activation.py', 'tests/test_source_context_markers.py',
        'tests/test_source_route_key_state.py', 'tests/test_smoke_source_context_input.py',
        'tests/fixtures/source_app_activation.json', 'tests/fixtures/source_context_markers.json',
        'tests/fixtures/SourceRouteKeyProbe.cs', 'tests/fixtures/source_context_left_player.log',
        'tests/fixtures/source_context_right_player.log', 'docs/SOURCE_APP_ACTIVATION.md'})
    files = {n: dict(bytes=(ROOT / n).stat().st_size, sha256=digest(ROOT / n)) for n in sorted(names)}
    result = dict(date='2026-11-04', passed=True, status='Ready with stated diagnostic limits',
        previous_milestone=dict(path=str(PREVIOUS.relative_to(ROOT)), sha256=digest(PREVIOUS)),
        previous_files_checked=len(old['files']), changed_previous_files=sorted(changed),
        base_commit=old['base_commit'], original_source_hashes_verified=old['original_source_hashes_verified'],
        csharp=74, meta=133, frozen_project_files=279,
        changed_existing_csharp=['ShipPointerReference', 'ShipFleetMoveInputReplay'],
        new_csharp=['SourceRouteKeyVisibility'], unchanged_existing_csharp=71,
        deterministic_core_unchanged=True, staged_resources_unchanged=80, tick_class='SingleStepClock',
        proofs=proofs, build=build, shipping=shipping, players=players,
        selected_tests=12, discovery=349, full_suite_run=False,
        explicit_source_context_integrated=True, unity_focus_callback_unchanged=True,
        physical_os_activation_validated=False, full_remake_complete=False,
        target='Windows11,1920x1080,16:9,ExclusiveFullScreen',
        preserved_diagnostics=['initial invalid GUID build', 'incorrect auxiliary registered-count assertion',
                               'missing netstandard reference in first shipping checker'],
        preexisting_runtime_warning='ComputeBuffer GC disposal also present in previous Shift players',
        next_step='Use real original installer in private offline guest to resolve registry startup block',
        published=False, applied=False, new_png=False, new_zip=False, files=files)
    OUTPUT.write_text(json.dumps(result, indent=2) + '\n')
    assert all(digest(ROOT / n) == m['sha256'] for n, m in files.items())
    print(dict(passed=True, milestone=str(OUTPUT.relative_to(ROOT)), sha256=digest(OUTPUT), files=len(files)))


if __name__ == '__main__':
    seal()
