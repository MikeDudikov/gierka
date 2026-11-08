#!/usr/bin/env python3
"""Bounded original ProcShipsWork caller schedule; no Unity/OS services or full Life."""
from __future__ import annotations
from pathlib import Path
import sys,hashlib,json,struct,importlib.util,argparse
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import validate_mission_object_selection as S
from tools import validate_mission_ship_seed as SS
from tools.validate_boss_ai_gate import require,EXPECTED
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_ECX,UC_X86_REG_EIP,UC_X86_REG_ESP
import pefile
OBJ,APP,SYSTEM,PAYLOAD,SPRITE=(S.CONTEXT,S.CONTEXT+0x10000,S.CONTEXT+0x20000,S.CONTEXT+0x30000,S.CONTEXT+0x40000)
GRID,WEATHER,PLAYERS=(S.CONTEXT+0x50000,S.CONTEXT+0x70000,S.CONTEXT+0x80000)
ENTRIES={0x4dc630:'ShipGetMessage',0x4e2ba0:'RequestCellMove',0x4dec40:'Life',0x4ab720:'Promote',0x4ab250:'PromoteMove',0x4abe50:'ArbitrateIncomingTask',0x4ab930:'ProcShipsWork',0x4a5f30:'MoveOrderWork',0x4a6330:'ProcPostMove',0x4a6150:'RecheckPlan',0x4a6100:'SaveRetryInputs',0x4a5740:'BuildPath',0x55c9a0:'Planner',0x4a3f40:'MoveShip',0x4a3320:'Turn',0x4a3560:'StateMove',0x4a3a70:'Reserve',0x4a3150:'Idle',0x4a9e30:'Command',0x4aa540:'ProcessStopRequest'}
class WorkOracle:
 def __init__(self,target=(0,0),counter=0,pending=1,session_seed=0):
  self.sources=S.checked_sources(S.SOURCE_ROOT);pe=pefile.PE(data=self.sources['installed/ancient.exe']);self.u=S.new_engine(pe.get_memory_mapped_image(),pe.OPTIONAL_HEADER.SizeOfImage)
  self.events=[];self.services=[];self.writes=[];self.phase='init';self.heap=0x71000000;self.history=[];self.target=target;self.tick=0;self.sample_index=0;self.operation='initial';self.epoch=1;self.session_seed=session_seed;self.publications=[];self.grid_writes=[];self.last_depth=19812;self.drawn_frame=20;self.render_world=[1028,132];self.tail=False
  self.u.mem_map(0x71000000,0x1000000)
  self.u.hook_add(UC_HOOK_CODE,self.hook);self.u.hook_add(UC_HOOK_MEM_WRITE,self.onwrite)
  records=SS.source_records(self.sources);payload=next(p for e,p in records if e['name']=='OBJ_0000000b');self.payload_sha256=hashlib.sha256(payload).hexdigest()
  self.w(0x5d1f90,0xabcdef01);self.invoke(0x4dc3f0)
  for off,value in ((0xc,APP),(0x10,APP),(0x4c,11),(0x68,APP),(0x6c,SYSTEM),(0x70,SYSTEM)):self.w(OBJ+off,value)
  self.u.mem_write(PAYLOAD,payload);self.invoke(0x4dfa90,(PAYLOAD,));self.w(0x5c7508,PLAYERS);self.invoke(0x4bece0)
  for a,v in ((OBJ+0x8be,SPRITE),(SPRITE+0x61,56),(SPRITE+0x65,56),(SPRITE+0x59,1028),(SPRITE+0x5d,132),(SPRITE+0x45,20),(SPRITE+0x7d,2),(SPRITE+0x81,0)):self.w(a,v)
  flags=(ROOT/'tests/fixtures/mission_cell_flags.bin').read_bytes();require(hashlib.sha256(flags).hexdigest()=='eb8c22b2dc3a3d6de5be5c5a28560701333cbc8610e8dd687052f4f93b260283','flags changed')
  for a,v in ((0x5c74fc,GRID),(0x5c74ec,24),(0x5c74f0,24),(0x5c74e8,576)):self.w(a,v)
  self.u.mem_write(GRID,struct.pack('<hhhh',24,24,64,64))
  for i,v in enumerate(struct.unpack('<576I',flags)):self.w(GRID+8+i*24,v)
  for i,(e,p) in enumerate(records):
   n=int(e['name'][4:],16);pointer=OBJ if n==11 else S.CONTEXT+0xa0000+i*0x1000;x,y=struct.unpack_from('<ii',p,36)
   for off,v in ((0x4c,n),(0x50,200+struct.unpack_from('<I',p,28)[0]),(0x5a3,x),(0x5a7,y)):self.w(pointer+off,v)
   self.invoke(0x499830,(0,pointer,y*24+x))
  for a,pointer in ((0x5c93bc,S.CONTEXT+0x90000),(0x5c9398,S.CONTEXT+0x91000),(0x5c93c0,S.CONTEXT+0x92000)):self.w(a,pointer)
  sp=S.STACK+S.STACK_SIZE-0x1000;self.w(sp,S.END);self.u.reg_write(UC_X86_REG_ESP,sp);self.u.reg_write(UC_X86_REG_ECX,OBJ)
  self.u.emu_start(0x49a950,0x49a9ce,count=50000);require(self.u.reg_read(UC_X86_REG_EIP)==0x49a9ce,'map prefix')
  for a,v in ((0x5c6a40,WEATHER),(WEATHER+0x34,0),(OBJ+0x25d,0),(OBJ+0x54e,target[0]),(OBJ+0x552,target[1]),(SYSTEM+0xde,counter),(APP+0xe2,pending)):self.w(a,v)
  self.u.mem_write(WEATHER+0x38,b'\x05');self.u.mem_write(OBJ+0x593,b'\x00');self.w(OBJ+0x18,(11*session_seed)&0xffffffff);self.phase='work';self.events.clear();self.writes.clear();self.services.clear()
 def w(self,a,v):S.put(self.u,a,v)
 def r(self,a):return S.get(self.u,a)
 def b(self,a):return bytes(self.u.mem_read(a,1))[0]
 def signed(self,a):return struct.unpack('<i',self.u.mem_read(a,4))[0]
 def ret(self,clean=0,eax=0):
  sp=self.u.reg_read(UC_X86_REG_ESP);self.u.reg_write(UC_X86_REG_EIP,self.r(sp));self.u.reg_write(UC_X86_REG_ESP,sp+4+clean);self.u.reg_write(UC_X86_REG_EAX,eax&0xffffffff)
 def state(self):
  p=self.r(OBJ+0x5c2);n=self.r(OBJ+0x5ba);i=self.r(OBJ+0x5be);cache=self.r(OBJ+0x5cd)
  require(n<=2048,'path size out of bound')
  count=self.r(cache+0xc)if cache else 0;require(count<=576,'cache size out of bound')
  data=self.r(cache+0x1c)if cache else 0;stride=self.r(cache+8)if cache else 4
  require(count==0 or data!=0 and stride==4,'invalid cache storage')
  coord=lambda index:list(struct.unpack('<hh',self.u.mem_read(p+index*5,4)))if p and index<n else[-1,-1]
  return {'sample_index':self.sample_index,'operation':self.operation,'epoch':self.epoch,'tick':self.tick,'counter':self.r(SYSTEM+0xde),'stamp':self.r(SYSTEM+0xde),'pending_steps':self.r(APP+0xe2),
   'cell':[self.signed(OBJ+0x5a3),self.signed(OBJ+0x5a7)],'world':[self.signed(SPRITE+0x59),self.signed(SPRITE+0x5d)],'state':self.b(OBJ+0x58c),'center_gate':self.b(OBJ+0x596),'heading':struct.unpack('b',self.u.mem_read(OBJ+0x5af,1))[0],'target_heading':struct.unpack('b',self.u.mem_read(OBJ+0x5b1,1))[0],'turn_step':struct.unpack('b',self.u.mem_read(OBJ+0x5b0,1))[0],
   'speed':self.signed(OBJ+0x59b),'remainder':self.signed(OBJ+0x597),'deceleration':self.signed(OBJ+0x284),'reserved':self.signed(OBJ+0x5ab),'next_cell':self.signed(OBJ+0x5b6),'last_cell':self.signed(OBJ+0x5b2),'path_count':n,'path_index':i,'path_hex':bytes(self.u.mem_read(p,n*5)).hex()if p and n else'','waypoint':coord(i),'next_waypoint':coord(i+1),'path_endpoint':coord(n-1)if n else[-1,-1],
   'frame':self.r(SPRITE+0x45),'last_frame_tick':self.r(SPRITE+0x81),'last_state_counter':self.r(OBJ+0x58d),'drawn_frame':self.drawn_frame,'render_world':self.render_world[:],'animation_tail_reached':self.tail,'pose_published':bool(self.publications),'publications':[dict(x,world=x['world'][:])for x in self.publications],
   'occupied_cell_count':sum(self.r(GRID+8+j*24+4)!=0 for j in range(576)),'owned_cells':[j for j in range(576)if self.r(GRID+8+j*24+4)==OBJ],
   'pending':self.r(OBJ+0x7d6),'active':self.r(OBJ+0x25d),'deferred':self.r(OBJ+0x265),'stop_mask':self.r(OBJ+0x818),'capabilities':self.r(OBJ+0x261),'ready':self.r(OBJ+0x7da),'requested_goal':[self.signed(OBJ+0x85c),self.signed(OBJ+0x860)],'active_target':[self.signed(OBJ+0x54e),self.signed(OBJ+0x552)],
   'request_new':self.b(OBJ+0x593),'retry':self.b(OBJ+0x591),'last_plan':self.r(OBJ+0x57b),'retry_interval':self.r(OBJ+0x57f),'navigation_radius':self.r(OBJ+0x5c9),'snapshot_retry':self.r(OBJ+0x562),'snapshot_mode':self.b(OBJ+0x566),'snapshot_target':[self.signed(OBJ+0x56b),self.signed(OBJ+0x56f)],'snapshot_cell':[self.signed(OBJ+0x573),self.signed(OBJ+0x577)],
   'random_state':self.r(OBJ+0x18),'cache_exists':cache!=0,'cache_count':count,'cache_cells':[self.signed(data+j*stride)for j in range(count)],
   'events':[dict(e)for e in self.events],'grid_writes':[dict(w)for w in self.grid_writes],'services':[dict(s)for s in self.services]}
 def hook(self,u,a,size,unused):
  self.history.append(hex(a));self.history=self.history[-25:]
  if self.phase=='work' and a in ENTRIES:
   sp=u.reg_read(UC_X86_REG_ESP);argc={0x4a6330:7,0x4a6150:6,0x4a9e30:2}.get(a,0)
   self.events.append({'tick':self.tick,'entry':hex(a),'name':ENTRIES[a],'counter':self.r(SYSTEM+0xde),'state':self.b(OBJ+0x58c),'active':self.r(OBJ+0x25d),'pending':self.r(OBJ+0x7d6),'cell':[self.signed(OBJ+0x5a3),self.signed(OBJ+0x5a7)],'arguments':[self.r(sp+4+4*i)for i in range(argc)]})
  if self.phase=='work' and a==0x4a4d49:self.tail=True
  if a==0x587318:self.ret();return
  if a in(0x557700,0x589bf5):
   sp=u.reg_read(UC_X86_REG_ESP);length=self.r(sp+4);p=self.heap;self.heap+=(length+15)&~15;require(self.heap<0x72000000,'16MiB isolated heap exceeded')
   if self.phase=='work':self.services.append({'tick':self.tick,'counter':self.r(SYSTEM+0xde),'entry':hex(a),'service':'bounded isolated heap allocation','arguments':[length],'result':hex(p)})
   self.ret(4 if a==0x557700 else 0,p);return
  if a==0x589bc6:
   if self.phase=='work':self.services.append({'tick':self.tick,'counter':self.r(SYSTEM+0xde),'entry':hex(a),'service':'bounded heap delete','arguments':[hex(self.r(u.reg_read(UC_X86_REG_ESP)+4))]})
   self.ret();return
  if a==0x5576e0:
   pointer=self.r(u.reg_read(UC_X86_REG_ESP)+4)
   if self.phase=='work':self.services.append({'tick':self.tick,'counter':self.r(SYSTEM+0xde),'entry':hex(a),'service':'bounded pointer deallocation','arguments':[hex(pointer),hex(self.r(pointer))]})
   self.w(pointer,0);self.ret(4);return
  init={0x4e7220:(0,'initial command dispatch'),0x4bee60:(0,'unrelated derived initialization'),0x50e640:(4,'object system message'),0x4e1bb0:(4,'damage sprite request'),0x4b97d0:(16,'initial order queue')}
  work={0x50d130:(8,'sprite depth publication'),0x50d5f0:(28,'sprite frame publication'),0x50e7c0:(12,'visibility remove'),0x50e780:(12,'visibility add'),0x4a1700:(16,'arrival system notification')}
  boundary=(init if self.phase=='init'else work).get(a)
  if boundary:
   clean,name=boundary;sp=u.reg_read(UC_X86_REG_ESP);args=[self.r(sp+4+i*4)for i in range(clean//4)]
   if self.phase=='work':self.services.append({'tick':self.tick,'counter':self.r(SYSTEM+0xde),'entry':hex(a),'service':name,'arguments':args})
   if a==0x50d130:self.last_depth=args[1]
   if a==0x50d5f0:
    require(args[0]==0,'unexpected publication slot');self.drawn_frame=args[1];self.render_world=args[2:4];self.publications.append({'frame':args[1],'world':args[2:4],'depth':self.last_depth})
   self.ret(clean);return
  if a in(0x556610,0x556880):raise AssertionError('original error '+hex(a))
 def onwrite(self,u,access,address,size,value,unused):
  if self.phase!='work':return
  if GRID+8<=address<GRID+8+24*576 and (address-GRID-8)%24==4:
   index=(address-GRID-8)//24
   self.grid_writes.append({'tick':self.tick,'counter':self.r(SYSTEM+0xde),'instruction':hex(u.reg_read(UC_X86_REG_EIP)),'cell_index':index,'cell':[index%24,index//24],'before':hex(self.r(address)),'after':hex(value&0xffffffff),'size':size})
 def invoke(self,address,args=()):
  sp=S.STACK+S.STACK_SIZE-0x1000
  for i,v in enumerate((S.END,*args)):self.w(sp+4*i,v)
  self.u.reg_write(UC_X86_REG_ESP,sp);self.u.reg_write(UC_X86_REG_ECX,OBJ)
  try:self.u.emu_start(address,S.END,count=500000)
  except Exception as e:raise AssertionError(f'{e}; entry={hex(address)} recent={self.history}')from e
  require(self.u.reg_read(UC_X86_REG_EIP)==S.END,'no normal return '+hex(address))
  return self.u.reg_read(UC_X86_REG_EAX)
 def reset_operation(self,operation):
  self.phase='work';self.operation=operation;self.events.clear();self.services.clear();self.writes.clear();self.grid_writes.clear();self.publications.clear();self.tail=False
 def sample(self):return self.state()
 def request(self,x,y):
  self.sample_index+=1;self.reset_operation('request')
  self.w(MESSAGE+0x10,0x280f);self.w(MESSAGE+0x14,ACTION)
  self.u.mem_write(ACTION+0xc,b'\x14');self.w(ACTION+0xd,DATA)
  self.u.mem_write(DATA,struct.pack('<IIB',x&0xffffffff,y&0xffffffff,255))
  self.invoke(0x4dc630,(MESSAGE,));return self.sample()
 def advance(self,pending=1):
  self.tick+=1;self.sample_index+=1;self.reset_operation('tick')
  self.w(SYSTEM+0xde,self.tick);self.w(APP+0xe2,pending)
  self.invoke(0x4ab720);self.invoke(0x4ab930)
  return self.sample()

MESSAGE,ACTION,DATA=(S.CONTEXT+0x61000,S.CONTEXT+0x62000,S.CONTEXT+0x63000)
OUT=ROOT/'artifacts/order-cycle/lifecycle'

def case(label,goals,*,session_seed=0,pending=1,maximum=600):
 o=WorkOracle(session_seed=session_seed);o.reset_operation('initial');samples=[o.sample()]
 samples.append(o.request(*goals[0]));next_goal=1;finished=False
 for _ in range(maximum):
  row=o.advance(pending);samples.append(row)
  ready=(row['active']&0x80)==0 and row['state']==0 and (row['pending']&0x88)==0
  idle_pub=ready and row['pose_published'] and 56<=row['drawn_frame']<=87
  if idle_pub:
   if next_goal<len(goals):
    o.epoch+=1;samples.append(o.request(*goals[next_goal]));next_goal+=1
   else:finished=True;break
 return {'label':label,'session_seed':session_seed,'pending_steps':pending,'goals':[list(g)for g in goals],'tick_bound':maximum,'finished':finished,'ticks':o.tick,'source_resource':'OBJ_0000000b','source_payload_sha256':o.payload_sha256,'samples':samples}

def validate(selected=None):
 specs=[('reach18_5',[(18,5)],0,1,600),('reach20_4',[(20,4)],0,1,600),('nearest18_2',[(18,2)],0,1,180),('blocked16_1',[(16,1)],0,1,180),('two18_5_then16_4',[(18,5),(16,4)],0,1,600),('seedFFFFFFFF18_5',[(18,5)],0xffffffff,1,600),('pending3_18_5',[(18,5)],0,3,600)]
 rows=[]
 for name,goals,seed,pending,bound in specs:
  if selected is None or name in selected:
   rows.append(case(name,goals,session_seed=seed,pending=pending,maximum=bound))
 S.checked_sources(S.SOURCE_ROOT)
 return {'schema_version':1,'original_exe_sha256':EXPECTED,'source_hashes':S.SOURCE_HASHES,'oracle_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_cell_flags_sha256':'eb8c22b2dc3a3d6de5be5c5a28560701333cbc8610e8dd687052f4f93b260283','kind':'Actual healthy source0b request/promotion/work/replan/MoveShip same-counter lifecycle with idle RNG and ordered publications/grid writes','ready_rule':'active&0x80==0 AND physicalstate0 AND pending&0x88==0; nextrequest after first drawn56..87 publication satisfying ready','initialization_intercepts':{'0x587318':'normal setjmp return','0x4e7220':'initial command dispatch boundary','0x4bee60':'unrelated derived initialization boundary; actual4bece0 is run separately','0x50e640':'object system dispatch','0x4e1bb0':'damage sprite request','0x4b97d0':'initial order queue'},'cases':rows,'limits':['No complete app/Life/audio/AI or OS-input pipeline','Controlled wind0/5 upgrade0 sourcefleet8; source actor RNG initialized to11*explicit session_seed','Only normal healthycellmove mode0/priority0; busy replacement and combat outside scope','Initialization and rendering/heap/system service boundaries are explicit; request, promotion, normalWork, replans, motion and idle execute original instructions']}

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=OUT/'native-ship-move-order.json');parser.add_argument('--case',action='append');args=parser.parse_args()
 report=validate(args.case);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'output':str(args.output.resolve().relative_to(ROOT)),'cases':[{'label':c['label'],'ticks':c['ticks'],'samples':len(c['samples']),'finished':c['finished'],'last':{k:c['samples'][-1][k]for k in('counter','cell','world','state','active','pending','frame','drawn_frame','cache_cells')}}for c in report['cases']]},indent=2))
