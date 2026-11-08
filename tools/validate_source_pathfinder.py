#!/usr/bin/env python3
"""Compare original55c9a0 direct/wave routes and full working maps with actual C#."""
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
else:
    import validate_boss_ai_gate as gate
    import validate_mission_object_selection as source

ROOT=gate.ROOT
MissingPrerequisite=gate.MissingPrerequisite
RUNTIME=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation'
SOURCES=[RUNTIME/'SourcePathfinder.cs',RUNTIME/'SourceWaveField.cs']
PROBE=ROOT/'tests/fixtures/SourcePathfinderProbe.cs'
FIXTURE=ROOT/'tests/fixtures/source_pathfinder.json'
FIXTURE_SHA256='1cca921bcb53f2398d708c3f117ea0370369d32d6a8dc2ad57f4b9ea5998a4d2'
OUTPUT=ROOT/'artifacts/long-routes/navigation/pathfinder-csharp-validation.json'


def case_inputs():
    cases=[]
    def add(label,w,h,start,goal,field,pref=0):
        cases.append({'label':label,'width':w,'height':h,'origin':list(start),'goal':list(goal),
                      'preferred_heading':pref,'field':list(field)})
    for w,h in ((1,1),(2,3),(3,2),(5,5),(8,7),(12,12)):
        for pref in (-1,0,1,2,3,4,5,6,7):
            add(f'open_{w}_{h}_{pref}',w,h,(0,0),(w-1,h-1),[0]*(w*h),pref)
            add(f'open_reverse_{w}_{h}_{pref}',w,h,(w-1,h-1),(0,0),[0]*(w*h),pref)
    rng=random.Random(0x55c9a0)
    for n in range(250):
        w,h=rng.randrange(3,25),rng.randrange(3,25)
        start=(rng.randrange(w),rng.randrange(h));goal=(rng.randrange(w),rng.randrange(h))
        field=[-1 if rng.random()<(.12+.1*(n%4)) else 0 for _ in range(w*h)]
        field[start[1]*w+start[0]]=field[goal[1]*w+goal[0]]=0
        add('random_'+str(n),w,h,start,goal,field,rng.randrange(-1,8))
    flags_raw=(ROOT/'tests/fixtures/mission_cell_flags.bin').read_bytes()
    gate.require(hashlib.sha256(flags_raw).hexdigest()=='eb8c22b2dc3a3d6de5be5c5a28560701333cbc8610e8dd687052f4f93b260283','Source mission flags differ')
    flags=struct.unpack('<576I',flags_raw)
    field=[0 if value&15<8 and (value>>4&15) not in (4,5,6) else -1 for value in flags]
    field[4*24+19]=-1
    for x,y in ((14,4),(16,4),(17,4),(18,3),(18,4),(18,5),(19,3),(20,3),(20,4),(20,6),(19,4),(16,1),(0,0),(23,23)):
        current=list(field);current[y*24+x]=0 if flags[y*24+x]&15<8 and (flags[y*24+x]>>4&15) not in (4,5,6) else -1
        add('mission_'+str(x)+'_'+str(y),24,24,(16,2),(x,y),current)
    add('blocked_start',3,3,(0,0),(2,2),[-1]+[0]*8)
    add('blocked_goal',3,3,(0,0),(2,2),[0]*8+[-1])
    return cases


def native_cases(inputs=None):
    import pefile
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EIP,UC_X86_REG_ESP
    raw=source.checked_sources(source.SOURCE_ROOT)['installed/ancient.exe']
    pe=pefile.PE(data=raw);image=pe.get_memory_mapped_image();size=pe.OPTIONAL_HEADER.SizeOfImage
    cases=[]
    for case in inputs or case_inputs():
        uc=source.new_engine(image,size);allocations={};next_heap=[source.CONTEXT+0x30000]
        put=lambda a,v:source.put(uc,a,v)
        get=lambda a:source.get(uc,a)
        services=[];algorithms=[]
        def ret(clean=0,value=0):
            sp=uc.reg_read(UC_X86_REG_ESP);uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+clean);uc.reg_write(UC_X86_REG_EAX,value)
        def alloc(length):
            pointer=next_heap[0];next_heap[0]+=(max(length,16)+15)&~15
            gate.require(next_heap[0]<source.CONTEXT+0xef000,'Native generic route heap exhausted')
            allocations[pointer]=length;return pointer
        def hook(engine,address,size,unused):
            if address in (0x571880,0x5578a0):algorithms.append(hex(address))
            if address in (0x557700,0x571200):
                sp=uc.reg_read(UC_X86_REG_ESP);length=get(sp+4);pointer=alloc(length)
                services.append({'entry':hex(address),'service':'allocation','bytes':length})
                ret(4,pointer)
            elif address==0x5711e0:
                sp=uc.reg_read(UC_X86_REG_ESP);old=get(sp+4);length=get(sp+8);pointer=alloc(length)
                if old:uc.mem_write(pointer,bytes(uc.mem_read(old,min(length,allocations[old]))))
                services.append({'entry':hex(address),'service':'reallocation','bytes':length})
                ret(8,pointer)
            elif address==0x5576e0:
                sp=uc.reg_read(UC_X86_REG_ESP);pointer=get(sp+4)
                put(pointer,0);services.append({'entry':hex(address),'service':'deallocation'});ret(4)
            elif address in (0x5565f0,0x556610,0x556880):
                raise AssertionError('Native pathfinder source error '+hex(address))
        uc.hook_add(UC_HOOK_CODE,hook)
        field_address=source.CONTEXT+0x1000;count_address=source.CONTEXT+0x2000
        field=case['field'];uc.mem_write(field_address,struct.pack('<'+str(len(field))+'h',*field));put(count_address,0)
        sp=source.STACK+source.STACK_SIZE-0x1000
        args=(source.END,field_address,case['width'],case['height'],*case['origin'],*case['goal'],case['preferred_heading'],count_address)
        for i,value in enumerate(args):put(sp+i*4,value)
        uc.reg_write(UC_X86_REG_ESP,sp);uc.emu_start(0x55c9a0,source.END,count=5000000)
        gate.require(uc.reg_read(UC_X86_REG_EIP)==source.END,'Native pathfinder did not return '+case['label'])
        pointer=uc.reg_read(UC_X86_REG_EAX);count=get(count_address)
        gate.require(count<=len(field)+2,'Native route exceeds map allocation bound')
        path=bytes(uc.mem_read(pointer,count*5)) if pointer else b''
        gate.require(bool(pointer)==bool(count),'Native null/count mismatch')
        working=bytes(uc.mem_read(field_address,len(field)*2))
        cases.append(dict(case,path_hex=path.hex(),point_count=count,working_field_hex=working.hex(),used_wave='0x5578a0'in algorithms,
                          algorithms=algorithms,services=services))
    return {'schema_version':1,'original_exe_sha256':gate.EXPECTED,'native_entry':'0x55c9a0',
            'algorithm_hooks':[],'service_boundary_entries':['0x557700','0x571200','0x5711e0','0x5576e0'],
            'cases':cases}


def load_fixture(path=FIXTURE):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA256:
        raise ValueError('Source pathfinder fixture SHA-256 differs')
    return json.loads(raw)


def validate(mono_root=None):
    _,unicorn,runtime,compiler=gate.prerequisites(mono_root=mono_root)
    frozen=load_fixture()
    native=native_cases();gate.require(native==frozen,'Fresh original pathfinder differs from pinned fixture')
    before={str(p.relative_to(ROOT)):gate.digest(p) for p in [*SOURCES,PROBE]}
    lines=[]
    for c in frozen['cases']:
        field=struct.pack('<'+str(len(c['field']))+'h',*c['field']).hex()
        lines.append('\t'.join(map(str,(c['label'],c['width'],c['height'],*c['origin'],*c['goal'],c['preferred_heading'],field))))
    with tempfile.TemporaryDirectory(prefix='source-pathfinder-')as temporary:
        exe=Path(temporary)/'SourcePathfinderProbe.exe'
        build=subprocess.run(compiler+['/nologo','/checked+','/target:exe','/out:'+str(exe),*map(str,SOURCES),str(PROBE)],capture_output=True,text=True,timeout=60)
        gate.require(build.returncode==0,'Pathfinder C# compilation failed:\n'+build.stdout+build.stderr)
        result=subprocess.run([str(runtime),str(exe)],input='\n'.join(lines)+'\n',capture_output=True,text=True,timeout=60)
        gate.require(result.returncode==0,'Pathfinder C# probe failed:\n'+result.stdout+result.stderr)
    rows=[];guards=[]
    for line in result.stdout.splitlines():
        f=line.split('\t')
        if f[0]=='ROW':rows.append(f[1:])
        elif f[0]=='GUARD':guards.append(f[1])
        else:raise ValueError('Unknown source pathfinder probe output: '+line)
    gate.require(len(rows)==len(frozen['cases']),'C# pathfinder row count differs')
    for actual,c in zip(rows,frozen['cases']):
        wanted=[c['label'],str(c['point_count']),str(int(c['used_wave'])),c['path_hex'],c['working_field_hex']]
        gate.require(actual==wanted,'Source pathfinder differs '+c['label']+': C# '+str(actual[:4])+' / native '+str(wanted[:4]))
    gate.require(before=={str(p.relative_to(ROOT)):gate.digest(p) for p in [*SOURCES,PROBE]},'Pathfinder source changed during validation')
    return {'passed':len(rows),'case_count':len(rows),'direct_cases':sum(not c['used_wave'] for c in frozen['cases']),
            'wave_cases':sum(c['used_wave'] for c in frozen['cases']),'guard_count':len(guards),'guards':guards,
            'fixture_sha256':FIXTURE_SHA256,'original_exe_sha256':gate.EXPECTED,'source_sha256':before,
            'validator_sha256':gate.digest(Path(__file__)),'checked_compilation':True,'unicorn_version':unicorn.__version__,
            'native_evidence':native,'scope':'Original55c9a0 paths plus every working-field cell; input0/free,-1/blocked, bounded maps; no ship order policy'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=OUTPUT);args=parser.parse_args()
    if args.output.exists():parser.error('Select a fresh output path')
    try:report=validate()
    except MissingPrerequisite as error:parser.exit(2,str(error)+'\n')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(str(report['passed'])+' source pathfinder cases PASS')

if __name__=='__main__':main()
