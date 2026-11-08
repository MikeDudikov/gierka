#!/usr/bin/env python3
"""Stage bounded original selection/cursor art; no preview or inferred artwork."""
from __future__ import annotations
import argparse,json,hashlib,struct
from pathlib import Path
from PIL import Image
if __package__:
 from .inspect_dkx import inspect_pair
 from .decode_sprite import resource_payload,decode_sprite,dib_palette
 from .inspect_world_reference import base_palette_sprite
 from .stage_unity_reference import bottom_up_rgba
 from .stage_mission_objects import write_payloads
else:
 from inspect_dkx import inspect_pair
 from decode_sprite import resource_payload,decode_sprite,dib_palette
 from inspect_world_reference import base_palette_sprite
 from stage_unity_reference import bottom_up_rgba
 from stage_mission_objects import write_payloads
ROOT=Path(__file__).resolve().parents[1]
SOURCE_ROOT=ROOT/'reference/raw/ancient-conquest'
MANIFEST_NAME='ShipPointerVisualsManifest.json'
SOURCE_HASHES={
 'installed/ancient.exe':'cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021',
 'installed/missions/controlm.dkx':'b32a80c703650d8873938544ee4b0718c70a2fd5a577d1b2814bf21b97224974',
 'installed/missions/controlm.dkd':'6f4b90903c880baf938d94577f8058904fafab5008b1963104cc8253cd842cbe',
 'installed/missions/maplib.dkx':'05484166ca374630f7c29c26e561656a11941ef331fb014e52f72aed81c23650',
 'installed/missions/maplib.dkd':'7fe0623d957e196e5279c6bced55db292648b5c9ebc6f1420fcd293c0685b685',
 'files/DATA/OBJECTS.DKX':'67aa31b7e7728a1c4f215c63932b55ea66f3ac1ecdb732bfd368bae2a8375f60',
 'files/DATA/OBJECTS.DKD':'01474065782a7170d54f564df2205572f8a0675411bef0f350dab55c3fd20e50'}
SEQUENCES=(('selector','RAM_056X056','objects',10,0,'source-counter'),
 ('cursor_std_n','CUR_STD_N','control',1,10000,'source-cached-ms'),('cursor_std_g','CUR_STD_G','control',1,10000,'source-cached-ms'),
 ('cursor_own_n','CUR_OWN_N','control',1,10000,'source-cached-ms'),('cursor_own_g','CUR_OWN_G','control',1,10000,'source-cached-ms'),
 ('cursor_select_n','CUR_SELECT_N','control',1,10000,'source-cached-ms'),('cursor_select_g','CUR_SELECT_G','control',1,10000,'source-cached-ms'),
 ('cursor_sea_n','CUR_SEA_N','control',4,150,'source-cached-ms'),('cursor_sea_g','CUR_SEA_G','control',4,150,'source-cached-ms'),
 ('confirm','TAKE_CMD','control',4,250,'source-cached-ms'))
def digest(raw):return hashlib.sha256(raw).hexdigest()
def checked_sources(source_root=SOURCE_ROOT):
 result={}
 for name,sha in SOURCE_HASHES.items():
  raw=(Path(source_root)/name).read_bytes()
  if digest(raw)!=sha:raise ValueError('Original pointer visual source differs: '+name)
  result[name]=raw
 return result
def healthbar_plane(palette):
 #50c650 full-health path:34-wide allocation;32-wide black rect,
 #inclusive horizontal lines x1..30 in palette200 and199. Final2columns untouched.
 rgba=Image.new('RGBA',(34,4));pixels=rgba.load()
 for y in range(4):
  for x in range(32):pixels[x,y]=tuple(palette[:3])+(255,)
 for y,index in ((1,200),(2,199)):
  rgb=tuple(palette[index*3:index*3+3])+(255,)
  for x in range(1,31):pixels[x,y]=rgb
 return rgba
def compose(source_root=SOURCE_ROOT):
 sources=checked_sources(source_root);archives={}
 for key,base,ix,dt in [('control','installed/missions/controlm','.dkx','.dkd'),('objects','files/DATA/OBJECTS','.DKX','.DKD'),('map','installed/missions/maplib','.dkx','.dkd')]:
  data=sources[base+dt];archives[key]=({(e['type'],e['name']):e for e in inspect_pair(sources[base+ix],data)},data)
 lookup,data=archives['map'];palraw=resource_payload(lookup[1,'PALETTE'],data);palette=dib_palette(palraw)
 atlas=Image.new('RGBA',(1024,128));frames=[];sequences=[]
 def add(name,image,metadata):
  index=len(frames);left=(index%16)*64;top=(index//16)*64
  if image.width>64 or image.height>64:raise ValueError('Source pointer plane exceeds64slot')
  atlas.paste(image,(left,top));frames.append(dict(name=name,atlas_x=left,atlas_y=128-top-image.height,width=image.width,height=image.height,rgba_sha256=digest(image.tobytes()),**metadata));return index
 for key,name,archive,count,interval,clock in SEQUENCES:
  lookup,data=archives[archive];raw=resource_payload(lookup[7,name],data)
  if len(raw)!=49:raise ValueError('Original pointer animation descriptor differs: '+name)
  prefix=raw[:32].split(b'\0')[0].decode('ascii');digits=raw[32];start,n=struct.unpack_from('<hh',raw,33)
  if (prefix,digits,start,n)!=(name,2,0,count):raise ValueError('Unexpected pointer animation descriptor: '+name)
  indices=[]
  for i in range(count):
   frame_name=prefix+f'{i:02d}';payload=resource_payload(lookup[6,frame_name],data);sprite=decode_sprite(payload)
   if sprite['flags']&0x100:raise ValueError('Unsupported alternate source pointer blend')
   image=base_palette_sprite(sprite,palette)
   indices.append(add(frame_name,image,dict(source_archive=archive,payload_sha256=digest(payload),flags=sprite['flags'],bounds=[sprite[k]for k in('left','top','box_width','box_height')],covered_pixels=sum(bool(x)for x in sprite['coverage']))))
  sequences.append(dict(id=key,resource_name=name,descriptor_sha256=digest(raw),frames=indices,clock=clock,interval=interval))
 health=add('HEALTH_100_60',healthbar_plane(palette),dict(source_archive='generated-from-native50c650',health_percent=100))
 if len(frames)!=29:raise ValueError('Pointer visual atlas count differs')
 manifest={'schema_version':1,'mission':'miss000','native_canvas_width':1920,'native_canvas_height':1080,'atlas_width':1024,'atlas_height':128,'slot_size':64,'frame_count':len(frames),'source_hashes':SOURCE_HASHES,'palette_resource':'maplib:PALETTE','palette_payload_sha256':digest(palraw),'frames':frames,'sequences':sequences,'selector':{'sequence':'selector','width':60,'height':60,'world_offset_x':-2,'world_offset_y':-2,'depth':1020},'healthbar':{'frame':health,'width':34,'height':4,'world_offset_x':12,'world_offset_y':-2,'depth':1020,'health_percent':100,'initially_visible':False},'cursor_hotspots':[{'type':0,'x':0,'y':0},{'type':5,'x':0,'y':0},{'type':6,'x':0,'y':0},{'type':7,'x':-18,'y':-17}],'confirm':{'sequence':'confirm','normal_map_world_offset_x':-11,'normal_map_world_offset_y':-24},'limits':['Healthy normal source0b logical56x56; full-health IL bar only','Source palette/index art is a fidelity reference,not final2026art','No full world/selected actors/cursor modes or OS input validation','CUR suffix N when cursor+e6==0,G otherwise; raw source planes include transparent margins']}
 return {'ShipPointerVisualsRgba.bytes':bottom_up_rgba(atlas)},manifest
def stage(source_root,project,*,replace_generated=False):
 payloads,manifest=compose(source_root);destination=Path(project)/'Assets/Resources/ShipPointerVisualsGenerated'
 return write_payloads(destination,payloads,manifest,replace_generated=replace_generated,manifest_name=MANIFEST_NAME)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,default=SOURCE_ROOT);p.add_argument('--project',type=Path,default=ROOT/'Unity/AncientConquest');p.add_argument('--replace-generated',action='store_true');a=p.parse_args();print(json.dumps(stage(a.source_root,a.project,replace_generated=a.replace_generated),indent=2))
if __name__=='__main__':main()
