#!/usr/bin/env python3
"""Actual native source0b adjacent planner; no general pathfinder or movement port."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import validate_mission_object_selection as source
from tools import validate_mission_ship_seed as ships
from tools.validate_boss_ai_gate import EXPECTED,require

OUT=ROOT/'artifacts/navigation/adjacent'
OBJ,APP,SYSTEM,PAYLOAD,SPRITE=(source.CONTEXT,source.CONTEXT+0x10000,source.CONTEXT+0x20000,
                            source.CONTEXT+0x30000,source.CONTEXT+0x40000)
GRID,PATH,WEATHER,PLAYERS=(source.CONTEXT+0x50000,source.CONTEXT+0x60000,
                        source.CONTEXT+0x70000,source.CONTEXT+0x80000)
END=source.END


def validate(source_root=source.SOURCE_ROOT):
    import pefile
    from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
    from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_ECX,UC_X86_REG_EIP,UC_X86_REG_ESP
    sources=source.checked_sources(source_root)
    image_pe=pefile.PE(data=sources['installed/ancient.exe'])
    image=image_pe.get_memory_mapped_image();image_size=image_pe.OPTIONAL_HEADER.SizeOfImage
    flagsraw=(ROOT/'tests/fixtures/mission_cell_flags.bin').read_bytes()
    require(hashlib.sha256(flagsraw).hexdigest()=='eb8c22b2dc3a3d6de5be5c5a28560701333cbc8610e8dd687052f4f93b260283','Flags fixture changed')
    records=ships.source_records(sources)
    selected=[(entry,payload) for entry,payload in records if entry['name']=='OBJ_0000000b']
    require(len(selected)==1,'Source0b missing')
    entry,payload=selected[0]
    heading=struct.unpack_from('<b',payload,44)[0]
    require(heading==5 and struct.unpack_from('<ii',payload,36)==(16,2),'Source0b seed differs')
    directions=[struct.unpack_from('<hhB',image,0x5c4f44-0x400000+h*5) for h in range(8)]
    require(directions==[(1,0,0),(1,-1,0),(0,-1,0),(-1,-1,0),(-1,0,0),(-1,1,0),(0,1,0),(1,1,0)],'Direction table changed')
    results=[]

    def run(label, pending, wind_strength=0, wind_heading=5, target=(15,3), blocked=False, maximum=150, native_navigation=False):
        uc=source.new_engine(image,image_size)
        put=lambda a,v:source.put(uc,a,v)
        get=lambda a:source.get(uc,a)
        signed=lambda a:struct.unpack('<i',uc.mem_read(a,4))[0]
        byte=lambda a:bytes(uc.mem_read(a,1))[0]
        phase=['init'];tick=[0];services=[];writes=[];next_heap=[source.CONTEXT+0xb0000];history=[];animation_tail=[False]

        def ret(clean=0,eax=0):
            sp=uc.reg_read(UC_X86_REG_ESP)
            uc.reg_write(UC_X86_REG_EIP,get(sp));uc.reg_write(UC_X86_REG_ESP,sp+4+clean)
            uc.reg_write(UC_X86_REG_EAX,eax&0xffffffff)

        def hook(engine,address,size,unused):
            history.append(address)
            if len(history)>32:history.pop(0)
            if phase[0]=='movement' and address==0x4a4d49:animation_tail[0]=True
            if address==0x587318:
                ret();return
            if address in (0x557700,0x589bf5):
                sp=uc.reg_read(UC_X86_REG_ESP);length=get(sp+4);allocated=next_heap[0]
                next_heap[0]+=(length+15)&~15
                require(next_heap[0]<source.CONTEXT+0xef000,'Bounded native path heap exhausted')
                services.append({'phase':phase[0],'tick':tick[0],'entry':hex(address),
                                 'service':'bounded path allocation','arguments':[length],'result':hex(allocated)})
                ret(4 if address==0x557700 else 0,allocated);return
            if address==0x589bc6:
                sp=uc.reg_read(UC_X86_REG_ESP)
                services.append({'phase':phase[0],'tick':tick[0],'entry':hex(address),
                                 'service':'bounded heap delete','arguments':[hex(get(sp+4))]})
                ret();return
            if address==0x5576e0:
                sp=uc.reg_read(UC_X86_REG_ESP);pointer=get(sp+4)
                services.append({'phase':phase[0],'tick':tick[0],'entry':hex(address),
                                 'service':'bounded path deallocation','arguments':[hex(pointer),hex(get(pointer))]})
                put(pointer,0);ret(4);return
            boundaries_init={0x4e7220:(0,'initial command dispatch'),0x4bee60:(0,'unrelated derived initialization'),
                             0x50e640:(4,'object system message'),0x4e1bb0:(4,'damage sprite request'),
                             0x4b97d0:(16,'initial order queue')}
            boundaries_move={0x50d130:(8,'sprite depth publication'),0x50d5f0:(28,'sprite frame publication'),
                             0x50e7c0:(12,'visibility remove'),0x50e780:(12,'visibility add'),
                             0x4a1700:(16,'arrival system notification')}
            boundaries=boundaries_init if phase[0]=='init' else boundaries_move
            if address in boundaries:
                clean,name=boundaries[address];sp=uc.reg_read(UC_X86_REG_ESP)
                services.append({'phase':phase[0],'tick':tick[0],'entry':hex(address),'service':name,
                                 'arguments':[get(sp+4+i*4) for i in range(clean//4)]})
                ret(clean);return
            if address in (0x556610,0x556880):raise AssertionError('Original error path '+hex(address))

        def onwrite(engine,access,address,size,value,unused):
            if phase[0]=='movement' and GRID+8<=address<GRID+8+24*576:
                offset=address-GRID-8
                if offset%24==4:
                    writes.append({'tick':tick[0],'instruction':hex(engine.reg_read(UC_X86_REG_EIP)),
                                   'cell_index':offset//24,'cell':[offset//24%24,offset//24//24],
                                   'before':hex(get(address)),'after':hex(value&0xffffffff),'size':size})

        uc.hook_add(UC_HOOK_CODE,hook);uc.hook_add(UC_HOOK_MEM_WRITE,onwrite)
        def invoke(address,args=()):
            sp=source.STACK+source.STACK_SIZE-0x1000
            for i,v in enumerate((END,*args)):put(sp+4*i,v)
            uc.reg_write(UC_X86_REG_ESP,sp);uc.reg_write(UC_X86_REG_ECX,OBJ)
            try:uc.emu_start(address,END,count=100000)
            except Exception as error:
                raise AssertionError(str(error)+' phase='+phase[0]+' entry='+hex(address)+' eip='+hex(uc.reg_read(UC_X86_REG_EIP))+' recent='+','.join(map(hex,history))) from error
            require(uc.reg_read(UC_X86_REG_EIP)==END,'Original call failed to return '+hex(address))
            
            if phase[0] != 'navigation': require(get(0x5d1f90)==0xabcdef01,'Exception chain not restored '+hex(address))
            return uc.reg_read(UC_X86_REG_EAX)

        put(0x5d1f90,0xabcdef01);invoke(0x4dc3f0)
        for off,value in ((0xc,APP),(0x10,APP),(0x4c,0xb),(0x68,APP),(0x6c,SYSTEM),(0x70,SYSTEM)):
            put(OBJ+off,value)
        uc.mem_write(PAYLOAD,payload);invoke(0x4dfa90,(PAYLOAD,))
        put(0x5c7508,PLAYERS)
        invoke(0x4bece0)
        speed_limit=signed(OBJ+0x59f);acceleration=signed(OBJ+0x280)
        require((speed_limit,acceleration)==(60000,1200),'Original baseline speed values differ')
        put(OBJ+0x8be,SPRITE);put(SPRITE+0x61,56);put(SPRITE+0x65,56)
        put(SPRITE+0x59,1028);put(SPRITE+0x5d,132);put(SPRITE+0x45,20)
        put(SPRITE+0x7d,2);put(SPRITE+0x81,0)
        put(0x5c74fc,GRID);put(0x5c74ec,24);put(0x5c74f0,24);put(0x5c74e8,576)
        uc.mem_write(GRID,struct.pack('<hhhh',24,24,64,64))
        for index,flags in enumerate(struct.unpack('<576I',flagsraw)):put(GRID+8+24*index,flags)
        pointermap={0xb:OBJ}
        for index,(record,raw) in enumerate(records):
            instance=int(record['name'][4:],16);pointer=OBJ if instance==0xb else source.CONTEXT+0xa0000+index*0x1000
            pointermap[instance]=pointer
            x,y=struct.unpack_from('<ii',raw,36)
            for off,value in ((0x4c,instance),(0x50,200+struct.unpack_from('<I',raw,28)[0]),(0x5a3,x),(0x5a7,y)):
                put(pointer+off,value)
            invoke(0x499830,(0,pointer,y*24+x))
        target_index=target[1]*24+target[0]
        if blocked:put(GRID+8+target_index*24+4,pointermap[0xc])
        put(0x5c6a40,WEATHER);put(WEATHER+0x34,wind_strength);uc.mem_write(WEATHER+0x38,bytes([wind_heading]))
        navigation=None
        if native_navigation:
            # Exact native passability-map initialization prefix. The rest
            # builds a separate shore map not read by this adjacent branch.
            for address,pointer in ((0x5c93bc,source.CONTEXT+0x90000),
                                    (0x5c9398,source.CONTEXT+0x91000),
                                    (0x5c93c0,source.CONTEXT+0x92000)):
                put(address,pointer)
            phase[0]='navigation';sp=source.STACK+source.STACK_SIZE-0x1000
            put(sp,END);uc.reg_write(UC_X86_REG_ESP,sp);uc.reg_write(UC_X86_REG_ECX,OBJ)
            uc.emu_start(0x49a950,0x49a9ce,count=30000)
            require(uc.reg_read(UC_X86_REG_EIP)==0x49a9ce,'Native path-map prefix did not finish')
            map_hashes={hex(address):hashlib.sha256(bytes(uc.mem_read(get(address),1152))).hexdigest()
                        for address in (0x5c93bc,0x5c9398)}
            # ProcPostMove refuses a second plan in the same source stamp.
            put(SYSTEM+0xde,1)
            navigation_return=invoke(0x4a6330,(0,0,*target,0,1,0))
            native_path=get(OBJ+0x5c2);path_count=get(OBJ+0x5ba)
            require(path_count in (0,2),'Unexpected adjacent path point count')
            navigation={'entry':'0x4a6330','return_low_byte':navigation_return&255,
                        'path_hex':bytes(uc.mem_read(native_path,path_count*5)).hex() if native_path else '',
                        'points':[list(struct.unpack('<hhB',uc.mem_read(native_path+5*i,5))) for i in range(path_count)],
                        'path_index':get(OBJ+0x5be),'state':byte(OBJ+0x58c),'center_gate':byte(OBJ+0x596),
                        'exception_chain_after':hex(get(0x5d1f90)),
                        'map_prefix':{'start':'0x49a950','stop_before':'0x49a9ce','hooks':{},'map_sha256':map_hashes}}
            require((not native_path and path_count==0) or get(0x5d1f90)==0xabcdef01,'Successful planner must restore exception chain')
            return {'label':label,'target':list(target),'target_flags':get(GRID+8+target_index*24),'navigation':navigation,'services':services}
    for h,(dx,dy,_) in enumerate(directions):
        results.append(run('heading'+str(h),1,target=(16+dx,2+dy),native_navigation=True))
    return {'original_exe_sha256':EXPECTED,'source_hashes':source.SOURCE_HASHES,
            'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'source_cell_flags_sha256':hashlib.sha256(flagsraw).hexdigest(),
            'kind':'Actual native adjacent ProcPostMove/GetWayNew for source0b static fleet8',
            'directions':directions,'cases':results}



def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=OUT/'native-planner.json')
    args=parser.parse_args()
    if args.output.exists():parser.error('Select a fresh output path')
    result=validate();args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print('8 actual native adjacent planner cases passed')

if __name__=='__main__':main()
