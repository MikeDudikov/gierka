"""Original source record restoration with canonical reloaded sprite observation.

Same CRT/graphics boundaries as probe_ship_state_restore. Reloaded sprite fields
replace the harness's last-publication cache at import;not a pixel validation.
Gate0/1/255 are controlled serialized inputs,not a source gameplay reachability claim.
"""
import argparse,json,struct
from pathlib import Path
from tools.probe_ship_state_restore import RestoreOracle,live


def fixture():
    cases=[]
    for actor in live.LOCAL:
        for warmup in(1,10,25,75):
            for gate in(0,1,255):
                variants=[(stop,deferred,0xffffffff)for stop in(None,0,128)for deferred in(0,128)]
                if actor==11 and warmup==10:variants.extend((None,deferred,0)for deferred in(0,128))
                for stop,deferred,ready in variants:
                    n=RestoreOracle();goal={11:(18,5),12:(20,6),13:(18,4)}[actor];n.receive(actor,*goal)
                    for t in range(1,warmup+1):n.tick_actor(actor,t,1)
                    n.current_id=actor;p,raw=n.export();raw=bytearray(raw);raw[0x542]=gate;
                    if stop is not None:
                        value=struct.unpack_from('<I',raw,0x789)[0]|8;struct.pack_into('<I',raw,0x789,value)
                        struct.pack_into('<I',raw,0x818-0x4d,stop)
                    struct.pack_into('<I',raw,0x7da-0x4d,ready)
                    n.w(live.motion.ACTORS[actor]+0x265,deferred)
                    n.u.mem_write(p,bytes(raw));n.restore(p)
                    a=live.motion.ACTORS[actor];sprite=live.motion.SPRITES[actor]
                    n.drawn_by_id[actor]=dict(frame=n.r(sprite+0x45),world=[n.signed(sprite+0x59),n.signed(sprite+0x5d)])
                    n.publications_by_id[actor]=[];n.tail_by_id[actor]=False;n.grid_writes.clear()
                    def snapshot():return dict(n.live_snapshot(actor),gate=n.b(a+0x58b))
                    restored=snapshot();received=dict(n.receive(actor,16,4,255),gate=n.b(a+0x58b));rows=[]
                    for t in range(warmup+1,warmup+33):rows.append(dict(n.tick_actor(actor,t,1),gate=n.b(a+0x58b)))
                    cases.append(dict(stop=stop,deferred=deferred,ready=ready,actor=actor,warmup=warmup,gate=gate,goal=list(goal),raw_hex=bytes(raw).hex(),restored=restored,received=received,rows=rows))
    return dict(schema_version=1,original_exe_sha256=live.original.EXPECTED,cases=cases,seed_payloads={str(i):n.records[i].hex()for i in live.LOCAL},scope=__doc__)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();d=fixture();a.output.write_text(json.dumps(d,separators=(',',':'))+'\n');print({'cases':len(d['cases'])})
