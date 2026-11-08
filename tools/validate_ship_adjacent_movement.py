#!/usr/bin/env python3
"""Original adjacent planner and whole MoveShip/turn traces vs actual C#."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

if __package__:
    from . import probe_ship_adjacent as native
    from . import validate_boss_ai_gate as gate
    from . import validate_mission_ship_seed as ship
else:
    import probe_ship_adjacent as native
    import validate_boss_ai_gate as gate
    import validate_mission_ship_seed as ship

ROOT=gate.ROOT
MissingPrerequisite=gate.MissingPrerequisite
FIXTURE=ROOT/'tests/fixtures/ship_adjacent_movement.json'
FIXTURE_SHA256='2ffc6d70e131770dc065b252e88818e02aca203f681ea1ff373875883f8e9075'
PROBE=ROOT/'tests/fixtures/ShipAdjacentMovementProbe.cs'
RUNTIME=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime'
SOURCES=[RUNTIME/name for name in ('MissionObjectSeed.cs','MissionShipSeed.cs','MissionOccupancyGrid.cs',
          'Simulation/ShipAdjacentQuery.cs','Simulation/ShipAdjacentPlanner.cs',
          'Simulation/ShipTurnProgression.cs','Simulation/ShipFrameProgression.cs','Simulation/ShipAdjacentMovement.cs')]
OUTPUT=ROOT/'artifacts/adjacent/kinematics/ship-adjacent-csharp-validation.json'


def load_fixture(path=FIXTURE):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA256:raise ValueError('Original adjacent movement fixture SHA-256 differs')
    result=json.loads(raw)
    if result['original_exe_sha256']!=gate.EXPECTED:raise ValueError('Original adjacent movement executable differs')
    return result


def expected_row(case,row):
    complete=case['accepted'] and row['state']==0 and row['cell']==case['goal'] and row['world']==[v*64+4 for v in case['goal']]
    values=[case['label'],row['tick'],row['stamp'],*row['cell'],*row['world'],row['state'],int(row['center_gate']),
            row['heading'],row['target_heading'],row['turn_step'],row['speed'],row['remainder'],row['deceleration'],
            row['reserved'],row['next_cell'],row['path_index'],row['path_count'],row['frame'],row['last_frame_tick'],
            row['last_state_counter'],row['drawn_frame'],*row['render_world'],int(row['animation_tail_reached']),
            int(row['pose_published']),row['occupied_cell_count'],','.join(map(str,row['owned_cells'])),int(complete)]
    return list(map(str,values))


def validate(mono_root=None,fixture=FIXTURE):
    frozen=load_fixture(fixture)
    pefile,unicorn,runtime,compiler=gate.prerequisites(mono_root=mono_root)
    actual=json.loads(json.dumps(native.validate()))
    gate.require(actual==frozen,'Fresh original adjacent execution differs from pinned native fixture')
    flags=ROOT/'tests/fixtures/mission_cell_flags.bin'
    gate.require(gate.digest(flags)==frozen['source_cell_flags_sha256'],'Original adjacent flags differ')
    gate.require(gate.digest(ship.FIXTURE)==ship.FIXTURE_SHA256,'Source ship initialization fixture differs')
    source0b=[row for row in json.loads(ship.FIXTURE.read_text())['records'] if row['instance_id']==0xb]
    gate.require(len(source0b)==1,'Source0b initialization fixture missing')
    hashes={str(path.relative_to(ROOT)):gate.digest(path) for path in [*SOURCES,PROBE]}
    lines=[];expected=[];expected_plans=[]
    for case in frozen['cases']:
        config=case['controlled_inputs'];trace=case['trace']
        lines.append('\t'.join(map(str,(case['label'],config['pending_steps_each_call'],*case['goal'],len(trace)-1,
                                       int(case['accepted']),int(config['occupied_target_after_plan_with_source0c_pointer'])))))
        expected.extend(expected_row(case,row) for row in trace)
        expected_plans.append([case['label'],str(int(case['accepted'])),case['active_path_hex']])
    with tempfile.TemporaryDirectory(prefix='source-ship-adjacent-') as temporary:
        folder=Path(temporary);exe=folder/'ShipAdjacentMovementProbe.exe';payload=folder/'source0b.hex'
        payload.write_text(source0b[0]['payload_hex']+'\n')
        compiled=subprocess.run(compiler+['/nologo','/checked+','/target:exe','/out:'+str(exe),*map(str,SOURCES),str(PROBE)],
                                capture_output=True,text=True,timeout=60)
        gate.require(compiled.returncode==0,'Adjacent C# compilation failed:\n'+compiled.stdout+compiled.stderr)
        result=subprocess.run([str(runtime),str(exe),str(flags),str(payload)],input='\n'.join(lines)+'\n',
                              capture_output=True,text=True,timeout=60)
        gate.require(result.returncode==0,'Adjacent C# probe failed:\n'+result.stdout+result.stderr)
    rows=[];plans=[];guards=[];guard_total=None
    for line in result.stdout.splitlines():
        fields=line.split('\t')
        if fields[0]=='ROW' and len(fields)==31:rows.append(fields[1:])
        elif fields[0]=='PLAN' and len(fields)==4:plans.append(fields[1:])
        elif fields[0]=='CHECK' and len(fields)==2:guards.append(fields[1])
        elif fields[0]=='GUARDS' and len(fields)==2:guard_total=int(fields[1])
        else:raise ValueError('Unexpected adjacent probe output: '+line)
    gate.require(plans==expected_plans,'C# adjacent plan outcome or route points differ from original')
    gate.require(len(rows)==len(expected),'Adjacent snapshot count differs from native trace')
    for index,(row,wanted) in enumerate(zip(rows,expected)):
        gate.require(row==wanted,f'Adjacent snapshot mismatch at{index}: C#{row}; native{wanted}')
    gate.require(guard_total==len(guards)==len(set(guards)),'Missing/duplicated adjacent API guard')
    gate.require(all(gate.digest(ROOT/path)==sha for path,sha in hashes.items()),'Adjacent C# source changed during comparison')
    native.source.checked_sources(native.source.SOURCE_ROOT)
    return {'kind':'Actual original adjacent planners, turns and whole MoveShip vs checked C# source0b adapter',
            'fixture_sha256':FIXTURE_SHA256,'original_exe_sha256':gate.EXPECTED,
            'native_oracle_sha256':gate.digest(Path(native.__file__)),'validator_sha256':gate.digest(Path(__file__)),
            'source_sha256':hashes,'case_count':len(frozen['cases']),'snapshot_count':len(rows),'passed_snapshots':len(rows),
            'native_move_ship_calls':sum(len(c['trace'])-1 for c in frozen['cases']),
            'native_planner_calls':len(frozen['cases']),'native_publications':sum(sum(t['pose_published'] for t in c['trace']) for c in frozen['cases']),
            'source_static_cases':sum(c['scenario']=='source_static' for c in frozen['cases']),
            'postplan_occupied_cases':sum(c['scenario']=='postplan_occupied' for c in frozen['cases']),
            'accepted_routes':sum(c['accepted'] for c in frozen['cases']),
            'rejected_routes':sum(not c['accepted'] for c in frozen['cases']),
            'arrived_routes':sum(c['accepted'] and c['trace'][-1]['cell']==c['goal'] and
                                c['trace'][-1]['world']==[v*64+4 for v in c['goal']] and
                                c['trace'][-1]['state']==0 for c in frozen['cases']),
            'deferred_timeout_routes':sum(c['scenario']=='postplan_occupied' and c['trace'][-1]['state']==0
                                          and c['trace'][-1]['cell']!=c['goal'] for c in frozen['cases']),
            'guard_count':len(guards),'guards':guards,'checked_compilation':True,
            'compiler_command':compiler,'mono_runtime':str(runtime),'unicorn_version':unicorn.__version__,
            'cases':[{'label':c['label'],'goal':c['goal'],'accepted':c['accepted'],'scenario':c['scenario'],
                      'snapshots':len(c['trace']),'final_snapshot':c['trace'][-1],'grid_writes':c['grid_writes']} for c in frozen['cases']],
            'reference_conditions':{'source_ship':'OBJ_0000000b','origin':[16,2],'initial_heading':5,
               'wind_force':0,'wind_heading':5,'owner_upgrade':0,'health_percent':100,'logical_size':[56,56],
               'planner_counter':1,'move_step_counter':'call_count+1','pending_steps':[1,2,3,7]},
            'boundary':'Actual ctor/load, derived velocity, source passability-map prefix, adjacent planner, turn and whole MoveShip; only explicit setjmp/heap/render-publication/visibility/system boundaries',
            'excluded':['No full source Life/command/planner/motion callback schedule replay or real-time cadence claim',
                        'Planner counter1 then MoveShip counters2,... is an explicit diagnostic schedule',
                        'A closed two-point C# plan adapter is compared with native path search; no general C# pathfinder',
                        'Weather and upgrade0 are controlled reference inputs, not guaranteed new-mission defaults',
                        'Other seven source fleet owners remain static minimal occupancy objects; their full constructors/AI do not run',
                        'Stopped physics freezes before native idle RNG; linked movement, combat, later commands and world simulation are excluded',
                        'Native rejected direct planner leaves its setjmp chain at a local frame; exception handling is not projected into C#',
                        'No Unity player, Win11 input or hardware performance is validated by this probe']}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=OUTPUT)
    parser.add_argument('--mono-root',type=Path);args=parser.parse_args();result=validate(args.mono_root)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ('case_count','snapshot_count','passed_snapshots','native_move_ship_calls','guard_count')},indent=2))


if __name__=='__main__':main()
