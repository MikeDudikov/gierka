"""First normal fleet click:actual cursor/packets,then explicit handoff to3actual bodies.

The UI oracle and body oracle are separate source engines. Immutable packets
cross this documented boundary;no full group-task scheduler/Life is claimed.
"""
from pathlib import Path
import argparse,json,struct
from tools import probe_ship_fleet_move_commands as dispatch,probe_ship_live_fleet as live
ROOT=live.ROOT


def fixture():
    ui=dispatch.MoveOracle(dispatch.membership.hover.source_metadata());selection=[]
    for kind,target,flags in((5,11,0),(5,12,4),(5,13,4),(7,None,0)):
        ui.selection_events.clear();state=ui.release(kind,target,flags=flags)
        selection.append(state)
    packets=[dict(p)for p in ui.commands];assert [p['action']for p in packets]==[41]*3+[20]*3
    body=live.LiveFleetOracle(0);initial=[body.live_snapshot(i)for i in live.LOCAL]
    received=[]
    for p in packets:
        raw=bytes.fromhex(p['payload_hex'])
        if p['action']==41:
            group=struct.unpack_from('<i',raw,1)[0]
            #UI words are a synchronized boundary input from the UI engine.
            body.u.mem_write(live.motion.ACTORS[p['actor']]+0x5c,struct.pack('<h',group))
            state=body.receive(p['actor'],group,0,action=41)
        else:state=body.receive(p['actor'],*struct.unpack('<iiB',raw))
        received.append({'packet':p,'state':state})
    rows=[]
    for counter in range(1,201):
        for identifier in live.LOCAL:rows.append({'counter':counter,'state':body.tick_actor(identifier,counter,1)})
    post=[]
    for kind,target,message,flags in((7,None,100,0),(5,12,98,8)):
        ui.selection_events.clear();state=ui.release(kind,target,message=message,flags=flags);post.append(state)
    return {'schema_version':1,'original_exe_sha256':live.original.EXPECTED,'selection':selection,'packets':packets,
            'initial':initial,'received':received,'rows':rows,'post_selection':post,'seed_payloads':{str(i):body.records[i].hex()for i in live.LOCAL},
            'scope':'First normal3member release18,5;actual UI/formation/serialization and cold UI Ctrl recall;separate actual body-engine receipt and600tickcalls;no taskLife scheduler/Shift editing/busy replacement/OSinput'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=fixture();a.output.write_text(json.dumps(r,separators=(',',':'))+'\n');print({'packets':len(r['packets']),'tickcalls':len(r['rows'])})


if __name__=='__main__':main()
