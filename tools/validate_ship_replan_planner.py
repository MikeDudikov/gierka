#!/usr/bin/env python3
"""Current-origin normal ship planning vs complete native map/nearest bodies."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile

if __package__:
    from . import probe_ship_replan_planner as native, validate_boss_ai_gate as gate
else:
    import probe_ship_replan_planner as native
    import validate_boss_ai_gate as gate

ROOT=gate.ROOT
MissingPrerequisite=gate.MissingPrerequisite
RUNTIME=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime'
SOURCES=[RUNTIME/p for p in ('MissionOccupancyGrid.cs','Simulation/SourcePathfinder.cs',
         'Simulation/SourceWaveField.cs','Simulation/SourceNearestPathfinder.cs','Simulation/ShipReplanPlanner.cs')]
PROBE=ROOT/'tests/fixtures/ShipReplanPlannerProbe.cs'
FIXTURE=ROOT/'tests/fixtures/ship_replan_planner.json'
FIXTURE_SHA256='0d28739a3703678201572bf8c5373446cb1118540565cc20dcd3d8fac5e4dc64'
OUTPUT=ROOT/'artifacts/order-lifecycle/planning/csharp-validation.json'


def load_fixture(path=FIXTURE):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA256:raise ValueError('Ship replan planner fixture SHA-256 differs')
    return json.loads(raw)


def expected(case):
    raw=bytes.fromhex(case['path_hex']);points=[struct.unpack_from('<hhB',raw,i)for i in range(0,len(raw),5)]
    install=len(points)>=2 and not(len(points)==2 and points[0][:2]==points[1][:2])
    heading=-1
    if install:
        dx=points[1][0]-points[0][0];dy=points[1][1]-points[0][1]
        heading={(1,0):0,(1,-1):1,(0,-1):2,(-1,-1):3,(-1,0):4,(-1,1):5,(0,1):6,(1,1):7}[dx,dy]
    return list(map(str,[case['label'],case['point_count'],int(case['used_nearest']),int(case['reached_within_range']),
          int(install),heading,*(points[-1][:2]if points else(-1,-1)),
          case['radius']+int(case['used_nearest']and not case['reached_within_range']),
          case['random_state_after'],int(case['retry_priority']>50),','.join(map(str,case['cached_obstacles_after'])),
          case['path_hex'],case['input_map_hex'],case['working_map_hex']]))


def validate(mono_root=None):
    frozen=load_fixture();_,unicorn,runtime,compiler=gate.prerequisites(mono_root=mono_root)
    fresh=native.validate();gate.require(fresh==frozen,'Fresh original replan execution differs from fixture')
    flags=ROOT/'tests/fixtures/mission_cell_flags.bin'
    gate.require(gate.digest(flags)=='eb8c22b2dc3a3d6de5be5c5a28560701333cbc8610e8dd687052f4f93b260283','Source flags differ')
    before={str(p.relative_to(ROOT)):gate.digest(p)for p in [*SOURCES,PROBE]}
    lines=[]
    for c in frozen['cases']:
        lines.append('\t'.join(map(str,[c['label'],*c['cell'],*c['origin'],*c['goal'],c['radius'],c['retry_priority'],
             int(c['preserve_destination_mask']),c['random_state'],','.join(map(str,c['cached_obstacles'])),
             *(c['reservation']or[-1,-1])])) )
    with tempfile.TemporaryDirectory(prefix='ship-replan-')as temporary:
        exe=Path(temporary)/'ShipReplanPlannerProbe.exe'
        compiled=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/target:exe','/out:'+str(exe),*map(str,SOURCES),str(PROBE)],capture_output=True,text=True,timeout=60)
        gate.require(compiled.returncode==0,'Replan C# compile failed:\n'+compiled.stdout+compiled.stderr)
        result=subprocess.run([str(runtime),str(exe),str(flags)],input='\n'.join(lines)+'\n',capture_output=True,text=True,timeout=90)
        gate.require(result.returncode==0,'Replan C# probe failed:\n'+result.stdout+result.stderr)
    rows=[];guards=[]
    for line in result.stdout.splitlines():
        f=line.split('\t')
        if f[0]=='ROW':rows.append(f[1:])
        elif f[0]=='GUARD':guards.append(f[1])
        else:raise ValueError('Unknown replan probe output: '+line)
    gate.require(len(rows)==len(frozen['cases']),'Replan C# row count differs')
    for row,c in zip(rows,frozen['cases']):
        wanted=expected(c)
        gate.require(row==wanted,'Replan differs '+c['label']+': C# '+str(row[:13])+' / native '+str(wanted[:13]))
    gate.require(before=={str(p.relative_to(ROOT)):gate.digest(p)for p in [*SOURCES,PROBE]},'Replan source changed during comparison')
    return {'passed':len(rows),'case_count':len(rows),'guard_count':len(guards),'guards':guards,
            'fixture_sha256':FIXTURE_SHA256,'source_sha256':before,'validator_sha256':gate.digest(Path(__file__)),
            'native_oracle_sha256':gate.digest(Path(native.__file__)),'checked_compilation':True,
            'warnings_as_errors':True,'unicorn_version':unicorn.__version__,'original':frozen,
            'scope':'Raw normal source0b current-origin path/map/RNG/cache branch; ProcPostMove transaction and full order scheduling are separate'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=OUTPUT);args=parser.parse_args()
    if args.output.exists():parser.error('Select a fresh output path')
    try:report=validate()
    except MissingPrerequisite as error:parser.exit(2,str(error)+'\n')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(str(report['passed'])+' current-origin ship planner cases PASS')

if __name__=='__main__':main()
