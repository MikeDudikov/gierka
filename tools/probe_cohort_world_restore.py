"""Actual world clock/mail/registry plus three in-place source record restores.

Counter/phase/mail/group/grid context is retained at10,not rewound. Other source
App/Life/graphics/CRT boundaries remain as documented in both parent oracles.
Nonzero serialized gates are synthetic test input,not gameplay reachability proof.
"""
import argparse,json,struct
from pathlib import Path
from tools.probe_ship_world_step import WorldOracle,original
from tools.probe_ship_state_restore import RestoreOracle,live


class CohortOracle(WorldOracle,RestoreOracle):
    pass


def fixture():
    cases=[]
    for order in((-1,11,12,13),(11,-1,12,13),(11,12,-1,13),(11,12,13,-1)):
        for gates in((0,0,0),(1,0,255),(255,1,1)):
            n=CohortOracle(order,2);n.request();rows=[];records={};restored={}
            initial=n.frame(0)
            for tick in range(1,213):
                if tick==10:n.notify()
                rows.append(dict(n.frame(tick*40),notified=tick==10))
                if tick in(1,10):
                    batch=[]
                    context=(n.r(original.SYSTEM+0xde),n.r(original.SYSTEM+0xe6),n.b(original.SYSTEM+0x3e),n.group_state(),n.queued())
                    for actor,gate in zip(live.LOCAL,gates):
                        n.current_id=actor;p,raw=n.export();raw=bytearray(raw);raw[0x542]=gate;n.u.mem_write(p,bytes(raw));n.restore(p)
                        sprite=live.motion.SPRITES[actor]
                        n.drawn_by_id[actor]=dict(frame=n.r(sprite+0x45),world=[n.signed(sprite+0x59),n.signed(sprite+0x5d)])
                        n.publications_by_id[actor]=[];n.tail_by_id[actor]=False;n.mutations[actor]=[]
                        batch.append(bytes(raw).hex())
                    assert context==(n.r(original.SYSTEM+0xde),n.r(original.SYSTEM+0xe6),n.b(original.SYSTEM+0x3e),n.group_state(),n.queued())
                    actors=[]
                    for actor in live.LOCAL:n.grid_writes=[];actors.append(n.live_snapshot(actor))
                    records[str(tick)]=batch
                    restored[str(tick)]=dict(counter=tick,phase=n.signed(original.SYSTEM+0xe6),mail_gate=n.b(original.SYSTEM+0x3e),actors=actors,group=n.group_state(),outgoing=n.queued())
            cases.append(dict(label=f'cohort-{order.index(-1)}-'+','.join(map(str,gates)),order=list(order),warm=2,members=list(live.LOCAL),gates=list(gates),initial=initial,records=records,restored=restored,rows=rows))
    return dict(schema_version=1,original_exe_sha256=original.EXPECTED,cases=cases,
        seed_payloads={str(i):n.records[i].hex()for i in live.LOCAL},terrain=list(struct.unpack('<576h',bytes(n.u.mem_read(n.r(0x5c93bc),1152)))),scope=__doc__)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();d=fixture();a.output.write_text(json.dumps(d,separators=(',',':'))+'\n');print({'cases':len(d['cases'])})
