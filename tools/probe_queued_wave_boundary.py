"""Original4ceab0 signed wave[-1] comparison under explicit adjacent-memory inputs.

No algorithm/branch is replaced. Only the two bytes before an actual1152B
wave allocation are controlled at4cebc7. These are synthetic context tests,
not claims about the original Windows CRT heap or gameplay reachability.
"""
from pathlib import Path
import argparse,json,struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EBP,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI
from tools import probe_ship_fleet_queued as queued
ROOT=queued.ROOT


def run(prefix,entry,metadata,terrain=None):
    n=queued.QueuedOracle(metadata,entry);observed=[]
    for op in(('select',11,12,13),('shift',18,6,0),('shift',16,4,1),('age',101)):n.run(op)
    if terrain is not None:
        assert len(terrain)==576
        n.u.mem_write(n.r(0x5c93bc),struct.pack('<576h',*terrain)) #Explicit map input,not altered wave logic.
    def compare(u,address,size,unused):
        if address==0x4cebc7:
            base=u.reg_read(UC_X86_REG_EAX);index=u.reg_read(UC_X86_REG_EDX)
            index=index if index<0x80000000 else index-0x100000000
            target=(base+2*index)&0xffffffff;assert index==-1 and n.allocations[base]==1152
            before=struct.unpack('<h',u.mem_read(target,2))[0]
            if prefix is not None:u.mem_write(target,struct.pack('<h',prefix))
            frame=u.reg_read(UC_X86_REG_EBP);actor=n.r(frame+8)
            observed.append(dict(id=n.r(actor+0x4c),index=index,allocation_bytes=n.allocations[base],offset_bytes=target-base,
                adjacent_before=before,adjacent_used=struct.unpack('<h',u.mem_read(target,2))[0],
                candidate=struct.unpack('<h',struct.pack('<H',u.reg_read(UC_X86_REG_ESI)&65535))[0]))
        elif address==0x4cebce:
            observed[-1]['result']=u.reg_read(UC_X86_REG_EBX)
    n.u.hook_add(UC_HOOK_CODE,compare,begin=0x4cebc7,end=0x4cebce)
    state=n.run(('work',1,2));assert len(observed)==3
    return dict(comparisons=observed,state=state)


def fixture():
    metadata=queued.normal.source.membership.hover.source_metadata();cases=[]
    for prefix in(None,0,5000,32767,-32768):
        ui=run(prefix,'ui',metadata);direct=run(prefix,'fleet',metadata)
        assert ui==direct
        cases.append(dict(adjacent_input=prefix,**ui))
    return dict(schema_version=1,original_exe_sha256=queued.normal.source.pointer.gate.EXPECTED,
        cases=cases,scope=__doc__,source_instruction='0x4cebc7',native_crt_layout_verified=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();data=fixture()
    a.output.write_text(json.dumps(data,separators=(',',':'))+'\n')
    print([(c['adjacent_input'],[p['actor']for p in c['state']['packets']])for c in data['cases']])


if __name__=='__main__':main()
