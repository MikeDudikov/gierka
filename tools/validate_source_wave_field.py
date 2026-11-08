#!/usr/bin/env python3
"""Compare SourceWaveField against complete original5578a0 field writes.

Only allocation/reallocation/free services are intercepted. Both the wave
body and its stable frontier insertion routine execute as original x86.
The projected signature is exactly the full-map0/-1 branch used by55c9a0.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile

if __package__:
    from . import validate_mission_object_selection as source
else:
    import validate_mission_object_selection as source

gate=source.gate
ROOT=source.ROOT
SOURCE=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/SourceWaveField.cs'
PROBE=ROOT/'tests/fixtures/SourceWaveFieldProbe.cs'
FIXTURE=ROOT/'tests/fixtures/source_wave_field.json'
NATIVE_MAP=ROOT/'tests/fixtures/source_wave_native_map.bin'
NATIVE_MAP_SHA256='9fd5e1c1e5495186ec2872f85bcbd22a41ae476a8fa83aec8c36c0dbba5ae06b'
FIXTURE_SHA256='f08d21859e99b7637b6c9913ccc058276bd05731a59711dc1057a15551b842fe'
OUTPUT=ROOT/'artifacts/navigation/long-route-wave/csharp-validation.json'
MissingPrerequisite=source.MissingPrerequisite


class NativeWave:
    """Bounded raw x86 harness; original wave/insertion bodies are not replaced."""
    def __init__(self,source_root=source.SOURCE_ROOT):
        try:
            import pefile
            from unicorn import UC_HOOK_CODE
            from unicorn.x86_const import UC_X86_REG_EIP,UC_X86_REG_ESP,UC_X86_REG_EAX
        except ModuleNotFoundError as error:
            raise MissingPrerequisite('Install tools/requirements-analysis.txt for native wave validation') from error
        self.EIP,self.ESP,self.EAX=UC_X86_REG_EIP,UC_X86_REG_ESP,UC_X86_REG_EAX
        self.sources=source.checked_sources(source_root)
        pe=pefile.PE(data=self.sources['installed/ancient.exe'])
        self.uc=source.new_engine(pe.get_memory_mapped_image(),pe.OPTIONAL_HEADER.SizeOfImage)
        self.map_address=source.CONTEXT+0x10000
        self.heap=0x71000000
        self.uc.mem_map(self.heap,0x1000000)
        self.services=[];self.allocations={};self.next_heap=self.heap
        self.wave_entries=0;self.insertions=0;self.realloc_mode='move'
        for address in (0x571200,0x5711e0,0x5576e0,0x557700,0x5578a0,0x571700):
            self.uc.hook_add(UC_HOOK_CODE,self._hook,begin=address,end=address)
    def get(self,address):return source.get(self.uc,address)
    def put(self,address,value):source.put(self.uc,address,value)
    def _return(self,cleanup,result=0):
        sp=self.uc.reg_read(self.ESP)
        self.uc.reg_write(self.EIP,self.get(sp));self.uc.reg_write(self.ESP,sp+4+cleanup)
        self.uc.reg_write(self.EAX,result &0xffffffff)
    def _allocate(self,length):
        result=self.next_heap;self.next_heap+=(length+15)&~15
        gate.require(self.next_heap<self.heap+0x1000000,'Native wave bounded allocation exhausted')
        self.allocations[result]=length;self.uc.mem_write(result,b'\0'*length)
        return result
    def _hook(self,engine,address,size,unused):
        if address==0x5578a0:self.wave_entries+=1;return
        if address==0x571700:self.insertions+=1;return
        sp=self.uc.reg_read(self.ESP)
        if address in (0x571200,0x557700):
            length=self.get(sp+4);pointer=self._allocate(length)
            self.services.append({'entry':hex(address),'kind':'allocation','bytes':length})
            self._return(4,pointer)
        elif address==0x5711e0:
            old,length=self.get(sp+4),self.get(sp+8);old_length=self.allocations[old]
            if self.realloc_mode=='inplace':
                pointer=old
                self.allocations[pointer]=length
                if length>old_length:self.uc.mem_write(old+old_length,b'\0'*(length-old_length))
                self.next_heap=max(self.next_heap,old+length)
            else:
                pointer=self._allocate(length)
                self.uc.mem_write(pointer,bytes(self.uc.mem_read(old,min(length,old_length))))
            self.services.append({'entry':hex(address),'kind':'reallocation','bytes':length,'mode':self.realloc_mode})
            self._return(8,pointer)
        elif address==0x5576e0:
            self.put(self.get(sp+4),0)
            self.services.append({'entry':hex(address),'kind':'free'})
            self._return(4)
    def invoke(self,entry,args,count=30000000):
        top=source.STACK+source.STACK_SIZE-0x1000
        for index,value in enumerate((source.END,*args)):self.put(top+4*index,value)
        self.uc.reg_write(self.ESP,top)
        self.uc.emu_start(entry,source.END,count=count)
        gate.require(self.uc.reg_read(self.EIP)==source.END,'Original wave did not return')
        return self.uc.reg_read(self.EAX)
    def wave(self,width,height,seed,target,field,*,realloc_mode='move'):
        self.services=[];self.allocations={};self.next_heap=self.heap
        self.wave_entries=0;self.insertions=0;self.realloc_mode=realloc_mode
        self.uc.mem_write(self.map_address,b'\0'*0x20000)
        self.uc.mem_write(self.map_address,struct.pack('<'+'h'*len(field),*field))
        result=self.invoke(0x5578a0,[self.map_address,width,0,0,width-1,height-1,*seed,*target,2*(width+height),-1,0,0])
        raw=bytes(self.uc.mem_read(self.map_address,width*height*2))
        return {'result':result,'output_base64':base64.b64encode(raw).decode(),
                'wave_entries':self.wave_entries,'frontier_insertions':self.insertions,'services':list(self.services)}


class Lcg:
    def __init__(self,seed):self.state=seed
    def next(self):self.state=(self.state*1664525+1013904223)&0xffffffff;return self.state
    def below(self,n):return self.next()%n


def specifications():
    specs=[]
    def add(label,w,h,seed,target,field,group):
        field=list(field);field[seed[1]*w+seed[0]]=field[target[1]*w+target[0]]=0
        specs.append({'label':label,'group':group,'width':w,'height':h,'seed':list(seed),'target':list(target),
                      'input_base64':base64.b64encode(struct.pack('<'+'h'*len(field),*field)).decode()})
    add('singleton',1,1,(0,0),(0,0),[0],'degenerate')
    for seed,target in (((0,0),(1,1)),((1,0),(0,1)),((1,1),(0,0)),((0,1),(1,0))):
        cells=[i for i in range(4) if i not in (seed[1]*2+seed[0],target[1]*2+target[0])]
        for mask in range(4):
            f=[0]*4
            for bit,index in enumerate(cells):f[index]=-1 if mask>>bit&1 else 0
            add(f'tiny-{seed}-{mask}',2,2,seed,target,f,'exhaustive2x2')
    for seed,target in (((0,0),(2,2)),((2,0),(0,2)),((2,2),(0,0)),((0,2),(2,0))):
        cells=[i for i in range(9) if i not in (seed[1]*3+seed[0],target[1]*3+target[0])]
        for mask in range(128):
            f=[0]*9
            for bit,index in enumerate(cells):f[index]=-1 if mask>>bit&1 else 0
            add(f'exhaustive-{seed}-{mask}',3,3,seed,target,f,'exhaustive3x3')
    rng=Lcg(0xa51c9e37)
    for w,h,limit in ((1,9,16),(9,1,16),(5,7,30),(8,8,30),(24,24,40),(32,32,30),(64,64,20),(128,128,6),(256,256,2)):
        for sample in range(limit):
            # High bits avoid low-LCG parity patterns; densities include open/unreachable maps.
            density=(sample%5)*15
            f=[-1 if (rng.next()>>16)%100<density else 0 for _ in range(w*h)]
            seed=(rng.below(w),rng.below(h));target=(rng.below(w),rng.below(h))
            add(f'random-{w}x{h}-{sample}',w,h,seed,target,f,'random')
    raw=NATIVE_MAP.read_bytes();gate.require(hashlib.sha256(raw).hexdigest()==NATIVE_MAP_SHA256,'Pinned original GetWayNew input map changed')
    f=struct.unpack('<576h',raw);free=[i for i,v in enumerate(f) if v==0]
    for index in range(30):
        a,b=free[rng.below(len(free))],free[rng.below(len(free))]
        add(f'original-map-{index}',24,24,(a%24,a//24),(b%24,b//24),f,'original-source-map')
    return specs


def original_cases(source_root=source.SOURCE_ROOT):
    engine=NativeWave(source_root);rows=[]
    for spec in specifications():
        field=struct.unpack('<'+'h'*(spec['width']*spec['height']),base64.b64decode(spec['input_base64']))
        result=engine.wave(spec['width'],spec['height'],spec['seed'],spec['target'],field)
        rows.append(dict(spec,**result))
    # Repeat every reallocating field with an in-place realloc service. Pointer relocation
    # is not an observable field result and must not change original scanline behavior.
    for row in list(rows):
        if any(s['kind']=='reallocation' for s in row['services']):
            field=struct.unpack('<'+'h'*(row['width']*row['height']),base64.b64decode(row['input_base64']))
            result=engine.wave(row['width'],row['height'],row['seed'],row['target'],field,realloc_mode='inplace')
            gate.require((result['result'],result['output_base64'])==(row['result'],row['output_base64']),
                         'Native wave changed with equivalent realloc service')
            rows.append(dict(row,**result,label=row['label']+'-inplace',group='reallocation-equivalence'))
    return {'schema_version':1,'original_exe_sha256':gate.EXPECTED,'source_hashes':source.SOURCE_HASHES,
            'scope':'Complete5578a0 field/return and571700 stable frontier, fullmap0/-1 reverse-wave signature used by55c9a0',
            'source_native_map_sha256':NATIVE_MAP_SHA256,
            'source_native_map_provenance':'Actual GetWayNew4a5740 ->55c9a0 input captured for source0b16,2 to18,4; see long-route navigation proof',
            'algorithm_intercepts':[],
            'service_intercepts':{'0x571200':'malloc wrapper','0x5711e0':'realloc wrapper','0x5576e0':'free wrapper'},
            'cases':rows}


def validate(source_root=source.SOURCE_ROOT,mono_root=None):
    # Reject altered source bytes even when optional execution dependencies
    # are absent; a changed EXE is never an optional-prerequisite skip.
    source.checked_sources(source_root)
    _,unicorn,runtime,compiler=gate.prerequisites(Path(source_root)/'installed/ancient.exe',mono_root)
    original=original_cases(source_root)
    gate.require(gate.digest(FIXTURE)==FIXTURE_SHA256,'Pinned source wave fixture changed')
    gate.require(json.loads(FIXTURE.read_text())==original,'Actual original wave differs from durable fixture')
    with tempfile.TemporaryDirectory(prefix='source-wave-') as temporary:
        executable=Path(temporary)/'SourceWaveFieldProbe.exe'
        result=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/target:exe','/out:'+str(executable),str(SOURCE),str(PROBE)],text=True,capture_output=True,timeout=60)
        gate.require(result.returncode==0,'Source wave C# compilation failed:\n'+result.stdout+result.stderr)
        lines=['\t'.join(map(str,[r['width'],r['height'],*r['seed'],*r['target'],r['input_base64']])) for r in original['cases']]
        result=subprocess.run([str(runtime),str(executable)],input='\n'.join(lines)+'\n',text=True,capture_output=True,timeout=90)
        gate.require(result.returncode==0,'Source wave C# execution failed:\n'+result.stdout+result.stderr)
    rows=[];guards=[]
    for line in result.stdout.splitlines():
        parts=line.split('\t')
        if parts[0]=='CHECK':guards.append(parts[1])
        elif parts[0]=='RESULT':rows.append((int(parts[1]),parts[2]))
        else:raise AssertionError('Unexpected wave probe output: '+line)
    gate.require(len(rows)==len(original['cases']),'Source wave C# case count differs')
    for index,(native,managed) in enumerate(zip(original['cases'],rows)):
        gate.require(managed==(native['result'],native['output_base64']),f'Wave result/wholefield mismatch case{index}:'+native['label'])
    gate.require(len(guards)==len(set(guards))==9,'Source wave API guard count differs')
    return {'passed':len(rows),'compared_field_cells':sum(r['width']*r['height'] for r in original['cases']),
            'native_reallocations':sum(s['kind']=='reallocation' for r in original['cases'] for s in r['services']),
            'checked_compilation':True,'warnings_as_errors':True,'csharp_contract_checks':len(guards),
            'fixture_sha256':FIXTURE_SHA256,'source_sha256':{str(p.relative_to(ROOT)):gate.digest(p) for p in (SOURCE,PROBE,NATIVE_MAP)},
            'validator_sha256':gate.digest(Path(__file__)),'source_hashes':source.SOURCE_HASHES,'original':original,
            'compiler_command':compiler,'mono_runtime':str(runtime),'unicorn_version':unicorn.__version__,
            'limits':['Only fullmap0/-1 field signature with maxSteps2*(w+h),heading-1,alternate0 andremaining0 is projected',
                      'Managed buffers avoid native pointer reallocations but retain exact stable insertion order',
                      'Allocation failures and arbitrary weighted/nonzero map labels are outside this projection',
                      'This proves a wave field only; no complete path assembly, ship movement, Life, AI or Unity/player runs here']}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=OUTPUT)
    args=parser.parse_args(argv)
    if args.output.exists():parser.error('Select a fresh output report')
    report=validate();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(f"{report['passed']} exact native/C# wave fields; {report['compared_field_cells']} cells; {report['csharp_contract_checks']} API checks")
    return 0

if __name__=='__main__':raise SystemExit(main())
