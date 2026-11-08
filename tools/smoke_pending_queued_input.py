"""First Shift through InputSystem;source route continues after graphics-only deselection."""
from pathlib import Path
import argparse,json,re
from tools import smoke_queued_input as shared,validate_pending_queued_input as proof
control=shared.control;ROOT=proof.ROOT;require=shared.require
COUNTERS=(1,3,10,25,50,51,80,120,160,200)
STAGES=control.STAGES[:9]+['pending-append-down','pending-append-up','pending-duplicate-down','pending-duplicate-up']+[
 'tick-'+str(n)for n in(1,3,10,25,50)]+['route-clear-point','route-clear-right-down','route-clear-right-up',
 'route-recall-c-down','route-recall-c-up']+[
 'tick-'+str(n)for n in(51,80,120,160,200)]+['hidden-duplicate-down','hidden-duplicate-up']+control.STAGES[-5:]


def reference(position=0,source_keys=False):
    data=proof.load();c=next(c for c in data['cases']if c['label']=='pending-queued-'+str(position))
    ops=[dict(kind='R',id=s['id'],counter=0,state=s)for s in c['initial']]
    for f in c['rows']:ops.extend(dict(kind='T',id=s['id'],counter=f['counter'],state=s)for s in f['actors'])
    base=control.rendering.load_reference(case_override=dict(initial=c['initial'],operations=ops),counters=COUNTERS)
    checkpoints={};contexts={};tasks={};markers={};selections={};tick=0;ui_index=-1
    depth=control.rendering.depth;image,size=depth.checked_image();q=depth.NativeQueue(image,size);q.w(depth.M,depth.M+0x80000)
    def register(d,callback=False):
        if callback:q.call(0x55dc20,(depth.M,depth.OUT,d,0,1,1,0))
        else:q.call(0x55d670,(depth.M,depth.OUT,d,1,0,0,1,1,0,0))
        return q.r(depth.OUT)
    for node in depth.cohort_registration():register(node['depth'])
    marker_nodes=[];points=[];selected=True;late_request=False
    for i,stage in enumerate(STAGES):
        if stage.startswith('tick-'):tick=int(stage[5:])
        if stage in('b-up','add-c-up','add-d-up'):register(1020);register(1020,True)
        if stage=='dispatch-up':ui_index=0;marker_nodes.append(register(7))
        if stage=='pending-append-up':ui_index=1;marker_nodes.append(register(7))
        if stage=='pending-duplicate-up':ui_index=2
        if source_keys and stage in('route-clear-point','clear-point'):
            for node in marker_nodes:q.call(0x55ed60,(depth.M,node))
            marker_nodes=[]
        if source_keys and stage=='hidden-duplicate-down':
            marker_nodes=[register(7)for _ in points]
        if stage=='route-clear-right-up':
            for node in marker_nodes:q.call(0x55ed60,(depth.M,node))
            marker_nodes=[]
        if stage=='hidden-duplicate-up':late_request=True
        if stage in('route-clear-right-up','clear-right-up'):selected=False
        if stage in('route-recall-c-up','recall-c-up'):selected=True
        key='tick-'+str(tick)if tick else'initial';cp=base['checkpoints'][key]
        checkpoints[stage]=dict(cp,queue=[dict(row,stage=stage)for row in cp['queue']])
        if i<8:
            ids=[11]+([12]if i>=4 else[])+([13]if i>=6 else[])if i>=2 else[]
            selections[stage]=(','.join(format(n,'08x')for n in ids)or'none',bool(ids),bool(ids))
            contexts[stage]=(0,0,0,2,'-1,-1,-1','-1,-1,-1');markers[stage]=[];continue
        selections[stage]=('0000000b,0000000c,0000000d'if selected else'none',False,selected)
        if tick==0:
            state=data['initial_ui_steps'][ui_index]['state'];task=state['task']['header'];points=[p['cell']for p in state['route']['points']]
            contexts[stage]=(0,0,6,2,'0,0,0','-1,-1,-1')
        else:
            frame=c['rows'][tick-1];task=frame['group']['task'];points=frame['group']['route']['points']
            consumed=sum(p['action']==41 for f in c['rows'][:tick]for p in f['received'])
            contexts[stage]=(frame['group']['age'],consumed,len(frame['outgoing']),frame['mail_gate'],'0,0,0','0,0,0')
        #4cf2c0 refreshes task+8 even when4ce6c0 returns duplicate;no world tick follows.
        tasks[stage]=(task[1],len(points),tick if late_request else task[2],task[3],task[4])
        count=q.r(depth.M+0x1a0);draw=[q.r(q.r(depth.ORDER+4*j)+0x40)for j in range(count)][::-1]
        alive=[n for n in draw if n>=21 and q.r(q.r(depth.IDS+4*n))&0x8000]
        markers[stage]=[(0,j,points[j][0]*64+14,points[j][1]*64+18,'WPMOVE_'+str(j),node,44+alive.index(node),True)for j,node in enumerate(marker_nodes)]
    packets=[dict(actor=p['actor'],action=p['action'],payload_hex=p['payload_hex'])for p in c['initial_packets']]
    require(packets==data['initial_ui_steps'][0]['state']['packets'],'Independent source first UI/world packets differ')
    base.update(checkpoints=checkpoints,contexts=contexts,taskstates=tasks,markers=markers,selections=selections,
        stage_order=STAGES,packets=packets,world=c,source_keys=source_keys,
        key_events=[(0,True,-1,True),(50,False,0,False),(200,True,0,False),(200,False,0,False)]if source_keys else[])
    return base


def negative_controls(log,ref):
    shared.validate_log(log,ref);detected=[]
    mutations={
        'recreated_hidden_marker':log.replace('[ShipFleetMotion] stage: hidden-duplicate-up;',
            '[ShipFleetWaypoint] visual: stage=hidden-duplicate-up; group=0; ordinal=0; position=1166,402; sprite=WPMOVE_0; node=27; order=50; visible=True\n[ShipFleetMotion] stage: hidden-duplicate-up;',1),
        'clear_erased_logical_route':log.replace('stage=route-clear-right-up; subtype=2; points=2','stage=route-clear-right-up; subtype=2; points=0',1),
        'clear_replaced_task':log.replace('stage=route-clear-right-up; subtype=2;','stage=route-clear-right-up; subtype=1;',1),
        'lost_first_membership':re.sub(r'^\[ShipFleetControl\] packet: id=11; action=41;[^\n]*\n','',log,count=1,flags=re.M),
        'early_first_delivery':log.replace('[ShipWorldStep] received: at=1;','[ShipWorldStep] received: at=0;',1),
        'lost_ctrl_recall':log.replace('checkpoint: stage=route-recall-c-up; members=0000000b,0000000c,0000000d; pending=False; selected=True;',
            'checkpoint: stage=route-recall-c-up; members=none; pending=False; selected=False;',1),
    }
    if ref.get('source_keys'):
        mutations['lost_key_envelope']=re.sub(r'^\[ShipFleetWaypoint\] key: [^\n]*\n','',log,count=1,flags=re.M)
        mutations['lost_shift_restore']=re.sub(r'^\[ShipFleetWaypoint\] visual: stage=hidden-duplicate-down;[^\n]*\n','',log,count=1,flags=re.M)
    if 'key_controls'in ref:
        expected=ref['key_controls'][0][0];other='LeftShift'if expected=='RightShift'else 'RightShift'
        mutations['wrong_shift_control']=log.replace('key-control: name='+expected+';','key-control: name='+other+';',1)
    for name,mutant in mutations.items():
        require(mutant!=log,'Pending checker mutation did not activate:'+name)
        try:shared.validate_log(mutant,ref)
        except (AssertionError,RuntimeError,ValueError):detected.append(name)
        else:raise AssertionError('Pending checker accepted:'+name)
    return detected


def run(output,position=0,right_shift=False):
    order=[11,12,13];order.insert(position,'fleet');ref=reference(position,source_keys=True)
    ref['key_controls']=[('RightShift'if right_shift else 'LeftShift',row[1])for row in ref['key_events']]
    r=control.run(output,reference_override=ref,extra_args=('--ship-pointer-fleet-world','--ship-fleet-world-registration',
        ','.join(map(str,order)),'--ship-fleet-wave-prefixes','117,117,117','--ship-pointer-fleet-pending-queued-replay',*(('--ship-pointer-right-shift-replay',)if right_shift else())),
        extra_provenance=(Path(__file__),Path(shared.__file__),proof.FIXTURE,proof.LIFECYCLE,shared.keys.FIXTURE,Path(shared.keys.native.__file__),
            ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime/WorldPointerInput.cs',
            ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime/ShipFleetMoveInputReplay.cs',
            ROOT/'tools/probe_pending_queued_input.py',ROOT/'tools/probe_queued_marker_lifecycle.py',
            ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime/ShipFleetVisualReference.cs',
            ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime/ShipPointerReference.cs'),
        log_validator=shared.validate_log,scope_override=__doc__)
    r.update(right_shift_replay=right_shift,key_control_events=len(ref["key_controls"]),source_key_visibility=True,key_envelopes=len(ref['key_events']),fleet_position=position,wave_prefixes=[117]*3,constant_controlled_memory_profile=True,
        first_pending_shift=True,marker_checkpoint_reads=sum(map(len,ref['markers'].values())),
        negative_controls=negative_controls((Path(output)/'player.log').read_text(),ref),image_capture=False)
    control.menu.write_json(Path(output)/'report.json',r);return r


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--fleet-position',type=int,choices=(0,3),default=0)
    p.add_argument('--right-shift',action='store_true');a=p.parse_args();r=run(a.output,a.fleet_position,a.right_shift);print({k:r[k]for k in('passed','checkpoints','actor_rows','publications','marker_checkpoint_reads','exit_code')})


if __name__=='__main__':main()
