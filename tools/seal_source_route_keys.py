"""Seal source-key integration against the preceding verified input checkpoint."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
PREVIOUS=ROOT/'docs/evidence/milestone-20261104-queued-input.json'
OUTPUT=ROOT/'docs/evidence/milestone-20261104-source-route-keys.json'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def seal():
    old=json.loads(PREVIOUS.read_text());changed=[]
    for name,m in old['files'].items():
        f=ROOT/name
        if not f.is_file():raise AssertionError('Missing inherited file:'+name)
        if digest(f)!=m['sha256']:changed.append(name)
    expected={'README.md',*('docs/'+n for n in('SHIP_POINTER_RESUME.md','UnityProjectContext.md','VALIDATION.md','UNITY_ENVIRONMENT.md','REMAKE_PLAN.md')),
        *('Unity/AncientConquest/Assets/AncientConquest/Runtime/'+n+'.cs'for n in('ShipPointerReference','WorldPointerInput')),
        *('artifacts/unity-reference/Windows/'+n for n in('AncientConquestReference_Data/Managed/Assembly-CSharp.dll','AncientConquestReference_Data/boot.config',
            'AncientConquestReference_Data/globalgamemanagers','AncientConquestReference_Data/resources.assets','build-report.json')),
        'tools/smoke_pending_queued_input.py','tools/smoke_queued_input.py'}
    assert set(changed)==expected,(set(changed)-expected,expected-set(changed))
    project=json.loads((ROOT/'artifacts/queued-key-visibility/project-frozen.json').read_text())
    for name,m in project.items():assert digest(ROOT/name)==m['sha256']
    for name,h in old['original_source_hashes_verified'].items():assert digest(ROOT/'reference/raw/ancient-conquest'/name)==h
    for name,count in(('historical-checkers.log',4),('source-tests.log',1),('runtime-tests-final.log',2)):
        log=(ROOT/'artifacts/queued-key-visibility'/name).read_text();assert re.search('Ran '+str(count)+r' tests? in ',log)and log.rstrip().endswith('OK'),name
    players={}
    for name in('committed-first','committed-last','pending-first','pending-last'):
        r=json.loads((ROOT/'artifacts/queued-key-visibility'/name/'report.json').read_text())
        assert r['passed']and r['exit_code']==0 and r['source_key_visibility']and r['key_envelopes']==4
        assert len(r['negative_controls'])==(7 if name.startswith('committed')else 8)
        players[name]={k:r[k]for k in('passed','checkpoints','actor_rows','component_rows','actual_queue_reads','publications','marker_checkpoint_reads','key_envelopes','negative_controls','exit_code')}
    build=json.loads((ROOT/'artifacts/unity-reference/Windows/build-report.json').read_text());assert build['result']=='Succeeded'and build['warnings']==build['errors']==0
    shipping=json.loads((ROOT/'artifacts/queued-key-visibility/shipping.json').read_text());assert digest(ROOT/'artifacts/unity-reference/Windows/AncientConquestReference_Data/Managed/Assembly-CSharp.dll')==shipping['assembly_sha256']
    for value in shipping.values():
        if isinstance(value,dict):assert value['passed']
    names=set(old['files'])|set(project)
    for folder in('artifacts/queued-key-visibility','artifacts/pending-queued-input','artifacts/unity-reference/Windows'):
        names.update(str(p.relative_to(ROOT))for p in(ROOT/folder).rglob('*')if p.is_file()and p.name not in('seal.log','config-draft-verified.json','previous-start-skill.txt','next-start-skill.txt'))
    for name in('tools/seal_source_route_keys.py','tests/test_source_key_visibility.py','tests/test_smoke_source_route_keys.py',
        'tests/fixtures/source_route_keys_committed_player.log','tests/fixtures/source_route_keys_pending_player.log','docs/SOURCE_ROUTE_KEY_VISIBILITY.md'):
        names.add(name)
    names.discard(str(OUTPUT.relative_to(ROOT)))
    files={name:dict(bytes=(ROOT/name).stat().st_size,sha256=digest(ROOT/name))for name in sorted(names)}
    result=dict(date='2026-11-04',passed=True,status='Ready with limitations',previous_milestone=dict(path=str(PREVIOUS.relative_to(ROOT)),sha256=digest(PREVIOUS)),
        previous_files_checked=len(old['files']),changed_previous_files=sorted(changed),base_commit=old['base_commit'],csharp=73,meta=132,frozen_project_files=len(project),
        changed_existing_csharp=['ShipPointerReference','WorldPointerInput'],unchanged_existing_csharp=71,new_csharp=[],staged_resource_files_unchanged=80,
        original_source_hashes_verified=old['original_source_hashes_verified'],build=build,shipping=shipping,players=players,selected_unit_tests=7,discovery=340,full_suite_run=False,
        tick_class='SingleStepClock',world_loop_unchanged=True,task_owner_unchanged=True,membership_unchanged=True,grid_unchanged=True,source_sprite_queue_unchanged=True,
        source_key_visibility_integrated=True,source_key_operations=10,source_accelerator_record_bytes=74,
        source_key_fixture_sha256='470fbee7542cf8f5552447f0cf1ee24ff9e4b871a5d17e9bea3b67e9c17f033e',
        same_tick_key_then_mouse_order_validated=True,source_key_envelopes=16,marker_checkpoint_reads=72,source_wave_memory_explicit=True,
        snapshot_with_two_shift_changes_rejected_without_assuming_order=True,original_global_accelerator_registry_executed=False,
        original_os_keyboard_polling_executed=False,c45e_input_producer_integrated=False,actual_right_shift_input_replay=False,
        target='Windows11,1920x1080,16:9,ExclusiveFullScreen',published=False,applied=False,new_png=False,new_zip=False,full_remake_complete=False,
        limitations=['Original global key registry and virtual recipients remain source-oracle boundaries',
            'Current player replays use LeftShift;RightShift accelerator bytes verified;separate RightShift replay is next',
            'No physicalOS/nativeWin11/laptop/performance/fullApp/Life/AI/Start/final2026art claim'],
        next_step='Separate actual RightShift InputSystem replay;then source C45E producer/registry and ordered/coalesced event contracts',files=files)
    OUTPUT.write_text(json.dumps(result,indent=2)+'\n')
    for name,m in files.items():assert digest(ROOT/name)==m['sha256']
    print(json.dumps(dict(passed=True,milestone=str(OUTPUT.relative_to(ROOT)),sha256=digest(OUTPUT),files=len(files),selected_unit_tests=7,players=len(players))))


if __name__=='__main__':seal()
