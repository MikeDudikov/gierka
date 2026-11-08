"""Actual normal20 overwrite/promotion/work on three healthy local bodies.

Only the source nonblocking arbitration profile:58b==0,normal move metadata0/255,
no combat/tasks10/20/40/100 or full Ship::Life. No interception of receipt,
arbitration,promotion,planning or motion;inherited init/heap/render boundaries.
"""
import argparse,json,struct
from pathlib import Path
from tools import probe_ship_live_fleet as live


def world_fixture():
    from tools.probe_ship_world_step import WorldOracle
    cases=[]
    for order in((-1,11,12,13),(11,-1,12,13),(11,12,-1,13),(11,12,13,-1)):
        for at in(10,36):
            n=WorldOracle(order,2);n.request();rows=[]
            for tick in range(1,213):
                if tick==at:n.notify()
                f=dict(n.frame(tick*40),notified=tick==at);rows.append(f)
                assert all(n.b(live.motion.ACTORS[i]+0x58b)==0 for i in live.LOCAL)
                assert all(p['action']in(20,41)for p in f['received']+f['emitted'])
            assert rows[at-1]['received']==[] and len(rows[at-1]['emitted'])==3
            assert len(rows[at]['received'])==3 and all(p['queued_at']==at for p in rows[at]['received'])
            cases.append(dict(label=f'world-busy-{order.index(-1)}-{at}',order=list(order),warm=2,members=list(live.LOCAL),rows=rows))
    return dict(schema_version=1,original_exe_sha256=live.original.EXPECTED,cases=cases,
        seed_payloads={str(i):n.records[i].hex()for i in live.LOCAL},
        terrain=list(struct.unpack('<576h',bytes(n.u.mem_read(n.r(0x5c93bc),1152)))),scope=__doc__)


def fixture():
    specs=[]
    for actor in live.LOCAL:
        for at in(0,1,10,25,100):
            specs.append(dict(label=f'replace-{actor}-at-{at}',actor=actor,at=at,seed=0,ticks=180,sequence=[1]))
    for seed,sequence in((7,[1]),(0xffffffff,[1,2,3,7]),(0,[3])):
        specs.append(dict(label=f'burst-{seed}-{sequence[0]}',actor=0,at=-1,seed=seed,ticks=180,sequence=sequence))
    cases=[];states=set();gates=set()
    for spec in specs:
        n=live.LiveFleetOracle(spec['seed']);ops=[];initial=[n.live_snapshot(i)for i in live.LOCAL]
        def receive(actor,x,y,argument=0):
            before=n.live_snapshot(actor);states.add(before['state']);gates.add(n.b(live.motion.ACTORS[actor]+0x58b))
            state=n.receive(actor,x,y,argument)
            ops.append(dict(kind='R',id=actor,goal=[x,y],argument=argument,state=state))
        for actor,goal in zip(live.LOCAL,((18,5),(20,6),(18,4))):
            n.receive(actor,0,0,action=41);ops.append(dict(kind='G',id=actor,group=0,state=n.live_snapshot(actor)))
            receive(actor,*goal)
        for tick in range(1,spec['ticks']+1):
            if tick==spec['at']+1:
                receive(spec['actor'],16,4,255)
                receive(spec['actor'],18,6,0) #Last write wins before promotion.
            if spec['actor']==0 and tick in(2,10,25,26,80,100,150):
                for actor in live.LOCAL:
                    receive(actor,16,4,255);receive(actor,18,6,0)
            pending=spec['sequence'][(tick-1)%len(spec['sequence'])]
            for actor in live.LOCAL:
                s=n.tick_actor(actor,tick,pending);assert n.b(live.motion.ACTORS[actor]+0x58b)==0
                ops.append(dict(kind='T',id=actor,counter=tick,pending=pending,state=s))
        cases.append(dict(label=spec['label'],seed=spec['seed'],initial=initial,operations=ops))
    assert gates=={0}
    return dict(schema_version=1,original_exe_sha256=live.original.EXPECTED,cases=cases,
        seed_payloads={str(i):n.records[i].hex()for i in live.LOCAL},receipt_states=sorted(states),arbitration_gate_values=sorted(gates),scope=__doc__)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--world',action='store_true');a=p.parse_args();d=world_fixture()if a.world else fixture()
    a.output.write_text(json.dumps(d,separators=(',',':'))+'\n');print({'cases':len(d['cases']),'world':a.world})


if __name__=='__main__':main()
