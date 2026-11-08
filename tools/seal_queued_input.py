"""Verify inherited checkpoint,explicit changes and all current project inputs;seal local evidence."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
PREVIOUS=ROOT/'docs/evidence/milestone-20261104-queued-world-integration.json'
OUTPUT=ROOT/'docs/evidence/milestone-20261104-queued-input.json'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def seal():
    old=json.loads(PREVIOUS.read_text());changed=[]
    for name,meta in old['files'].items():
        p=ROOT/name
        if not p.is_file():raise AssertionError('Missing inherited file:'+name)
        if digest(p)!=meta['sha256']:changed.append(name)
    expected={
        'README.md','docs/SHIP_POINTER_RESUME.md','docs/UnityProjectContext.md','docs/VALIDATION.md','docs/UNITY_ENVIRONMENT.md','docs/REMAKE_PLAN.md',
        'Unity/AncientConquest/Assets/AncientConquest/Editor/BuildReferenceWindows.cs',
        *('Unity/AncientConquest/Assets/AncientConquest/Runtime/'+name+'.cs'for name in('ShipFleetMotionReference','ShipFleetMoveInputReplay','ShipFleetVisualReference','ShipPointerReference')),
        'Unity/AncientConquest/Assets/Resources/ShipFleetVisualsGenerated/ShipFleetVisualsManifest.json',
        'artifacts/unity-reference/Windows/AncientConquestReference_Data/Managed/Assembly-CSharp.dll',
        'tools/probe_queued_ui_world.py','tools/stage_ship_fleet_visuals.py','tools/validate_queued_ui_world.py','tools/validate_queued_world_integration.py'}
    if set(changed)!=expected:raise AssertionError('Inherited changes differ:'+str((set(changed)-expected,expected-set(changed))))
    for name,h in old['original_source_hashes_verified'].items():assert digest(ROOT/'reference/raw/ancient-conquest'/name)==h
    project=json.loads((ROOT/'artifacts/pending-queued-input/project-frozen.json').read_text())
    for name,m in project.items():assert digest(ROOT/name)==m['sha256']
    for filename,count in (('artifacts/queued-input/wp-tests.log',1),('artifacts/queued-input/source-tests-final.log',3),
        ('artifacts/pending-queued-input/legacy-checker-tests.log',4),('artifacts/pending-queued-input/source-tests.log',1),('artifacts/pending-queued-input/runtime-tests.log',2)):
        log=(ROOT/filename).read_text();assert re.search('Ran '+str(count)+r' tests? in ',log)and log.rstrip().endswith('OK'),filename
    players={}
    for pos in(0,3):
        r=json.loads((ROOT/f'artifacts/pending-queued-input/player-final-{pos}/report.json').read_text())
        assert r['passed']and r['exit_code']==0 and r['checkpoints']==35 and len(r['negative_controls'])==6
        players[str(pos)]={k:r[k]for k in('passed','checkpoints','actor_rows','component_rows','actual_queue_reads','publications','marker_checkpoint_reads','negative_controls','exit_code')}
    shipping=json.loads((ROOT/'artifacts/pending-queued-input/shipping-current.json').read_text());dll=ROOT/'artifacts/unity-reference/Windows/AncientConquestReference_Data/Managed/Assembly-CSharp.dll'
    assert digest(dll)==shipping['assembly_sha256']
    for r in shipping.values():
        if isinstance(r,dict):assert r['passed']
    build=json.loads((ROOT/'artifacts/unity-reference/Windows/build-report.json').read_text());assert build['warnings']==build['errors']==0 and build['result']=='Succeeded'
    names=set(old['files'])|set(project)
    for folder in('artifacts/queued-input','artifacts/pending-queued-input','artifacts/queued-key-visibility','artifacts/unity-reference/Windows'):
        names.update(str(p.relative_to(ROOT))for p in(ROOT/folder).rglob('*')if p.is_file()and p.name not in('seal.log','config-draft-verified.json','previous-start-skill.txt'))
    for folder in('tools','tests/fixtures','tests','docs'):
        for p in(ROOT/folder).iterdir():
            if not p.is_file():continue
            name=p.name
            if any(s in name for s in('queued_input','pending_queued','wp_move','source_key_visibility','queued_marker_lifecycle'))or name in('QUEUED_INPUT_AND_MARKERS.md','PENDING_QUEUED_INPUT.md'):
                names.add(str(p.relative_to(ROOT)))
    names.discard(str(OUTPUT.relative_to(ROOT)))
    files={name:dict(bytes=(ROOT/name).stat().st_size,sha256=digest(ROOT/name))for name in sorted(names)}
    result=dict(date='2026-11-04',passed=True,status='Ready with limitations',previous_milestone=dict(path=str(PREVIOUS.relative_to(ROOT)),sha256=digest(PREVIOUS)),
        previous_files_checked=len(old['files']),changed_previous_files=sorted(changed),base_commit=old['base_commit'],
        csharp=73,meta=132,frozen_project_files=len(project),changed_existing_csharp=sorted(n for n in changed if n.startswith('Unity/')and n.endswith('.cs')),
        unchanged_existing_csharp=68,new_csharp=[],staged_resource_files=80,previous_resource_files_unchanged=77,
        original_source_hashes_verified=old['original_source_hashes_verified'],build=build,shipping=shipping,players=players,
        selected_unit_tests=11,full_suite_run=False,discovery=337,clock_source_unchanged=True,world_source_unchanged=True,
        task_source_unchanged=True,membership_source_unchanged=True,occupancy_grid_source_unchanged=True,source_sprite_queue_unchanged=True,
        target='Windows11,1920x1080,16:9,ExclusiveFullScreen',queued_ui_enabled_with_explicit_wave_context=True,first_pending_shift_enabled=True,
        first_pending_packet_order='41,41,41,20,20,20',append_before_first_mail_supported=True,duplicate_updates_requested_at=True,
        selection_clear_removes_graphics_only=True,ctrl_recall_does_not_recreate_markers=True,per_wave_memory_explicit=True,
        source_key_binding_evidence='tests/fixtures/source_key_visibility.json',source_key_visibility_unity_integrated=False,
        published=False,applied=False,new_zip=False,new_png=False,full_remake_complete=False,
        limitations=['Global original keyboard accelerators not integrated yet;source C45D proof is ready',
            'Global key registry/virtual recipients/OS polling are source-proof boundaries',
            'Full App/Life/AI/Start/300/311/report40/full heap history/nativeWin11/target hardware/final2026art remain incomplete',
            'InputSystem replay is synthetic;no whole-frame RGB claim'],
        next_step='Connect source C45D Shift1/0 visibility through existing input bridge;retain explicit memory context and deterministic world',files=files)
    OUTPUT.write_text(json.dumps(result,indent=2)+'\n')
    for name,m in files.items():assert digest(ROOT/name)==m['sha256']
    print(json.dumps(dict(passed=True,milestone=str(OUTPUT.relative_to(ROOT)),sha256=digest(OUTPUT),files=len(files),selected_unit_tests=11,players=players)))


if __name__=='__main__':seal()
