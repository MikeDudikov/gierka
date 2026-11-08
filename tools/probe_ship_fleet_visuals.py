"""Native selector56/64/72 progression, all RLE planes, actual health initialization and pixels."""
import argparse,json,struct
from pathlib import Path
from tools import probe_ship_selection_visuals as original,probe_ship_pointer_pixels as pixels,stage_ship_fleet_visuals as stage
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_ECX,UC_X86_REG_EAX

class NativeSizedSelection(original.NativeSelection):
    def __init__(self,image,size,logical):
        self.logical=logical;super().__init__(image,size);self.w(original.MAIN+0x61,logical);self.w(original.MAIN+0x65,logical)
    def hook(self,u,a,size,unused):
        sp=u.reg_read(UC_X86_REG_ESP);logical=self.logical
        if a==0x4e0c80:
            assert [self.r(sp+4),self.r(sp+8)]==[logical,logical]
            self.u.mem_write(original.NAME,f'RAM_{logical:03d}X{logical:03d}\0'.encode());self.ret(8,original.NAME)
        elif a==0x50d010:
            args=[self.r(sp+4+i*4)for i in range(5)];assert args[:3]==[4,7,0]
            assert bytes(u.mem_read(args[3],11)).decode()==f'RAM_{logical:03d}X{logical:03d}'
            self.w(original.SEL+0x61,logical+4);self.w(original.SEL+0x65,logical+4);self.w(original.SEL+0x49,10);self.ret(20)
        elif a==0x50c890:
            assert [self.r(sp+4)&65535,self.r(sp+8)&65535,self.r(sp+12)]==[0x6464,logical+4,1020]
            self.w(original.OBJ+0x3e,22);self.ret(12)
        else:super().hook(u,a,size,unused)

def sized_cases():
    _,image,size=original.native_image();rows=[]
    for logical in stage.SIZES:
        for case in original.cases():
            n=NativeSizedSelection(image,size,logical)
            rows.append(dict(case,logical_size=logical,rows=[n.op(op)for op in case['operations']]))
    return rows

def rle():
    saved=original.art.SEQUENCES
    try:
        original.art.SEQUENCES=tuple((f'selector_{size}',f'RAM_{size:03d}X{size:03d}','objects',10,0,'counter')for size in stage.SIZES)
        return pixels.rle()
    finally:original.art.SEQUENCES=saved

def health():
    from tools.inspect_dkx import inspect_pair
    from tools.decode_sprite import resource_payload,dib_palette
    sources=stage.pointer.checked_sources();data=sources['installed/missions/maplib.dkd'];lut={(e['type'],e['name']):e for e in inspect_pair(sources['installed/missions/maplib.dkx'],data)};palette=dib_palette(resource_payload(lut[1,'PALETTE'],data));records=[]
    _,image,size=original.native_image()
    for logical in stage.SIZES:
        q=original.queue.NativeQueue(image,size);u=q.u;u.mem_map(0,4096);canvas=original.BUFFER;surface=original.SURFACE
        q.w(original.queue.M,original.APP)
        for a,value in((original.OBJ+0x10,original.APP),(original.APP+0xda5,original.queue.M),(original.APP+0xd9d,surface),(surface+0x20,8),(surface+0x70,canvas),(surface+0x74,64),(surface+0x88,64),(surface+0x8c,16),(surface+0x9c,0xffffffff)):q.w(a,value)
        def ret(clean=0):
            sp=u.reg_read(UC_X86_REG_ESP);u.reg_write(UC_X86_REG_EIP,q.r(sp));u.reg_write(UC_X86_REG_ESP,sp+4+clean);u.reg_write(UC_X86_REG_EAX,0)
        def boundary(u,a,size,unused):
            if a==0x587318:ret()
            elif a in(0x556610,0x556880,0x5565f0):raise AssertionError('Native health error')
            elif a in(0x567d20,0x567de0):ret(4)
            elif a==0x567850:
                sp=u.reg_read(UC_X86_REG_ESP);s,x,y,w,h,color=[q.r(sp+4+i*4)for i in range(6)];assert s==surface
                for row in range(h):u.mem_write(canvas+(y+row)*64+x,bytes([color&255])*w)
                ret(24)
        u.hook_add(UC_HOOK_CODE,boundary);u.reg_write(UC_X86_REG_ECX,original.OBJ);q.call(0x50c890,(0x6464,logical+4,1020))
        width=struct.unpack('<H',u.mem_read(original.OBJ+0x44,2))[0];assert width==logical-22
        node=q.r(original.queue.IDS+4*q.r(original.OBJ+0x3e));assert q.r(node+0x20)==width and q.r(node+0x24)==4 and q.r(node+0x44)==1020
        expected=stage.healthbar(palette,width).tobytes()
        for sentinel in(0x55,0xaa):
            u.mem_write(canvas,bytes([sentinel])*(64*16));q.call(0x50c650,(0,0,0,5,3,0,0,original.OBJ));result=bytes(u.mem_read(canvas,64*16));rgba=bytearray()
            for y in range(4):
                for x in range(width):
                    index=result[(y+3)*64+x+5];rgba.extend((*palette[index*3:index*3+3],255)if index!=sentinel else(0,0,0,0))
            assert bytes(rgba)==expected
            records.append({'logical_size':logical,'selector_size':logical+4,'health_width':width,'sentinel':sentinel,'rgba_sha256':stage.pointer.digest(rgba),'buffer_sha256':stage.pointer.digest(result)})
    return {'records':records,'entries':['50c890 actual callback initialization','50c650','56ea10'],'boundaries':['normal setjmp','solid fill567850 into owned buffer','surface lock/unlock']}

def fixture():return {'schema_version':1,'original_exe_sha256':stage.pointer.SOURCE_HASHES['installed/ancient.exe'],'cases':sized_cases(),'rle':rle(),'health':health(),'scope':'Normal square selector56/64/72 and100% health. Shared existing isolated renderer-loader boundaries, no full ship Life/damage/2026 art proof.'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();data=fixture();a.output.write_text(json.dumps(data,indent=2)+'\n');print({'states':sum(len(c['rows'])for c in data['cases']),'rle_frames':data['rle']['frames'],'rle_comparisons':data['rle']['comparisons'],'health_cases':len(data['health']['records'])})
if __name__=='__main__':main()
