"""Original single-source0b cursor release, selection, fleet and command trace.

Hover fields are explicit upstream inputs. The source actors, release handler,
fleet selection/temporarygroup conversion and serializer execute original x86.
"""
from pathlib import Path
import hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT)not in sys.path:sys.path.insert(0,str(ROOT))
from tools import probe_ship_move_order as motion
from tools import validate_boss_ai_gate as gate
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_EIP,UC_X86_REG_ESP
BASE=0x72000000
CUR=BASE+0x1000;FLEET=BASE+0x10000;SCENE=BASE+0x20000;VIEW=BASE+0x30000
GROUPS=BASE+0x40000;GROUP_DATA=BASE+0x41000;SELECTED=BASE+0x42000;SELECTED_DATA=BASE+0x43000
ACTORS=BASE+0x44000;ACTOR_DATA=BASE+0x45000;VTABLE=BASE+0x46000

class PointerOracle(motion.WorkOracle):
 def __init__(self,selection='none'):
  self.pointer_ready=False;self.allocations={};self.releases=[];self.commands=[];self.envelopes=[];self.confirm_count=0;self.rng_writes=[];self.render_boundaries=[]
  super().__init__()
  self.u.mem_map(BASE,0x100000)
  try:self.u.mem_map(0,0x1000)
  except Exception:pass
  self.w(CUR+0xa9,motion.APP);self.w(CUR+0xb9,1);self.w(CUR+0xfd,2)
  self.w(motion.APP+0x15b5,SCENE);self.w(motion.APP+0x3219,FLEET)
  self.u.mem_write(motion.APP+0x3212,b'\x01\x01');self.w(SCENE+0x17ca,VIEW)
  self.w(FLEET,VTABLE);self.w(VTABLE,0x49ab30);self.w(FLEET+0xc,motion.SYSTEM);self.w(FLEET+0x10,motion.APP);self.u.mem_write(FLEET+0x21,b'\x05')
  self.w(FLEET+0x22+20,GROUPS);self.w(FLEET+0x72+20,SELECTED);self.w(FLEET+0xc2+20,0xffffffff)
  self.vector(GROUPS,61,0,GROUP_DATA);self.vector(SELECTED,4,0,SELECTED_DATA);self.vector(ACTORS,4,1,ACTOR_DATA);self.w(ACTOR_DATA,motion.OBJ)
  self.w(motion.PLAYERS+5*0xba0+3000,ACTORS);self.u.mem_write(motion.OBJ+0x57,b'\x01');self.w(motion.OBJ+0x58,0)
  self.w(motion.SYSTEM+0x18,motion.APP);self.u.mem_write(motion.APP+0x1a22,b'\x01')
  self.w(motion.APP+0x38+0xce8,0) # Explicitly disabled source audio backend.
  self.u.hook_add(UC_HOOK_MEM_WRITE,self.pointer_write)
  self.pointer_ready=True;self.membership_read_index=0
  if selection!='none':
   self.observe(5,True,16,2);self.release(0x62)
   if selection=='group':
    self.observe(7,False,18,5);self.release(0x62);self.consume_membership()
   elif selection!='pending':raise ValueError(selection)
   self.commands.clear();self.envelopes.clear();self.confirm_count=0
 def vector(self,p,stride,count,data):
  for off,value in((8,stride),(12,count),(16,16),(20,16),(28,data)):self.w(p+off,value)
 def hook(self,u,address,size,unused):
  if address==0x557700:return # Execute the actual malloc wrapper.
  if address in(0x589bf5,0x589c69):
   sp=u.reg_read(UC_X86_REG_ESP);old=0 if address==0x589bf5 else self.r(sp+4);length=self.r(sp+4 if address==0x589bf5 else sp+8)
   p=self.heap;self.heap+=(length+15)&~15;gate.require(self.heap<0x72000000,'isolated source heap exceeded')
   self.u.mem_write(p,b'\x00'*length)
   if old:self.u.mem_write(p,bytes(self.u.mem_read(old,min(length,self.allocations[old]))))
   self.allocations[p]=length;self.ret(0,p);return
  if self.pointer_ready:
   sp=u.reg_read(UC_X86_REG_ESP)
   if address==0x49ab30:
    msg=self.r(sp+4)
    if self.r(msg+0x10)==0xc453:self.envelopes.append({'code':0xc453,'selected':self.r(msg+0x14),'target_self':self.r(msg+0x18)==motion.OBJ})
   if address==0x520c50:
    actor=self.r(sp+4);action=self.r(sp+12)&255;data=self.r(sp+16)
    gate.require(action in(20,41),'unexpected singleactor command '+str(action))
    self.commands.append({'actor':actor,'action':action,'payload_hex':bytes(self.u.mem_read(data,9 if action==20 else 6)).hex()})
   boundaries={0x516640:(8,'cursor draw'),0x516d90:(4,'cursor asset load'),0x515df0:(0,'confirm sprite'),0x4e0b80:(0,'selection sprite create')}
   if address in boundaries:
    clean,label=boundaries[address];self.render_boundaries.append({'entry':hex(address),'label':label})
    if address==0x515df0:self.confirm_count+=1
    self.ret(clean);return
  super().hook(u,address,size,unused)
 def pointer_write(self,u,access,address,size,value,unused):
  if self.pointer_ready and address<=motion.OBJ+0x18<address+size:
   self.rng_writes.append({'instruction':hex(u.reg_read(UC_X86_REG_EIP)),'before':self.r(motion.OBJ+0x18),'value':value,'size':size})
 def invoke_cursor(self,address,args=()):
  sp=motion.S.STACK+motion.S.STACK_SIZE-0x1000
  for i,v in enumerate((motion.S.END,*args)):self.w(sp+4*i,v)
  self.u.reg_write(UC_X86_REG_ESP,sp);self.u.reg_write(UC_X86_REG_ECX,CUR)
  try:self.u.emu_start(address,motion.S.END,count=1000000)
  except Exception as error:raise AssertionError(f'{error}; EIP={self.u.reg_read(UC_X86_REG_EIP):x}; events={self.events[-8:]}')from error
  gate.require(self.u.reg_read(UC_X86_REG_EIP)==motion.S.END,'source cursor did not return')
  gate.require(self.r(0x5d1f90)==0xabcdef01,'source cursor exception chain drift')
 def observe(self,kind,hover_self,x,y,mask=0,bit=0,blocked=False,enabled=True):
  self.input={'cursor_type':kind,'hover_self':hover_self,'cell':[x,y],'mask':mask,'bit':bit,'blocked':blocked,'enabled':enabled}
  self.u.mem_write(CUR+0x101,struct.pack('<H',kind));self.w(CUR+0xd9,motion.OBJ if hover_self else 0);self.w(CUR+0xc9,x);self.w(CUR+0xcd,y)
  self.u.mem_write(CUR+0xe2,struct.pack('<HH',mask,bit));self.w(CUR+0xe6,int(blocked));self.w(CUR+0xfd,2 if enabled else 1)
 def release(self,message,flags=0):
  self.commands.clear();self.envelopes.clear();self.confirm_count=0;self.rng_writes.clear();self.render_boundaries.clear();self.membership_read_index=0
  self.invoke_cursor(0x518070,(message,flags));return self.snapshot()
 def consume_membership(self,group=None):
  packet=self.commands[self.membership_read_index];gate.require(packet['action']==41,'membership consumer order changed');expected=struct.unpack('<i',bytes.fromhex(packet['payload_hex'])[1:5])[0];gate.require(group is None or group==expected,'membershipgroup order changed');self.membership_read_index+=1;self.w(motion.MESSAGE+0x10,0x280f);self.w(motion.MESSAGE+0x14,motion.ACTION);self.u.mem_write(motion.ACTION+0xc,b'\x29');self.w(motion.ACTION+0xd,motion.DATA);self.u.mem_write(motion.DATA,bytes.fromhex(packet['payload_hex']));self.invoke(0x4dc630,(motion.MESSAGE,));return self.snapshot()
 def snapshot(self):
  short=lambda p:struct.unpack('<h',self.u.mem_read(p,2))[0]
  return {'group_count':self.r(GROUPS+12),'selected':self.r(motion.APP+0x3221)!=0,'pending':self.b(FLEET+0x20)!=0,'current_group':self.signed(FLEET+0xc2+20),'ui_group':short(motion.OBJ+0x5c),'sim_group':short(motion.OBJ+0x5e),'visual':self.b(motion.OBJ+0x252),'cursor_type':short(CUR+0x101),'mask':struct.unpack('<H',self.u.mem_read(CUR+0xe2,2))[0],'bit':struct.unpack('<H',self.u.mem_read(CUR+0xe4,2))[0],'blocked':self.r(CUR+0xe6)!=0,'commands':[dict(c)for c in self.commands],'clear_count':sum(not e['selected']for e in self.envelopes),'select_count':sum(bool(e['selected'])for e in self.envelopes),'confirm_count':self.confirm_count,'rng':self.r(motion.OBJ+0x18),'rng_writes':list(self.rng_writes),'render_boundaries':list(self.render_boundaries),'sound_backend_enabled':self.r(motion.APP+0x38+0xce8)!=0}

def event(kind=0, owner=False, x=18, y=5, message=0x62, flags=0, mask=0, bit=0, blocked=False, enabled=True):
 return {'operation':'release','input':{'cursor_type':kind,'hover_self':owner,'cell':[x,y],'mask':mask,'bit':bit,'blocked':blocked,'enabled':enabled},'message':message,'flags':flags}
def cases():
 select=event(5,True,16,2);move=event(7);consume={'operation':'consume41','group':0};cancel=event(7,message=0x64)
 return [
  {'label':'source-up-only-selection-and-two-orders','operations':[select,event(6,True,16,2),move,consume,event(7,x=16,y=4)]},
  {'label':'down-held-up-does-not-latch','operations':[event(5,True,message=0x61),event(5,True,message=0x61),select,event(5,True,message=0x60),event(6,True,message=0x63),event(7,message=0x61),move,consume]},
  {'label':'clear-reselect-group1-group2','operations':[select,move,consume,cancel,select,move,{'operation':'consume41','group':-1},{'operation':'consume41','group':1},cancel,select,move,{'operation':'consume41','group':-1},{'operation':'consume41','group':2}]},
  {'label':'self-right-cancels-cursor-keeps-selection','operations':[select,event(6,True,message=0x64,mask=0,bit=4),move,consume]},
  {'label':'blank-zero-clear-retains-mask-bit','operations':[select,event(0,message=0x64,mask=0x101,bit=1)]},
  {'label':'friendly-reselect-clears-before-select','operations':[select,select,move,consume]},
  {'label':'blocked-and-disabled-context','operations':[event(5,True,blocked=True),event(5,True,enabled=False),select,event(7,blocked=True),event(7,enabled=False),event(5,True,message=0x64,blocked=True,mask=0x101,bit=1),move,consume]},
  {'label':'right-friendly-no-action-and-empty-clear','operations':[event(5,True,message=0x64),event(0,message=0x64),select,event(5,True,message=0x64),event(7,message=0x64)]},
  {'label':'cached-map-corners-byte0','operations':[select,event(7,x=0,y=0),consume,event(7,x=23,y=23),event(7,x=18,y=2),event(7,x=16,y=1)]},
 ]
def original_cases():
 rows=[]
 for case in cases():
  o=PointerOracle();states=[]
  for op in case['operations']:
   if op['operation']=='consume41':state=o.consume_membership(op['group'])
   else:
    i=op['input'];o.observe(i['cursor_type'],i['hover_self'],*i['cell'],i['mask'],i['bit'],i['blocked'],i['enabled']);state=o.release(op['message'],op['flags'])
   states.append(state)
  rows.append(dict(case,rows=states))
 from tools import probe_ship_selection_visuals as visuals
 _,image,size=visuals.native_image();v=visuals.NativeSelection(image,size)
 removal=[v.op(op)for op in [['S',1028,132],['D'],['A',1,1,1028,132]]]
 gate.require([r['selection']for r in removal]==[1,2,0] and removal[-1]['deletes'],'source visual removal acknowledgement precondition differs')
 return {'schema_version':1,'original_exe_sha256':gate.EXPECTED,'native_entries':['0x518070','0x518c90','0x49ab30','0x49e230','0x49ca60','0x49b990','0x49bd60','0x4cf070','0x520c50','0x5593a0','0x4dc630','0x50c970'],
 'cases':rows,'selection_removal':removal,'scope':'Normal unmodified single0b; explicit upstream hover/cachedcell and map gates; normal actor/fleet release, pendinggroup conversion, serialized20/41 and membership consumption execute actualx86.',
 'boundaries':['Original initialized WorkOracle0b and seven static peers with frozen constructor/load boundaries','Controlled Fleet owner slot5 with source actor registry and empty group vector','Actual50e500 and525300 execute with audio backend disabled; renderer516640,assetloader516d90,confirm515df0,selectionctor4e0b80 are intercepted boundaries','CRT malloc/realloc isolated allocation; original memory wrappers execute','Visual removal uses separate actual4e0d00 NativeSelection fixture; renderer/allocation boundaries documented there'],
 'excluded':['OS/window input and full actorLife','modified selection/queued commands','other actors and contextual right-release cycles','busy motion replacement','audible backend and complete rendering construction']}
if __name__=='__main__':
 output=Path(sys.argv[1])if len(sys.argv)>1 else ROOT/'tests/fixtures/ship_pointer_commands.json'
 data=original_cases();output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(data,indent=2)+'\n');print('native pointer snapshots',sum(len(c['rows'])for c in data['cases']))
