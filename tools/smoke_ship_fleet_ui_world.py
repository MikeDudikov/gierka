"""Actual InputSystem first release -> world FIFO -> group/ship Work;no captures."""
from pathlib import Path
import argparse,json,re
from tools import smoke_ship_fleet_control as control,validate_ship_fleet_ui_world as proof
ROOT=proof.ROOT;require=control.require


def reference(warm=0,position=0):
    data=proof.load();case=next(c for c in data['cases']if c['label']==f'ui-world-{position}-{warm}')
    #R is the renderer observer's release checkpoint marker,not an emulated receipt.
    ops=[dict(kind='R',id=s['id'],counter=0,state=s)for s in case['initial']]
    for frame in case['rows']:
        require(frame['publications']==[[s['id'],p['frame'],*p['world'],p['depth']]for s in frame['actors']for p in s['publications']],
            'Source UI world publications must preserve registry order')
        ops.extend(dict(kind='T',id=s['id'],counter=frame['counter'],state=s)for s in frame['actors'])
    #The release only queues source mail. No immediate20 receipt or selector/body reordering.
    base=control.rendering.load_reference(case_override=dict(initial=case['initial'],operations=ops),counters=control.COUNTERS)
    checkpoints={}
    for stage in control.STAGES:
        key=stage if stage.startswith('tick-')else'tick-200'if control.STAGES.index(stage)>=18 else'initial'
        cp=base['checkpoints'][key];checkpoints[stage]=dict(cp,queue=[dict(r,stage=stage)for r in cp['queue']])
    base.update(checkpoints=checkpoints,packets=data['packets'],world=case)
    return base


def validate_log(log,ref):
    log=log[:log.rfind('\n')+1] #A concurrent player may still be writing its last line.
    rows,done=control.validate_log(log,ref);frames=ref['world']['rows']
    expected=[(f['counter'],proof.world.packet(p,True))for f in frames for p in f['received']]
    actual=[(int(m[1]),m[2])for m in re.finditer(r'^\[ShipWorldStep\] received: at=(\d+); packet=([^\r\n]+)$',log,re.M)]
    require(actual==expected[:len(actual)],'UI world mail delivery stamp/order/payload differs')
    require('[ShipWorldStep] emitted:'not in log,'Unexpected UI world group emission without a source event')
    checks=[]
    pattern=r'^\[ShipFleetControl\] world: stage=([^;]+); age=(\d+); consumed=(\d+); queued=(\d+); prep=(\d+); ui=([^;]+); sim=([^\r\n]+)$'
    for match in re.finditer(pattern,log,re.M):
        stage=match[1];checks.append(stage);index=control.STAGES.index(stage)
        if index<8:expected_values=(0,0,0,ref['world']['warm'],'-1,-1,-1','-1,-1,-1')
        elif index==8:expected_values=(0,0,6,ref['world']['warm'],'0,0,0','-1,-1,-1')
        else:
            count=int(stage[5:])if stage.startswith('tick-')else 200
            frame=frames[count-1];consumed=sum(p['action']==41 for f in frames[:count]for p in f['received'])
            expected_values=(frame['group']['age'],consumed,len(frame['outgoing']),frame['mail_gate'],'0,0,0',
                '0,0,0'if consumed else'-1,-1,-1')
        actual_values=(*map(int,match.groups()[1:5]),match[6],match[7])
        require(actual_values==expected_values,'UI world context differs at '+stage+': '+str(actual_values)+'/'+str(expected_values))
    require(checks==control.STAGES[:len(checks)],'UI world context stage order differs')
    if done:
        require(checks==control.STAGES and actual==expected,'UI world lifecycle observations incomplete')
        require('[ShipFleetControl] ready: first_normal_move=True; ctrl_recall=True; group_task_scheduler=True;'in log,'Input did not bind the world task lifecycle')
    return rows,done


def run(output,warm=0,position=0):
    order=[11,12,13];order.insert(position,'fleet')
    result=control.run(output,reference_override=reference(warm,position),
        extra_args=('--ship-pointer-fleet-world','--ship-fleet-world-registration',','.join(map(str,order)),
            '--ship-pointer-fleet-world-mail',str(warm)),extra_provenance=(Path(__file__),proof.FIXTURE,ROOT/'tools/validate_ship_fleet_ui_world.py'),
        log_validator=validate_log,scope_override='First normal UI release through one shared membership,world mail and source-ordered task100/1/ship Work;explicit registry/mail input;source UI/world engines separate with packet equality;no full Life/Shift/busy UI/pixels/OSmouse/Win11/hardware proof')
    result.update(mail_initial=warm,fleet_position=position,source_ui_world_boundary_checked=True,first_delivery_tick=3-warm,
        world_context_checkpoints=len(control.STAGES),group_task_lifecycle=True,image_capture=False)
    control.menu.write_json(Path(output)/'report.json',result)
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--mail',type=int,choices=(0,1,2),default=0);p.add_argument('--fleet-position',type=int,choices=range(4),default=0)
    a=p.parse_args();result=run(a.output,a.mail,a.fleet_position)
    print({k:result[k]for k in('passed','checkpoints','actor_rows','publications','first_delivery_tick','exit_code')})


if __name__=='__main__':main()
