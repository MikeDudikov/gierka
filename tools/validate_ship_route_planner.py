#!/usr/bin/env python3
"""Initial source0b GetWayNew map and routes for all576 goals vs actual C#."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

if __package__:
    from . import probe_ship_route_navigation as native, validate_boss_ai_gate as gate
    from . import validate_mission_ship_seed as ship
else:
    import probe_ship_route_navigation as native
    import validate_boss_ai_gate as gate
    import validate_mission_ship_seed as ship

ROOT=gate.ROOT
MissingPrerequisite=gate.MissingPrerequisite
RUNTIME=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime'
SOURCES=[RUNTIME/p for p in ('MissionObjectSeed.cs','MissionShipSeed.cs','MissionOccupancyGrid.cs',
         'Simulation/ShipAdjacentQuery.cs','Simulation/ShipRoutePlan.cs','Simulation/ShipRoutePlanner.cs',
         'Simulation/SourcePathfinder.cs','Simulation/SourceWaveField.cs')]
PROBE=ROOT/'tests/fixtures/ShipRoutePlannerProbe.cs'
FIXTURE=ROOT/'tests/fixtures/ship_route_planner.json'
FIXTURE_SHA256='b291068ee191a53826436ca8fe8e92c88c2a7e76fc7cd779f2c59b737564caa7'
OUTPUT=ROOT/'artifacts/long-routes/navigation/ship-route-planner-csharp-validation.json'


def compact(report):
    cases=[]
    for c in report['cases']:
        n=c['navigation'];calls=n['pathfinder_calls'];points=n['points']
        cases.append({'goal':c['target'],'goal_flags':c['target_flags'],'planned':bool(points),
                      'return_low_byte':n['return_low_byte'],'points':points,'path_hex':n['path_hex'],
                      'path_index':n['path_index'],'state':n['state'],'center_gate':n['center_gate'],
                      'target_heading':points[1][2] if points else 0,
                      'input_map_hex':calls[0]['input_map_hex'] if calls else None})
    return {'schema_version':1,'original_source_hashes':report['source_hashes'],
            'source_cell_flags_sha256':report['source_cell_flags_sha256'],
            'source0b_payload_sha256':'fbcbf7c873f418fffdd9761954cea7b3844c2567b08baa85b0f3489faa51bbdb',
            'origin':[16,2],'initial_heading':5,'restriction':0,'priority':0,
            'static_reference_actor_metadata':'Other seven minimal occupancy records: source runtime tag, source cell andID; all remaining fields zero. Source0b ctor/load/base execute.',
            'cases':cases}


def load_fixture(path=FIXTURE):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA256:
        raise ValueError('Ship route planner fixture SHA-256 differs')
    return json.loads(raw)


def validate(mono_root=None):
    _,unicorn,runtime,compiler=gate.prerequisites(mono_root=mono_root)
    fixture=load_fixture();actual=native.validate(goals=[(x,y) for y in range(24) for x in range(24)])
    gate.require(compact(actual)==fixture,'Fresh original ship plans differ from pinned fixture')
    flags=ROOT/'tests/fixtures/mission_cell_flags.bin';gate.require(gate.digest(flags)==fixture['source_cell_flags_sha256'],'Source flags differ')
    gate.require(gate.digest(ship.FIXTURE)==ship.FIXTURE_SHA256,'Source ship seed fixture differs')
    seed=next(row for row in json.loads(ship.FIXTURE.read_text())['records'] if row['instance_id']==11)
    gate.require(seed['payload_sha256']==fixture['source0b_payload_sha256'],'Source0b payload differs')
    before={str(p.relative_to(ROOT)):gate.digest(p) for p in [*SOURCES,PROBE]}
    with tempfile.TemporaryDirectory(prefix='ship-route-planner-')as temporary:
        exe=Path(temporary)/'ShipRoutePlannerProbe.exe';payload=Path(temporary)/'source0b.hex';payload.write_text(seed['payload_hex'])
        compiled=subprocess.run(compiler+['/nologo','/checked+','/target:exe','/out:'+str(exe),*map(str,SOURCES),str(PROBE)],capture_output=True,text=True,timeout=60)
        gate.require(compiled.returncode==0,'Route planner C# compile failed:\n'+compiled.stdout+compiled.stderr)
        result=subprocess.run([str(runtime),str(exe),str(flags),str(payload)],capture_output=True,text=True,timeout=60)
        gate.require(result.returncode==0,'Route planner C# probe failed:\n'+result.stdout+result.stderr)
    rows=[];guards=[]
    for line in result.stdout.splitlines():
        f=line.split('\t')
        if f[0]=='ROW':rows.append(f[1:])
        elif f[0]=='GUARD':guards.append(f[1])
        else:raise ValueError('Unknown ship route planner output: '+line)
    gate.require(len(rows)==len(fixture['cases']),'Ship planner case count differs')
    for c,row in zip(fixture['cases'],rows):
        wanted=[*c['goal'],int(c['planned']),len(c['points']),c['path_index'],c['state'],c['center_gate'],c['target_heading'],c['path_hex']]
        gate.require(row[:9]==list(map(str,wanted)),'Ship route differs '+str(c['goal'])+': C# '+str(row[:9])+' / native '+str(wanted))
        if c['input_map_hex'] is not None:gate.require(row[9]==c['input_map_hex'],'Ship planning map differs '+str(c['goal']))
    gate.require(before=={str(p.relative_to(ROOT)):gate.digest(p) for p in [*SOURCES,PROBE]},'Source changed during ship route planner validation')
    return {'passed':len(rows),'case_count':len(rows),'planned':sum(c['planned'] for c in fixture['cases']),
            'no_route':sum(not c['planned'] for c in fixture['cases']),'guard_count':len(guards),'guards':guards,
            'fixture_sha256':FIXTURE_SHA256,'original_source_hashes':fixture['original_source_hashes'],
            'source_sha256':before,'validator_sha256':gate.digest(Path(__file__)),'native_oracle_sha256':gate.digest(Path(native.__file__)),
            'checked_compilation':True,'unicorn_version':unicorn.__version__,'cases':fixture['cases'],
            'scope':'All576 goals from initial source0b/staticfleet8,mode0/restriction0/priority0. Actual native ProcPostMove/GetWayNew plus line/wave routes; not full work/Life or dynamic obstacle policy.',
            'limitations':['Other seven actors are reference minimal records; their full constructors and AI do not run',
                           'Distant occupied destination restores base map and may plan; motion/arrival is separate',
                           'GetWayNew higher priority/RNG/local alternatives, shore mode and arbitrary ship state are not projected',
                           'ProcPostMove lowbyte0 is not a success bool; installed points define the result']}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=OUTPUT);args=parser.parse_args()
    if args.output.exists():parser.error('Select a fresh output path')
    try:report=validate()
    except MissingPrerequisite as error:parser.exit(2,str(error)+'\n')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(str(report['passed'])+' native/C# ship route planner cases PASS')

if __name__=='__main__':main()
