"""Source RAM selector families56/64/72 and their full-health bars; separate ninth resource set."""
from pathlib import Path
import argparse,json,struct
from PIL import Image
from tools import stage_ship_pointer_visuals as pointer
from tools import compose_wp_move
ROOT=pointer.ROOT;MANIFEST_NAME='ShipFleetVisualsManifest.json';SIZES=(56,64,72)
def healthbar(palette,width):
    result=Image.new('RGBA',(width,4));p=result.load()
    for y in range(4):
        for x in range(width-2):p[x,y]=tuple(palette[:3])+(255,)
    for y,index in ((1,200),(2,199)):
        for x in range(1,width-3):p[x,y]=tuple(palette[index*3:index*3+3])+(255,)
    return result

def compose(source_root=pointer.SOURCE_ROOT):
    sources=pointer.checked_sources(source_root)
    raw=sources['files/DATA/OBJECTS.DKD'];lookup={(e['type'],e['name']):e for e in pointer.inspect_pair(sources['files/DATA/OBJECTS.DKX'],raw)}
    mraw=sources['installed/missions/maplib.dkd'];mlookup={(e['type'],e['name']):e for e in pointer.inspect_pair(sources['installed/missions/maplib.dkx'],mraw)}
    palette=pointer.dib_palette(pointer.resource_payload(mlookup[1,'PALETTE'],mraw))
    atlas=Image.new('RGBA',(640,400));frames=[];families=[]
    def add(name,image,extra):
        index=len(frames);x=(index%8)*80;y=(index//8)*80
        assert image.width<=80 and image.height<=80
        atlas.paste(image,(x,y));frames.append(dict(name=name,atlas_x=x,atlas_y=400-y-image.height,width=image.width,height=image.height,rgba_sha256=pointer.digest(image.tobytes()),**extra));return index
    for size in SIZES:
        name=f'RAM_{size:03d}X{size:03d}';descriptor=pointer.resource_payload(lookup[7,name],raw)
        assert descriptor[:32].split(b'\0')[0].decode()==name and descriptor[32]==2 and struct.unpack_from('<hh',descriptor,33)==(0,10)
        indices=[]
        for i in range(10):
            frame=name+f'{i:02d}';payload=pointer.resource_payload(lookup[6,frame],raw);sprite=pointer.decode_sprite(payload);image=pointer.base_palette_sprite(sprite,palette)
            assert image.size==(size+4,size+4)
            indices.append(add(frame,image,{'payload_sha256':pointer.digest(payload)}))
        h=add(f'HEALTH_100_{size+4}',healthbar(palette,size-22),{'source':'50c890/50c650 full-health callback'})
        families.append({'logical_size':size,'selector_size':size+4,'frames':indices,'health_frame':h,'health_width':size-22})
    marker,marker_manifest=compose_wp_move.compose(sources)
    return {'ShipFleetVisualsRgba.bytes':pointer.bottom_up_rgba(atlas),'WpMoveRgba.bytes':marker},{'schema_version':1,'native_canvas_width':1920,'native_canvas_height':1080,'atlas_width':640,'atlas_height':400,'frame_count':33,'frames':frames,'families':families,'wp_move':marker_manifest,'source_hashes':pointer.SOURCE_HASHES,'scope':'Normal selectors/full-health plus source WPMOVE mask table;not final2026 art'}
def stage(source_root,project,replace_generated=False):
    payloads,manifest=compose(source_root);return pointer.write_payloads(Path(project)/'Assets/Resources/ShipFleetVisualsGenerated',payloads,manifest,replace_generated=replace_generated,manifest_name=MANIFEST_NAME)
def main():
    p=argparse.ArgumentParser();p.add_argument('--source-root',type=Path,default=pointer.SOURCE_ROOT);p.add_argument('--project',type=Path,default=ROOT/'Unity/AncientConquest');p.add_argument('--replace-generated',action='store_true');a=p.parse_args();print(json.dumps(stage(a.source_root,a.project,a.replace_generated),indent=2))
if __name__=='__main__':main()
