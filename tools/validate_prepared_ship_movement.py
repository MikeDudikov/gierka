#!/usr/bin/env python3
"""Actual prepared source0b MoveShip traces vs checked C#, not full gameplay."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

if __package__:
    from . import probe_ship_kinematics as native
    from . import validate_boss_ai_gate as gate
    from . import validate_mission_ship_seed as ship
else:
    import probe_ship_kinematics as native
    import validate_boss_ai_gate as gate
    import validate_mission_ship_seed as ship

ROOT=gate.ROOT
MissingPrerequisite=gate.MissingPrerequisite
FIXTURE=ROOT/'tests/fixtures/prepared_ship_movement.json'
FIXTURE_SHA256='28931c2849e05f46c7fd005c0f7b923f1d19bf26c045148a1a2388191cf2d374'
PROBE=ROOT/'tests/fixtures/PreparedShipMovementProbe.cs'
RUNTIME=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime'
SOURCES=[RUNTIME/name for name in ('MissionObjectSeed.cs','MissionShipSeed.cs','MissionOccupancyGrid.cs',
                                  'Simulation/PreparedShipMovement.cs','Simulation/ShipFrameProgression.cs')]
OUTPUT=ROOT/'artifacts/movement/kinematics/prepared-movement-csharp-validation.json'


def load_fixture(path=FIXTURE):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA256:raise ValueError('Original movement fixture SHA-256 differs')
    result=json.loads(raw)
    if result['original_exe_sha256']!=gate.EXPECTED:raise ValueError('Original movement executable differs')
    return result


def pose_publications(case):
    events={}
    for service in case['service_boundaries']:
        if service['phase']=='movement' and service['entry']=='0x50d5f0':
            args=service['arguments']
            gate.require(len(args)==7 and args[0]==0,'Unexpected original sprite publication')
            gate.require(service['tick'] not in events,'Multiple original main sprite publications in one call')
            events[service['tick']]=args
    frame=case['trace'][0]['frame'];world=case['trace'][0]['world'];rows=[]
    for snapshot in case['trace']:
        event=events.get(snapshot['tick'])
        if event is not None:frame=event[1];world=event[2:4]
        rows.append({'tick':snapshot['tick'],'should_publish_pose':event is not None,
                     'published_frame':frame,'published_world':world[:]})
    return rows


def expected_row(label,row,publication):
    return [label,str(row['tick']),*[str(value) for value in row['cell']],
            *[str(value) for value in row['world']],str(row['state']),str(int(row['center_gate'])),
            str(row['heading']),str(row['speed']),str(row['remainder']),str(row['deceleration']),
            str(row['reserved']),str(row['next_cell']),str(row['path_index']),str(row['path_count']),
            str(row['frame']),str(int(row['animation_tail_reached'])),str(row['occupied_cell_count']),
            ','.join(map(str,row['owned_cells'])),str(int(publication['should_publish_pose'])),
            str(publication['published_frame']),*[str(value) for value in publication['published_world']]]


def validate(mono_root=None,fixture=FIXTURE):
    frozen=load_fixture(fixture)
    pefile,unicorn,runtime,compiler=gate.prerequisites(mono_root=mono_root)
    actual=json.loads(json.dumps(native.validate()))
    gate.require(actual==frozen,'Fresh original movement execution differs from the pinned fixture')
    flags=ROOT/'tests/fixtures/mission_cell_flags.bin'
    gate.require(gate.digest(flags)==frozen['source_cell_flags_sha256'],'Original movement flags differ')
    seeds=json.loads(ship.FIXTURE.read_text())
    gate.require(gate.digest(ship.FIXTURE)==ship.FIXTURE_SHA256,'Original ship fixture differs')
    source0b=[row for row in seeds['records'] if row['instance_id']==0xb]
    gate.require(len(source0b)==1,'Source0b fixture is missing')
    hashes={str(path.relative_to(ROOT)):gate.digest(path) for path in [*SOURCES,PROBE]}
    lines=[];expected=[]
    for case in frozen['cases']:
        trace=case['trace'];config=case['controlled_inputs']
        lines.append('\t'.join(map(str,(case['label'],config['pending_steps_each_call'],trace[0]['stamp'],
                                       len(trace)-1,int(config['blocked_target_with_source0c_pointer'])))))
        expected.extend(expected_row(case['label'],row,pub) for row,pub in zip(trace,pose_publications(case)))
    with tempfile.TemporaryDirectory(prefix='prepared-source-ship-') as temporary:
        temporary=Path(temporary);exe=temporary/'PreparedShipMovementProbe.exe';payload=temporary/'source0b.hex'
        payload.write_text(source0b[0]['payload_hex']+'\n')
        compiled=subprocess.run(compiler+['/nologo','/checked+','/target:exe','/out:'+str(exe),
                                          *map(str,SOURCES),str(PROBE)],capture_output=True,text=True,timeout=60)
        gate.require(compiled.returncode==0,'Prepared movement C# compilation failed:\n'+compiled.stdout+compiled.stderr)
        run=subprocess.run([str(runtime),str(exe),str(flags),str(payload)],input='\n'.join(lines)+'\n',
                           capture_output=True,text=True,timeout=60)
        gate.require(run.returncode==0,'Prepared movement C# probe failed:\n'+run.stdout+run.stderr)
    guards=[];rows=[];guard_total=None
    for line in run.stdout.splitlines():
        values=line.split('\t')
        if values[0]=='ROW' and len(values)==25:rows.append(values[1:])
        elif values[0]=='CHECK' and len(values)==2:guards.append(values[1])
        elif values[0]=='GUARDS' and len(values)==2:guard_total=int(values[1])
        else:raise ValueError('Unexpected movement probe output: '+line)
    gate.require(guard_total==len(guards)==len(set(guards)),'Missing/duplicated movement guard checks')
    gate.require(len(rows)==len(expected),'Unexpected movement trace snapshot count')
    for index,(observed,wanted) in enumerate(zip(rows,expected)):
        gate.require(observed==wanted,f'Prepared movement mismatch at snapshot{index}: C#{observed}; original{wanted}')
    gate.require(all(gate.digest(ROOT/path)==value for path,value in hashes.items()),'Movement C# source changed during validation')
    native.source.checked_sources(native.source.SOURCE_ROOT)
    return {'kind':'Actual x86 prepared adjacent source0b movement vs actual checked C#',
            'original_exe_sha256':gate.EXPECTED,'fixture_sha256':FIXTURE_SHA256,
            'native_oracle_sha256':gate.digest(Path(native.__file__)),'validator_sha256':gate.digest(Path(__file__)),
            'source_sha256':hashes,'case_count':len(frozen['cases']),'snapshot_count':len(rows),'passed_snapshots':len(rows),
            'move_ship_calls':sum(len(case['trace'])-1 for case in frozen['cases']),
            'native_planner_cases':sum(case['native_navigation'] is not None for case in frozen['cases']),
            'publication_snapshots_compared':len(rows),
            'source_publication_count':sum(sum(p['should_publish_pose'] for p in pose_publications(case)) for case in frozen['cases']),
            'guard_count':len(guards),'guards':guards,'checked_compilation':True,
            'compiler_command':compiler,'mono_runtime':str(runtime),'unicorn_version':unicorn.__version__,
            'cases':[{'label':case['label'],'snapshots':len(case['trace']),
                      'final_snapshot':case['trace'][-1],'grid_writes':case['grid_writes']} for case in frozen['cases']],
            'boundary':'Renderer/visibility/arrival and bounded heap services only; movement math, source grid reserve/release and adjacent native planner are original instructions',
            'reference_conditions':{'source_ship':'OBJ_0000000b','target':[15,3],'native_path':[[16,2,5],[15,3,5]],
                                    'wind_force':0,'wind_heading':5,'owner_upgrade_level':0,'requested_health_percent':100,
                                    'logical_dimensions':[56,56],'pending_steps':[1,2,3,7]},
            'excluded':['No full game Life/message/click sequence replay; command and planner evidence are separate',
                        'Fixed verified adjacent route is projected, not a C# pathfinder',
                        'Weather and owner upgrade are explicit controlled reference inputs, not default miss000 values',
                        'After state0 the diagnostic freezes; original idle RNG/animation are not implemented',
                        'No Unity player, real-time cadence, combat, AI, target changes, turns or linked-ship movement are validated']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=OUTPUT);parser.add_argument('--mono-root',type=Path)
    args=parser.parse_args();result=validate(args.mono_root)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'cases':result['case_count'],'snapshots':result['snapshot_count'],
                      'passed':result['passed_snapshots'],'guards':result['guard_count'],'output':str(args.output)},indent=2))


if __name__=='__main__':main()
