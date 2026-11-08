#!/usr/bin/env python3
"""Actual current-cell4a5740/4a51b0 maps, nearest paths, RNG and blocker cache."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT)not in sys.path:sys.path.insert(0,str(ROOT))
from tools import validate_mission_object_selection as source


def case_inputs():
    cases=[]
    def add(label,cell,origin,goal,radius=0,retry=0,preserve=True,seed=0,cache=(),reservation=None):
        cases.append({'label':label,'cell':list(cell),'origin':list(origin),'goal':list(goal),'radius':radius,
                      'retry_priority':retry,'preserve_destination_mask':preserve,'random_state':seed,
                      'cached_obstacles':list(cache),'reservation':list(reservation)if reservation else None})
    for cell in ((16,2),(17,2),(18,3),(18,5),(20,4),(14,4),(16,4)):
        for goal in ((20,4),(18,2),(16,5),(16,1),(19,4),(21,5),(14,4),(2,3),(0,0),(23,23)):
            for radius,retry in ((0,0),(1,0),(0,1)):
                add('matrix_'+str(len(cases)),cell,cell,goal,radius,retry)
    for retry in (49,50,51,79,149,150,255):
        for preserve in (False,True):
            add('priority_'+str(retry)+'_'+str(int(preserve)),(18,3),(18,3),(19,4),1,retry,preserve,0xffffffff,(115,))
    add('cached_outside_window',(14,4),(14,4),(20,4),0,0,True,0,(115,))
    add('two_cached',(20,4),(20,4),(18,2),1,0,True,123,(115,141))
    add('reservation_start',(16,2),(17,2),(20,4),0,0,True,0,(),(17,2))
    add('reservation_nearest',(17,2),(18,3),(18,2),1,1,True,0,(115,),(18,3))
    return cases


def oracle_type():
    # The established source bootstrap is retained verbatim in historical
    # evidence; this read-only adapter supplies current world and call inputs.
    p=ROOT/'artifacts/long-routes/ordering/probe_work_order.py'
    expected='fbfae5bc082465e1f4ffd896d4b2261dee2f7f4cdf8b203207e9437065c00480'
    raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Original work bootstrap SHA-256 differs')
    spec=importlib.util.spec_from_file_location('ship_replan_reference_bootstrap',p)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def run_case(case,module=None):
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP
    m=module or oracle_type();o=m.WorkOracle(tuple(case['goal']))
    obj=m.OBJ;grid=m.GRID
    # Relocate only the requester. Other seven static source pointer records
    # preserve the established controlled group/state metadata.
    o.w(grid+12+(2*24+16)*24,0)
    x,y=case['cell'];o.w(obj+0x5a3,x);o.w(obj+0x5a7,y);o.w(grid+12+(y*24+x)*24,obj)
    o.w(m.SPRITE+0x59,x*64+4);o.w(m.SPRITE+0x5d,y*64+4)
    if case['reservation']:
        rx,ry=case['reservation'];o.w(grid+12+(ry*24+rx)*24,obj)
    o.w(obj+0x18,case['random_state'])
    for index in case['cached_obstacles']:o.invoke(0x4a7230,(index,))
    count_pointer=source.CONTEXT+0x60000;reached_pointer=count_pointer+4
    o.w(count_pointer,0);o.w(reached_pointer,0)
    paths=[]
    def capture(engine,address,size,unused):
        if address not in (0x55c9a0,0x55b9e0):return
        sp=engine.reg_read(UC_X86_REG_ESP);pointer=o.r(sp+4)
        paths.append({'entry':hex(address),'input_map_hex':bytes(engine.mem_read(pointer,1152)).hex(),
                      'reached_pointer':o.r(sp+40)if address==0x55b9e0 else None})
    o.u.hook_add(UC_HOOK_CODE,capture,begin=0x55b9e0,end=0x55c9a0)
    nearest=case['radius']!=0 or case['retry_priority']!=0
    if nearest:
        entry=0x4a51b0;args=(obj,*case['origin'],*case['goal'],0,reached_pointer,case['radius'],count_pointer,
                            case['retry_priority'],int(case['preserve_destination_mask']))
    else:
        entry=0x4a5740;args=(obj,*case['origin'],*case['goal'],count_pointer,case['retry_priority'])
    result=o.invoke(entry,args);count=o.r(count_pointer)
    source.gate.require(count<=577,'Native replan path count exceeded bound')
    points=bytes(o.u.mem_read(result,count*5))if result and count else b''
    source.gate.require(bool(result)==bool(count),'Native replan null/count mismatch')
    cache=[];pointer=o.r(obj+0x5cd)
    if pointer:
        n=o.r(pointer+0xc);stride=o.r(pointer+8);data=o.r(pointer+0x1c)
        source.gate.require(n<=7,'Native static blocker cache exceeded fleet')
        cache=[o.r(data+i*stride)for i in range(n)]
    working=o.r(0x5c93c0)
    return dict(case,used_nearest=nearest,point_count=count,path_hex=points.hex(),
                input_map_hex=paths[0]['input_map_hex']if paths else bytes(o.u.mem_read(working,1152)).hex(),
                working_map_hex=bytes(o.u.mem_read(working,1152)).hex(),
                reached_within_range=bool(o.r(reached_pointer))if nearest else
                    bool(o.r(paths[0]['reached_pointer']))if paths and paths[0]['reached_pointer']else bool(count),
                random_state_after=o.r(obj+0x18),cached_obstacles_after=cache,
                planner_entries=[p['entry']for p in paths])


def validate(inputs=None):
    source.checked_sources(source.SOURCE_ROOT)
    module=oracle_type()
    return {'schema_version':1,'source_hashes':source.SOURCE_HASHES,'kind':'Actual current-cell GetWayNew/GetWayNear normal-source0b static-fleet reference',
            'cases':[run_case(c,module)for c in inputs or case_inputs()],
            'limits':['Raw planning bodies execute; ProcPostMove stamps, live-route transaction and Work scheduling are compared separately',
                      'Other seven actors remain static minimal source records; source0b group-1, others group0/state0, route-byte0 and restriction0',
                      'Init, heap, graphics and unrelated work-query service boundaries are inherited from the pinned source bootstrap']}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():parser.error('Select a fresh output path')
    report=validate();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(str(len(report['cases']))+' actual current-origin planner cases')
