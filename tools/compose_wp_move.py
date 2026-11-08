"""Map original4ced80 masks and controlm8:WPMOVE into source-palette frames."""
import hashlib,json
from pathlib import Path
from PIL import Image
from tools import stage_ship_pointer_visuals as pointer
from tools.decode_composite_sprite import decode_composite_frame
FIXTURE_SHA='1b14a1a5c30b802ba81113b8f13fd4ae921609ca2636d9751096029512782d91'


def compose(sources):
    fixture=pointer.ROOT/'tests/fixtures/wp_move.json';raw=fixture.read_bytes()
    if pointer.digest(raw)!=FIXTURE_SHA:raise ValueError('Original WPMOVE constructor fixture differs')
    rows=json.loads(raw)['rows'];data=sources['installed/missions/controlm.dkd']
    entries=pointer.inspect_pair(sources['installed/missions/controlm.dkx'],data)
    descriptor=next(e for e in entries if(e['type'],e['name'])==(8,'WPMOVE'))
    mdata=sources['installed/missions/maplib.dkd'];lookup={(e['type'],e['name']):e for e in pointer.inspect_pair(sources['installed/missions/maplib.dkx'],mdata)}
    palette=pointer.dib_palette(pointer.resource_payload(lookup[1,'PALETTE'],mdata))
    atlas=Image.new('RGBA',(400,320));frames=[];indices=[];masks={}
    for row in rows:
        mask=row['load']['mask']
        if mask not in masks:
            decoded=decode_composite_frame(descriptor,data,entries,0,mask)
            image=Image.new('RGBA',(decoded['width'],decoded['height']))
            for part in decoded['inline_components']:
                plane=pointer.base_palette_sprite(part['sprite'],palette)
                image.alpha_composite(plane,(part['offset_x'],part['offset_y']))
            index=len(frames);x=index%10*40;y=index//10*32
            atlas.paste(image,(x,y));masks[mask]=index
            frames.append(dict(name='WPMOVE_'+str(row['ordinal']),mask=mask,atlas_x=x,atlas_y=320-y-image.height,
                width=image.width,height=image.height,rgba_sha256=pointer.digest(image.tobytes()),
                parts=[dict(index=p['source_index'],name=p['name'],x=p['offset_x'],y=p['offset_y'],depth=p['depth'],sha256=p['payload_sha256'])for p in decoded['components']]))
        indices.append(masks[mask])
    assert len(frames)==100 and len(indices)==256
    payload=pointer.bottom_up_rgba(atlas)
    return payload,dict(resource='ShipFleetVisualsGenerated/WpMoveRgba',width=400,height=320,
        payload_sha256=pointer.digest(payload),frames=frames,ordinal_frames=indices,
        cell_size=64,world_offset_x=14,world_offset_y=18,depth=7,source_resource='controlm:8:WPMOVE',
        source_descriptor=descriptor,constructor_fixture_sha256=FIXTURE_SHA,
        source_functions=['4ced80','545e80','4ced10','554d50','55e0e0'])
