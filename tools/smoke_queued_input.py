"""Synthetic InputSystem Shift100/2 replay against x86 world,route and sprite-slot reads.

No screenshot capture;no claim about full App/Life,OS mouse or native Win11.
"""
from pathlib import Path
import argparse,json,re
from tools import smoke_ship_fleet_control as control,validate_queued_ui_world as proof
from tools import validate_ship_fleet_ui_replace as normal,validate_source_key_visibility as keys
ROOT=proof.ROOT;require=control.require
COUNTERS=(1,3,10,25,26,50,85,86,120,160,200)
STAGES=control.STAGES[:9]+['tick-'+str(n)for n in(1,3,10,25)]+[
 'queue-first-down','queue-first-up','queue-append-down','queue-append-up','queue-duplicate-down','queue-duplicate-up']+[
 'tick-'+str(n)for n in(26,50,85)]+['queue-normal-down','queue-normal-up']+[
 'tick-'+str(n)for n in(86,120,160,200)]+control.STAGES[-5:]


FIXTURE=ROOT/'tests/fixtures/queued_input_world.json'
FIXTURE_SHA='3463d6f0b8931cf9196acad494a85d40b3a579c4f92f7c74a53090a5b9febad3'


def load():
    raw=FIXTURE.read_bytes()
    require(control.menu.file_sha256(FIXTURE)==FIXTURE_SHA,'Accessible-cell x86 input fixture differs')
    return json.loads(raw)


def reference(position=0,source_keys=False):
    c=next(c for c in load()['cases']if c['label']==f'queued-ui-{position}-25')
    initial=next(c for c in normal.load()['cases']if c['label']==f'ui-replace-{position}-25')['initial']
    ops=[dict(kind='R',id=s['id'],counter=0,state=s)for s in initial]
    for frame in c['rows']:
        require(frame['publications']==[[s['id'],p['frame'],*p['world'],p['depth']]for s in frame['actors']for p in s['publications']], 'Queued publications left registry order')
        ops.extend(dict(kind='T',id=s['id'],counter=frame['counter'],state=s)for s in frame['actors'])
    base=control.rendering.load_reference(case_override=dict(initial=initial,operations=ops),counters=COUNTERS)
    checkpoints={};contexts={};taskstates={};marker_reads={};tick=0;request=-1
    # Original lower slot registration,including callback health nodes.
    depth=control.rendering.depth;image,size=depth.checked_image();q=depth.NativeQueue(image,size)
    q.w(depth.M,depth.M+0x80000)
    def register(d,callback=False):
        if callback:q.call(0x55dc20,(depth.M,depth.OUT,d,0,1,1,0))
        else:q.call(0x55d670,(depth.M,depth.OUT,d,1,0,0,1,1,0,0))
        return q.r(depth.OUT)
    for node in depth.cohort_registration():register(node['depth'])
    marker_nodes=[]
    for i,stage in enumerate(STAGES):
        if stage.startswith('tick-'):tick=int(stage[5:]);request=-1
        if stage in('b-up','add-c-up','add-d-up'):register(1020);register(1020,True)
        if stage=='queue-first-up':request=0;marker_nodes.append(register(7))
        if stage=='queue-append-up':request=1;marker_nodes.append(register(7))
        if stage=='queue-duplicate-up':request=2
        if stage=='queue-normal-down'and source_keys:
            for node in marker_nodes:q.call(0x55ed60,(depth.M,node))
            marker_nodes=[]
        if stage=='queue-normal-up':
            request=3
            for node in marker_nodes:q.call(0x55ed60,(depth.M,node))
            marker_nodes=[]
        key='tick-'+str(tick)if tick else'initial';cp=base['checkpoints'][key]
        checkpoints[stage]=dict(cp,queue=[dict(row,stage=stage)for row in cp['queue']])
        if i<8:contexts[stage]=(0,0,0,2,'-1,-1,-1','-1,-1,-1');marker_reads[stage]=[];continue
        frame=c['requests'][request]['snapshot']if request>=0 else c['rows'][tick-1]if tick else None
        if frame is None:
            contexts[stage]=(0,0,6,2,'0,0,0','-1,-1,-1');taskstates[stage]=(1,0,0,18,5);marker_reads[stage]=[];continue
        consumed=sum(p['action']==41 for f in c['rows'][:tick]for p in f['received'])
        contexts[stage]=(frame['group']['age'],consumed,len(frame['outgoing']),frame['mail_gate'],'0,0,0','0,0,0')
        task=frame['group']['task'];points=frame['group'].get('route',{}).get('points',[])
        taskstates[stage]=(task[1],len(points),task[2],task[3],task[4])
        count=q.r(depth.M+0x1a0);draw=[q.r(q.r(depth.ORDER+4*j)+0x40)for j in range(count)][::-1]
        alive=[n for n in draw if n>=21 and q.r(q.r(depth.IDS+4*n))&0x8000]
        marker_reads[stage]=[(0,j,points[j][0]*64+14,points[j][1]*64+18,'WPMOVE_'+str(j),node,44+alive.index(node),True)for j,node in enumerate(marker_nodes)]
    packets=[dict(actor=p['actor'],action=p['action'],payload_hex=p['payload_hex'])for p in c['initial_packets']]
    packets.extend(dict(actor=p['actor'],action=p['action'],payload_hex=p['payload_hex'])for request in c['requests']for p in request['packets'])
    base.update(checkpoints=checkpoints,contexts=contexts,taskstates=taskstates,markers=marker_reads,packets=packets,world=c,
        source_keys=source_keys,key_events=[(0,True,-1,True),(0,False,-1,True),(25,True,0,False),(85,False,0,False)]if source_keys else[])
    return base


def validate_log(log,ref):
    log=log[:log.rfind('\n')+1];rows,_=control.rendering.parse(log,ref)
    key_events=[(int(m[1]),m[2]=='True',int(m[3]),m[4]=='True')for m in re.finditer(r'^\[ShipFleetWaypoint\] key: counter=(\d+); visible=(True|False); group=(-?\d+); pending=(True|False)$',log,re.M)]
    require(key_events==ref.get('key_events',[])[:len(key_events)],'Source C45D key envelope sequence differs')
    key_controls=[(m[1],m[2]=='True')for m in re.finditer(r'^\[ShipFleetWaypoint\] key-control: name=([^;]+); visible=(True|False)$',log,re.M)]
    if 'key_controls'in ref:require(key_controls==ref['key_controls'][:len(key_controls)],'Actual Shift KeyControl differs')
    packets=[dict(actor=int(m[1]),action=int(m[2]),payload_hex=m[3])for m in re.finditer(r'^\[ShipFleetControl\] packet: id=(\d+); action=(\d+); payload=([0-9a-f]+)$',log,re.M)]
    require(packets==ref['packets'][:len(packets)],'Queued InputSystem packet order/payload differs')
    selections={m[1]:(m[2],m[3]=='True',m[4]=='True')for m in re.finditer(r'^\[ShipFleetSelection\] checkpoint: stage=([^;]+); members=([^;]+); pending=(True|False); selected=(True|False); counter=(\d+)$',log,re.M)}
    contexts={m[1]:(*map(int,m.groups()[1:5]),m[6],m[7])for m in re.finditer(r'^\[ShipFleetControl\] world: stage=([^;]+); age=(\d+); consumed=(\d+); queued=(\d+); prep=(\d+); ui=([^;]+); sim=([^\r\n]+)$',log,re.M)}
    tasks={m[1]:tuple(map(int,m.groups()[1:]))for m in re.finditer(r'^\[ShipFleetControl\] queued-task: stage=([^;]+); subtype=(\d+); points=(\d+); requested=(\d+); goal=(-?\d+),(-?\d+)$',log,re.M)}
    markers={stage:[]for stage in rows}
    for m in re.finditer(r'^\[ShipFleetWaypoint\] visual: stage=([^;]+); group=(\d+); ordinal=(\d+); position=(-?\d+),(-?\d+); sprite=([^;]+); node=(\d+); order=(\d+); visible=(True|False)$',log,re.M):
        markers.setdefault(m[1],[]).append((*map(int,m.groups()[1:5]),m[6],int(m[7]),int(m[8]),m[9]=='True'))
    stages=ref.get('stage_order',STAGES)
    for stage,row in rows.items():
        if not row['ended']:continue
        i=stages.index(stage);members=[];pending=False
        if 2<=i<=7:members=[11]+([12]if i>=4 else[])+([13]if i>=6 else[]);pending=True
        elif 8<=i<stages.index('clear-right-up')or stage=='recall-c-up':members=[11,12,13]
        expected_selection=ref.get('selections',{}).get(stage,(','.join(format(n,'08x')for n in members)or'none',pending,bool(members)))
        require(selections.get(stage)==expected_selection, 'Queued selection differs at '+stage)
        require(contexts.get(stage)==ref['contexts'][stage], 'Queued world context differs at '+stage)
        require(tasks.get(stage)==ref['taskstates'].get(stage), 'Queued task header/route differs at '+stage)
        require(markers[stage]==ref['markers'][stage], 'Queued marker position/mask/slot/depth differs at '+stage+':'+str((markers[stage],ref['markers'][stage])))
    for kind in('received','emitted'):
        expected=[(f['counter'],proof.world.packet(p,kind=='received'))for f in ref['world']['rows']for p in f[kind]]
        actual=[(int(m[1]),m[2])for m in re.finditer(r'^\[ShipWorldStep\] '+kind+r': at=(\d+); packet=([^\r\n]+)$',log,re.M)]
        require(actual==expected[:len(actual)],'Queued '+kind+' FIFO/stamp differs')
        if '[ShipFleetMoveReplay] complete:'in log:require(actual==expected,'Incomplete queued '+kind)
    done='[ShipFleetMoveReplay] complete:'in log
    if done:
        require(list(rows)==stages and all(r['ended']for r in rows.values()),'Incomplete queued InputSystem replay')
        require(packets==ref['packets']and contexts==ref['contexts']and tasks==ref['taskstates'],'Incomplete queued InputSystem observations')
        require(key_events==ref.get('key_events',[]),'Incomplete source key envelopes')
        if 'key_controls'in ref:require(key_controls==ref['key_controls'],'Incomplete Shift KeyControl readouts')
        require('[ShipFleetControl] guard:'not in log,'Queued replay unexpectedly hit a guard')
    return rows,done


def negative_controls(log,ref):
    validate_log(log,ref);detected=[]
    mutations={
        'lost_ui_packet':re.sub(r'^\[ShipFleetControl\] packet: [^\n]*\n','',log,count=1,flags=re.M),
        'wrong_marker_pixel':log.replace('position=1166,402; sprite=WPMOVE_0','position=1167,402; sprite=WPMOVE_0',1),
        'wrong_marker_mask':log.replace('sprite=WPMOVE_0; node=27','sprite=WPMOVE_1; node=27',1),
        'wrong_marker_order':log.replace('node=27; order=50; visible=True','node=27; order=49; visible=True',1),
        'lost_route_append':log.replace('stage=queue-append-up; subtype=2; points=2','stage=queue-append-up; subtype=2; points=1',1),
        'delayed_mail':log.replace('[ShipWorldStep] received: at=26;','[ShipWorldStep] received: at=27;',1),
    }
    if ref.get('source_keys'):
        mutations['lost_key_envelope']=re.sub(r'^\[ShipFleetWaypoint\] key: [^\n]*\n','',log,count=1,flags=re.M)
    if 'key_controls'in ref:
        expected=ref['key_controls'][0][0];other='LeftShift'if expected=='RightShift'else 'RightShift'
        mutations['wrong_shift_control']=log.replace('key-control: name='+expected+';','key-control: name='+other+';',1)
    for name,mutant in mutations.items():
        require(mutant!=log,'Runtime checker mutation did not activate:'+name)
        try:validate_log(mutant,ref)
        except (AssertionError,RuntimeError,ValueError):detected.append(name)
        else:raise AssertionError('Runtime checker accepted:'+name)
    return detected


def run(output,position=0,right_shift=False):
    registration=[11,12,13];registration.insert(position,'fleet')
    ref=reference(position,source_keys=True)
    ref['key_controls']=[('RightShift'if right_shift else 'LeftShift',row[1])for row in ref['key_events']]
    r=control.run(output,reference_override=ref,extra_args=('--ship-pointer-fleet-world',
        '--ship-fleet-world-registration',','.join(map(str,registration)),'--ship-pointer-fleet-world-mail','2',
        '--ship-fleet-wave-prefixes','117,117,117','--ship-pointer-fleet-queued-replay',*(('--ship-pointer-right-shift-replay',)if right_shift else())),
        extra_provenance=(Path(__file__),FIXTURE,proof.FIXTURE,keys.FIXTURE,Path(keys.native.__file__),
            ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime/WorldPointerInput.cs',
            ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime/ShipFleetMoveInputReplay.cs',
            ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime/ShipPointerReference.cs',ROOT/'tools/compose_wp_move.py',ROOT/'tests/fixtures/wp_move.json',
            *sorted((ROOT/'Unity/AncientConquest/Assets/Resources/ShipFleetVisualsGenerated').glob('*'))),
        log_validator=validate_log,scope_override=__doc__)
    controls=negative_controls((Path(output)/'player.log').read_text(),ref)
    r.update(right_shift_replay=right_shift,key_control_events=len(ref["key_controls"]),negative_controls=controls,source_key_visibility=True,key_envelopes=len(ref['key_events']),fleet_position=position,wave_prefixes=[117]*3,constant_controlled_memory_profile=True,
        shift_requests=3,normal_return_requests=1,marker_checkpoint_reads=sum(map(len,ref['markers'].values())),image_capture=False)
    control.menu.write_json(Path(output)/'report.json',r);return r


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--fleet-position',type=int,choices=range(4),default=0)
    p.add_argument('--right-shift',action='store_true');a=p.parse_args();r=run(a.output,a.fleet_position,a.right_shift);print({k:r[k]for k in('passed','checkpoints','actor_rows','publications','marker_checkpoint_reads','exit_code')})


if __name__=='__main__':main()
