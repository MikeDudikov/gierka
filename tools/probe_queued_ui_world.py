"""Actual Shift/normal UI requests during original world movement.

Two source engines:cursor518070 and clock/mail/world. Current cells,58c,5e,
counter and age are explicit UI handoff inputs;packets/headers/points must match.
NoC#UIport,OS input,fullLife or allocator-universal117 claim.
"""
from pathlib import Path
import argparse,copy,json,struct
from tools import probe_fleet_queued_world as coupled
ROOT=coupled.ROOT;world=coupled.world;fleet=coupled.fleet;pointer=fleet.pointer


def fixture(*,normal_goal=(18,5),positions=range(4),afters=(10,25,100)):
    metadata=fleet.normal.source.membership.hover.source_metadata();cases=[]
    for position in positions:
        order=[11,12,13];order.insert(position,-1)
        for after in afters:
            cursor=fleet.QueuedOracle(metadata,'ui');cursor.run(('select',11,12,13));ui=cursor.run(('click',18,5,0))
            n=coupled.QueuedWorldOracle(order,2,{11:117,12:117,13:117});n.request()
            assert ui['packets']==[dict(actor=p['actor'],action=p['action'],payload_hex=p['payload_hex'])for p in n.queued()]
            initial_packets=copy.deepcopy(n.queued());rows=[];requests=[]
            for tick in range(1,201):
                frame=n.frame(tick*40);rows.append(frame);actions=[]
                if tick==after:actions=[('shift',18,6),('shift',16,4),('shift',18,6)]
                if tick==after+60:actions=[('click',*normal_goal)]
                for kind,x,y in actions:
                    for state in frame['actors']:
                        actor=cursor.actors[state['id']];live=world.live.motion.ACTORS[state['id']]
                        cursor.w(actor+0x5a3,state['cell'][0]);cursor.w(actor+0x5a7,state['cell'][1])
                        cursor.u.mem_write(actor+0x58c,bytes([state['state']]))
                        cursor.u.mem_write(actor+0x5e,bytes(n.u.mem_read(live+0x5e,2)))
                    group=n.r(world.GROUPS+28);age=n.r(group+8);cursor.w(cursor.group()+8,age)
                    result=cursor.run((kind,x,y,tick));before=n.queued()
                    if kind=='shift':n.append_point(x,y)
                    else:
                        request=world.W+0x51000;n.u.mem_write(request,struct.pack('<4i',x,y,1,0))
                        n.call_this(0x4ccc30,world.FLEET,(5,0,group,request))
                    added=n.queued()[len(before):]
                    assert result['packets']==[dict(actor=p['actor'],action=p['action'],payload_hex=p['payload_hex'])for p in added]
                    state=n.group_state();assert state['age']==age and state['task']==result['task']['header']
                    if kind=='shift':assert state['route']['points']==[p['cell']for p in result['route']['points']]
                    snapshot=dict(frame,group=state,outgoing=n.queued())
                    requests.append(dict(after=tick,kind=kind,goal=[x,y],packets=added,snapshot=snapshot,
                        ui_header=result['task']['header'],ui_packet_count=len(result['packets'])))
            cases.append(dict(label=f'queued-ui-{position}-{after}',order=order,warm=2,members=world.live.LOCAL,
                prefixes=[117]*3,after=after,initial_packets=initial_packets,requests=requests,rows=rows))
    return dict(schema_version=1,original_exe_sha256=world.original.EXPECTED,cases=cases,scope=__doc__,
        seed_payloads={str(i):n.records[i].hex()for i in world.live.LOCAL},
        terrain=list(fleet.normal.source.formation.mission_terrain()))


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();d=fixture()
    a.output.write_text(json.dumps(d,separators=(',',':'))+'\n');print(dict(cases=len(d['cases']),frames=sum(len(c['rows'])for c in d['cases']),requests=sum(len(c['requests'])for c in d['cases'])))


if __name__=='__main__':main()
