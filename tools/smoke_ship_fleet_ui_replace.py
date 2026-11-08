"""InputSystem replacements at held25,source FIFO at26,renderer/selection readouts."""
from pathlib import Path
import argparse,re
from tools import smoke_ship_fleet_control as control,validate_ship_fleet_ui_replace as proof
ROOT=proof.ROOT;require=control.require
COUNTERS=(1,3,10,25,26,50,80,120,160,200)
STAGES=control.STAGES[:9]+['tick-'+str(n)for n in(1,3,10,25)]+[
 'queued-guard-down','queued-guard-up','replace-first-down','replace-first-up','replace-last-down','replace-last-up']+[
 'tick-'+str(n)for n in(26,50,80,120,160,200)]+control.STAGES[-5:]


def reference(position=0):
    data=proof.load();case=next(c for c in data['cases']if c['label']==f'ui-replace-{position}-25')
    ops=[dict(kind='R',id=s['id'],counter=0,state=s)for s in case['initial']]
    for frame in case['rows']:
        require(frame['publications']==[[s['id'],p['frame'],*p['world'],p['depth']]for s in frame['actors']for p in s['publications']],
            'Source replacement publications must preserve registry order')
        ops.extend(dict(kind='T',id=s['id'],counter=frame['counter'],state=s)for s in frame['actors'])
    base=control.rendering.load_reference(case_override=dict(initial=case['initial'],operations=ops),counters=COUNTERS)
    checkpoints={};contexts={};taskstates={}
    for index,stage in enumerate(STAGES):
        tick=int(stage[5:])if stage.startswith('tick-')else 200 if index>=STAGES.index('clear-point')else 25 if index>=13 else 0
        key='tick-'+str(tick)if tick else'initial';cp=base['checkpoints'][key]
        checkpoints[stage]=dict(cp,queue=[dict(row,stage=stage)for row in cp['queue']])
        if index<8:contexts[stage]=(0,0,0,2,'-1,-1,-1','-1,-1,-1');continue
        if index==8:contexts[stage]=(0,0,6,2,'0,0,0','-1,-1,-1');taskstates[stage]=(0,18,5);continue
        frame=case['rows'][tick-1]
        if stage in('replace-first-up','replace-last-down'):frame=case['requests'][0]['snapshot']
        elif stage=='replace-last-up':frame=case['requests'][1]['snapshot']
        consumed=sum(p['action']==41 for f in case['rows'][:tick]for p in f['received'])
        contexts[stage]=(frame['group']['age'],consumed,len(frame['outgoing']),frame['mail_gate'],'0,0,0','0,0,0')
        task=frame['group']['task'];taskstates[stage]=(task[2],task[3],task[4])
    packets=[dict(actor=p['actor'],action=p['action'],payload_hex=p['payload_hex'])for p in case['initial_packets']]
    packets.extend(p for request in case['requests']for p in request['ui']['commands'])
    base.update(checkpoints=checkpoints,contexts=contexts,taskstates=taskstates,packets=packets,world=case)
    return base


def validate_log(log,ref):
    log=log[:log.rfind('\n')+1];rows,_=control.rendering.parse(log,ref)
    packets=[dict(actor=int(m[1]),action=int(m[2]),payload_hex=m[3])for m in re.finditer(
        r'^\[ShipFleetControl\] packet: id=(\d+); action=(\d+); payload=([0-9a-f]+)$',log,re.M)]
    require(packets==ref['packets'][:len(packets)],'Replacement packet order/payload differs')
    selections={m[1]:(m[2],m[3]=='True',m[4]=='True')for m in re.finditer(
        r'^\[ShipFleetSelection\] checkpoint: stage=([^;]+); members=([^;]+); pending=(True|False); selected=(True|False); counter=(\d+)$',log,re.M)}
    committed={m[1]:(int(m[2]),int(m[3]),m[4]=='True')for m in re.finditer(
        r'^\[ShipFleetControl\] selection: stage=([^;]+); group=(-?\d+); temporary=(\d+); dispatched=(True|False)$',log,re.M)}
    for stage,row in rows.items():
        if not row['ended']:continue
        index=STAGES.index(stage);members=[];pending=False;group=-1
        if 2<=index<=7:members=[11]+([12]if index>=4 else[])+([13]if index>=6 else[]);pending=True
        elif 8<=index<STAGES.index('clear-right-up')or stage=='recall-c-up':members=[11,12,13];group=0
        expected=','.join(format(i,'08x')for i in members)or'none'
        require(selections.get(stage)==(expected,pending,bool(members)),'Replacement UI selection differs at '+stage)
        require(committed.get(stage)==(group,len(members)if pending else 0,index>=8),'Replacement committed group differs at '+stage)
    for kind in('received','emitted'):
        expected=[]
        for frame in ref['world']['rows']:
            expected.extend((frame['counter'],proof.world.packet(p,kind=='received'))for p in frame[kind])
        actual=[(int(m[1]),m[2])for m in re.finditer(r'^\[ShipWorldStep\] '+kind+r': at=(\d+); packet=([^\r\n]+)$',log,re.M)]
        require(actual==expected[:len(actual)],'Replacement '+kind+' FIFO/stamp differs')
        if '[ShipFleetMoveReplay] complete:'in log:require(actual==expected,'Incomplete replacement '+kind)
    checks=[]
    for match in re.finditer(r'^\[ShipFleetControl\] world: stage=([^;]+); age=(\d+); consumed=(\d+); queued=(\d+); prep=(\d+); ui=([^;]+); sim=([^\r\n]+)$',log,re.M):
        stage=match[1];checks.append(stage);actual=(*map(int,match.groups()[1:5]),match[6],match[7])
        require(actual==ref['contexts'][stage],'Replacement world context differs at '+stage)
    require(checks==STAGES[:len(checks)],'Replacement world checkpoint order differs')
    tasks={m[1]:tuple(map(int,m.groups()[1:]))for m in re.finditer(r'^\[ShipFleetControl\] task: stage=([^;]+); requested=(\d+); goal=(-?\d+),(-?\d+)$',log,re.M)}
    for stage,value in tasks.items():require(ref['taskstates'].get(stage)==value,'Replacement task fields differ at '+stage)
    replacements=[tuple(map(int,m.groups()))for m in re.finditer(r'^\[ShipFleetControl\] replacement: counter=(\d+); group=(\d+); goal=(-?\d+),(-?\d+); requested=(\d+); age=(\d+); queued=(\d+)$',log,re.M)]
    expected=[(25,0,18,6,25,25,3),(25,0,16,4,25,25,6)]
    require(replacements==expected[:len(replacements)],'Replacement reused task/age/queue differs')
    done='[ShipFleetMoveReplay] complete:'in log
    if done:
        require(list(rows)==STAGES and all(row['ended']for row in rows.values()),'Incomplete replacement actor/render stages')
        require(checks==STAGES and tasks==ref['taskstates']and replacements==expected,'Incomplete replacement task lifecycle')
        require(packets==ref['packets'],'Incomplete replacement packets')
        require(log.count('[ShipFleetControl] guard: reason=normal-committed-replacement-only')==1,'Shift queue guard not exercised exactly once')
    return rows,done


def run(output,position=0):
    order=[11,12,13];order.insert(position,'fleet')
    result=control.run(output,reference_override=reference(position),extra_args=('--ship-pointer-fleet-world',
        '--ship-fleet-world-registration',','.join(map(str,order)),'--ship-pointer-fleet-world-mail','2','--ship-pointer-fleet-replace-replay'),
        extra_provenance=(Path(__file__),proof.FIXTURE,proof.PROBE,ROOT/'tools/probe_ship_fleet_ui_replace.py',
            ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime/ShipFleetMoveInputReplay.cs'),
        log_validator=validate_log,scope_override='Committed normal UI two requests at25,one world FIFO receive26,last20wins,task100/1reuse;Shift guard;explicit registry and mail2;source UI/world separate packet-equal engines,not full App/Life/pixels/OSmouse/Win11/hardware')
    result.update(fleet_position=position,replacement_requests=2,first_replacement_delivery_tick=26,world_context_checkpoints=len(STAGES),
        task_context_checkpoints=len(reference(position)['taskstates']),shift_guard=True,image_capture=False)
    control.menu.write_json(Path(output)/'report.json',result);return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--fleet-position',type=int,choices=range(4),default=0)
    a=p.parse_args();result=run(a.output,a.fleet_position)
    print({k:result[k]for k in('passed','checkpoints','actor_rows','publications','first_replacement_delivery_tick','exit_code')})


if __name__=='__main__':main()
