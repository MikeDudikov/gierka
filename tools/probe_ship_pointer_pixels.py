#!/usr/bin/env python3
"""Original RLE/IL line pixels and overlay-cohort creation/order evidence."""
from __future__ import annotations
import argparse,json,struct,hashlib
from pathlib import Path
if __package__:
 from . import probe_ship_selection_visuals as v
 from . import validate_source_sprite_depth_queue as q
 from .inspect_dkx import inspect_pair
 from .decode_sprite import resource_payload,decode_sprite,dib_palette
else:
 import probe_ship_selection_visuals as v
 import validate_source_sprite_depth_queue as q
 from inspect_dkx import inspect_pair
 from decode_sprite import resource_payload,decode_sprite,dib_palette
ROOT=v.ROOT;digest=lambda b:hashlib.sha256(b).hexdigest()
def rle():
 from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
 from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_EFLAGS
 _,image,size=v.native_image();u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,(size+4095)&~4095);u.mem_write(0x400000,image);u.mem_map(v.BASE,0x100000);u.mem_map(q.STACK,0x20000);sources=v.art.checked_sources();records=[]
 for key,name,archive,count,_,_ in v.art.SEQUENCES:
  base='files/DATA/OBJECTS'if archive=='objects'else'installed/missions/controlm';ix='.DKX'if archive=='objects'else'.dkx';dt='.DKD'if archive=='objects'else'.dkd';data=sources[base+dt];lut={(e['type'],e['name']):e for e in inspect_pair(sources[base+ix],data)}
  for index in range(count):
   n=name+f'{index:02d}';raw=resource_payload(lut[6,n],data);s=decode_sprite(raw);u.mem_write(v.BASE,raw);left,top,w,h=[s[k]for k in('left','top','box_width','box_height')];cases=[]
   rects=[(0,0,w,h)]+([(1,1,w-2,h-2)]if w>2 and h>2 else[])+([(1,17,w-2,h-18)]if w>2 and h>18 else[])
   for sx,sy,dw,dh in rects:
    for sentinel in(0x55,0xaa):
     dest=v.BASE+0x10000;pitch=96;guard=256;total=guard+96*pitch+guard;wanted=bytearray([sentinel])*total;offset=guard+(top+sy)*pitch+left+sx
     for y in range(dh):
      for x in range(dw):
       i=(top+sy+y)*s['width']+left+sx+x
       if s['coverage'][i]:wanted[offset+y*pitch+x]=s['indices'][i]
     u.mem_write(dest,bytes([sentinel])*total);sp=q.STACK+0x1f000;u.mem_write(sp,struct.pack('<13I',q.END,dest+offset,pitch,v.BASE,sx,sy,dw,dh,0,0,0,0,0));u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_EFLAGS,0x202);u.emu_start(0x574290,q.END,count=1000000);assert u.reg_read(UC_X86_REG_EIP)==q.END;actual=bytes(u.mem_read(dest,total));assert actual==wanted,(n,sx,sy,sentinel);cases.append({'rectangle':[sx,sy,dw,dh],'sentinel':sentinel,'destination_sha256':digest(actual)})
   records.append({'name':n,'payload_sha256':digest(raw),'cases':cases})
 return {'frames':len(records),'comparisons':sum(len(r['cases'])for r in records),'entry':'0x574290','hooks':[],'records':records}
def health():
 from unicorn import UC_HOOK_CODE
 from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_EAX
 _,image,size=v.native_image();n=q.NativeQueue(image,size);u=n.u;u.mem_map(0,4096);canvas=v.BUFFER;surface=v.SURFACE;calls=[]
 def ret(clean=0):
  sp=u.reg_read(UC_X86_REG_ESP);u.reg_write(UC_X86_REG_EIP,n.r(sp));u.reg_write(UC_X86_REG_ESP,sp+4+clean);u.reg_write(UC_X86_REG_EAX,0)
 def hook(u,a,z,k):
  sp=u.reg_read(UC_X86_REG_ESP)
  if a==0x587318:ret()
  elif a in(0x556610,0x556880,0x5565f0):raise AssertionError('Health source error')
  elif a in(0x567d20,0x567de0):ret(4)
  elif a==0x567850:
   args=[n.r(sp+4+i*4)for i in range(6)];assert args[0]==surface;_,x,y,w,h,color=args;calls.append(args)
   for row in range(h):u.mem_write(canvas+(y+row)*64+x,bytes([color&255])*w)
   ret(24)
 u.hook_add(UC_HOOK_CODE,hook)
 for a,value in((v.OBJ+0x10,v.APP),(v.APP+0xd9d,surface),(surface+0x20,8),(surface+0x70,canvas),(surface+0x74,64),(surface+0x88,64),(surface+0x8c,16),(surface+0x9c,0xffffffff)):
  n.w(a,value)
 raw=v.art.checked_sources();data=raw['installed/missions/maplib.dkd'];lut={(e['type'],e['name']):e for e in inspect_pair(raw['installed/missions/maplib.dkx'],data)};palette=dib_palette(resource_payload(lut[1,'PALETTE'],data));plane=v.art.healthbar_plane(palette);wanted=plane.tobytes();records=[]
 for sentinel in(0x55,0xaa):
  u.mem_write(canvas,bytes([sentinel])*(64*16));u.mem_write(v.OBJ+0x42,struct.pack('<HHH',0x6464,34,0));sp=q.STACK+0x1f000;u.mem_write(sp,struct.pack('<9I',q.END,0,0,0,5,3,0,0,v.OBJ));u.reg_write(UC_X86_REG_ESP,sp);u.emu_start(0x50c650,q.END,count=100000);assert u.reg_read(UC_X86_REG_EIP)==q.END
  result=bytes(u.mem_read(canvas,64*16));rgba=bytearray()
  for y in range(4):
   for x in range(34):
    index=result[(y+3)*64+x+5];rgba.extend((*palette[index*3:index*3+3],255)if index!=sentinel else(0,0,0,0))
  assert bytes(rgba)==wanted;records.append({'sentinel':sentinel,'buffer_sha256':digest(result),'rgba_sha256':digest(rgba),'last_packed_health':struct.unpack('<H',u.mem_read(v.OBJ+0x46,2))[0]})
 return {'width':34,'height':4,'health_percent':100,'rgba_sha256':digest(wanted),'entry':'0x50c650','line_entries':['0x56ea10','0x56f100'],'external_boundaries':['normalsetjmp','DirectDraw solidrectanglefill567850','surface lock/unlock567d20/567de0'],'rectangles':calls,'records':records}
def cohort():
 image,size=q.checked_image();n=q.NativeQueue(image,size)
 for row in q.cohort_registration():n.register(row['depth'])
 n.call(0x55db10,(q.M,q.OUT,1020,0,0,0x8000000,0xffffffff,0xffffffff,0));selector=n.r(q.OUT);snode=n.r(q.IDS+selector*4)
 n.call(0x55dc20,(q.M,q.OUT,1020,0x50c650,34,4,v.OBJ));health=n.r(q.OUT);hnode=n.r(q.IDS+health*4);n.call(0x55e080,(q.M,health,0))
 def state(label):
  asc=[n.r(n.r(q.ORDER+4*i)+0x40)for i in range(n.r(q.M+0x1a0))];return {'label':label,'draw_order':asc[::-1],'selector_flags':hex(n.r(snode)),'health_flags':hex(n.r(hnode))}
 rows=[state('created-health-hidden')];n.call(0x55e080,(q.M,health,1));rows.append(state('health-enabled'));n.call(0x55ed60,(q.M,health));rows.append(state('health-deleted'));n.call(0x55ed60,(q.M,selector));rows.append(state('selector-deleted'))
 assert rows[0]['draw_order'][-2:]==[health,selector]
 return {'selector_node':selector,'health_node':health,'depth':1020,'registration_order':['selector','health'],'visible_layer_order':['base34renderers','health','selector'],'node_entries':['0x55db10','0x55dc20','0x55e080','0x55ed60'],'hooks':[],'states':rows}
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();d={'passed':True,'original_exe_sha256':v.art.SOURCE_HASHES['installed/ancient.exe'],'rle':rle(),'health':health(),'cohort':cohort()};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n');print('RLE',d['rle']['frames'],d['rle']['comparisons'],'health',len(d['health']['records']),'cohort',d['cohort']['selector_node'],d['cohort']['health_node'])
if __name__=='__main__':main()
