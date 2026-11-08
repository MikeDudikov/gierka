"""Actual ship4e12e0 export/4e2180 restore followed by source Promote+Work.

One engine per case. CRT allocation/reallocation and graphical resource creation
are explicit service boundaries. Export/import,route/cache copying,grid reclaim,
arbitration,promotion and Work are original instructions. Patched gate bytes in
exported buffers are synthetic inputs,not gameplay/save-file reachability proof.
"""
import argparse,json
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_ESP
from tools import probe_ship_live_fleet as live


class RestoreOracle(live.LiveFleetOracle):
    def __init__(self,seed=0):
        self.allocations={};self.restoring=False;self.boundaries=[]
        super().__init__(seed);self.u.mem_map(0x74000000,0x10000)

    def hook(self,u,a,size,unused):
        sp=u.reg_read(UC_X86_REG_ESP)
        if a in(0x557700,0x589bf5):self.allocations[self.heap]=self.r(sp+4)
        if a==0x589c69: #CRT realloc only;the source558fd0 wrapper runs normally.
            old=self.r(sp+4);length=self.r(sp+8);assert old==0 or old in self.allocations,hex(old)
            p=self.heap;self.heap+=(max(length,1)+15)&~15
            if old:u.mem_write(p,bytes(u.mem_read(old,min(length,self.allocations[old]))))
            self.allocations[p]=length;self.boundaries.append('CRT-realloc');self.ret(0,p);return
        if self.restoring:
            services={0x50cb80:(28,0),0x50d4f0:(4,live.motion.SPRITES[self.current_id]),
                0x4e1bb0:(4,0),0x4e0120:(20,0x74000100),0x542eb0:(16,0),0x50e640:(4,0)}
            if a in services:
                clean,result=services[a];self.boundaries.append(hex(a));self.ret(clean,result);return
        super().hook(u,a,size,unused)

    def export(self):
        pointer=self.call_actor(0x4e12e0,(0x74000000,));length=self.r(0x74000000)
        assert 0x89d<=length<0x10000
        return pointer,bytes(self.u.mem_read(pointer,length))

    def restore(self,pointer):
        self.restoring=True
        try:self.call_actor(0x4e2180,(pointer,))
        finally:self.restoring=False


def pilot():
    n=RestoreOracle();n.receive(11,18,5)
    for t in range(1,26):n.tick_actor(11,t,1)
    p,raw=n.export();before=n.live_snapshot(11);n.restore(p);after=n.live_snapshot(11)
    return dict(length=len(raw),gate=raw[0x542],before=before,after=after,boundaries=n.boundaries)


def fixture():
    cases=[]
    for actor in live.LOCAL:
        for warmup in(1,10,25,75):
            for gate in(0,1,255):
                n=RestoreOracle();control=live.LiveFleetOracle();goal={11:(18,5),12:(20,6),13:(18,4)}[actor]
                for engine in(n,control):
                    engine.receive(actor,*goal)
                    for t in range(1,warmup+1):engine.tick_actor(actor,t,1)
                n.current_id=actor;a=live.motion.ACTORS[actor]
                p,raw=n.export();before=n.live_snapshot(actor)
                assert raw[0x542]==0 #Natural initialized/normal-work state in this corpus.
                #Controlled serialized input;not a discovered original saved game.
                n.u.mem_write(p+0x542,bytes([gate]));n.restore(p)
                after=n.live_snapshot(actor);assert before==after
                assert n.b(a+0x58b)==gate
                control.u.mem_write(a+0x58b,bytes([gate])) #Independent non-import control.
                assert n.receive(actor,16,4,255)==control.receive(actor,16,4,255)
                rows=[]
                for t in range(warmup+1,warmup+33):
                    state=n.tick_actor(actor,t,1);expected=control.tick_actor(actor,t,1)
                    assert state==expected,(actor,warmup,gate,t)
                    rows.append(state)
                cases.append(dict(actor=actor,warmup=warmup,gate=gate,buffer_length=len(raw),buffer_sha256=__import__('hashlib').sha256(raw).hexdigest(),
                    exported_gate=raw[0x542],imported_gate=n.b(a+0x58b),before=before,restored=after,
                    boundaries=list(n.boundaries),rows=rows))
    return dict(schema_version=1,original_exe_sha256=live.original.EXPECTED,cases=cases,scope=__doc__)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--fixture',action='store_true');a=p.parse_args();d=fixture()if a.fixture else pilot()
    a.output.write_text(json.dumps(d,separators=(',',':'))+'\n');print({'cases':len(d['cases'])}if a.fixture else{'length':d['length'],'gate':d['gate'],'boundaries':d['boundaries']})


if __name__=='__main__':main()
