"""Strict three-actor order/render QA against pinned x86 states and native depth updates."""
from pathlib import Path
import argparse,json,os,re,subprocess,time
from PIL import Image,ImageChops
from tools import smoke_ship_movement as movement,smoke_ship_order as order
from tools import validate_ship_live_fleet as live,validate_source_sprite_depth_queue as depth
from tools import stage_ship_heavy_movement as heavy

units,menu,terrain,require=movement.units,movement.menu,movement.terrain,movement.require
ROOT=menu.REPOSITORY
PREFIX='[ShipFleetMotion] '
COUNTERS=(1,3,6,10,16,25,35,50,60,80,100,125,150,200,250)
CASE={'requested':(9,0),'actual':(9,0),'visible_ids':(11,12,13)}
HEAVY_FIXTURE=ROOT/'tests/fixtures/ship_heavy_poses.json'
HEAVY_SHA='abc5d63688c335ad456dbeea4adfb1f9d9be254ddec53aa8d93af42308f7bbe2'


def provenance():
    r=order.provenance()
    paths=[Path(__file__),HEAVY_FIXTURE,ROOT/'tests/fixtures/ship_live_fleet.json']
    paths+=list((ROOT/'Unity/AncientConquest/Assets/Resources/ShipHeavyMovementGenerated').glob('*'))
    for p in paths:
        if p.is_file():r[str(p.relative_to(ROOT))]={'path':str(p),'bytes':p.stat().st_size,'sha256':menu.file_sha256(p)}
    return r


def load_reference(pending=1,reverse=False,*,case_override=None,counters=COUNTERS):
    reference=movement.load_reference();proof=units.pinned_json(HEAVY_FIXTURE,HEAVY_SHA)
    payloads,meta,atlas=heavy.compose();manifest=ROOT/'Unity/AncientConquest/Assets/Resources/ShipHeavyMovementGenerated'
    require((manifest/'ShipHeavyMovementRgba.bytes').read_bytes()==payloads['ShipHeavyMovementRgba.bytes'],'Heavy staged atlas differs')
    raw=(units.SOURCE_ROOT/'files/DATA/OBJECTS.DKD').read_bytes();entries=movement.inspect_pair((units.SOURCE_ROOT/'files/DATA/OBJECTS.DKX').read_bytes(),raw)
    descriptor=next(e for e in entries if(e['type'],e['name'])==(8,'SHIP_H1110'))
    md=(units.SOURCE_ROOT/'installed/missions/maplib.dkd').read_bytes();me=movement.inspect_pair((units.SOURCE_ROOT/'installed/missions/maplib.dkx').read_bytes(),md)
    palette=movement.dib_palette(movement.resource_payload(next(e for e in me if(e['type'],e['name'])==(1,'PALETTE')),md))
    poses={11:reference['poses'],12:reference['poses'],13:{}}
    for index in range(88):
        f=movement.decode_composite_frame(descriptor,raw,entries,index,0xa3);native=proof['row']['frames'][index]
        require([{k:p[k]for k in('name','offset_x','offset_y','depth')}for p in f['components']]==native['components'],'Heavy native selection differs')
        require([p['name']for p in f['inline_components']]==native['inline_names'],'Heavy inline order differs')
        poses[13][index]={p['source_index']:dict(p,image=movement.base_palette_sprite(p['sprite'],palette))for p in f['components']}
    data=live.load();case=case_override or next(c for c in data['cases']if c['label']=='normal-'+str(pending)+'-'+str(13 if reverse else 11))
    image,size=depth.checked_image();q=depth.NativeQueue(image,size);registration=depth.cohort_registration()
    for g in registration:require(q.register(g['depth'])==g['node_id'],'Native registration changed')
    parent={int(g['resource_name'][4:],16):g['node_id']for g in registration if g['kind']=='inline_parent'}
    states={s['id']:s for s in case['initial']};checkpoints={};publications=[];restores=0
    def checkpoint(stage,claims):
        native_queue=q.snapshot();draws=[];rows=[];groups={}
        for draw in reference['draws']:
            updated=draw;identifier=draw['instance_id']
            if draw['kind']=='ship'and identifier in states:
                state=states[identifier];frame=state['drawn']['frame'];x,y=state['drawn']['world'];part=poses[identifier][frame][draw['source_index']]
                updated=dict(draw,name=part['name'],image=part['image'],x=x+part['offset_x'],y=y+part['offset_y'],depth=21000 if part['source_index']==0 else max(10000,20000-(72 if identifier==13 else 56)-y))
            groups.setdefault(order.group_key(updated),[]).append(updated)
        for node in native_queue['draw_order']:
            g=registration[node];identifier=int(g['resource_name'][4:],16);kind={'inline_parent':'body','separate_shadow':'shadow','reef':'reef'}[g['kind']]
            for draw in groups[kind,identifier]:
                require(draw['depth']==native_queue['depths'][node],'Native depth differs from world pose')
                rows.append({'stage':stage,'node':node,'kind':g['kind'],'id':identifier,'part':draw.get('source_index',-1),'depth':draw['depth'],'order':10+len(draws)})
                draws.append(draw)
        ships=dict(reference['ships'])
        for identifier,s in states.items():
            alpha=Image.new('L',(72,72)if identifier==13 else(56,56))
            for part in poses[identifier][s['drawn']['frame']].values():alpha=ImageChops.lighter(alpha,part['image'].getchannel('A'))
            ships[identifier]=dict(ships[identifier],world_pixel=tuple(s['drawn']['world']),alpha=alpha)
        result=dict(reference,draws=draws,ships=ships);result['world']=units.compose_world(result)
        expected_parts=[dict(id=d['instance_id'],index=d['source_index'],sprite=d['name'],order=10+i,world=[d['x'],d['y']])for i,d in enumerate(draws)if d['kind']=='ship'and d['instance_id']in states]
        checkpoints[stage]={'actors':[live.expected(dict(states[i],claims=claims))for i in(11,12,13)],'parts':expected_parts,'queue':rows,
                            'image':units.expected_image(result,CASE),'regions':units.ship_regions(result,CASE),'publications':list(publications),'claims':claims}
    checkpoint('initial',case['initial'][-1]['claims'])
    operations=case['operations']
    for i,op in enumerate(operations):
        if op['kind']=='G':continue
        state=op['state'];states[op['id']]=state
        for j,p in enumerate(state['publications']):
            publications.append(dict(counter=op['counter'],id=op['id'],index=j,frame=p['frame'],world=p['world'],depth=p['depth']))
            q.update(parent[op['id']],p['depth'])
        if op['kind']=='R'and(i+1==len(operations)or operations[i+1]['kind']!='R'):checkpoint('requests',state['claims'])
        if op['kind']=='T'and op['counter']in counters and(i+1==len(operations)or operations[i+1]['kind']=='L'or operations[i+1].get('counter')!=op['counter']):checkpoint('tick-'+str(op['counter']),state['claims'])
        if op['kind']=='L'and(i+1==len(operations)or operations[i+1]['kind']!='L'):
            restores+=1;checkpoint('restore-'+str(op['counter']),state['claims'])
    require(len(checkpoints)==2+len(counters)+restores,'Incomplete fleet reference checkpoints')
    return dict(checkpoints=checkpoints,publications=publications,registration=registration,pending=pending,reverse=reverse)


def parse(log,reference):
    stages={};current=None;publications=[];complete=False
    for line in log.splitlines(keepends=True):
        if not line.endswith('\n'):continue
        line=line.rstrip('\r\n')
        if not line.startswith(PREFIX):continue
        text=line[len(PREFIX):]
        if text.startswith('stage: '):
            stage=text[7:].split(';')[0];require(stage not in stages and stage in reference['checkpoints'],'Unknown/duplicate fleet stage')
            current=stage;stages[stage]=dict(actors=[],parts=[],queue=[],ended=False,publications=list(publications))
        elif text.startswith('actor: '):
            stage,row=text[7:].split('\t',1);require(stage==current and not stages[stage]['ended'],'Actor leaves checkpoint')
            stages[stage]['actors'].append(row)
        elif text.startswith('part: '):
            m=re.fullmatch(r'part: ([^;]+); id=(\d+); index=(\d+); sprite=([^;]+); order=(\d+); world=(-?\d+),(-?\d+)',text);require(m is not None,'Malformed fleet component')
            stage,identifier,index,sprite,rank,x,y=m.groups();require(stage==current and not stages[stage]['ended'],'Component leaves checkpoint')
            stages[stage]['parts'].append(dict(id=int(identifier),index=int(index),sprite=sprite,order=int(rank),world=[int(x),int(y)]))
        elif text.startswith('queue: '):
            m=re.fullmatch(r'queue: stage=([^;]+); node=(\d+); kind=([^;]+); id=([0-9a-f]{8}); part=(-?\d+); depth=(-?\d+); order=(\d+)',text);require(m is not None,'Malformed fleet queue')
            stage,node,kind,identifier,part,d,rank=m.groups();require(stage==current and not stages[stage]['ended'],'Queue leaves checkpoint')
            stages[stage]['queue'].append(dict(stage=stage,node=int(node),kind=kind,id=int(identifier,16),part=int(part),depth=int(d),order=int(rank)))
        elif text.startswith('publication: '):
            m=re.fullmatch(r'publication: (\d+); id=(\d+); index=(\d+); frame=(\d+); world=(-?\d+),(-?\d+); depth=(-?\d+)',text);require(m is not None,'Malformed fleet publication')
            counter,identifier,index,frame,x,y,d=map(int,m.groups());publications.append(dict(counter=counter,id=identifier,index=index,frame=frame,world=[x,y],depth=d))
            require(publications==reference['publications'][:len(publications)],'Fleet publication order differs from x86')
        elif text.startswith('end: '):
            stage=text[5:];require(stage==current and not stages[stage]['ended'],'Invalid fleet end fence');row=stages[stage];expected=reference['checkpoints'][stage]
            require(row['actors']==expected['actors'],'Fleet actor state differs at '+stage)
            require(sorted(row['parts'],key=lambda p:(p['id'],p['index']))==sorted(expected['parts'],key=lambda p:(p['id'],p['index'])),'Fleet component differs at '+stage)
            require(row['queue']==expected['queue'],'Fleet renderer queue differs at '+stage)
            require(row['publications']==expected['publications'],'Fleet publication checkpoint differs')
            row['ended']=True
        elif text.startswith('complete: '):complete=True
        else:require(text.startswith(('registration: ','conditions: ','cleanup: ')),'Unknown fleet log record')
    if complete:require(list(stages)==list(reference['checkpoints'])and all(r['ended']for r in stages.values())and publications==reference['publications'],'Incomplete fleet replay')
    return stages,complete


def run(output,pending=1,reverse=False):
    output=Path(output).resolve();require(not output.exists(),'Use a fresh fleet motion output path');output.mkdir(parents=True)
    reference=load_reference(pending,reverse);baseline=provenance();env=os.environ.copy();env['DISPLAY']=menu.DISPLAY;env['LD_LIBRARY_PATH']=str(menu.TOOLCHAIN/'usr/lib/x86_64-linux-gnu')
    log=output/'player.log';launch=['bash',str(terrain.LAUNCHER),str(terrain.EXECUTABLE),'-logFile',str(log),'--ship-fleet-motion-reference','--ship-fleet-motion-pending',str(pending),'--terrain-origin-x','9','--terrain-origin-y','0','--terrain-reference-exit-after','1']
    if reverse:launch.append('--ship-fleet-motion-reverse')
    metadata=dict(launch=launch,provenance=baseline,pending=pending,reverse=reverse,scope='Three actual local actors;normal explicit idle goals/groups;controlled clock;no mouse/group-task/fullLife/final2026art/nativeWindows11/hardware claim')
    menu.write_json(output/'launch.json',metadata);player=xvfb=wl=xl=None;captures={};failure=None;started=time.monotonic()
    try:
        require(not menu.DISPLAY_SOCKET.exists(),'Display79 is owned')
        xl=(output/'xvfb.log').open('w');xvfb=subprocess.Popen([str(menu.TOOLCHAIN/'usr/bin/Xvfb'),menu.DISPLAY,'-screen','0','1920x1080x24','-nolisten','tcp','-ac'],env=env,stdout=xl,stderr=subprocess.STDOUT);menu.wait_for_display(xvfb)
        wl=(output/'wine-launch.log').open('w');player=subprocess.Popen(launch,cwd=terrain.EXECUTABLE.parent,env=env,stdout=wl,stderr=subprocess.STDOUT)
        window=units.wait_for_ready(player,env,log);geometry=menu.xdotool(env,'getwindowgeometry','--shell',window);(output/'geometry.txt').write_text(geometry)
        g=dict(x.split('=',1)for x in geometry.splitlines()if'='in x);require(tuple(int(g[x])for x in('X','Y','WIDTH','HEIGHT'))==(0,0,1920,1080),'Fleet player not fullscreen1920x1080')
        while True:
            text=terrain.read_log(log);stages,complete=parse(text,reference);ready=[s for s,r in stages.items()if r['ended']]
            if ready:
                stage=ready[-1];require(all(s in captures for s in ready[:-1]),'Missed held fleet checkpoint')
                if stage not in captures:
                    cp=reference['checkpoints'][stage];attempts=[];began=time.monotonic()
                    while True:
                        path=menu.capture(env,output,stage+'-attempt-'+str(len(attempts)+1).zfill(2))
                        with Image.open(path)as im:maximum=max(v[1]for v in ImageChops.difference(im.convert('RGB'),cp['image']).getextrema())
                        attempts.append(dict(screenshot=path.name,maximum_channel_error=maximum))
                        require(time.monotonic()-began<1.0,'Fleet presentation exceeded held fence')
                        if maximum==0:break
                        require(player.poll()is None,'Player exited before fleet capture');time.sleep(.02)
                    relevant=lambda t:[s for s in t.splitlines()if s.startswith(PREFIX)]
                    require(relevant(text)==relevant(terrain.read_log(log)),'Fleet state changed during capture')
                    cp['image'].save(output/(stage+'-expected.png'),compress_level=0)
                    captures[stage]=dict(attempts=attempts,maximum_channel_error=maximum,actors=3,components=10,queue_reads=34)
                    menu.write_json(output/'captures.json',captures)
            if player.poll()is not None:break
            require(time.monotonic()-started<150,'Fleet runtime timeout');time.sleep(.02)
        require(player.wait(timeout=10)==0 and complete and list(captures)==list(reference['checkpoints']),'Fleet player did not finish')
        final=terrain.read_log(log);require('Exception'not in final,'Fleet runtime exception')
        expected_claims=len(reference['checkpoints']['tick-250']['claims'])
        require('claimed_released='+str(expected_claims)+'; visual_refs_cleared=True'in final and PREFIX+'cleanup: pose_owners=3; visual_refs_cleared=True'in final,'Fleet resources/claims leaked')
        require(provenance()==baseline,'Fleet build/source changed during QA')
    except Exception as error:failure=error
    finally:
        issues=[]
        for process,label in((player,'fleet player'),(xvfb,'fleet Xvfb')):
            issue=menu.stop_owned_process(process,label)
            if issue:issues.append(issue)
        for stream in(wl,xl):
            if stream is not None:stream.close()
        if issues and failure is None:failure=RuntimeError(str(issues))
    if failure:menu.write_json(output/'failure.json',dict(metadata,passed=False,error=str(failure)));raise failure
    r=dict(metadata,passed=True,captures=captures,publications=len(reference['publications']),actor_states=3*len(captures),components=10*len(captures),queue_reads=34*len(captures),exit_code=0,elapsed_seconds=time.monotonic()-started,
           screenshots={p.name:menu.file_sha256(p)for p in sorted(output.glob('*.png'))})
    menu.write_json(output/'report.json',r);return r


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--pending',type=int,default=1,choices=(1,2,3,7));p.add_argument('--reverse',action='store_true');a=p.parse_args()
    r=run(a.output,a.pending,a.reverse);print(json.dumps({k:r[k]for k in('passed','actor_states','components','queue_reads','publications','exit_code')}))


if __name__=='__main__':main()
