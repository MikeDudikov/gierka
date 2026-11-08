#!/usr/bin/env python3
"""Execute source49a580 normal-ship queries, observing real predicate entries.
No source code, registers or returns are intercepted by the observational hook.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path
try:from . import validate_boss_ai_gate as gate
except ImportError:import validate_boss_ai_gate as gate
ROOT=gate.ROOT
BASE=0x70000000;DUMP=BASE;GRID=BASE+0x10000;APP=BASE+0x20000;END=BASE+0x7f0000;STACK=0x7ff00000

class NativeShipWorldPicker:
 def __init__(self,original=gate.ORIGINAL):
  self.original=Path(original)
  if not self.original.is_file():raise gate.MissingPrerequisite('Optional original executable unavailable')
  raw=self.original.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=gate.EXPECTED:raise ValueError('Original executable SHA256 differs')
  import pefile
  from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
  from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_ESP
  self.pe=pefile.PE(data=raw);image=self.pe.get_memory_mapped_image();self.u=Uc(UC_ARCH_X86,UC_MODE_32)
  self.u.mem_map(0x400000,(self.pe.OPTIONAL_HEADER.SizeOfImage+4095)&~4095);self.u.mem_write(0x400000,image);self.u.mem_map(BASE,0x800000);self.u.mem_map(STACK,0x100000)
  self.actors={};self.claims={};self.mask_cache={};self.mask_next=BASE+0x500000;self.calls=[]
  self.invoke(0x499530);self.put(DUMP+0x10,APP)
  for entry in (0x499ff0,0x499e00,0x499f00):self.invoke(entry,(24,))
  self.put(0x5c74ec,24);self.put(0x5c74f0,24);self.put(0x5c74fc,GRID);self.put(0x5ca546,0)
  self.u.mem_write(GRID,struct.pack('<4h',24,24,64,64));self.u.mem_write(APP+0x3212,b'\x01\x01')
  self.counts=[self.get(DUMP+0x18+4*i)for i in range(9)]
  self.offsets=[[self.signed(DUMP+0x3c+32*k+4*j)for j in range(self.counts[k])]for k in range(9)]
  def observe(uc,address,size,unused):
   actor=uc.reg_read(UC_X86_REG_ECX);sp=uc.reg_read(UC_X86_REG_ESP)
   self.calls.append({'owner_id':self.get(actor+0x4c),'args':[self.get(sp+4*i)for i in range(1,6)]})
  self.u.hook_add(UC_HOOK_CODE,observe,begin=0x4e06c0,end=0x4e06c0)
 def put(self,a,v):self.u.mem_write(a,struct.pack('<I',v&0xffffffff))
 def get(self,a):return struct.unpack('<I',self.u.mem_read(a,4))[0]
 def signed(self,a):return struct.unpack('<i',self.u.mem_read(a,4))[0]
 def invoke(self,entry,args=(),this=DUMP):
  from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP
  sp=STACK+0xff000
  for i,v in enumerate((END,*args)):self.put(sp+4*i,v)
  self.u.reg_write(UC_X86_REG_ESP,sp);self.u.reg_write(UC_X86_REG_ECX,this);self.u.emu_start(entry,END,count=50000)
  if self.u.reg_read(UC_X86_REG_EIP)!=END:raise AssertionError('Native picker entry did not return '+hex(entry))
  return self.u.reg_read(UC_X86_REG_EAX)
 def set_actor(self,instance_id,published_world,stored_frame,heading,mask_family,runtime_class_tag=200):
  if not(0<=instance_id<=0xffffffff and 200<=runtime_class_tag<=211):raise ValueError('Normal source ship ID/class required')
  if instance_id not in self.actors:
   if len(self.actors)>=576:raise ValueError('Native actor capacity exceeded')
   self.actors[instance_id]=BASE+0x100000+len(self.actors)*0x1000
  a=self.actors[instance_id];sprite=a+0x900;planes=mask_family['planes'];width=mask_family['width'];height=mask_family['height'];raw=b''.join(planes)
  if len(planes)!=24 or any(len(p)!=(width+7)//8*height for p in planes):raise ValueError('Invalid native mask planes')
  key=(width,height,hashlib.sha256(raw).hexdigest())
  if key not in self.mask_cache:
   desc=self.mask_next;data=desc+0x100;end=data+len(raw)
   if end>=BASE+0x7e0000:raise ValueError('Native mask memory capacity exceeded')
   self.u.mem_write(desc+0x23,struct.pack('<h',24))
   for i,p in enumerate(planes):self.put(desc+0x30+4*i,data+i*len(p))
   self.u.mem_write(data,raw);self.mask_cache[key]=desc;self.mask_next=(end+255)&~255
  self.put(a,0x59b48c);self.put(a+0x4c,instance_id);self.put(a+0x50,runtime_class_tag);self.u.mem_write(a+0x57,b'\x01');self.u.mem_write(a+0x5af,bytes([heading&255]));self.put(a+0x8be,sprite);self.put(a+0x8e2,self.mask_cache[key])
  for off,v in ((0x45,stored_frame),(0x59,published_world[0]),(0x5d,published_world[1]),(0x61,width),(0x65,height)):self.put(sprite+off,v)
 def set_claims(self,claims):
  for index in self.claims:self.put(GRID+8+24*index+4,0)
  self.claims=dict(claims)
  for index,instance_id in self.claims.items():
   if not(0<=index<576)or instance_id not in self.actors:raise ValueError('Invalid source occupant claim')
   self.put(GRID+8+24*index+4,self.actors[instance_id])
 def query(self,world_x,world_y,cell_x,cell_y,precise):
  if not(0<=cell_x<24 and 0<=cell_y<24):raise ValueError('Valid source query cell required')
  self.calls=[];ptr=self.invoke(0x49a580,(world_x,world_y,cell_x,cell_y,int(bool(precise))))
  return {'hit_id':None if ptr==0 else self.get(ptr+0x4c),'visits':[x['owner_id']for x in self.calls],'calls':[dict(x)for x in self.calls]}

def original_cases(original=gate.ORIGINAL):
 n=NativeShipWorldPicker(original);family={'width':56,'height':56,'planes':[b'\xff'*392]*24}
 for i in range(576):n.set_actor(i,(10000,10000),20,5,family)
 claims={i:i for i in range(576)};n.set_claims(claims);cases=[]
 def row(label,x,y,precise,hit_ids=(),aliases=None):
  world=(x*64+32,y*64+32)
  for i in hit_ids:n.set_actor(i,(world[0]-1,world[1]-1),20,5,family)
  if aliases:n.set_claims(dict(claims,**{})|aliases)
  actual=n.query(*world,x,y,precise)
  cases.append({'label':label,'world':list(world),'cell':[x,y],'precise':precise,'hit_ids':list(hit_ids),'aliases':[[k,v]for k,v in (aliases or {}).items()],**actual})
  for i in hit_ids:n.set_actor(i,(10000,10000),20,5,family)
  if aliases:n.set_claims(claims)
 for y in range(24):
  for x in range(24):
   i=y*24+x;row('coarse-'+str(i),x,y,False);row('precise-'+str(i),x,y,True)
   kind=n.invoke(0x49a1d0,(i,));gate.require(cases[-2]['hit_id']==i and cases[-2]['visits']==[i],'Native coarse changed')
   gate.require(cases[-1]['hit_id']is None and cases[-1]['visits']==[i]+[i+d for d in n.offsets[kind-1]],'Native precise order changed')
 for k,(x,y)in enumerate(((0,0),(23,0),(23,23),(0,23),(12,0),(23,12),(12,23),(0,12),(12,12))):
  index=y*24+x;kind=n.invoke(0x49a1d0,(index,));order=[index]+[index+d for d in n.offsets[kind-1]]
  for pos,target in enumerate(order):
   row('first-hit-'+str(k)+'-'+str(pos),x,y,True,(target,));gate.require(cases[-1]['hit_id']==target and cases[-1]['visits']==order[:pos+1],'Native first-hit changed')
 index=300;row('duplicate-owner',12,12,True,aliases={275:index});gate.require(cases[-1]['visits'][:2]==[index,index],'Native owner was deduplicated')
 order=[index]+[index+d for d in n.offsets[8]]
 for first,second in((0,1),(1,2),(2,8),(4,7)):
  row('overlap-'+str(first)+'-'+str(second),12,12,True,(order[first],order[second]));gate.require(cases[-1]['hit_id']==order[first],'Native overlap priority changed')
 gate.require(hashlib.sha256(Path(original).read_bytes()).hexdigest()==gate.EXPECTED,'Original changed during native query')
 return {'schema_version':1,'original_exe_sha256':gate.EXPECTED,'native_oracle_sha256':gate.digest(Path(__file__)),'query_count':len(cases),'grid':[24,24],'counts':n.counts,'offsets':n.offsets,'mask':{'width':56,'height':56,'planes':24,'fill':255},'cases':cases,'intercepted_callees':[],'observational_hook':'4e06c0entryreadsonly','scope':'Normalclass200 ship-only query order with controlled noFog and other object slots empty; synthetic allone masks','excluded':['Full fog/other object slots/classes/mission lifecycle','Original mask shapes (separatelyvalidated)','Unity/renderer/OS input']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args();d=original_cases();args.output.parent.mkdir(parents=True,exist_ok=True)
 with args.output.open('x')as f:f.write(json.dumps(d,indent=2)+'\n')
 print(json.dumps({'query_count':d['query_count'],'passed':True}))
if __name__=='__main__':main()
