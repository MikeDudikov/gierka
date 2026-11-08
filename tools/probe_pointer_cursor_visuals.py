#!/usr/bin/env python3
"""Actual cursorSetGCType/DrawSprite/CreateConfirm with original sprite transactions."""
from __future__ import annotations
import argparse,json,struct
from pathlib import Path
if __package__:
 from . import probe_ship_selection_visuals as visual
 from . import validate_source_sprite_depth_queue as queue
 from .inspect_dkx import inspect_pair
 from .decode_sprite import resource_payload,decode_sprite
else:
 import probe_ship_selection_visuals as visual
 import validate_source_sprite_depth_queue as queue
 from inspect_dkx import inspect_pair
 from decode_sprite import resource_payload,decode_sprite
ROOT=visual.ROOT;CUR=visual.OBJ;APP=visual.APP;LIB=0x12345678
class NativeCursor:
 def __init__(self,image,size):
  from unicorn import UC_HOOK_CODE
  self.q=queue.NativeQueue(image,size);self.u=self.q.u;self.u.mem_map(0,4096);self.u.hook_add(UC_HOOK_CODE,self.hook);self.now=0;self.draws=[];self.deletes=False;self.confirm_drawn=-1;self.heap=visual.BASE+0x7d000;self.confirm_cache={'frame':0,'world':[0,0],'stamp':0}
  self.descriptors={};self.resources=[];src=visual.art.checked_sources();data=src['installed/missions/controlm.dkd'];lut={(e['type'],e['name']):e for e in inspect_pair(src['installed/missions/controlm.dkx'],data)};dest=visual.BASE+0x80000
  for _,name,archive,count,_,_ in (*visual.art.SEQUENCES,('menu','MENU_CUR','control',1,500,'source-cached-ms')):
   if archive!='control':continue
   animation=resource_payload(lut[7,name],data);prefix=animation[:32].split(b'\0')[0].decode('ascii')
   desc=dest;dest+=0x100;w=h=None
   self.u.mem_write(desc,bytes(0x100));self.u.mem_write(desc+0x23,struct.pack('<h',count))
   for i in range(count):
    raw=resource_payload(lut[6,prefix+f'{i:02d}'],data);s=decode_sprite(raw);w,h=s['width'],s['height'];self.u.mem_write(dest,raw);self.w(desc+0x2d+4*i,dest);dest+=(len(raw)+15)&~15
   self.u.mem_write(desc+0x29,struct.pack('<hh',w,h));self.descriptors[name]=desc
  self.w(CUR+0x10,APP);self.w(CUR+0xa9,APP);self.w(APP+0xda5,queue.M);self.w(APP+0xd5c,LIB);self.w(CUR+0xbd,1);self.u.mem_write(CUR+0x101,b'\xff\xff')
  self.invoke(0x545e00,(),CUR+0x18);self.invoke(0x515c50)
  # Ready gameplay cursor precondition: its UI activation has already shown
  # the initial standard cursor. DrawSprite's55ea00 gate requires this flag.
  self.q.call(0x55eb50,(queue.M,self.r(CUR+0x59),0,0,0))
 def w(self,a,v):self.q.w(a,v)
 def r(self,a):return self.q.r(a)
 def s(self,a):return self.q.s(a)
 def cstr(self,a):
  b=bytearray()
  while True:
   c=bytes(self.u.mem_read(a+len(b),1))
   if c==b'\0':return b.decode('ascii')
   b.extend(c)
 def ret(self,clean=0,value=0):
  from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_EAX
  sp=self.u.reg_read(UC_X86_REG_ESP);self.u.reg_write(UC_X86_REG_EIP,self.r(sp));self.u.reg_write(UC_X86_REG_ESP,sp+4+clean);self.u.reg_write(UC_X86_REG_EAX,value&0xffffffff)
 def hook(self,u,a,size,unused):
  from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX
  sp=u.reg_read(UC_X86_REG_ESP)
  if a==0x587318:self.ret()
  elif a in(0x556610,0x556880):raise AssertionError('Native cursor error '+hex(a))
  elif a==0x5428d0:
   args=[self.r(sp+4+i*4)for i in range(8)];name=self.cstr(args[2]);assert args[0]==LIB and args[1]==7,args;self.resources.append(name);self.ret(value=self.descriptors[name])
  elif a==0x58739e:
   assert self.r(sp+4)==0x91;self.heap+=0x100;self.ret(value=self.heap)
  elif a==0x587393:self.ret()
  elif a==0x546050:
   if u.reg_read(UC_X86_REG_ECX)==self.r(CUR+0xf1):
    self.deletes=True;c=self.r(CUR+0xf1);self.confirm_cache={'frame':self.s(c+0x45),'world':[self.s(c+0x59),self.s(c+0x5d)],'stamp':self.r(c+0x81)}
  elif a==0x55eb50:
   args=[self.r(sp+4+i*4)for i in range(5)];self.draws.append({'node':args[1],'frame_argument':args[2]if args[2]<2**31 else args[2]-2**32,'position':[args[3]if args[3]<2**31 else args[3]-2**32,args[4]if args[4]<2**31 else args[4]-2**32]})
 def invoke(self,a,args=(),this=CUR):
  from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_ECX
  sp=queue.STACK+0x1f000
  for i,v in enumerate((queue.END,*args)):self.w(sp+i*4,v)
  self.u.reg_write(UC_X86_REG_ESP,sp);self.u.reg_write(UC_X86_REG_ECX,this);self.u.emu_start(a,queue.END,count=100000);assert self.u.reg_read(UC_X86_REG_EIP)==queue.END
 def op(self,op):
  self.draws=[];self.resources=[];self.deletes=False
  if op[0]=='S':
   _,typ,green,now,x,y=op;self.now=now;self.w(APP+0x18,now);self.w(CUR+0xe6,int(green));self.invoke(0x516e30,(typ,x,y))
  elif op[0]=='C':
   _,x,y=op;self.w(CUR+0xc1,x);self.w(CUR+0xc5,y);self.invoke(0x515df0);self.confirm_drawn=-1
  else:
   _,now,x,y=op;self.now=now;self.w(APP+0x18,now);self.invoke(0x516640,(x,y))
  node=self.r(queue.IDS+4*self.r(CUR+0x59));con=self.r(CUR+0xf1);cnode=self.r(queue.IDS+4*self.r(con+0x41))if con else None
  if cnode and self.r(cnode)&0x20:self.confirm_drawn=self.s(cnode+0xc4)
  if con:self.confirm_cache={'frame':self.s(con+0x45),'world':[self.s(con+0x59),self.s(con+0x5d)],'stamp':self.r(con+0x81)}
  return {'type':struct.unpack('<h',self.u.mem_read(CUR+0x101,2))[0],'green':bool(self.r(CUR+0xe6)),'frame':self.s(node+0xc4),'screen':[self.s(CUR+0x71),self.s(CUR+0x75)],'visible':bool(self.r(node)&0x20),'draw_position':[self.s(node+0x18),self.s(node+0x1c)],'last_tick':self.r(CUR+0x99),'interval':self.r(CUR+0x95),'confirm_exists':bool(con),'confirm_frame':self.confirm_cache['frame'],'confirm_drawn':self.confirm_drawn,'confirm_visible':bool(cnode and self.r(cnode)&0x20),'confirm_world':self.confirm_cache['world'],'confirm_last_tick':self.confirm_cache['stamp'],'cursor_publishes':any(d['node']==self.r(CUR+0x59)for d in self.draws),'confirm_publishes':bool(con and any(d['node']==self.r(con+0x41)for d in self.draws)),'deletes_confirm':self.deletes,'resources':self.resources,'draws':self.draws}
def cases():
 ops=[['S',0,False,0,100,100],['S',5,False,0,100,100],['S',6,False,0,100,100],['S',7,False,0,200,200],['C',1184,352]]
 ops.extend([['D',t,-1,-1]for t in(0,149,150,249,250,300,499,500,600,749,750,751,900,901,10000,10001)])
 ops.extend([['S',0,False,10001,100,100],['S',7,False,20001,200,200],['C',1024,256],['D',20001,-1,-1],['C',1280,384],['D',20251,500,500],['D',20501,-1,-1],['D',20751,-1,-1],['D',20752,-1,-1]])
 a={'label':'normal-transitions-and-confirms','operations':ops}
 ops=[['S',0,False,0,1,1]]
 for typ in(5,6,7,0):
  for green in(False,True):ops.extend([['S',typ,green,12345,23,45],['D',12345,-1,-1],['D',12495,-1,-1]])
 b={'label':'suffix-and-typechanges','operations':ops}
 c={'label':'unsigned-clock-wrap','operations':[['S',7,False,0xfffffffe,1,1],['C',1024,256]]+[['D',n,-1,-1]for n in(0xfffffffe,0xffffffff,0,1,2,149,150,249,250,251,500)]}
 initial=[{'label':'initial-sea-old500-'+str(t),'operations':[['S',7,False,t,20,30],['D',t,-1,-1],['D',t+150,-1,-1],['C',1024,256],['D',t+250,-1,-1]]}for t in(0,499,500,10000)]
 move={'label':'global-move-typechange-two-draw-boundary','operations':[
  ['S',7,False,0,100,100],['C',1184,352],['D',250,-1,-1],['D',500,-1,-1],
  ['S',5,False,750,100,100],['D',750,120,140]]}
 return[a,b,c,*initial,move]
def fixture():
 _,image,size=visual.native_image();rows=[]
 for c in cases():
  n=NativeCursor(image,size);rows.append(dict(c,rows=[n.op(op)for op in c['operations']]))
 return {'schema_version':1,'original_exe_sha256':visual.art.SOURCE_HASHES['installed/ancient.exe'],'cases':rows,'native_entries':['0x515c50','0x516e30','0x516640','0x515df0','0x545e00','0x545e80','0x546160','0x55e0e0','0x55eb50','0x546050','0x55ed60','0x5417d0'],'boundaries':['normal setjmp','resource-loader returnschecked source type7 framepointer tables','operatornew/delete arena'],'precondition':'Ready gameplay cursor: source Init515c50 loadsMENU_CUR/interval500; callerUIactivation has shownnode before SetGCType. Explicit cachedapp+18 millis input, actual5417d0readexecutes.','scope':'Normalmap1 cursors0/5/6/7 and TAKE_CMD sprite transactions; noOSinput/screenblitter/fullworld'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();d=fixture();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n');print('Native cursor snapshots',sum(len(c['rows'])for c in d['cases']))
if __name__=='__main__':main()
