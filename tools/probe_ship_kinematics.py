#!/usr/bin/env python3
"""Read-only x86 kinematics evidence: controlled prepared path, not order/AI replay."""
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

OUT=ROOT/'artifacts/movement/kinematics'
OBJ,APP,SYSTEM,PAYLOAD,SPRITE=(source.CONTEXT,source.CONTEXT+0x10000,source.CONTEXT+0x20000,
                            source.CONTEXT+0x30000,source.CONTEXT+0x40000)
GRID,PATH,WEATHER,PLAYERS=(source.CONTEXT+0x50000,source.CONTEXT+0x60000,
                        source.CONTEXT+0x70000,source.CONTEXT+0x80000)
END=source.END


def validate():
    import pefile
    from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
    from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_ECX,UC_X86_REG_EIP,UC_X86_REG_ESP
    sources=source.checked_sources(source.SOURCE_ROOT)
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
            require(get(0x5d1f90)==0xabcdef01,'Exception chain not restored '+hex(address))
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
            require(native_path and path_count==2,'Adjacent native path must contain source and target')
            navigation={'entry':'0x4a6330','return_low_byte':navigation_return&255,
                        'path_hex':bytes(uc.mem_read(native_path,path_count*5)).hex(),
                        'points':[list(struct.unpack('<hhB',uc.mem_read(native_path+5*i,5))) for i in range(path_count)],
                        'path_index':get(OBJ+0x5be),'state':byte(OBJ+0x58c),'center_gate':byte(OBJ+0x596),
                        'map_prefix':{'start':'0x49a950','stop_before':'0x49a9ce','hooks':{},'map_sha256':map_hashes}}
            require(navigation['points']==[[16,2,5],[15,3,5]],'Actual native adjacent path differs')
        else:
            uc.mem_write(PATH,struct.pack('<hhBhhB',16,2,heading,*target,heading))
            put(OBJ+0x5c2,PATH);put(OBJ+0x5ba,2);put(OBJ+0x5be,1)
            put(OBJ+0x5b2,target_index);put(OBJ+0x5ab,-1)
            uc.mem_write(OBJ+0x58c,b'\x03');uc.mem_write(OBJ+0x596,b'\x01')
        phase[0]='movement';snapshots=[]
        def snapshot():
            return {'tick':tick[0],'pending_steps':get(APP+0xe2),'stamp':get(SYSTEM+0xde),
                    'cell':[signed(OBJ+0x5a3),signed(OBJ+0x5a7)],
                    'world':[signed(SPRITE+0x59),signed(SPRITE+0x5d)],
                    'state':byte(OBJ+0x58c),'center_gate':byte(OBJ+0x596),'heading':byte(OBJ+0x5af),
                    'speed':signed(OBJ+0x59b),'remainder':signed(OBJ+0x597),'deceleration':signed(OBJ+0x284),
                    'reserved':signed(OBJ+0x5ab),'next_cell':signed(OBJ+0x5b6),'path_index':signed(OBJ+0x5be),
                    'path_count':signed(OBJ+0x5ba),'frame':signed(SPRITE+0x45),
                    'animation_tail_reached':animation_tail[0],
                    'occupied_cell_count':sum(get(GRID+8+i*24+4)!=0 for i in range(576)),
                    'owned_cells':[i for i in range(576) if get(GRID+8+i*24+4)==OBJ]}
        snapshots.append(snapshot())
        for step in range(1,maximum+1):
            tick[0]=step;put(APP+0xe2,pending);put(SYSTEM+0xde,step+(1 if native_navigation else 0))
            animation_tail[0]=False
            invoke(0x4a3f40);snapshots.append(snapshot())
            if not blocked and snapshots[-1]['cell']==list(target) and snapshots[-1]['world']==[target[0]*64+4,target[1]*64+4] and snapshots[-1]['state']==0:
                break
            if blocked and snapshots[-1]['state']==0:break
        return {'label':label,'source_resource':entry['name'],'source_payload_sha256':hashlib.sha256(payload).hexdigest(),
                'prepared_target':list(target),'active_path_hex':bytes(uc.mem_read(get(OBJ+0x5c2),get(OBJ+0x5ba)*5)).hex(),
                'native_navigation':navigation,
                'controlled_inputs':{'pending_steps_each_call':pending,'wind_strength':wind_strength,'wind_heading':wind_heading,
                                     'owner_upgrade_byte':0,'blocked_target_with_source0c_pointer':blocked},
                'baseline_speed':speed_limit,'baseline_acceleration':acceleration,
                'trace':snapshots,'grid_writes':writes,'service_boundaries':services,
                'other_seven_source_ship_cells':[{ 'instance_id':int(e['name'][4:],16),'cell':list(struct.unpack_from('<ii',raw,36))}
                                                for e,raw in records if e['name']!=entry['name']]}

    for values in [('southwest_pending1',1),('southwest_pending2',2),('southwest_pending3',3),('southwest_pending7',7),('blocked_target',1,0,5,(15,3),True)]:
        results.append(run(*values))
    results.append(run('native_adjacent_path_pending1',1,native_navigation=True))
    return {'original_exe_sha256':EXPECTED,'source_hashes':source.SOURCE_HASHES,
            'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'source_cell_flags_sha256':hashlib.sha256(flagsraw).hexdigest(),
            'kind':'Actual x86 adjacent planner and full MoveShip traces with controlled weather/time and graphics/visibility/arrival boundaries',
            'directions':directions,'cases':results,
            'excluded':['Move command intake is not executed; native path search is executed only in native_adjacent_path_pending1',
                        'Prepared path and controlled weather/player upgrade do not prove the full original mission world initialization',
                        'Other seven source ships are static occupancy pointers; their AI and lifecycle do not run',
                        'Native wall clock rate is not inferred from pending_steps or animation stamps',
                        'No Unity implementation is compared by this original-only evidence']}


if __name__=='__main__':
    result=validate();OUT.mkdir(parents=True,exist_ok=True)
    output=OUT/'prepared-path-kinematics.json';output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'output':str(output.relative_to(ROOT)), 'cases':len(result['cases']),
                      'last':[{'label':c['label'],'snapshot':c['trace'][-1],'grid_writes':c['grid_writes']} for c in result['cases']]},indent=2))
