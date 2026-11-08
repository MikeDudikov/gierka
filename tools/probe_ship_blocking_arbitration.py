"""Actual4abe50->4abc60->4a6330 and subsequent4ab720,controlled boundary inputs.

Gate58b and pending/deferred words are EXPLICIT injected test inputs,not proven
gameplay-reachable states. Physical bodies/routes come from actual normal Work.
No interception of arbitration,cancellation,PostMove or promotion.
"""
import argparse,json
from pathlib import Path
from unicorn import UC_HOOK_CODE
from tools import probe_ship_live_fleet as live
from unicorn.x86_const import UC_X86_REG_EIP


def gate_initialization():
    class GateWrites(live.LiveFleetOracle):
        def __init__(self):self.gates=[];super().__init__()
        def onwrite(self,u,access,address,size,value,unused):
            for i,a in live.motion.ACTORS.items():
                if address<=a+0x58b<address+size:
                    self.gates.append(dict(actor=i,instruction=hex(u.reg_read(UC_X86_REG_EIP)),address=hex(address),size=size,value=hex(value)))
            super().onwrite(u,access,address,size,value,unused)
    n=GateWrites()
    return dict(writes=n.gates,final={str(i):n.b(a+0x58b)for i,a in live.motion.ACTORS.items()})


def fixture():
    cases=[]
    for actor in live.LOCAL:
        for at in(1,10,25,75):
            for gate in(0,1):
                for pending in(0,0x80,0x88):
                    for same in(False,True):
                        n=live.LiveFleetOracle();a=live.motion.ACTORS[actor]
                        goal={11:(18,5),12:(20,6),13:(18,4)}[actor]
                        n.receive(actor,*goal)
                        for t in range(1,at+1):n.tick_actor(actor,t,1)
                        n.receive(actor,16,4,255)
                        n.u.mem_write(a+0x58b,bytes([gate]));n.w(a+0x7d6,pending);n.w(a+0x265,0x80)
                        n.w(live.original.SYSTEM+0xde,(n.r(a+0x57b)+(0 if same else 1))&0xffffffff)
                        trace=[]
                        def capture(engine,address,size,unused):
                            if address in(0x4abe50,0x4abc60,0x4a6330,0x4ab250):trace.append(hex(address))
                        n.u.hook_add(UC_HOOK_CODE,capture)
                        before=n.live_snapshot(actor);n.call_actor(0x4abe50);after=n.live_snapshot(actor)
                        first=list(trace);trace.clear();n.call_actor(0x4ab720);promoted=n.live_snapshot(actor)
                        cases.append(dict(actor=actor,at=at,gate=gate,pending_input=pending,deferred_input=128,
                            same_last_plan_counter=same,counter=n.r(live.original.SYSTEM+0xde),before=before,
                            after=after,promoted=promoted,arbitration_trace=first,promotion_trace=trace))
    return dict(schema_version=1,original_exe_sha256=live.original.EXPECTED,cases=cases,scope=__doc__)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();d=fixture()
    a.output.write_text(json.dumps(d,separators=(',',':'))+'\n');print({'cases':len(d['cases'])})


if __name__=='__main__':main()
