"""Seal verified BaseSystem evidence while requiring a byte-identical Unity project."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / 'docs/evidence/milestone-20261104-right-shift-input.json'
OUTPUT = ROOT / 'docs/evidence/milestone-20261104-base-dispatch.json'
PHASE = ROOT / 'artifacts/native-base-vtable'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seal():
    assert not OUTPUT.exists(), 'Do not overwrite a sealed milestone'
    old = json.loads(PREVIOUS.read_text())
    changed = []
    for name, meta in old['files'].items():
        path = ROOT / name
        assert path.is_file(), name
        if digest(path) != meta['sha256']:
            changed.append(name)
    expected = {'README.md', 'docs/REFERENCE_MATRIX.csv',
                *('docs/' + n for n in ('SHIP_POINTER_RESUME.md', 'UnityProjectContext.md',
                   'VALIDATION.md', 'UNITY_ENVIRONMENT.md', 'REMAKE_PLAN.md'))}
    assert set(changed) == expected, (set(changed) - expected, expected - set(changed))
    for name, sha in old['original_source_hashes_verified'].items():
        assert digest(ROOT / 'reference/raw/ancient-conquest' / name) == sha
    proof = json.loads((PHASE / 'validation.json').read_text())
    assert proof['passed'] and proof['actual_recursive_recipient_executed']
    assert proof['direct_operations'] == 42 and proof['context_cases'] == 108
    assert len(proof['negative_controls']) == 5
    tests = (PHASE / 'tests.log').read_text()
    assert re.search(r'Ran 9 tests in ', tests) and tests.rstrip().endswith('OK')
    attempts = {}
    for index in range(1, 5):
        run = PHASE / f'run-{index:02d}'
        status = json.loads((run / 'host-status.json').read_text())
        serial = (run / 'serial.log').read_text()
        trace = [json.loads(line) for line in (run / 'trace.jsonl').read_text().splitlines()]
        assert status['original_file_unchanged'] and not status['timed_out']
        assert 'IA32_EXIT=0' in serial and 'CONTROL32_EXIT=0' in serial
        assert 'SOURCE_PROBE_EXIT=2' in serial
        assert trace[-1]['event'] == 'status' and not trace[-1]['source_hit']
        attempts[run.name] = dict(**status, source_hit=False)
    assert any('registry record is corrupted' in event.get('title', '')
               for event in trace), 'Missing explicit startup error'
    names = set(old['files'])
    excluded = {'seal.log', 'config-draft-verified.json', 'previous-start-skill.txt', 'next-start-skill.txt'}
    names.update(str(p.relative_to(ROOT)) for p in PHASE.rglob('*')
                 if p.is_file() and p.name not in excluded)
    names.update({'tools/seal_source_base_dispatch.py', 'tools/probe_source_base_dispatch.py',
                  'tools/validate_source_base_dispatch.py', 'tools/run_source_vtable_vm.py',
                  'tools/win32_source_vtable_probe.c', 'tests/test_source_base_dispatch.py',
                  'tests/fixtures/source_base_dispatch.json', 'docs/SOURCE_BASE_DISPATCH.md'})
    files = {name: dict(bytes=(ROOT / name).stat().st_size, sha256=digest(ROOT / name))
             for name in sorted(names)}
    result = dict(date='2026-11-04', passed=True, status='Evidence complete; Unity integration pending',
                  previous_milestone=dict(path=str(PREVIOUS.relative_to(ROOT)), sha256=digest(PREVIOUS)),
                  previous_files_checked=len(old['files']), changed_previous_files=sorted(changed),
                  base_commit=old['base_commit'], original_source_hashes_verified=old['original_source_hashes_verified'],
                  csharp=73, meta=132, frozen_project_files=277, unity_project_byte_identical=True,
                  shipping_build_byte_identical=True, deterministic_core_unchanged=True,
                  tick_class='SingleStepClock', proof=proof, native_attempts=attempts,
                  selected_tests=9, discovery=344, full_suite_run=False,
                  c45e_unity_lifecycle_integrated=False, full_original_application=False,
                  next_step='Execute source4ee970 WM_ACTIVATEAPP branch with explicit OS-service boundaries',
                  published=False, applied=False, new_png=False, new_zip=False,
                  full_remake_complete=False, files=files)
    OUTPUT.write_text(json.dumps(result, indent=2) + '\n')
    assert all(digest(ROOT / name) == meta['sha256'] for name, meta in files.items())
    print(dict(passed=True, milestone=str(OUTPUT.relative_to(ROOT)), sha256=digest(OUTPUT), files=len(files)))


if __name__ == '__main__':
    seal()
