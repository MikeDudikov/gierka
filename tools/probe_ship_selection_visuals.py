#!/usr/bin/env python3
"""Bounded native selection4e0b80/4e0d00, IL callback and source sprite buffers."""
from __future__ import annotations
import argparse,json,struct,hashlib
from pathlib import Path
if __package__:
 from . import stage_ship_pointer_visuals as art
 from . import validate_source_sprite_depth_queue as queue
else:
 import stage_ship_pointer_visuals as art
 import validate_source_sprite_depth_queue as queue
ROOT=art.ROOT;BASE=0x70000000;OBJ=BASE+0x70000;MAIN=BASE+0x71000;SEL=BASE+0x72000;APP=BASE+0x73000;SYSTEM=BASE+0x77000;NAME=BASE+0x78000;SURFACE=BASE+0x79000;BUFFER=BASE+0x7a000;ARRAY=BASE+0x7b000;RECORD=BASE+0x7c000

def native_image():
 raw=art.checked_sources()['installed/ancient.exe']
 import pefile
 p=pefile.PE(data=raw);return p,p.get_memory_mapped_image(),p.OPTIONAL_HEADER.SizeOfImage
class NativeSelection:
 def __init__(self,image,size):
  from unicorn import UC_HOOK_CODE
  self.q=queue.NativeQueue(image,size);self.u=self.q.u;self.u.hook_add(UC_HOOK_CODE,self.hook);self.drawn=-1;self.visible=False;self.health=False;self.healthx=0;self.healthy=0;self.calls=[];self.publications=[];self.deleted=False;self.hidden=False
  for a,v in ((OBJ+0x10,APP),(OBJ+0x70,SYSTEM),(OBJ+0x8be,MAIN),(OBJ+0x3e,-1),(MAIN+0x61,56),(MAIN+0x65,56),(OBJ+0x271,650),(OBJ+0x25a,0)):
   self.q.w(a,v)
  self.q.w(0x5c76b0,650) # Controlled full-health denominator; ratio exactly100.
 def r(self,a):return self.q.r(a)
 def w(self,a,v):self.q.w(a,v)
 def signed(self,a):return self.q.s(a)
 def ret(self,clean=0,value=0):
  from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_EAX
  sp=self.u.reg_read(UC_X86_REG_ESP);self.u.reg_write(UC_X86_REG_EIP,self.r(sp));self.u.reg_write(UC_X86_REG_ESP,sp+4+clean);self.u.reg_write(UC_X86_REG_EAX,value&0xffffffff)
 def hook(self,u,a,size,unused):
  from unicorn.x86_const import UC_X86_REG_ESP
  sp=u.reg_read(UC_X86_REG_ESP)
  if a==0x587318:self.ret()
  elif a in(0x556610,0x556880):raise AssertionError('Original selection error '+hex(a))
  elif a==0x50cb80:
   args=[self.r(sp+4+i*4)for i in range(7)];assert args[:4]==[4,1020,1,7];self.u.mem_write(SEL,bytes(0x100));self.w(OBJ+0x8d6,SEL);self.w(OBJ+0x48,ARRAY);self.w(ARRAY+8,16);self.w(ARRAY+12,1);self.w(ARRAY+28,RECORD);self.w(RECORD,SEL);self.w(RECORD+4,4);self.w(RECORD+8,1);self.w(SEL+4,BASE);self.w(SEL+0x41,21);self.visible=False;self.drawn=-1;self.health=False;self.ret(28)
  elif a==0x50d4f0:self.ret(4,SEL)
  elif a==0x4e0c80:
   assert [self.r(sp+4),self.r(sp+8)]==[56,56];self.u.mem_write(NAME,b'RAM_056X056\0');self.ret(8,NAME)
  elif a==0x50d010:
   args=[self.r(sp+4+i*4)for i in range(5)];assert args[:3]==[4,7,0];assert bytes(u.mem_read(args[3],11))==b'RAM_056X056';self.w(SEL+0x61,60);self.w(SEL+0x65,60);self.w(SEL+0x49,10);self.ret(20)
  elif a==0x50c890:
   args=[self.r(sp+4+i*4)for i in range(3)];assert args[0]&65535==0x6464 and args[1]&65535==60 and args[2]==1020,args;self.w(OBJ+0x3e,22);self.ret(12)
  elif a==0x55ec00:
   args=[self.r(sp+4+i*4)for i in range(5)];assert args[:2]==[BASE,21];self.drawn=args[2];self.visible=True;self.publications.append({'frame':self.drawn,'world':[args[3]if args[3]<2**31 else args[3]-2**32,args[4]if args[4]<2**31 else args[4]-2**32]});self.ret(20)
  elif a==0x50c7b0:
   self.health=True;self.healthx=(self.r(sp+4)+14)&0xffffffff;self.healthy=self.r(sp+8);self.ret(8)
  elif a==0x55ed60:self.health=False;self.hidden=True;self.ret(8)
  elif a==0x50cd40:self.visible=False;self.deleted=True;self.ret(4)
 def invoke(self,a):
  from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_ECX
  sp=queue.STACK+0x1f000;self.w(sp,queue.END);self.u.reg_write(UC_X86_REG_ESP,sp);self.u.reg_write(UC_X86_REG_ECX,OBJ);self.u.emu_start(a,queue.END,count=10000);assert self.u.reg_read(UC_X86_REG_EIP)==queue.END
 def op(self,op):
  self.publications=[];self.deleted=False;self.hidden=False
  if op[0]=='S':
   self.w(MAIN+0x59,op[1]);self.w(MAIN+0x5d,op[2])
   if not self.r(OBJ+0x8d6):self.invoke(0x4e0b80)
   self.u.mem_write(OBJ+0x252,b'\x01')
  elif op[0]=='D':
   if bytes(self.u.mem_read(OBJ+0x252,1))[0]:self.u.mem_write(OBJ+0x252,b'\x02')
  else:
   _,now,pending,x,y=op;self.w(SYSTEM+0xde,now);self.w(SYSTEM+0xe2,pending);self.w(MAIN+0x59,x);self.w(MAIN+0x5d,y)
   if self.r(OBJ+0x8d6):self.invoke(0x4e0d00)
  flag=bytes(self.u.mem_read(OBJ+0x252,1))[0];exists=bool(self.r(OBJ+0x8d6));signed=lambda v:v if v<2**31 else v-2**32
  return {'selection':flag,'exists':exists,'frame':self.signed(SEL+0x45),'drawn_frame':self.drawn,'last_counter':self.r(SEL+0x81),'visible':self.visible,'world':[self.signed(SEL+0x59),self.signed(SEL+0x5d)],'health_exists':self.r(OBJ+0x3e)!=0xffffffff,'health_visible':self.health,'health_world':[signed(self.healthx),signed(self.healthy)],'publishes':bool(self.publications),'deletes':self.deleted,'hides_health':self.hidden,'publications':self.publications}
def cases():
 result=[]
 for pending in(1,2,3,7,255):
  ops=[['S',1028,132],['A',0,pending,1028,132]]
  for i in range(1,25):ops.extend([['A',i,pending,1028+i,132+i],['A',i,pending,1050,150]])
  ops.append(['D']);ops.extend([['A',i,pending,1060,164]for i in range(25,40)]);ops.extend([['S',1100,200],['A',40,pending,1100,200]])
  result.append({'label':'pending'+str(pending),'operations':ops})
 ops=[['D'],['S',1028,132]]+[['A',i,1,1028,132]for i in range(1,11)]+[['D'],['A',11,1,1028,132],['S',1028,132]]+[['A',i,1,1028,132]for i in range(12,26)]+[['D']]+[['A',i,1,1028,132]for i in range(26,40)]
 result.append({'label':'reselect-during-reverse','operations':ops})
 result.append({'label':'counter-wrap-and-int-coordinate-stress','operations':[['S',-2147483648,2147483647]]+[['A',n,3,-2147483648,2147483647]for n in(0xfffffffe,0xffffffff,0,0,1,2,3)]+[['D']]+[['A',n,3,-2147483648,2147483647]for n in range(4,18)]})
 return result
def native_fixture():
 _,image,size=native_image();rows=[]
 for c in cases():
  n=NativeSelection(image,size);rows.append(dict(c,rows=[n.op(op)for op in c['operations']]))
 return {'schema_version':1,'original_exe_sha256':art.SOURCE_HASHES['installed/ancient.exe'],'native_entries':['0x4e0b80','0x4e0d00','0x4e0cb0','0x50d5f0'],'cases':rows,'boundaries':['setjmp normalreturn','spritecollection allocation/resource loading withsourceRAM_056X056 dimensions60x60','renderer55ec00 boundary recordsframe/world beforestoredadvance;actualGameObjsetterexecutes','IL drawing/deletion boundaries','name formatter56x56 fixed reference'],'scope':'Healthy0b selectionstate andsprite-publication transaction; no fullrenderer/actorLife/OSinput'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();d=native_fixture();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n');print('native selection snapshots',sum(len(c['rows'])for c in d['cases']))
if __name__=='__main__':main()
