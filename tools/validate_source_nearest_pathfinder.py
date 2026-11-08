#!/usr/bin/env python3
"""Actual original55b9e0 paths/reached bits/full fields versus managed C#."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import tempfile

if __package__:
    from . import validate_boss_ai_gate as gate, validate_mission_object_selection as source
    from .validate_source_wave_field import NativeWave
else:
    import validate_boss_ai_gate as gate
    import validate_mission_object_selection as source
    from validate_source_wave_field import NativeWave

ROOT=gate.ROOT
MissingPrerequisite=gate.MissingPrerequisite
RUNTIME=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation'
SOURCES=[RUNTIME/'SourceNearestPathfinder.cs',RUNTIME/'SourceWaveField.cs']
PROBE=ROOT/'tests/fixtures/SourceNearestPathfinderProbe.cs'
FIXTURE=ROOT/'tests/fixtures/source_nearest_pathfinder.json'
FIXTURE_SHA256='d79d1c319a22176c209839ff7320fc5b83cb70d21b373459eaa1ed9fe2eb8f9a'
OUTPUT=ROOT/'artifacts/order-lifecycle/nearest/nearest-csharp-validation.json'


def case_inputs():
    cases=[]
    def add(label,w,h,origin,target,field,range=0,pref=0):
        cases.append({'label':label,'width':w,'height':h,'origin':list(origin),'target':list(target),
                      'range':range,'preferred_heading':pref,'field':list(field)})
    for w,h in ((1,1),(2,3),(3,2),(5,5),(8,7),(12,12)):
        for pref in (-1,0,1,2,3,4,5,6,7):
            for radius in (0,1,2,3):
                add(f'open_{w}_{h}_{pref}_{radius}',w,h,(0,0),(w-1,h-1),[0]*(w*h),radius,pref)
                add(f'open_reverse_{w}_{h}_{pref}_{radius}',w,h,(w-1,h-1),(0,0),[0]*(w*h),radius,pref)
    # All tiny obstacle arrangements, preserving blocked origins and targets.
    for mask in range(512):
        field=[-1 if mask>>index&1 else 0 for index in range(9)]
        add('tiny_'+str(mask),3,3,(0,0),(2,2),field,mask%3,mask%9-1)
    rng=random.Random(0x55b9e0)
    for index in range(400):
        w,h=rng.randrange(3,25),rng.randrange(3,25)
        origin=(rng.randrange(w),rng.randrange(h));target=(rng.randrange(w),rng.randrange(h))
        field=[-1 if rng.random()<(.12+.1*(index%4)) else 0 for _ in range(w*h)]
        if index%5:field[origin[1]*w+origin[0]]=0
        if index%2:field[target[1]*w+target[0]]=-1
        add('random_'+str(index),w,h,origin,target,field,rng.randrange(0,5),rng.randrange(-1,8))
    raw=(ROOT/'tests/fixtures/mission_cell_flags.bin').read_bytes()
    gate.require(hashlib.sha256(raw).hexdigest()=='eb8c22b2dc3a3d6de5be5c5a28560701333cbc8610e8dd687052f4f93b260283','Source mission flags differ')
    flags=struct.unpack('<576I',raw)
    field=[0 if v&15<8 and(v>>4&15)not in(4,5,6) else -1 for v in flags]
    field[4*24+19]=-1
    for target in ((18,2),(16,5),(16,1),(15,1),(18,4),(18,5),(20,4),(0,0),(23,23),(16,2)):
        for radius in (0,1,2):add('mission_'+str(target)+'_'+str(radius),24,24,(16,2),target,field,radius)
    # Explicit distance discrepancy:557410(2,2)=2 while5573d0(2,2)=3.
    for radius in (1,2,3):
        add('metric_2_2_open_'+str(radius),5,5,(0,0),(2,2),[0]*25,radius)
        field=[0]*25;field[6]=-1
        add('metric_2_2_wave_'+str(radius),5,5,(0,0),(2,2),field,radius)
    return cases


def native_cases(inputs=None):
    engine=NativeWave();uc=engine.uc;results=[]
    from unicorn import UC_HOOK_CODE
    observed_iterations=[0]
    def observe_wave_return(guest,address,size,unused):
        observed_iterations[0]=guest.reg_read(engine.EAX)
    uc.hook_add(UC_HOOK_CODE,observe_wave_return,begin=0x55bc13,end=0x55bc13)
    for case in inputs or case_inputs():
        engine.services=[];engine.allocations={};engine.next_heap=engine.heap;engine.wave_entries=0;engine.insertions=0;observed_iterations[0]=0
        field_address=engine.map_address;count_address=source.CONTEXT+0x70000;reached_address=count_address+4
        field=case['field'];uc.mem_write(field_address,b'\0'*0x20000)
        uc.mem_write(field_address,struct.pack('<'+str(len(field))+'h',*field));engine.put(count_address,0);engine.put(reached_address,0)
        pointer=engine.invoke(0x55b9e0,[field_address,case['width'],case['height'],*case['origin'],*case['target'],
                                     case['preferred_heading'],case['range'],reached_address,count_address])
        count=engine.get(count_address);reached=engine.get(reached_address)
        gate.require(count<=len(field)+2,'Native partial route exceeds map bound:'+case['label'])
        path=bytes(uc.mem_read(pointer,count*5)) if pointer else b''
        gate.require(bool(pointer)==bool(count),'Native partial null/count mismatch')
        working=bytes(uc.mem_read(field_address,len(field)*2))
        results.append(dict(case,path_hex=path.hex(),point_count=count,reached=reached,
                            working_field_hex=working.hex(),used_wave=engine.wave_entries!=0,wave_iterations=observed_iterations[0],
                            frontier_insertions=engine.insertions,services=list(engine.services)))
    return {'schema_version':1,'original_exe_sha256':gate.EXPECTED,'native_entry':'0x55b9e0',
            'algorithm_hooks':[],'service_boundary_entries':['0x557700','0x571200','0x5711e0','0x5576e0'],
            'cases':results}


def load_fixture(path=FIXTURE):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA256:raise ValueError('Source nearest pathfinder fixture SHA-256 differs')
    return json.loads(raw)


def validate(mono_root=None):
    frozen=load_fixture()
    source.checked_sources(source.SOURCE_ROOT)
    _,unicorn,runtime,compiler=gate.prerequisites(mono_root=mono_root)
    native=native_cases();gate.require(native==frozen,'Fresh original nearest pathfinder differs from pinned fixture')
    before={str(p.relative_to(ROOT)):gate.digest(p) for p in [*SOURCES,PROBE]}
    lines=[]
    for c in frozen['cases']:
        field=struct.pack('<'+str(len(c['field']))+'h',*c['field']).hex()
        lines.append('\t'.join(map(str,(c['label'],c['width'],c['height'],*c['origin'],*c['target'],c['range'],c['preferred_heading'],field))))
    with tempfile.TemporaryDirectory(prefix='source-nearest-')as temporary:
        exe=Path(temporary)/'SourceNearestPathfinderProbe.exe'
        build=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/target:exe','/out:'+str(exe),*map(str,SOURCES),str(PROBE)],capture_output=True,text=True,timeout=60)
        gate.require(build.returncode==0,'Nearest pathfinder C# compilation failed:\n'+build.stdout+build.stderr)
        result=subprocess.run([str(runtime),str(exe)],input='\n'.join(lines)+'\n',capture_output=True,text=True,timeout=60)
        gate.require(result.returncode==0,'Nearest pathfinder C# probe failed:\n'+result.stdout+result.stderr)
    rows=[];guards=[]
    for line in result.stdout.splitlines():
        f=line.split('\t')
        if f[0]=='ROW':rows.append(f[1:])
        elif f[0]=='GUARD':guards.append(f[1])
        else:raise ValueError('Unknown nearest pathfinder probe output:'+line)
    gate.require(len(rows)==len(frozen['cases']),'C# nearest row count differs')
    for actual,c in zip(rows,frozen['cases']):
        wanted=[c['label'],str(c['point_count']),str(c['reached']),str(int(c['used_wave'])),str(c['wave_iterations']),c['path_hex'],c['working_field_hex']]
        gate.require(actual==wanted,'Source nearest pathfinder differs '+c['label']+': C#'+str(actual[:5])+' / native'+str(wanted[:5]))
    gate.require(len(guards)==9 and len(set(guards))==9,'Nearest API checks missing/duplicated')
    gate.require(before=={str(p.relative_to(ROOT)):gate.digest(p) for p in [*SOURCES,PROBE]},'Nearest source changed during validation')
    return {'passed':len(rows),'case_count':len(rows),'direct_cases':sum(not c['used_wave'] for c in frozen['cases']),
            'wave_cases':sum(c['used_wave'] for c in frozen['cases']),'guard_count':len(guards),'guards':guards,
            'fixture_sha256':FIXTURE_SHA256,'original_exe_sha256':gate.EXPECTED,'source_sha256':before,
            'validator_sha256':gate.digest(Path(__file__)),'checked_compilation':True,'warnings_as_errors':True,
            'unicorn_version':unicorn.__version__,'native_evidence':native,
            'scope':'Original55b9e0 raw partial paths/reached bit and every working-field cell; no ship order policy/Life'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=OUTPUT);args=p.parse_args()
    if args.output.exists():p.error('Select a fresh output path')
    try:report=validate()
    except MissingPrerequisite as error:p.exit(2,str(error)+'\n')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(str(report['passed'])+' source nearest cases PASS')

if __name__=='__main__':main()
