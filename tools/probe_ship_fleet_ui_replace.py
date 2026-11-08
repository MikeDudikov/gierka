"""Source UI committed-group replacement matched to the same world FIFO/task/ships.

UI and world use separate source engines with explicit current cell/state/5e
synchronization and exact emitted-packet equality. World clock/mail/fleet/Work
then run together;full ShipLife/App/OS input remain outside the boundary.
"""
from pathlib import Path
import argparse,copy,json,struct
from tools import probe_ship_fleet_ui_world as first
from tools import probe_ship_world_step as world
ROOT=world.ROOT;pointer=first.ui.dispatch.pointer


def replace(engine,goal):
    #4ccc30 reuses100/1,including its allocation and group+8;onlyRequest fields change.
    group=engine.r(world.GROUPS+28);task=engine.r(group+0x25);age=engine.r(group+8)
    request=world.W+0x51000;engine.u.mem_write(request,struct.pack('<4i',*goal,1,0))
    engine.call_this(0x4ccc30,world.FLEET,(5,0,group,request))
    assert engine.r(group+0x25)==task and engine.r(group+8)==age


def actors(engine):
    #Observer-only per-actor mutation lists,as WorldOracle.frame. No native state writes.
    previous=engine.grid_writes;result=[]
    for identifier in world.live.LOCAL:
        engine.grid_writes=engine.mutations[identifier];result.append(engine.live_snapshot(identifier))
    engine.grid_writes=previous
    return result


def fixture():
    metadata=first.ui.dispatch.membership.hover.source_metadata();cases=[];states=set()
    for order in((-1,11,12,13),(11,-1,12,13),(11,12,-1,13),(11,12,13,-1)):
        for after,goals in((10,((18,6),)),(25,((18,6),(16,4))),(100,((16,4),))):
            cursor=first.ui.dispatch.MoveOracle(metadata)
            for kind,target,flags in((5,11,0),(5,12,4),(5,13,4),(7,None,0)):
                cursor.selection_events.clear();cursor.release(kind,target,flags=flags)
            engine=world.WorldOracle(order,2);initial=[engine.live_snapshot(i)for i in world.live.LOCAL];engine.request()
            assert cursor.commands==[dict(actor=p['actor'],action=p['action'],payload_hex=p['payload_hex'])for p in engine.queued()]
            initial_packets=copy.deepcopy(engine.queued());rows=[];requests=[]
            for tick in range(1,201):
                frame=dict(engine.frame(tick*40),notified=False);rows.append(frame)
                if tick!=after:continue
                for goal in goals:
                    #Explicit observer boundary:current world cells,58c and received5e,not invented motion.
                    for state in frame['actors']:
                        actor=cursor.actors[state['id']];native=world.live.motion.ACTORS[state['id']]
                        cursor.w(actor+0x5a3,state['cell'][0]);cursor.w(actor+0x5a7,state['cell'][1])
                        cursor.u.mem_write(actor+0x58c,bytes([state['state']]))
                        cursor.u.mem_write(actor+0x5e,bytes(engine.u.mem_read(native+0x5e,2)));states.add(state['state'])
                    cursor.w(pointer.motion.SYSTEM+0xde,tick);cursor.commands.clear();cursor.selection_events.clear()
                    cursor.observe(7,False,*goal);cursor.w(pointer.CUR+0xd9,0);cursor.invoke_cursor(0x518070,(0x62,0))
                    ui=cursor.snapshot_pending();before=engine.queued();actors_before=actors(engine)
                    replace(engine,goal);new=engine.queued()[len(before):]
                    assert [p['action']for p in new]==[20]*3
                    assert cursor.commands==[dict(actor=p['actor'],action=p['action'],payload_hex=p['payload_hex'])for p in new]
                    assert not ui['pending']and ui['current_group']==0 and ui['selected']and ui['visuals']==[1,1,1]and not ui['events']
                    assert actors_before==actors(engine)
                    snapshot=dict(frame,actors=actors_before,group=engine.group_state(),outgoing=engine.queued())
                    requests.append(dict(after=tick,goal=goal,ui=ui,packets=new,snapshot=snapshot))
                assert all(engine.b(world.live.motion.ACTORS[i]+0x58b)==0 for i in world.live.LOCAL)
            delivered=next(f for f in rows if f['counter']==after+1)
            assert [p['payload_hex']for p in delivered['received']]==[p['payload_hex']for request in requests for p in request['packets']]
            assert all(p['queued_at']==after for p in delivered['received'])
            cases.append(dict(label=f'ui-replace-{order.index(-1)}-{after}',order=order,warm=2,members=world.live.LOCAL,
                initial=initial,initial_packets=initial_packets,requests=requests,rows=rows))
    return dict(schema_version=1,original_exe_sha256=world.original.EXPECTED,cases=cases,receipt_states=sorted(states),
        seed_payloads={str(i):engine.records[i].hex()for i in world.live.LOCAL},
        terrain=list(struct.unpack('<576h',bytes(engine.u.mem_read(engine.r(0x5c93bc),1152)))),scope=__doc__)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();data=fixture()
    a.output.write_text(json.dumps(data,separators=(',',':'))+'\n')
    print(dict(cases=len(data['cases']),frames=sum(len(c['rows'])for c in data['cases']),requests=sum(len(c['requests'])for c in data['cases']),states=data['receipt_states']))


if __name__=='__main__':main()
