#!/usr/bin/env python3
"""Whole original normal-idle step and init RNG block vs actual checked C#."""
from __future__ import annotations
import argparse,hashlib,json,random,struct,subprocess,tempfile
from pathlib import Path
if __package__:
 from .validate_boss_ai_gate import ROOT,EXPECTED,ORIGINAL,MissingPrerequisite,digest,prerequisites,require
else:
 from validate_boss_ai_gate import ROOT,EXPECTED,ORIGINAL,MissingPrerequisite,digest,prerequisites,require
SOURCE=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipIdleProgression.cs'
PROBE=ROOT/'tests/fixtures/ShipIdleProgressionProbe.cs'
FIXTURE=ROOT/'tests/fixtures/ship_idle_progression.json'
FIXTURE_SHA256='4487780fd8cfd3367c7af2e920a41d3be7e4a2534f4e22837d773327d4df1fd4'
OUTPUT=ROOT/'artifacts/order-cycle/idle/csharp-validation.json'
OBJ,SPRITE,SYSTEM,GRID,APP,MSG,PAYLOAD,END,STACK=(0x70000000,0x70004000,0x70006000,0x70008000,0x70010000,0x70014000,0x70016000,0x700f0000,0x71000000)
KEYS=('frame','heading','frame_step','now','last_tick','interval','random_state','speed','reserved','cell')

def image_checked(original=ORIGINAL):
 p=Path(original)
 if not p.is_file():raise MissingPrerequisite('Optional original executable missing: '+str(p))
 raw=p.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=EXPECTED:raise ValueError('Original executable SHA-256 differs from verified idle source')
 try:
  import pefile
  import unicorn
 except ImportError as error:
  raise MissingPrerequisite('Optional idle analysis dependency missing: '+str(error))from error
 pe=pefile.PE(data=raw);return pe.get_memory_mapped_image(),pe.OPTIONAL_HEADER.SizeOfImage

class IdleOracle:
 def __init__(self,image,size):
  from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
  self.u=Uc(UC_ARCH_X86,UC_MODE_32);self.u.mem_map(0x400000,(size+4095)&~4095);self.u.mem_write(0x400000,image);self.u.mem_map(OBJ,0x100000);self.u.mem_map(STACK,0x20000)
  self.u.hook_add(UC_HOOK_CODE,self.hook);self.u.hook_add(UC_HOOK_MEM_WRITE,self.onwrite)
  self.draws=[];self.releases=[];self.grid_writes=[];self.entries=[];self.depth=19812;self.watch=False
 def w(self,a,v):self.u.mem_write(a,struct.pack('<I',v&0xffffffff))
 def r(self,a):return struct.unpack('<I',self.u.mem_read(a,4))[0]
 def signed(self,a):return struct.unpack('<i',self.u.mem_read(a,4))[0]
 def ret(self,clean=0,value=0):
  from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_EAX
  sp=self.u.reg_read(UC_X86_REG_ESP);self.u.reg_write(UC_X86_REG_EIP,self.r(sp));self.u.reg_write(UC_X86_REG_ESP,sp+4+clean);self.u.reg_write(UC_X86_REG_EAX,value)
 def hook(self,u,a,size,unused):
  from unicorn.x86_const import UC_X86_REG_ESP
  if a==0x587318:self.ret();return
  if a in(0x556610,0x556880):raise AssertionError('Original idle error path '+hex(a))
  if not self.watch:return
  if a in(0x4a3150,0x4a3320,0x4a3560,0x4a4d49):self.entries.append(hex(a))
  if a==0x4a3970:self.releases.append(self.r(u.reg_read(UC_X86_REG_ESP)+4))
  if a==0x50d130:
   sp=u.reg_read(UC_X86_REG_ESP);require(self.r(sp+4)==0,'Unexpected source sprite depth slot');self.depth=self.r(sp+8);self.ret(8);return
  if a==0x50d5f0:
   sp=u.reg_read(UC_X86_REG_ESP);args=[self.r(sp+4+4*i)for i in range(7)];require(args[0]==0,'Unexpected idle sprite slot')
   self.draws.append({'frame':args[1]if args[1]<0x80000000 else args[1]-0x100000000,'world':args[2:4],'depth':self.depth,'last_tick_at_draw':self.r(SPRITE+0x81),'random_state_at_draw':self.r(OBJ+0x18),'speed_at_draw':self.signed(OBJ+0x59b),'reserved_at_draw':self.signed(OBJ+0x5ab)})
   self.ret(28)
 def onwrite(self,u,access,address,size,value,unused):
  if self.watch and GRID+8<=address<GRID+8+576*24 and(address-GRID-8)%24==4:
   from unicorn.x86_const import UC_X86_REG_EIP
   self.grid_writes.append({'cell':(address-GRID-8)//24,'value':value&0xffffffff,'instruction':hex(u.reg_read(UC_X86_REG_EIP))})
 def setup(self,c,foreign=False):
  self.u.mem_write(OBJ,bytes(0x900));self.u.mem_write(SPRITE,bytes(0x100));self.u.mem_write(GRID,bytes(8+576*24));self.u.mem_write(GRID,struct.pack('<hhhh',24,24,64,64))
  cell=c['cell'];self.w(0x5c74fc,GRID);self.w(0x5c74ec,24);self.w(0x5c74f0,24)
  for a,v in((OBJ+0x8be,SPRITE),(OBJ+0x70,SYSTEM),(OBJ+0xc,APP),(OBJ+0x18,c['random_state']),(OBJ+0x59b,c['speed']),(OBJ+0x5ab,c['reserved']),(OBJ+0x5a3,cell%24),(OBJ+0x5a7,cell//24),(SPRITE+0x45,c['frame']),(SPRITE+0x7d,c['interval']),(SPRITE+0x81,c['last_tick']),(SPRITE+0x59,1028),(SPRITE+0x5d,132),(SPRITE+0x61,56),(SPRITE+0x65,56),(SYSTEM+0xde,c['now'])):self.w(a,v)
  self.u.mem_write(OBJ+0x5af,bytes([c['heading']&255]));self.u.mem_write(OBJ+0x5b0,bytes([c['frame_step']&255]));self.u.mem_write(OBJ+0x74,b'\x01')
  self.w(GRID+8+24*cell+4,OBJ)
  if c['reserved']>=0:self.w(GRID+8+24*c['reserved']+4,OBJ+0x2000 if foreign else OBJ)
 def invoke(self,entry=0x4a3150):
  from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_ECX,UC_X86_REG_EAX
  self.draws=[];self.releases=[];self.grid_writes=[];self.entries=[];self.watch=True
  sp=STACK+0x1f000;self.w(sp,END);self.u.reg_write(UC_X86_REG_ESP,sp);self.u.reg_write(UC_X86_REG_ECX,OBJ);self.u.emu_start(entry,END,count=50000)
  require(self.u.reg_read(UC_X86_REG_EIP)==END,'Idle did not return');self.watch=False
  result=[self.signed(SPRITE+0x45),struct.unpack('<b',self.u.mem_read(OBJ+0x5b0,1))[0],self.r(SPRITE+0x81),self.r(SPRITE+0x7d),self.r(OBJ+0x18),self.signed(OBJ+0x59b),self.signed(OBJ+0x5ab),self.releases[0]if self.releases else-1,int(bool(self.draws)),self.draws[0]['frame']if self.draws else 0]
  require(len(self.draws)<=1 and len(self.releases)<=1,'Normal idle produced multiple draws/releases')
  return {'result':result,'return':self.u.reg_read(UC_X86_REG_EAX),'draws':list(self.draws),'release_calls':list(self.releases),'grid_writes':list(self.grid_writes),'last_state_counter':self.r(OBJ+0x58d),'entries':list(self.entries)}

def cases():
 rows=[]
 for heading in range(8):
  for seed in(0,1,0x80000000,0xffffffff):
   frame,step,last,rng,speed,reserved=heading*4,0,0,seed,21907,87
   # Populated with actual prior native result, below, not a Python idle model.
   rows.append({'label':f'trace_h{heading}_seed{seed}','trace':True,'initial':{'frame':frame,'heading':heading,'frame_step':step,'now':0,'last_tick':last,'interval':2,'random_state':rng,'speed':speed,'reserved':reserved,'cell':64},'ticks':list(range(120))})
 for heading in range(8):
  for i,seed in enumerate((0,1,0x80000000,0xffffffff)):
   new=(seed*0x41c64e6d+0x3039)&0xffffffff;t=(new>>16)%7+15
   for j,(now,last)in enumerate(((0,0),(t-1,0),(t,0),(t+1,0),(0,1),(3,0xfffffffa))):
    reserved=(-2,-1,64,65,87)[(i+j)%5]
    rows.append({'label':f'boundary_h{heading}_seed{seed}_{j}','trace':False,'input':{'frame':(56+heading*4+[0,1,2,3,-1,4][j]),'heading':heading,'frame_step':(-1,0,1)[j%3],'now':now,'last_tick':last,'interval':(0,2,0xffffffff)[j%3],'random_state':seed,'speed':(-1,0,1,7,21907,0x7fffffff)[j],'reserved':reserved,'cell':64}})
 for heading in(-128,-1,0,7,127):
  for frame in(-0x80000000,-1,0,55,56,59,87,0x7fffffff):
   for step in(-128,-1,0,1,127):
    rows.append({'label':f'raw_h{heading}_frame{frame}_step{step}','trace':False,'input':{'frame':frame,'heading':heading,'frame_step':step,'now':100,'last_tick':0,'interval':0xffffffff,'random_state':0xffffffff,'speed':0,'reserved':-1,'cell':64}})
 return rows

def native_cases(image,size):
 oracle=IdleOracle(image,size);out=[]
 for case in cases():
  entries=[]
  if case['trace']:
   state=dict(case['initial']);oracle.setup(state)
   for now in case['ticks']:
    state['now']=now;oracle.w(SYSTEM+0xde,now);got=oracle.invoke();require(got['return']==0,'Idle returned nonzero')
    entries.append({'input':dict(state),'native':got})
    values=got['result'];state.update(frame=values[0],frame_step=values[1],last_tick=values[2],interval=values[3],random_state=values[4],speed=values[5],reserved=values[6])
  else:
   oracle.setup(case['input']);got=oracle.invoke();require(got['return']==0,'Idle returned nonzero');entries.append({'input':case['input'],'native':got})
  out.append({'label':case['label'],'trace':case['trace'],'entries':entries})
 return out

def seed_cases(image,size):
 from unicorn.x86_const import UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EIP
 oracle=IdleOracle(image,size);rows=[]
 for seed in(0,1,2,0x12345678,0x7fffffff,0x80000000,0xffffffff):
  for instance in(0,1,11,12,13,16,39,40,41,42,0xffffffff):
   for a,v in((OBJ+0x68,APP),(OBJ+0x4c,instance),(OBJ+0x18,0xdeadbeef),(APP+0x2ee5,seed),(MSG+0x14,PAYLOAD)):oracle.w(a,v)
   oracle.u.reg_write(UC_X86_REG_ESI,OBJ);oracle.u.reg_write(UC_X86_REG_EDI,MSG)
   oracle.u.emu_start(0x4dc6d9,0x4dc6ec,count=30);require(oracle.u.reg_read(UC_X86_REG_EIP)==0x4dc6ec,'Init seed block incomplete')
   value=oracle.r(OBJ+0x18);require(value==(seed*instance)&0xffffffff,'Init seed product differs')
   rows.append({'session_seed':seed,'instance_id':instance,'ship_random_state':value})
 return rows

def caller_cases(image,size):
 oracle=IdleOracle(image,size);rows=[]
 for heading in range(8):
  for seed in(0,1,0x80000000,0xffffffff):
   new=(seed*0x41c64e6d+0x3039)&0xffffffff;t=(new>>16)%7+15
   for now in(0,t,t+1):
    c={'frame':heading*4,'heading':heading,'frame_step':1,'now':now,'last_tick':0,'interval':2,'random_state':seed,'speed':21907,'reserved':87,'cell':64}
    oracle.setup(c);isolated=oracle.invoke();oracle.setup(c);whole=oracle.invoke(0x4a3f40)
    require(whole['return']==1 and whole['entries']==['0x4a3150'],'MoveShip did not return after idle')
    require(whole['result']==isolated['result']and whole['draws']==isolated['draws']and whole['grid_writes']==isolated['grid_writes'],'Whole MoveShip idle differs')
    require(whole['last_state_counter']==now,'MoveShip did not stamp state0 before idle')
    rows.append({'input':c,'whole':whole})
 return rows

def fixture_object(original=ORIGINAL):
 image,size=image_checked(original)
 return {'schema_version':1,'original_exe_sha256':EXPECTED,'scope':'Normal spriteMode0 healthy no-support/no-link branch; raw frame/heading stress is arithmetic only','idle_entry':'0x4a3150','native_graphics_boundary_hooks':['normal setjmp in DrawSprite','0x50d130 SetDepth boundary','0x50d5f0 published frame/world boundary'],'native_query_and_grid_hooks':[],'seed_range':['0x4dc6d9','0x4dc6ec'],'seed_hooks':[],'seed_cases':seed_cases(image,size),'cases':native_cases(image,size),'caller_cases':caller_cases(image,size)}

def load_fixture(path=FIXTURE):
 raw=Path(path).read_bytes();require(hashlib.sha256(raw).hexdigest()==FIXTURE_SHA256,'Idle fixture SHA-256 differs');data=json.loads(raw);require(data['original_exe_sha256']==EXPECTED,'Idle fixture source differs');return data

def validate(original=ORIGINAL,mono_root=None):
 fresh=fixture_object(original);require(digest(Path(original))==EXPECTED,'Original changed during native idle execution');fixture=load_fixture();require(fresh==fixture,'Fresh original idle execution differs from pinned fixture')
 pefile,unicorn,runtime,compiler=prerequisites(Path(original),mono_root);before={str(p):digest(p)for p in(Path(original),SOURCE,PROBE,FIXTURE)}
 inputs=[row for case in fresh['cases']for row in case['entries']];lines=['\t'.join(str(row['input'][k])for k in KEYS)for row in inputs]
 lines.extend('SEED\t'+str(row['session_seed'])+'\t'+str(row['instance_id'])for row in fresh['seed_cases'])
 with tempfile.TemporaryDirectory(prefix='ship-idle-csharp-')as temporary:
  exe=Path(temporary)/'ShipIdleProgressionProbe.exe';built=subprocess.run(compiler+['/nologo','/checked+','/target:exe','/out:'+str(exe),str(SOURCE),str(PROBE)],capture_output=True,text=True,timeout=60)
  require(built.returncode==0,'Idle C# compilation failed:\n'+built.stdout+built.stderr)
  result=subprocess.run([str(runtime),str(exe)],input='\n'.join(lines)+'\n',check=True,capture_output=True,text=True,timeout=60)
 outputs=result.stdout.splitlines();require(len(outputs)==len(lines),'Unexpected idle probe row count')
 for row,line in zip(inputs,outputs):require([int(v)for v in line.split('\t')]==row['native']['result'],'Idle C#/x86 mismatch: '+str(row['input']))
 for native,line in zip(fresh['seed_cases'],outputs[len(inputs):]):require(line=='SEED\t'+str(native['ship_random_state']),'Initial RNG C#/x86 mismatch')
 require(before=={str(p):digest(p)for p in(Path(original),SOURCE,PROBE,FIXTURE)},'Original/idle sources changed during validation')
 return {'passed':len(inputs),'trace_count':sum(c['trace']for c in fresh['cases']),'isolated_case_count':sum(not c['trace']for c in fresh['cases']),'normal_trace_calls':sum(len(c['entries'])for c in fresh['cases']if c['trace']),'seed_case_count':len(fresh['seed_cases']),'whole_move_ship_case_count':len(fresh['caller_cases']),'publication_count':sum(len(r['native']['draws'])for r in inputs),'release_call_count':sum(len(r['native']['release_calls'])for r in inputs),'grid_write_count':sum(len(r['native']['grid_writes'])for r in inputs),'checked_compilation':True,'original_exe_sha256':EXPECTED,'fixture_sha256':FIXTURE_SHA256,'source_sha256':digest(SOURCE),'probe_sha256':digest(PROBE),'validator_sha256':digest(Path(__file__)),'scope':fresh['scope'],'native_query_and_grid_hooks':[],'native_graphics_boundary_hooks':fresh['native_graphics_boundary_hooks'],'seed_range':fresh['seed_range'],'seed_hooks':[]}

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path,default=ORIGINAL);p.add_argument('--mono-root',type=Path);p.add_argument('--output',type=Path,default=OUTPUT);args=p.parse_args(argv)
 if args.output.exists():p.error('Refusing to replace existing idle report')
 try:report=validate(args.original,args.mono_root)
 except MissingPrerequisite as e:p.exit(2,str(e)+'\n')
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
