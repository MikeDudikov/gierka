"""Execute the original H1110/A3 type8 loader, inline sort and RLE blitter.

The pinned historical loader bootstrap supplies only source I/O, allocation
and setjmp boundaries. Loader selection/sorting and every RLE pixel execute x86.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_EFLAGS

ROOT=Path(__file__).resolve().parents[1]
BOOTSTRAP=ROOT/'artifacts/movement/animation/validate_ship_a_poses.py'
BOOTSTRAP_SHA='221af8df6348ebe547f4af82d7e79d4c3ce08538e07982416b324669fed93ae7'


def bootstrap():
    raw=BOOTSTRAP.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=BOOTSTRAP_SHA:raise ValueError('Type8 loader bootstrap SHA differs')
    prefix=raw.decode().split("\nrow = load_original(",1)
    if len(prefix)!=2:raise ValueError('Type8 loader bootstrap boundary differs')
    namespace={'__file__':str(BOOTSTRAP),'__name__':'heavy_pose_bootstrap'}
    exec(compile(prefix[0],str(BOOTSTRAP),'exec'),namespace)
    return namespace


def fixture():
    from tools.decode_sprite import decode_sprite
    m=bootstrap();row=m['load_original']('SHIP_H1110',0xa3,list(range(88)))
    names=sorted({p['name']for f in row['frames']for p in f['components']})
    engine=m['engine']();data_address=m['MEM']+0x200000;destination=m['MEM']+0x300000
    pitch=96;canvas=96;guard=256;frames=[];comparisons=0
    for name in names:
        raw=m['resource_payload'](m['resources'][6,name],m['data']);sprite=decode_sprite(raw);engine.mem_write(data_address,raw)
        left,top,w,h=[sprite[k]for k in('left','top','box_width','box_height')]
        rects=[(0,0,w,h)]
        if w>2 and h>2:rects.append((1,1,w-2,h-2))
        if w>2 and h>18:rects.append((1,17,w-2,h-18))
        cases=[]
        for sx,sy,dw,dh in rects:
            for fill in(0x55,0xaa):
                size=guard+canvas*pitch+guard;expected=bytearray([fill])*size;engine.mem_write(destination,bytes(expected))
                offset=guard+(top+sy)*pitch+left+sx
                for y in range(dh):
                    for x in range(dw):
                        pixel=(top+sy+y)*sprite['width']+left+sx+x
                        if sprite['coverage'][pixel]:expected[offset+y*pitch+x]=sprite['indices'][pixel]
                sp=m['STACK']+0x1f000;engine.mem_write(sp,struct.pack('<13I',m['STOP'],destination+offset,pitch,data_address,sx,sy,dw,dh,0,0,0,0,0))
                engine.reg_write(UC_X86_REG_ESP,sp);engine.reg_write(UC_X86_REG_EFLAGS,0x202)
                engine.emu_start(0x574290,m['STOP'],count=1000000)
                assert engine.reg_read(UC_X86_REG_EIP)==m['STOP']
                actual=bytes(engine.mem_read(destination,size));assert actual==expected,(name,sx,sy,fill)
                cases.append({'rectangle':[sx,sy,dw,dh],'sentinel':fill,'destination_sha256':hashlib.sha256(actual).hexdigest()});comparisons+=1
        frames.append({'name':name,'payload_sha256':hashlib.sha256(raw).hexdigest(),'flags':sprite['flags'],
                       'dimensions':[sprite['width'],sprite['height']],'bounds':[left,top,w,h],'cases':cases})
    return {'schema_version':1,'passed':True,'source_hashes':m['SOURCE_HASHES'],'bootstrap_sha256':BOOTSTRAP_SHA,
            'descriptor':'SHIP_H1110','mask':0xa3,'loader_va':'0x554d50','sort_range':['0x55e56b','0x55e659'],
            'loader_hooks':['setjmp','source type8 payload/metadata I/O','allocation','source type6 I/O/cache','resource release'],
            'sort_hooks':[],'pixel_entry':'0x574290','pixel_hooks':[],'row':row,'planes':frames,
            'selected_frames':len(row['frames']),'component_rows':sum(len(f['components'])for f in row['frames']),
            'pixel_buffer_comparisons':comparisons,
            'scope':'Actual H1110 full-health A3 poses0..87;selection/order/indices/coverage only;palette and Unity presentation verified separately'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.error('Use a fresh native output path')
    r=fixture();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,separators=(',',':'))+'\n')
    print({k:r[k]for k in('passed','selected_frames','component_rows','pixel_buffer_comparisons')});print('planes',len(r['planes']))


if __name__=='__main__':main()
