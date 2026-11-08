#!/usr/bin/env python3
"""Source global cursor/map hover and real one-ship fleet/actor callbacks.
Graphics assets/publication and system lookup are explicit boundaries.
The original cached UI-clock read5417d0 executes normally.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path
try:
 from . import probe_ship_world_picker as picking,probe_ship_pointer_mask as mask,validate_boss_ai_gate as gate,validate_mission_ship_seed as seed
except ImportError:
 import probe_ship_world_picker as picking,probe_ship_pointer_mask as mask,validate_boss_ai_gate as gate,validate_mission_ship_seed as seed
ROOT=gate.ROOT
M=picking.BASE;CUR=M+0x600000;GAME=M+0x610000;VIEW=M+0x620000;FLEET=M+0x630000;VT=M+0x631000;GROUPV=M+0x650000;GROUP=M+0x651000;MEMBERS=M+0x652000;MEMBUF=M+0x653000;AV=M+0x654000;ABUF=M+0x655000;PENDING=M+0x656000;REG=M+0x660000;ENGINE=M+0x680000;IDS=M+0x681000;RECORD=M+0x682000;MAP=M+0x690000;MSG=M+0x6a0000

class NativeShipPointerHover:
 def __init__(self):
  if gate.digest(seed.FIXTURE)!=seed.FIXTURE_SHA256:raise ValueError('Pinned source ship fields differ')
  families,_=mask.mask_inputs(ROOT/'reference/raw/ancient-conquest');self.families={f['family']:f for f in families if f['family']!='PAD'}
  self.records=json.loads(seed.FIXTURE.read_text())['records'];self.n=picking.NativeShipWorldPicker();self.u=self.n.u;self.metadata={};self.selected=False;self.queries=0;self.boundaries={};self.graphics=[];self.moves=[]
  for r in self.records:
   i=r['instance_id'];variant='ABGH'['ABGH'.index(chr(65+r['model_variant']))];family=variant+str(r['origin_side']);f=self.families[family];x=r['cell_x']*64+(64-f['width'])//2;y=r['cell_y']*64+(64-f['height'])//2
   self.n.set_actor(i,(x,y),r['heading']*4,r['heading'],f,r['runtime_class_tag']);a=self.n.actors[i]
   for off,val in((0x10,picking.APP),(0x68,picking.APP),(0x261,r['masked_flags'])):self.n.put(a+off,val)
   self.u.mem_write(a+0x54,bytes([r['owner_side'],r['owner_player'],0,1]));self.u.mem_write(a+0x24f,bytes([r['source_player_slot']]));self.metadata[i]={'family':family,'record':r}
  self.claims={r['cell_y']*24+r['cell_x']:r['instance_id']for r in self.records};self.n.set_claims(self.claims)
  raw=(ROOT/'tests/fixtures/mission_cell_flags.bin').read_bytes()
  if hashlib.sha256(raw).hexdigest()!='eb8c22b2dc3a3d6de5be5c5a28560701333cbc8610e8dd687052f4f93b260283':raise ValueError('Source cell flags differ')
  for i,v in enumerate(struct.unpack('<576I',raw)):self.n.put(picking.GRID+8+i*24,v)
  for off,val in((0x10,picking.APP),(0xa9,picking.APP),(0xad,picking.DUMP),(0xfd,2),(0xbd,1),(0x1c,ENGINE),(0x59,0)):self.n.put(CUR+off,val)
  self.n.put(picking.APP+0x15b5,GAME);self.n.put(picking.APP+0x15cd,CUR);self.n.put(picking.APP+0x3219,FLEET);self.n.put(GAME+0x17ca,VIEW)
  self.n.put(ENGINE+0x1a0,1);self.n.put(ENGINE+0x1b0,IDS);self.n.put(IDS,RECORD);self.n.put(RECORD,0x8020)
  self.n.put(FLEET,VT);self.n.put(VT,0x49ab30);self.n.put(FLEET+0xc,GAME);self.n.put(FLEET+0x10,picking.APP);self.u.mem_write(FLEET+0x21,b'\x05');self.n.put(FLEET+0x22+20,GROUPV);self.n.put(FLEET+0xc2+20,0)
  self.vec(GROUPV,0x3d,1,GROUP);self.n.put(GROUP+0x31,MEMBERS);self.vec(MEMBERS,4,1,MEMBUF);self.n.put(MEMBUF,0);self.vec(AV,4,1,ABUF);self.n.put(ABUF,self.n.actors[11]);self.n.put(0x5c7508,REG);self.n.put(REG+5*0xba0+0xbb8,AV)
  self.vec(PENDING,4,1,ABUF);self.n.put(FLEET+0x72+20,PENDING)
  for off,val in((0x481,picking.APP),(0x485,GAME),(0x3c,24),(0x40,24),(0x54,64),(0x489,-1)):self.n.put(MAP+off,val)
  self.u.mem_write(MAP+0x58,b'\x01');self.n.put(0x5ca542,0);self.n.put(0x5d1f90,0xabcdef01)
  from unicorn import UC_HOOK_CODE
  self.u.hook_add(UC_HOOK_CODE,self.hook)
 def vec(self,a,stride,count,buffer):
  for off,v in((8,stride),(12,count),(16,8),(20,8),(28,buffer)):self.n.put(a+off,v)
 def ret(self,clean=0,value=0):
  from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_EAX
  sp=self.u.reg_read(UC_X86_REG_ESP);self.u.reg_write(UC_X86_REG_EIP,self.n.get(sp));self.u.reg_write(UC_X86_REG_ESP,sp+4+clean);self.u.reg_write(UC_X86_REG_EAX,value&0xffffffff)
 def hook(self,u,address,size,unused):
  from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EIP
  sp=u.reg_read(UC_X86_REG_ESP)
  if address==0x587318:self.ret();return
  if address==0x540540:
   msg=self.n.get(sp+4);target=self.n.get(msg+8)
   if target==0x69:u.reg_write(UC_X86_REG_ECX,MAP);u.reg_write(UC_X86_REG_EIP,0x51cd60)
   else:self.ret(4)
   self.boundaries['system_lookup']=self.boundaries.get('system_lookup',0)+1;return
  if address==0x516d90:
   p=self.n.get(sp+4);text=bytearray()
   while self.u.mem_read(p+len(text),1)!=b'\0':text.extend(self.u.mem_read(p+len(text),1))
   self.graphics.append(text.decode());self.ret(4);return
  if address==0x55eb50:self.ret(20);return
  if address==0x499560 and self.n.get(self.n.get(sp+4)+0x10)==0xc44f:self.queries+=1
  if address in(0x556610,0x556880):raise AssertionError('Unexpected native hover error '+hex(address))
 def source_message(self,message):
  self.n.put(MSG+0x10,message);self.n.invoke(0x518d90,(MSG,),CUR)
 def set_selected(self,selected,pending=False):
  self.selected=selected;self.n.put(picking.APP+0x3221,int(selected));self.u.mem_write(FLEET+0x20,bytes([int(pending)]))
 def move(self,screen,world,selected=False,pending=False):
  self.set_selected(selected,pending);self.n.put(MAP+0x24,screen[0]-world[0]);self.n.put(MAP+0x28,screen[1]-world[1]);self.n.put(MSG+0x18,(screen[0]&65535)|((screen[1]&65535)<<16));self.queries=0;self.n.calls=[];self.source_message(0x60);return self.snapshot()
 def refresh(self,selected=False,pending=False):
  self.set_selected(selected,pending);self.queries=0;self.n.calls=[];self.source_message(0);return self.snapshot()
 def snapshot(self):
  n=self.n;target=n.get(CUR+0xd9)
  return {'has_map':bool(n.get(CUR+0xb9)),'screen':[n.signed(CUR+0xb1),n.signed(CUR+0xb5)],'world':[n.signed(CUR+0xc1),n.signed(CUR+0xc5)],'cell':[n.signed(CUR+0xc9),n.signed(CUR+0xcd)],'hovered_id':None if target==0 else n.get(target+0x4c),'cursor_type':struct.unpack('<H',self.u.mem_read(CUR+0x101,2))[0],'action_mask':struct.unpack('<H',self.u.mem_read(CUR+0xe2,2))[0],'action_bit':struct.unpack('<H',self.u.mem_read(CUR+0xe4,2))[0],'blocked':bool(n.get(CUR+0xe6)),'selector':struct.unpack('<H',self.u.mem_read(CUR+0xef,2))[0],'last_query':bool(self.queries),'visits':[x['owner_id']for x in n.calls]}

def source_metadata():
 families,_=mask.mask_inputs(ROOT/'reference/raw/ancient-conquest');by_family={f['family']:f for f in families if f['family']!='PAD'}
 records=json.loads(seed.FIXTURE.read_text())['records'];result=[]
 for r in records:
  family=chr(65+r['model_variant'])+str(r['origin_side']);f=by_family[family]
  result.append({'id':r['instance_id'],'family':family,'world':[r['cell_x']*64+(64-f['width'])//2,r['cell_y']*64+(64-f['height'])//2],'cell':[r['cell_x'],r['cell_y']],'frame':r['heading']*4,'heading':r['heading'],'side':r['owner_side'],'player':r['owner_player'],'caps':r['masked_flags'],'class':r['runtime_class_tag']})
 return result

def original_cases():
 n=NativeShipPointerHover();operations=[];actor_rows=source_metadata();initial_claims=dict(n.claims)
 def record(op):
  kind=op['op']
  if kind=='MOVE':state=n.move(op['screen'],op['world'],op['selected'],op.get('pending',False))
  elif kind=='REFRESH':state=n.refresh(op['selected'],op.get('pending',False))
  elif kind=='CAPS':n.n.put(n.n.actors[op['id']]+0x261,op['value']);state=None
  elif kind=='CLAIMS':n.claims=dict(op['claims']);n.n.set_claims(n.claims);state=None
  elif kind=='POSE':
   row=next(a for a in actor_rows if a['id']==op['id']);n.n.set_actor(op['id'],op['world'],op['frame'],op['heading'],n.families[row['family']],row['class']);state=None
  elif kind=='IMPORT':
   for off,value in((0x101,op['type']),(0xe2,op['mask']),(0xe4,op['bit'])):n.u.mem_write(CUR+off,struct.pack('<H',value))
   n.n.put(CUR+0xe6,int(op['blocked']));n.queries=0;n.n.calls=[];state=n.snapshot()
  elif kind=='INVALIDATE':
   from unicorn.x86_const import UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EIP
   from unicorn import UC_HOOK_CODE
   stop=n.u.hook_add(UC_HOOK_CODE,lambda u,a,z,d:u.emu_stop(),begin=0x518f39,end=0x518f39)
   n.u.reg_write(UC_X86_REG_ESI,CUR);n.u.reg_write(UC_X86_REG_EDI,0);n.u.emu_start(0x518f2d,picking.END,count=4);n.u.hook_del(stop)
   gate.require(n.u.reg_read(UC_X86_REG_EIP)==0x518f39,'Map invalidation range did not complete');n.queries=0;n.n.calls=[];state=n.snapshot()
  else:raise ValueError('Unknown hover operation')
  operations.append(dict(op,index=len(operations),state=state))
 def move(label,world,selected=False,pending=False,screen=None):record({'op':'MOVE','label':label,'world':list(world),'screen':list(world if screen is None else screen),'selected':selected,'pending':pending})
 def refresh(label,selected=False,pending=False):record({'op':'REFRESH','label':label,'selected':selected,'pending':pending})
 move('initial-zero-screen',(0,0));refresh('initial-no-map')
 move('own-unselected',(1056,160));refresh('own-unselected-stationary')
 move('foreign-unselected-preserves-type',(736,1184));refresh('foreign-unselected-stationary');move('back-to-own-unselected',(1056,160))
 refresh('selection-refresh-without-move',True);move('same-screen-new-world-ignored',(1057,160),True,screen=(1056,160))
 move('self-selected-pending',(1057,160),True,True);refresh('self-selected-current',True)
 move('sea-selected',(1184,352),True);refresh('sea-selected-stationary',True)
 record({'op':'CAPS','label':'remove-move-cap','id':11,'value':0xfffff3ff});refresh('no-move-cap',True)
 record({'op':'CAPS','label':'restore-move-cap','id':11,'value':0xfffff7ff});refresh('restored-move-cap',True)
 record({'op':'CLAIMS','label':'reserve-hovered-cell','claims':list((initial_claims|{138:11}).items())});refresh('occupied-transparent-cell',True)
 record({'op':'CLAIMS','label':'release-hovered-cell','claims':list(initial_claims.items())});refresh('released-cell',True)
 move('changed-screen-same-world',(1184,352),True,screen=(1185,352));refresh('invalidated-same-world-refresh',True)
 move('changed-world-restores-map',(1185,352),True,screen=(1186,352))
 record({'op':'POSE','label':'actor-under-stationary-pointer','id':11,'world':[1157,324],'frame':20,'heading':5});record({'op':'CLAIMS','label':'actor-moved-claims','claims':list((({k:v for k,v in initial_claims.items()if v!=11})|{138:11}).items())});refresh('stationary-pointer-finds-moved-self',True)
 record({'op':'POSE','label':'restore-actor-pose','id':11,'world':[1028,132],'frame':20,'heading':5});record({'op':'CLAIMS','label':'restore-actor-claims','claims':list(initial_claims.items())});refresh('stationary-pointer-loses-moved-self',True)
 # A changed STORED turning mask is re-picked by Life under a stationary pointer.
 f=n.families['A1'];stride=(f['width']+7)//8
 bit=lambda plane,x,y:bool(plane[y*stride+x//8]&(128>>(x%8)))
 px,py=next((x,y)for y in range(56)for x in range(56)if bit(f['planes'][15],x,y)and not bit(f['planes'][3],x,y))
 move('turn-mask-before',(1028+px,132+py),True)
 record({'op':'POSE','label':'stored-turn-frame','id':11,'world':[1028,132],'frame':35,'heading':5});refresh('stationary-stored-turn-mask',True)
 record({'op':'POSE','label':'restore-stored-frame','id':11,'world':[1028,132],'frame':20,'heading':5});refresh('stationary-restored-mask',True)
 move('other-friendly',(1376,352),True);refresh('friendly-mask-unchanged',True,True)
 record({'op':'IMPORT','label':'cycle-state-import','type':12,'mask':0x101,'bit':0x100,'blocked':False});refresh('unchanged-mask-preserves-cycle',True)
 record({'op':'CAPS','label':'target-cap31-off','id':12,'value':0xfffff7fb});refresh('friendly-no-cap31',True)
 record({'op':'CAPS','label':'target-cap31-on','id':12,'value':0xfffff7ff});refresh('friendly-cap31-restored',True)
 record({'op':'INVALIDATE','label':'source-map-invalidation'});refresh('invalid-map-does-not-repick',True)
 # Full source-cell matrix. Selected foreign/combat branches are excluded.
 skipped=[]
 for selected in(False,True):
  for y in range(24):
   for x in range(24):
    world=(x*64+32,y*64+32);picked=n.n.query(*world,x,y,True)['hit_id']
    if selected and picked is not None:
     actor=next(a for a in actor_rows if a['id']==picked)
     if(actor['side'],actor['player'])!=(1,1):skipped.append([x,y]);continue
    move(('selected'if selected else'unselected')+'-cell-'+str(y*24+x),world,selected,bool((x+y)&1));refresh('life-'+str(int(selected))+'-'+str(y*24+x),selected,bool((x+y)&1))
 gate.require(gate.digest(gate.ORIGINAL)==gate.EXPECTED,'Original changed during hover execution')
 return {'schema_version':1,'original_exe_sha256':gate.EXPECTED,'native_oracle_sha256':gate.digest(Path(__file__)),'picker_oracle_sha256':gate.digest(Path(picking.__file__)),'mask_fixture_sha256':gate.digest(mask.ROOT/'tests/fixtures/ship_pointer_mask.json'),'ship_seed_fixture_sha256':seed.FIXTURE_SHA256,'source_cell_flags_sha256':'eb8c22b2dc3a3d6de5be5c5a28560701333cbc8610e8dd687052f4f93b260283','actors':actor_rows,'operations':operations,'state_count':sum(o['state']is not None for o in operations),'selected_foreign_cells_excluded':skipped,'boundaries':{'587318':'normal setjmp return','540540':'system69 lookup tailcalls actual51cd60; other UI systems absent','516d90':'cursor asset loader only; SetGCType prelude/mapping still executes','55eb50':'cursor graphics publication only; actual516640 updates its coordinates first'},'source_entries':['518d90','51cd60','517a60','517540','499560','49a580','499530','49a1d0','4e06c0','5431d0','5575d0','49ab30','49e620','49e490','4dc630','4e6700','50e800','499a40','4999e0','516e30','516640','55ea00','5417d0'],'scope':'Normal cursorcontext0/mode2; noFog/normalship-only/static8 with controlled0b selection; current and pending oneactor group callbacks; actual flags/masks','excluded':['Selected foreign/combat hover','Modal UI/help/build contexts/other object slots/fog','Full application initialization and OS input','Cursor bitmaps/publication and real-time animation cadence','Selection/release dispatch (separate adapter)']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();d=original_cases();a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('x')as f:f.write(json.dumps(d,indent=2)+'\n')
 print(json.dumps({'passed':True,'states':d['state_count'],'operations':len(d['operations']),'excluded_foreign_cells':len(d['selected_foreign_cells_excluded'])}))
if __name__=='__main__':main()
