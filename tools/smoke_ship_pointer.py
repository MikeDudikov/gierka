#!/usr/bin/env python3
"""Queued InputSystem mouse integration and source-art validation, without OS mouse claims."""
from __future__ import annotations
import argparse,json,os,re,subprocess,time,struct
from pathlib import Path
from PIL import Image
if __package__:
 from . import smoke_ship_order as order,ship_pointer_image_reference as images,smoke_ship_picking as picking
 from . import probe_ship_pointer_commands as command_native,probe_ship_selection_visuals as selection_native
else:
 import smoke_ship_order as order
 import ship_pointer_image_reference as images
 import smoke_ship_picking as picking
 import probe_ship_pointer_commands as command_native
 import probe_ship_selection_visuals as selection_native
menu,terrain,units,require=order.menu,order.terrain,order.units,order.require
ROOT=menu.REPOSITORY;PREFIX='[ShipPointerReference] ';REPLAY='[ShipPointerReplay] '
READY=PREFIX+'ready: canvas=1920,1080; origin=576,0; scale=2; input=InputSystem.onEvent; actor=0000000b; actors=8; fog=False; other_object_slots=empty; membership=explicit-ui-and-simulation; planner_membership=bounded-different-group; audio=False; full_game=False'
INPUT_STAGES=['initial','hover-friendly','select-down','selected','sea-before-right','right-down','wrong-right-release',
 'rehover-friendly','reselected-same-frame','cancel-hover','cancel-down','device-cancelled','device-recovered','move-down','request-1','subpixel-same-logical']
MOTION1=(1,3,19,23,47,87,98,99,101);MOTION2=(102,104,120,124,150,175,185,197)
MOTION_FIELDS=('counter','cell','world','published','frame','drawn','heading','state','pending_flags','active_flags','reserved','rng','can_request')
EVENT_FIELDS=('index','counter','visual_ms','message','raw','logical','world','cell','has_map','picked','cursor','selected','pending','ui_group','simulation_group','rng','outcome')
CHECK_FIELDS=('stage','counter','visual_ms','selected','pending','ui_group','simulation_group','group_count','selection_visual_flag',
 'selector_state','selector_exists','selector_frame','selector_drawn','selector_visible','selector_last_counter','health_visible','health_exists',
 'cursor','cursor_frame','cursor_visible','cursor_last_tick','cursor_interval','confirm','confirm_frame','confirm_stored','confirm_visible','confirm_last_tick','held')
BOOLS={'has_map','selected','pending','can_request','selector_exists','selector_visible','health_visible','health_exists',
 'cursor_visible','confirm','confirm_visible','held','exists','visible','synthesized_up','confirm_late','cursor_gui'}
PAIRS={'raw','logical','world','cell','published','position'}
STRINGS={'stage','kind','sprite','sampling','outcome','payload'}
PINS={'ship_pointer_commands.json':'6d88a2300b7a7619f5379aec8192963ac3cf8cebd07fedb7e2a714381b0592cd',
 'ship_pointer_hover.json':'8b6378752fed97d06f5890e6ed4de07646f96b0c14860971ad2ffa7d010ba547',
 'ship_selection_visuals.json':'62b771352ae781b101a2e2bfe3ccd1edecc45b900e2c52863b45130e240b9067',
 'pointer_cursor_visuals.json':'1cb33c999e98813329edf7b04c90d5f5def9dcadfe8ac5c158b3259a518b20d2'}
LIMITATIONS=['Synthetic queued InputSystem MouseState events; no OS mouse/nativeWindows11/targetlaptop performance validation',
 'Single source0b, seven static peers, noFog/emptyotherslots, audiooff, explicitdifferentgroup projection; unfinished game',
 'Source command/hover/selector/cursor primitives have separate native proofs; enabledaudio,otheractors,modifiers,busyreplacement/boxselection excluded',
 'Clock-held input stages preserve counter0 and101; holds do not establish real-game cadence',
 'Selector timing is reconstructed from original4e0d00 and sourcebody publication schedule',
 'Unheld realtime cursor/confirm phase is observed with source-validated frame/position/stamp constraints, not reconstructed from every unlogged Life draw',
 'Image composition uses independently checked sourceplanes and validated geometry/order; sourceart is not final2026art',
 'Internal QA framebuffers only; no presentationpreview/ZIP/publication']


FOCUS_PROBE=ROOT/'artifacts/pointer-input/win32-focus-probe/probe.exe'
FOCUS_PROBE_SOURCE=ROOT/'tools/win64_pointer_focus_probe.c'
FOCUS_PROBE_BUILD=ROOT/'tools/build_win64_pointer_focus_probe.sh'
FOCUS_PROBE_SHA256='d6bc85fd7b632c8cc1d44fd6fe367f6f3fe0be133350a52e9051ca0fe5359069'
FOCUS_PROBE_SOURCE_SHA256='027b22060d98b468149d9cf3514f3658edd61577cbf26486a9505f8becff1b29'
FOCUS_PROBE_BUILD_SHA256='bc31b184a726392bcf0d8bc4e72be600523a9d68f414d7d8ab7beda5aae88b24'

def focus_probe_metadata():
 result={}
 for key,path,digest in(('executable',FOCUS_PROBE,FOCUS_PROBE_SHA256),('source',FOCUS_PROBE_SOURCE,FOCUS_PROBE_SOURCE_SHA256),('build_script',FOCUS_PROBE_BUILD,FOCUS_PROBE_BUILD_SHA256)):
  require(path.is_file()and not path.is_symlink()and menu.file_sha256(path)==digest,'Native focus probe differs: '+str(path))
  result[key]={'path':str(path),'sha256':digest,'bytes':path.stat().st_size}
 result['launch']=['bash',str(terrain.LAUNCHER),str(FOCUS_PROBE)]
 return result

def validate_focus_foreground(raw):
 require(raw.endswith('\n')and len(raw.splitlines())==1,'Native focus probe must emit one complete JSON line')
 result=json.loads(raw);require(set(result)=={'player_hwnd','sink_hwnd','before','sink','restored','passed'},'Malformed native foreground schema')
 positive=lambda x:type(x)is int and x>0
 player,sink=result['player_hwnd'],result['sink_hwnd']
 require(positive(player)and positive(sink)and player!=sink and result['passed']is True,'Native foreground transition failed')
 for phase,wanted in(('before',player),('sink',sink),('restored',player)):
  row=result[phase]
  require(set(row)=={'foreground','pid','matched','set_foreground_result','bring_to_top_result','title'},'Malformed native foreground phase')
  require(row['foreground']==wanted and positive(row['pid'])and row['matched']is True,'Native foreground HWND/PID mismatch')
  require(isinstance(row['title'],str)and all(type(row[k])is int and 0<=row[k]<=0xffffffff for k in('set_foreground_result','bring_to_top_result')),'Malformed native activation result')
 require(result['before']['pid']==result['restored']['pid']!=result['sink']['pid'],'Native foreground processes are not distinct/restored')
 require(result['before']['title']==result['restored']['title']=='AncientConquest','Native player title differs')
 return result

def stages(two=False):
 return INPUT_STAGES+[f'motion-1-{x}'for x in MOTION1]+(['second-down','request-2']+[f'motion-2-{x}'for x in MOTION2]if two else [])

def provenance():
 result=order.provenance();files={'pointer_qa_helper':Path(__file__).resolve(),'pointer_image_oracle':Path(images.__file__),
 'pointer_command_oracle':Path(command_native.__file__),'pointer_selection_oracle':Path(selection_native.__file__),
 'pointer_visual_manifest':images.RESOURCE_ROOT/images.MANIFEST_NAME,'pointer_visual_payload':images.RESOURCE_ROOT/images.ATLAS_NAME}
 files.update({'pointer_fixture:'+name:ROOT/'tests/fixtures'/name for name in PINS})
 for key,path in files.items():
  require(path.is_file()and not path.is_symlink(),'Missing/symbolic pointer evidence: '+str(path));result[key]={'path':str(path),'bytes':path.stat().st_size,'sha256':menu.file_sha256(path)}
 return result

def load_reference():
 for name,digest in PINS.items():units.pinned_json(ROOT/'tests/fixtures'/name,digest)
 r=picking.load_reference();r['pointer_visuals']=images.load_visual_reference();return r

def tokens(line,kind):
 content=line[len(PREFIX+kind+': '):];d={}
 for token in content.split('; '):
  require('='in token,'Malformed pointer token');k,v=token.split('=',1);require(k not in d,'Duplicate pointer field')
  if k in BOOLS:require(v in('True','False'),'Malformed pointer boolean');v=v=='True'
  elif k in PAIRS:require(re.fullmatch(r'-?\d+,-?\d+',v),'Malformed pointer pair');v=[int(x)for x in v.split(',')]
  elif k=='picked':require(v=='none'or re.fullmatch(r'[0-9a-f]{8}',v),'Malformed picked owner');v=None if v=='none'else int(v,16)
  elif k=='id':require(re.fullmatch(r'[0-9a-f]{8}',v),'Malformed owner');v=int(v,16)
  elif k=='order'and v=='gui-last':pass
  elif k not in STRINGS:v=int(v)
  d[k]=v
 return d

def motion_sample(case,counter,moves):
 if moves==0:
  require(counter==0,'Physics advanced before first mouse move');return case['samples'][0]
 operation='request'if(counter==0 or moves==2 and counter==101)else'tick'
 return next(s for s in case['samples']if s['counter']==counter and s['operation']==operation and s['epoch']==moves)

def expected_motion(sample):
 return {'counter':sample['counter'],'cell':sample['cell'],'world':sample['world'],'published':sample['render_world'],
 'frame':sample['frame'],'drawn':sample['drawn_frame'],'heading':sample['heading'],'state':sample['state'],
 'pending_flags':sample['pending'],'active_flags':sample['active'],'reserved':sample['reserved'],'rng':sample['random_state'],
 'can_request':order.can_request(sample)}

def input_specs(two):
 pairs=[(96,(1,1)),(96,(960,320)),(97,(960,320)),(98,(960,320)),(96,(1216,704)),(99,(1216,704)),
 (100,(1216,704)),(96,(960,320)),(97,(960,320)),(98,(960,320)),(96,(1216,704)),(97,(1216,704)),
 (96,(1218,704)),(96,(1216,576)),(97,(1216,576)),(96,(1216,704)),(98,(1216,704)),(96,(1217,704))]
 if two:pairs.extend(((96,(960,576)),(97,(960,576)),(98,(960,576))))
 return pairs

class ExpectedRun:
 def __init__(self,reference,two):
  self.reference=reference;self.case=reference['native_order']['two18_5_then16_4'if two else'reach18_5'];self.two=two
  self.specs=input_specs(two);self.moves=0;self.last_counter=0;self.selected=False;self.pending=False;self.cursor=0;self.picked=None
  self.logical=[0,0];self.world=[0,0];self.cell=[0,0];self.has_map=False;self.commands=command_native.PointerOracle()
  _,image,size=selection_native.native_image();self.selection=selection_native.NativeSelection(image,size)
  self.sel=self.selection.op(['A',0,1,1028,132]);self.rows={};self.samples={};self.events=[];self.packets=[];self.checkpoints={}
 def advance(self,counter):
  require(counter>=self.last_counter,'Simulation counter moved backwards')
  for tick in range(self.last_counter+1,counter+1):
   sample=motion_sample(self.case,tick,self.moves)
   for pub in sample['publications']:self.sel=self.selection.op(['A',tick,1,*pub['world']])
   if self.sel['frame']<10 or self.sel['selection']==2:self.sel=self.selection.op(['A',tick,1,*sample['render_world']])
  self.last_counter=counter
 def event(self,row,packets):
  require(set(row)==set(EVENT_FIELDS),'Missing/unknown pointer event field');i=row['index'];require(i==len(self.events)and i<len(self.specs),'Pointer event order/count differs')
  msg,raw=self.specs[i];counter=101 if i>=18 else 0
  require(row['message']==msg and row['raw']==list(raw)and row['counter']==counter,'Queued event edge/position/counter differs')
  self.advance(counter);old_selected=self.selected
  if msg==96 and [raw[0]//2,raw[1]//2]!=self.logical:
   self.logical=[raw[0]//2,raw[1]//2];self.world=[576+self.logical[0],self.logical[1]];self.cell=[x//64 for x in self.world];self.has_map=True
   # These frozen replay points are respectively the independently proven mask
   # centre of source0b or empty passable SEA. No arbitrary point rule inferred.
   self.picked=11 if self.world==[1056,160]and counter==0 else None
   self.cursor=5 if self.picked==11 and not self.selected else 6 if self.picked==11 else 7 if self.selected else 0
  if msg in(98,100):
   self.commands.observe(self.cursor,self.picked==11,*self.cell,enabled=self.has_map)
   state=self.commands.release(msg)
   wanted=[{'event':i,'index':j,'action':p['action'],'payload':p['payload_hex']}for j,p in enumerate(state['commands'])]
   require(packets==wanted,'Mouse release packet order/payload differs from original518070/Fleet/serializer')
   for p in state['commands']:
    if p['action']==41:self.commands.consume_membership(struct.unpack_from('<i',bytes.fromhex(p['payload_hex']),1)[0])
    elif p['action']==20:self.moves+=1
   state=self.commands.snapshot();self.selected=state['selected'];self.pending=state['pending'];self.cursor=state['cursor_type']
   if old_selected and not self.selected:self.sel=self.selection.op(['D'])
   if not old_selected and self.selected:self.sel=self.selection.op(['S',*motion_sample(self.case,counter,self.moves)['render_world']])
  else:require(not packets,'A move/down edge emitted actor packets')
  state=self.commands.snapshot();sample=motion_sample(self.case,counter,self.moves)
  wanted={'index':i,'counter':counter,'visual_ms':750 if i==17 else row['visual_ms'],'message':msg,'raw':list(raw),
   'logical':self.logical,'world':self.world,'cell':self.cell,'has_map':self.has_map,'picked':self.picked,'cursor':self.cursor,
   'selected':self.selected,'pending':self.pending,'ui_group':state['ui_group'],'simulation_group':state['sim_group'],
   'rng':sample['random_state'],'outcome':'handled'}
  require(row==wanted,'Pointer event differs from source context/selection/membership/RNG')
  if i<17:require(row['visual_ms']==0,'Pre-command source clock advanced during held replay')
  self.events.append(row);self.packets.extend(packets)
 def checkpoint(self,header,motion,visuals,queue):
  require(set(header)==set(CHECK_FIELDS),'Missing/unknown pointer checkpoint field');stage=header['stage'];self.advance(header['counter'])
  sample=motion_sample(self.case,header['counter'],self.moves);require(motion==expected_motion(sample),'Checkpoint motion differs from frozen original')
  group=self.commands.snapshot();sel=self.sel
  expected={'selected':group['selected'],'pending':group['pending'],'ui_group':group['ui_group'],'simulation_group':group['sim_group'],
   'group_count':group['group_count'],'selection_visual_flag':sel['selection'],'selector_state':sel['selection'],'selector_exists':sel['exists'],
   'selector_frame':sel['frame'],'selector_drawn':sel['drawn_frame'],'selector_visible':sel['visible'],'selector_last_counter':sel['last_counter'],
   'health_visible':sel['health_visible'],'health_exists':sel['health_exists'],'held':True}
  require(all(header[k]==v for k,v in expected.items()),'Selector/member checkpoint differs from original4e0d00/commands')
  require(len(visuals)==4 and [v['kind']for v in visuals]==['selector','health','confirm','cursor'],'Missing/duplicate pointer visual')
  by={v['kind']:v for v in visuals};sc=by['selector'];hp=by['health'];cu=by['cursor'];co=by['confirm']
  require(sc['exists']==sel['exists']and sc['visible']==sel['visible']and sc['position']==sel['world']and sc['sprite']==('none'if sel['drawn_frame']<0 else f"RAM_056X056{sel['drawn_frame']:02d}"),'Selector renderer differs from original')
  require(hp['exists']==sel['health_exists']and hp['visible']==sel['health_visible']and hp['position']==sel['health_world']and hp['sprite']=='HEALTH_100_60','Native healthy IL plane differs')
  if sel['exists']and sel['health_exists']:require((hp['order'],sc['order'])==(44,45),'Native equal-depth IL/selector order differs')
  require(co['order']==46 and co['exists']==header['confirm']and co['visible']==header['confirm_visible'],'Confirmation publication differs')
  if self.moves:require(co['position']==([1173,328]if self.moves==1 else[1045,264]),'Wrong source confirmation click offset')
  require(cu['exists']==header['cursor_visible']and cu['visible']==header['cursor_visible']and cu['order']==32767,'Cursor renderer visibility/order differs')
  typ=header['cursor'];require(typ in(-1,0,5,6,7),'Unsupported cursor type');require(header['cursor_interval']==(500 if typ==-1 else 150 if typ==7 else 10000),'Wrong source cursor interval');require(header['cursor_frame']in(range(4)if typ==7 else(0,)),'Cursor frame outside source sequence')
  if typ>=0:
   name={0:'STD',5:'OWN',6:'SELECT',7:'SEA'}[typ];require(cu['sprite']==f"CUR_{name}_N{header['cursor_frame']:02d}",'Wrong source cursor family/frame')
   point=[self.logical[0]+(-18 if typ==7 else 0),self.logical[1]+(-17 if typ==7 else 0)];require(cu['position']==point,'Wrong source cursor hotspot/coordinate space')
  require(header['cursor_last_tick']<=header['visual_ms']and header['confirm_last_tick']<=header['visual_ms'],'UI stamp lies after cached time')
  if header['counter']==0:
   require(header['cursor_frame']==0 and header['cursor_last_tick']==0,'Held input unexpectedly advanced cursor')
   if stage=='initial':require(typ==-1 and not header['cursor_visible'],'Initial source-screen no-op manufactured a cursor draw')
   if stage in('request-1','subpixel-same-logical'):
    require(header['confirm']and not header['confirm_visible']and header['confirm_frame']==-1 and header['confirm_stored']==0 and header['confirm_last_tick']==0,'No-op/subpixel manufactured a confirmation draw')
  if header['confirm_visible']:require(header['confirm_frame']in(1,2,3)and co['sprite']==f"TAKE_CMD{header['confirm_frame']:02d}",'Invalid command confirmation source frame')
  cache=self.reference.setdefault('_pointer_base_cache',{});key=(self.case['label'],stage,sample['sample_index'])
  if key not in cache:cache[key]=order.checkpoint_reference(self.reference,self.case,stage,sample)
  base=cache[key];require(queue==base['expected_queue_rows'],'Base34 renderer queue differs from original history')
  pixels=self.reference.setdefault('_pointer_pixel_cache',{});pixelkey=key+(json.dumps(visuals,sort_keys=True),)
  if pixelkey not in pixels:pixels[pixelkey]=images.compose_overlay(base['expected_image'],visuals,visual_reference=self.reference['pointer_visuals'])
  cp=dict(base,expected_image=pixels[pixelkey],pointer_header=header,pointer_visuals=visuals)
  self.rows[stage]=cp;self.samples[stage]=sample;self.checkpoints[stage]=header
  return cp

_PARSE_CACHE={}
def parse_log(log,reference,two=False,complete=False):
 if log and not log.endswith('\n'):
  require(not complete,'Final player log has an unterminated tail')
  log=log.rsplit('\n',1)[0]+'\n'if'\n'in log else''
 require([x for x in log.splitlines()if x.startswith(PREFIX+'ready:')]==[READY],'Missing/duplicate pointer scope/readiness')
 cachekey=(id(reference),two,complete,log)
 if cachekey in _PARSE_CACHE:return _PARSE_CACHE[cachekey]
 model=ExpectedRun(reference,two);parsed={'events':[],'packets':[],'motions':[],'checkpoints':[],'visuals':{},'queue':{},'visual_queue':{},'cancels':[]};current=None;motion=None;pending={};cancel_phase_count=0;replay_complete=False
 for line in log.splitlines():
  if line.startswith(REPLAY+'complete:'):replay_complete=True
  if line.startswith(PREFIX+'packet: '):
   p=tokens(line,'packet');require(set(p)=={'event','index','action','payload'},'Malformed pointer packet');pending.setdefault(p['event'],[]).append(p);parsed['packets'].append(p)
  elif line.startswith(PREFIX+'event: '):
   row=tokens(line,'event');model.event(row,pending.pop(row['index'],[]));parsed['events'].append(row)
  elif line.startswith(PREFIX+'motion: '):
   row=tokens(line,'motion');require(set(row)==set(MOTION_FIELDS),'Missing/unknown motion field');model.advance(row['counter']);require(row==expected_motion(motion_sample(model.case,row['counter'],model.moves)),'Actual mouse-driven Tick differs from original');parsed['motions'].append(row)
   if current:motion=row
  elif line.startswith(PREFIX+'checkpoint: '):
   require(current is None,'Next checkpoint precedes completion of previousvisual/queue block')
   current=tokens(line,'checkpoint');parsed['checkpoints'].append(current);parsed['visuals'][current['stage']]=[];parsed['queue'][current['stage']]=[];motion=None
  elif line.startswith(PREFIX+'visual_queue: '):
   row=tokens(line,'visual_queue');require(current and row['stage']==current['stage'],'Overlay queue outside checkpoint')
   want={'stage':current['stage'],'nodes':int(current['selector_exists'])+int(current['health_exists']),'source_depth':1020,'base_renderers':34,'confirm_late':True,'cursor_gui':False}
   require(row==want and row['stage']not in parsed['visual_queue'],'Invalid/duplicate source overlay queue');parsed['visual_queue'][row['stage']]=row
  elif line.startswith(PREFIX+'visual: '):
   row=tokens(line,'visual');require(current and row['stage']==current['stage'],'Visual outside checkpoint');parsed['visuals'][row['stage']].append(row)
  elif line.startswith(PREFIX+'queue: '):
   row=tokens(line,'queue');require(current and row['stage']==current['stage'],'Queue outside checkpoint');parsed['queue'][row['stage']].append(row)
   if len(parsed['queue'][row['stage']])==34 and len(parsed['visuals'][row['stage']])==4:
    require(current['stage']in parsed['visual_queue'],'Missing source overlay queue')
    model.checkpoint(current,motion,parsed['visuals'][current['stage']],parsed['queue'][current['stage']]);current=None
  elif line.startswith(PREFIX+'cancel: '):
   row=tokens(line,'cancel');require(set(row)=={'counter','selected','synthesized_up'},'Malformed pointer cancellation schema')
   require(row['synthesized_up']is False,'Cancellation manufactured source Up')
   require(row['counter']==model.last_counter and row['selected']==model.selected,'Cancellation context differs from active source state')
   if not replay_complete:
    require(parsed['checkpoints']and parsed['checkpoints'][-1]['stage']=='cancel-down'and len(parsed['events'])==12 and row['counter']==0,'Cancellation outside held device/focus phase')
    cancel_phase_count+=1
   else:require(row['counter']==(197 if two else 101),'Tail cancellation precedes final counter')
   parsed['cancels'].append(row);model.has_map=False;model.cursor=0
 names=[x['stage']for x in parsed['checkpoints']];require(names==stages(two)[:len(names)],'Missing/reordered pointer stages')
 if complete:
  require(names==stages(two)and len(parsed['events'])==len(model.specs)and not pending,'Incomplete pointer event/stage sequence')
  require(cancel_phase_count>=1,'Missing held device/focus cancellation')
  require({row['counter']for row in parsed['motions']}==set(range(198 if two else 102)),'Missing mouse-driven simulation counter')
  require(current is None,'Final pointer checkpoint block incomplete')
  require(REPLAY+'complete:'in log and PREFIX+'cleanup: input_unsubscribed=True; visual_refs_cleared=True'in log,'Pointer completion/cleanup missing')
  require('Mission unit reference cleanup: claimed_released=8; visual_refs_cleared=True'in log,'Actor claims leaked')
 if len(_PARSE_CACHE)>6:_PARSE_CACHE.clear()
 _PARSE_CACHE[cachekey]=(parsed,model)
 return parsed,model

def capture_checkpoint(player,environment,output,player_log,reference,two,stage):
 started=time.monotonic();attempts=[]
 while True:
  before,model=parse_log(terrain.read_log(player_log),reference,two);require(stage in model.rows and before['checkpoints'][-1]['stage']==stage,'Incomplete/wrong pointer fence')
  cp=model.rows[stage];path=menu.capture(environment,output,f'{stage}-attempt-{len(attempts)+1:02d}')
  with Image.open(path)as im:passed,metrics=order.frame_metrics(im.convert('RGB'),cp['expected_image'],cp['regions'])
  after,_=parse_log(terrain.read_log(player_log),reference,two);elapsed=time.monotonic()-started
  attempts.append({'screenshot':path.name,'metrics':metrics,'elapsed_seconds':elapsed});menu.write_json(output/(stage+'-attempts.json'),attempts)
  require(before==after,'Input/motion/visual/queue state changed during capture');require(elapsed<=1.0,'Pointer presentation exceeded1s inside1.25hold')
  if passed:
   cp['expected_image'].save(output/(stage+'-expected.png'),compress_level=0)
   return {'screenshot':path.name,'metrics':metrics,'capture_seconds':elapsed,'presentation_attempt_count':len(attempts),'failed_presentation_attempt_count':len(attempts)-1,'presentation_attempts':attempts}
  require(player.poll()is None and time.monotonic()-started<1.0,'Pointer sourceart framebuffer persistently differs');time.sleep(.02)

def run_smoke(output,two=False,focus_cancel=False):
 output=Path(output).resolve();require(not output.exists(),'Choose a fresh pointer output directory');output.mkdir(parents=True)
 baseline,reference=provenance(),load_reference();env=os.environ.copy();env['DISPLAY']=menu.DISPLAY;env['LD_LIBRARY_PATH']=str(menu.TOOLCHAIN/'usr/lib/x86_64-linux-gnu')
 log=output/'player.log';launch=['bash',str(terrain.LAUNCHER),str(terrain.EXECUTABLE),'-logFile',str(log),'--ship-pointer-reference','--ship-pointer-input-replay','--terrain-origin-x','9','--terrain-origin-y','0']
 if two:launch.append('--ship-pointer-replay-two-orders')
 sink_path=menu.TOOLCHAIN/'opt/wine-stable/lib/wine/x86_64-windows/notepad.exe';sink_launch=['bash',str(terrain.LAUNCHER),str(sink_path)]
 metadata={'launch':launch,'provenance':baseline,'two_orders':two,'focus_cancel_requested':focus_cancel,'input_injection':'synthetic-InputSystem-QueueStateEvent','os_mouse_validated':False,'limitations':LIMITATIONS}
 if focus_cancel:
  require(sink_path.is_file(),'Owned Wine Notepad focus sink missing');metadata['focus_probe']=focus_probe_metadata();metadata['focus_sink']={'kind':'owned-Wine-Notepad','path':str(sink_path),'sha256':menu.file_sha256(sink_path),'launch':sink_launch}
 menu.write_json(output/'launch.json',metadata)
 player=xvfb=sink=probe=wl=xl=sl=None;sink_window=None;failure=None;report=None;captures={};focus_done=False;focus_evidence=None;started=time.monotonic()
 try:
  require(not menu.DISPLAY_SOCKET.exists(),'Display79 already owned')
  xl=(output/'xvfb.log').open('w');xvfb=subprocess.Popen([str(menu.TOOLCHAIN/'usr/bin/Xvfb'),menu.DISPLAY,'-screen','0','1920x1080x24','-nolisten','tcp','-ac'],env=env,stdout=xl,stderr=subprocess.STDOUT);menu.wait_for_display(xvfb)
  if focus_cancel:
   sl=(output/'focus-sink.log').open('w');sink=subprocess.Popen(sink_launch,cwd=terrain.EXECUTABLE.parent,env=env,stdout=sl,stderr=subprocess.STDOUT)
   deadline=time.monotonic()+12
   while sink_window is None:
    require(sink.poll()is None,'Owned Wine Notepad exited before visible focus sink')
    found=subprocess.run([str(menu.TOOLCHAIN/'usr/bin/xdotool'),'search','--onlyvisible','--name','[Nn]otepad'],env=env,capture_output=True,text=True,timeout=2)
    if found.returncode==0 and found.stdout.strip():sink_window=found.stdout.strip().splitlines()[-1]
    else:require(time.monotonic()<deadline,'No visible owned Wine Notepad within12s');time.sleep(.05)
  wl=(output/'wine-launch.log').open('w');player=subprocess.Popen(launch,cwd=terrain.EXECUTABLE.parent,env=env,stdout=wl,stderr=subprocess.STDOUT)
  window=units.wait_for_ready(player,env,log);geometry=menu.xdotool(env,'getwindowgeometry','--shell',window);(output/'geometry.txt').write_text(geometry)
  values=dict(x.split('=',1)for x in geometry.splitlines()if'='in x);require(tuple(int(values[x])for x in('X','Y','WIDTH','HEIGHT'))==(0,0,1920,1080),'Pointer player notfullscreen1920x1080')
  while True:
   text=terrain.read_log(log)
   if REPLAY+'stage:'in text:
    parsed,model=parse_log(text,reference,two);seen=re.findall(re.escape(REPLAY)+r'stage: ([^;\r\n]+);',text)
    if seen:
     stage=seen[-1];require(all(s in captures for s in seen[:-1]),'Missed pointer capture stage')
     if stage not in captures:captures[stage]=capture_checkpoint(player,env,output,log,reference,two,stage);menu.write_json(output/'captures.json',captures)
     if focus_cancel and stage=='cancel-down'and not focus_done:
      # Foreground HWND is a Win32 observation; X input focus alone did not deliver Unity focus loss.
      require(sink.poll()is None and sink_window!=window,'Owned focus sink is unavailable')
      parsed,_=parse_log(terrain.read_log(log),reference,two);cancels_before=len(parsed['cancels'])
      with(output/'focus-probe-stdout.log').open('w')as po,(output/'focus-probe-stderr.log').open('w')as pe:
       probe=subprocess.Popen(metadata['focus_probe']['launch'],cwd=terrain.EXECUTABLE.parent,env=env,stdout=po,stderr=pe)
       require(probe.wait(timeout=1.0)==0,'Native Win32 foreground probe failed; see preserved stdout/stderr')
      foreground=validate_focus_foreground((output/'focus-probe-stdout.log').read_text());menu.write_json(output/'focus-probe-result.json',foreground)
      metadata['focus_probe_observed']=foreground
      deadline=time.monotonic()+.25
      while True:
       focus_parsed,_=parse_log(terrain.read_log(log),reference,two)
       if len(focus_parsed['cancels'])>cancels_before:break
       require(time.monotonic()<deadline,'Verified Win32 foreground changes did not produce actual Unity cancellation');time.sleep(.01)
      new_cancels=focus_parsed['cancels'][cancels_before:]
      require(new_cancels and all(row=={'counter':0,'selected':True,'synthesized_up':False}for row in new_cancels),'Unexpected focus cancellation context')
      require(len(focus_parsed['events'])==12 and focus_parsed['checkpoints'][-1]['stage']=='cancel-down','Focus cancellation manufactured input edges or missed held phase')
      focus_evidence={'sink_xwindow':sink_window,'player_xwindow':window,'win32_foreground':foreground,'cancels':new_cancels,'cancel':new_cancels[0],'event_count_before':len(parsed['events']),'event_count_after':len(focus_parsed['events'])};focus_done=True
   if player.poll()is not None:break
   require(time.monotonic()-started<145,'Pointer replay timeout');time.sleep(.02)
  require(player.wait(timeout=10)==0,'Pointer player exit failure');parsed,model=parse_log(terrain.read_log(log),reference,two,complete=True)
  require(not focus_cancel or focus_done,'Requested focus cancellation was not validated')
  require(set(captures)==set(stages(two)),'Notall pointerframescaptured');require(provenance()==baseline,'Pointer sources/build changed')
  report=dict(metadata,passed=True,geometry=geometry,captures=captures,parsed_log=parsed,exit_code=0,focus_cancel_performed=focus_done,focus_cancel_evidence=focus_evidence,elapsed_seconds=time.monotonic()-started,
   screenshots={p.name:menu.file_sha256(p)for p in sorted(output.glob('*.png'))})
 except Exception as e:failure=e
 finally:
  cleanup=[]
  for process,label in((probe,'owned Win32 foreground probe'),(player,'player'),(sink,'owned Wine Notepad'),(xvfb,'Xvfb')):
   issue=menu.stop_owned_process(process,label)
   if issue:cleanup.append(issue)
  for stream in(wl,sl,xl):
   if stream is not None:stream.close()
  if cleanup and failure is None:failure=RuntimeError('Own pointer process cleanup failed: '+str(cleanup))
 if failure is not None:
  menu.write_json(output/'failure.json',dict(metadata,passed=False,failure_type=type(failure).__name__,failure=str(failure)));raise failure
 report['owned_focus_sink_stopped']=sink is None or sink.poll()is not None
 menu.write_json(output/'report.json',report);return report

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--two-orders',action='store_true');p.add_argument('--focus-cancel',action='store_true');p.add_argument('--validate-log',type=Path)
 a=p.parse_args()
 if a.validate_log:
  parsed,_=parse_log(a.validate_log.read_text(),load_reference(),a.two_orders,complete=True);print(json.dumps({'passed':True,'stages':len(parsed['checkpoints']),'events':len(parsed['events']),'scope':'logonly'}));return
 r=run_smoke(a.output,a.two_orders,a.focus_cancel);print(json.dumps({'passed':r['passed'],'captures':len(r['captures'])}))
if __name__=='__main__':main()
