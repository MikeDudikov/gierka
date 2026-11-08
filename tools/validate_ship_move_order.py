#!/usr/bin/env python3
"""Compare a whole native normal MOVE request/work/motion chain with checked C#."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,tempfile
from pathlib import Path
if __package__:
 from . import validate_boss_ai_gate as gate,validate_mission_ship_seed as ship
else:
 import validate_boss_ai_gate as gate,validate_mission_ship_seed as ship
ROOT=gate.ROOT
MissingPrerequisite=gate.MissingPrerequisite
FIXTURE=ROOT/'tests/fixtures/ship_move_order.json'
FIXTURE_SHA256='5a11bf625ea6d3a5a4f7b3e6d037b2eafb348eb1f5c7a9b5075e62586a3409ac'
RUNTIME=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime'
PROBE=ROOT/'tests/fixtures/ShipMoveOrderProbe.cs'
SOURCES=[RUNTIME/name for name in ('MissionObjectSeed.cs','MissionShipSeed.cs','MissionOccupancyGrid.cs',
 'Simulation/ShipMoveOrder.cs','Simulation/ShipAdjacentQuery.cs','Simulation/ShipTurnProgression.cs',
 'Simulation/ShipFrameProgression.cs','Simulation/ShipIdleProgression.cs','Simulation/ShipReplanPlanner.cs',
 'Simulation/SourceNearestPathfinder.cs','Simulation/SourcePathfinder.cs','Simulation/SourceWaveField.cs')]
COLUMNS=('label sample_index operation counter cell_x cell_y world_x world_y state center_gate heading target_heading '
 'turn_step speed remainder deceleration reserved next_cell path_index path_count frame last_frame_tick '
 'last_state_counter drawn_frame render_world_x render_world_y animation_tail_reached pose_published '
 'occupied_cell_count owned_cells complete waypoint_x waypoint_y next_waypoint_x next_waypoint_y '
 'publication_count pending active deferred stop_mask ready capabilities requested_goal_x requested_goal_y '
 'active_target_x active_target_y request_new retry last_plan retry_interval snapshot_retry snapshot_target_x '
 'snapshot_target_y snapshot_cell_x snapshot_cell_y random_state can_request path_endpoint_x path_endpoint_y '
 'requested_reached last_cell cache_count cache_cells path_hex navigation_radius').split()

def expected_row(case,row):
 path=bytes.fromhex(row['path_hex']);hasroute=bool(path)
 endpoint=[row['last_cell']%24,row['last_cell']//24] if hasroute else [-1,-1]
 complete=hasroute and row['state']==0 and row['cell']==endpoint and row['world']==[v*64+4 for v in endpoint]
 requested_reached=row['state']==0 and row['cell']==row['active_target'] and row['world']==[v*64+4 for v in row['active_target']]
 can_request=row['state']==0 and not(row['active']&0x80) and not(row['pending']&0x88)
 values=[case['label'],row['sample_index'],row['operation'],row['counter'],*row['cell'],*row['world'],row['state'],int(row['center_gate']),
  row['heading'],row['target_heading'],row['turn_step'],row['speed'],row['remainder'],row['deceleration'],row['reserved'],row['next_cell'],
  row['path_index'],row['path_count'],row['frame'],row['last_frame_tick'],row['last_state_counter'],row['drawn_frame'],*row['render_world'],
  int(row['animation_tail_reached']),int(row['pose_published']),row['occupied_cell_count'],','.join(map(str,row['owned_cells'])),int(complete),
  *row['waypoint'],*row['next_waypoint'],len(row['publications']),row['pending'],row['active'],row['deferred'],row['stop_mask'],row['ready'],row['capabilities'],
  *row['requested_goal'],*row['active_target'],int(bool(row['request_new'])),row['retry'],row['last_plan'],row['retry_interval'],row['snapshot_retry'],
  *row['snapshot_target'],*row['snapshot_cell'],row['random_state'],int(can_request),*endpoint,int(requested_reached),row['last_cell'],row['cache_count'],
  ','.join(map(str,row['cache_cells'])),row['path_hex'],row['navigation_radius']]
 gate.require(len(values)==len(COLUMNS),'Validator column definition differs')
 return list(map(str,values))

def compare(frozen,mono_root=None):
 pe,uc,runtime,compiler=gate.prerequisites(mono_root=mono_root)
 hashes={str(p.relative_to(ROOT)):gate.digest(p)for p in [*SOURCES,PROBE]}
 gate.require(gate.digest(ship.FIXTURE)==ship.FIXTURE_SHA256,'Ship seed fixture changed')
 seed=next(r for r in json.loads(ship.FIXTURE.read_text())['records']if r['instance_id']==11)
 lines=[];expected=[];pubs=[];mutations=[]
 for case in frozen['cases']:
  lines.append('\t'.join(('START',case['label'],str(case['session_seed']))))
  for row in case['samples']:
   if row['operation']=='request':lines.append('\t'.join(map(str,('R',*row['requested_goal'],255))))
   elif row['operation']=='tick':lines.append('\t'.join(map(str,('T',row['counter'],case['pending_steps']))))
   elif row['operation']!='initial':raise ValueError('Unknown native operation')
   expected.append(expected_row(case,row))
   for i,pub in enumerate(row['publications']):pubs.append(list(map(str,(case['label'],row['sample_index'],i,pub['frame'],*pub['world'],pub['depth']))))
   for i,mutation in enumerate(row['grid_writes']):
    mutations.append(list(map(str,(case['label'],row['sample_index'],i,mutation['cell_index'],int(mutation['after']!='0x0')))))
 with tempfile.TemporaryDirectory(prefix='ship-move-order-')as temporary:
  d=Path(temporary);exe=d/'ShipMoveOrderProbe.exe';payload=d/'source.hex';payload.write_text(seed['payload_hex']+'\n')
  cp=subprocess.run(compiler+['/nologo','/checked+','/target:exe','/out:'+str(exe),*map(str,SOURCES),str(PROBE)],capture_output=True,text=True,timeout=60)
  gate.require(cp.returncode==0,'Order C# compilation failed:\n'+cp.stdout+cp.stderr)
  rp=subprocess.run([str(runtime),str(exe),str(ROOT/'tests/fixtures/mission_cell_flags.bin'),str(payload)],input='\n'.join(lines)+'\n',capture_output=True,text=True,timeout=90)
  # Keep partial successful output available to explain the first mismatch.
  Path('/tmp/ship-order-last-probe.txt').write_text(rp.stdout+rp.stderr)
  gate.require(rp.returncode==0,'Order C# execution failed:\n'+rp.stdout[-3000:]+rp.stderr)
 rows=[];actualpubs=[];actualmutations=[];guards=[];total=None
 for line in rp.stdout.splitlines():
  f=line.split('\t')
  if f[0]=='ROW':rows.append(f[1:])
  elif f[0]=='PUB':actualpubs.append(f[1:])
  elif f[0]=='GRID':actualmutations.append(f[1:])
  elif f[0]=='CHECK':guards.append(f[1])
  elif f[0]=='GUARDS':total=int(f[1])
  else:raise ValueError('Unknown probe output '+line)
 gate.require(len(rows)==len(expected),'Snapshot count differs')
 for i,(a,b)in enumerate(zip(rows,expected)):
  if a!=b:
   diff={key:{'csharp':av,'native':bv}for key,av,bv in zip(COLUMNS,a,b)if av!=bv}
   raise AssertionError(f'Order snapshot mismatch {i} {a[:4]}: {diff}')
 gate.require(actualpubs==pubs,'Ordered source frame/depth publications differ')
 gate.require(actualmutations==mutations,'Ordered owner grid writes differ')
 gate.require(total==len(guards)==len(set(guards)),'Guard count differs')
 gate.require(all(gate.digest(ROOT/p)==h for p,h in hashes.items()),'Source C# changed during comparison')
 return {'passed':True,'case_count':len(frozen['cases']),'snapshot_count':len(rows),'publication_count':len(pubs),'grid_mutation_count':len(mutations),
  'guard_count':len(guards),'guards':guards,'checked_compilation':True,'source_sha256':hashes,'compiler_command':compiler,'mono_runtime':str(runtime)}

def load_fixture(path=FIXTURE):
 raw=Path(path).read_bytes()
 gate.require(hashlib.sha256(raw).hexdigest()==FIXTURE_SHA256,'Original whole-order fixture changed')
 frozen=json.loads(raw)
 gate.require(frozen['original_exe_sha256']==gate.EXPECTED,'Original executable differs')
 return frozen

def validate(mono_root=None,fixture=FIXTURE):
 frozen=load_fixture(fixture)
 # Check prerequisites before importing the native engine module.
 gate.prerequisites(mono_root=mono_root)
 if __package__:
  from . import probe_ship_move_order as native
 else:
  import probe_ship_move_order as native
 actual=native.validate()
 gate.require(actual==frozen,'Fresh original order-chain execution differs from the pinned native fixture')
 result=compare(frozen,mono_root)
 result.update(kind='Actual original normal cell-MOVE request/promotion/work/replanning/movement/idle chain vs checked C#',
  fixture_sha256=FIXTURE_SHA256,original_exe_sha256=gate.EXPECTED,
  native_oracle_sha256=gate.digest(Path(native.__file__)),validator_sha256=gate.digest(Path(__file__)),
  native_tick_calls=sum(c['ticks']for c in frozen['cases']),
  operation_counts={name:sum(r['operation']==name for c in frozen['cases']for r in c['samples'])for name in ('initial','request','tick')},
  maximum_publications_per_operation=max(len(r['publications'])for c in frozen['cases']for r in c['samples']),
  cases=[{'label':c['label'],'goals':c['goals'],'session_seed':c['session_seed'],'pending_steps':c['pending_steps'],
   'ticks':c['ticks'],'sample_count':len(c['samples']),'finished':c['finished'],
   'final':{k:c['samples'][-1][k]for k in ('counter','cell','world','state','active','pending','requested_goal','active_target','path_endpoint','retry','request_new','random_state','cache_cells')}}for c in frozen['cases']],
  reference_conditions={'ship_id':11,'origin':[16,2],'initial_heading':5,'health_percent':100,
   'wind_force':0,'wind_heading':5,'owner_upgrade':0,'static_fleet_count':8,
   'initial_counter':0,'schedule':'request between ticks; promotion then normal work/planning and movement at the same tick counter',
   'session_seeds':[0,4294967295],'pending_steps':[1,3]},
  limits=frozen['limits']+[
   'The reachable cases stop at the first idle pose publication after physical state0 and move-active clearance',
   'Nearest and blocked commands are bounded180-tick observations, not requested-target arrival or full retry exhaustion',
   'Busy replacement, full actor Life/application cadence, AI, damage/combat/equipment and hardware performance are excluded',
   'Heap, setjmp, init-service, visibility/system notification and render-publication boundaries remain explicit',
   'The core does not use a guessed Unity navigation or interpolation system'])
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixture',type=Path,default=FIXTURE);p.add_argument('--output',type=Path,default=ROOT/'artifacts/order-cycle/lifecycle/csharp-validation.json');a=p.parse_args()
 result=validate(fixture=a.fixture);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in('source_sha256','guards','compiler_command')},indent=2))
if __name__=='__main__':main()
