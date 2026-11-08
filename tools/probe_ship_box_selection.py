"""Actual49c3f0/49c520, normal517b90 and rectangle56ff10 source transactions."""
from pathlib import Path
import json,struct,argparse,hashlib
from tools import probe_ship_world_picker as pick,probe_ship_pointer_commands as command
from tools.probe_ship_pointer_hover import source_metadata
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_EAX,UC_X86_REG_ECX
ROOT=pick.ROOT;RECT=pick.BASE+0x60000;FLEET=pick.BASE+0x70000
class BoxOracle(command.PointerOracle):
 def __init__(self):
  self.visits=[];super().__init__();self.actors={};self.claims={}
  template=bytes(self.u.mem_read(command.motion.OBJ,0xa00))
  for i,r in enumerate(source_metadata()):
   actor=command.motion.OBJ if r['id']==11 else command.BASE+0x60000+i*0x1000
   self.u.mem_write(actor,template);self.actors[r['id']]=actor
   for off,v in((0x4c,r['id']),(0x50,r['class']),(0x5ab,-1)):self.w(actor+off,v)
   self.u.mem_write(actor+0x54,bytes([r['side'],r['player']]))
  self.set_claims({r['cell'][1]*24+r['cell'][0]:r['id']for r in source_metadata()})
 def hook(self,u,a,size,unused):
  if self.pointer_ready and a==0x49c2f0:
   sp=u.reg_read(UC_X86_REG_ESP);self.visits.append(self.r(self.r(sp+8)+0x4c))
  super().hook(u,a,size,unused)
 def set_claims(self,claims):
  for i in range(576):self.w(command.motion.GRID+8+i*24+4,0)
  self.claims=dict(claims)
  for i,identifier in self.claims.items():self.w(command.motion.GRID+8+i*24+4,self.actors[identifier])
 def call(self,a,args):
  self.invoke_cursor(a,args) if a==0x517b90 else self.invoke_fleet(a,args)
  return self.u.reg_read(UC_X86_REG_EAX)
 def invoke_fleet(self,a,args):
  sp=command.motion.S.STACK+command.motion.S.STACK_SIZE-0x1000
  for i,v in enumerate((command.motion.S.END,*args)):self.w(sp+4*i,v)
  self.u.reg_write(UC_X86_REG_ESP,sp);self.u.reg_write(UC_X86_REG_ECX,command.FLEET)
  self.u.emu_start(a,command.motion.S.END,count=500000)
  assert self.u.reg_read(UC_X86_REG_EIP)==command.motion.S.END
 def query(self,rect,owner=5,reserved=-1,claims=None):
  self.w(self.actors[11]+0x5ab,reserved)
  if claims is not None:self.set_claims(claims)
  address=command.BASE+0x58000;self.u.mem_write(address,struct.pack('<4i',*rect));self.visits=[]
  self.w(command.SELECTED+12,0)
  # Each tested owner gets the same isolated temporary vector; the original
  # predicate still compares actual side*4+player before the actual Add function.
  self.w(command.FLEET+0x72+owner*4,command.SELECTED)
  has=bool(self.call(0x49c3f0,(owner,address)))
  count=self.call(0x49c520,(owner,address))
  n=self.r(command.SELECTED+12);data=self.r(command.SELECTED+28)
  members=[self.r(self.r(data+4*i)+0x4c)for i in range(n)]
  assert count==n and has==bool(n)
  return {'has_any':has,'count':count,'members':members,'add_visits':self.visits.copy()}

class PolicyOracle(command.PointerOracle):
 def __init__(self,selection):self.selection_calls=[];super().__init__(selection);self.selection_calls=[]
 def hook(self,u,a,size,unused):
  if self.pointer_ready and a==0x4dc630:
   msg=self.r(u.reg_read(UC_X86_REG_ESP)+4)
   if self.r(msg+0x10)==0xc453:self.selection_calls.append(self.r(msg+0x14))
  super().hook(u,a,size,unused)
def policy_cases():
 rows=[]
 for selection in('none','pending','group'):
  for kind in(0,5,6,7):
   for flags in(0,4,8,12):
    for rect in((16,2,1,1),(15,1,3,3),(0,0,2,2)):
     o=PolicyOracle(selection);o.observe(kind,False,18,5)
     for i in range(576):o.w(command.motion.GRID+8+24*i+4,0)
     o.w(command.motion.GRID+8+24*64+4,command.motion.OBJ)
     o.u.mem_write(command.motion.OBJ+0x54,b'\x01\x01');o.w(command.motion.OBJ+0x5ab,-1)
     o.commands.clear();o.envelopes.clear();before=o.snapshot();o.invoke_cursor(0x517b90,(flags,*rect));after=o.snapshot()
     rows.append({'initial':selection,'kind':kind,'flags':flags,'rect':list(rect),'before':before,'after':after,'selection_calls':o.selection_calls.copy()})
 return rows

def raster_cases():
 n=pick.NativeShipWorldPicker();n.u.mem_map(0,4096)
 surface=pick.BASE+0x30000;buffer=pick.BASE+0x40000;map_object=pick.BASE+0x60000
 for off,v in((0x20,8),(0x24,1),(0x70,buffer),(0x74,64),(0x80,0),(0x84,0),(0x88,64),(0x8c,64)):n.put(surface+off,v)
 def boundary(u,a,size,unused):
  if a in(0x542530,0x567d20,0x567de0):
   sp=u.reg_read(UC_X86_REG_ESP);u.reg_write(UC_X86_REG_EIP,n.get(sp));u.reg_write(UC_X86_REG_ESP,sp+(4 if a==0x542530 else 8));u.reg_write(UC_X86_REG_EAX,0)
 n.u.hook_add(UC_HOOK_CODE,boundary)
 n.invoke(0x5195c0,(),map_object)
 tables={str(t):bytes(n.u.mem_read(map_object+off,32*28)).hex()for t,off in((1,0x48d),(2,0x80d))}
 rows=[]
 for thickness,off in((1,0x48d),(2,0x80d)):
  for phase in range(32):
   for width,height in((20,20),(-11,20),(20,-11),(-11,-11),(0,0),(1,1),(10,3),(64,1),(80,80),(-70,-35)):
    for x,y in((10,10),(0,0),(60,60)):
     n.u.mem_write(buffer,b'\x11'*4096)
     n.invoke(0x56ff10,(surface,0,phase,x,y,width,height,map_object+off))
     pixels=bytes(n.u.mem_read(buffer,4096));assert set(pixels)<={17,201}
     bits=bytearray(512)
     for i,v in enumerate(pixels):
      if v==201:bits[i//8]|=128>>(i%8)
     rows.append({'x':x,'y':y,'width':width,'height':height,'phase':phase,'thickness':thickness,'bitmap_hex':bits.hex()})
 return {'tables':tables,'cases':rows,'boundaries':['baseobject constructor','surface lock/unlock return success for owned8-bit RAM buffer'],'entries':['0x5195c0','0x56ff10','0x56ea10','actual8bit span writers'],'background_index':17,'ink_index':201}

def fixture():
 o=BoxOracle();cases=[];claims=o.claims.copy()
 for owner in(0,5,16):
  for y in range(24):
   for x in range(24):
    rect=[x,y,1,1];cases.append({'rect':rect,'owner':owner,'reserved':-1,'result':o.query(rect,owner)})
 for rect in([0,0,24,24],[15,1,8,6],[16,2,1,1],[18,5,1,1],[16,2,3,4],[0,0,1,24],[23,0,1,24]):
  cases.append({'rect':rect,'owner':5,'reserved':-1,'result':o.query(rect)})
 for reserved in(64,89,138):
  combined=claims|{reserved:11};o.set_claims(combined)
  for rect in([0,0,24,24],[reserved%24,reserved//24,1,1],[16,2,1,1]):
   cases.append({'rect':rect,'owner':5,'reserved':reserved,'claims':[[i,v]for i,v in combined.items()],'result':o.query(rect,5,reserved)})
 o.set_claims(claims)
 # Abnormal duplicate non-reservation claims are de-duplicated by the real
 # AddObjToTmpFleet boundary in this projection, not by grid scan.
 combined=claims|{65:11,66:11};cases.append({'rect':[16,2,3,1],'owner':5,'reserved':-1,'claims':list(map(list,combined.items())),'result':o.query([16,2,3,1],5,-1,combined)})
 return {'schema_version':1,'original_exe_sha256':pick.gate.EXPECTED,'actors':source_metadata(),'claims':list(map(list,claims.items())),'queries':cases,'policies':policy_cases(),'raster':raster_cases(),'boundaries':['49c3f0/49c520/49c2f0 plus real vector uniqueness execute original instructions;observer records candidate visits only','normal517b90 uses actualFleet/ShipGetMessage with renderer and disabled audio boundaries from existing pointer oracle'],'scope':'Normalships200..211,valid24x24 cellrectangles;owner slot,skipreserved;single0b policy;no buildings/fullfleet'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();d=fixture();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+'\n');print({'queries':len(d['queries']),'policies':len(d['policies'])})
if __name__=='__main__':main()
