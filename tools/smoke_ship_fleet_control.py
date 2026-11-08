"""First fleet command through real InputSystem events;strict domain/renderer readouts.

This helper does not claim pixel validation of the moving UI composite.
The established rendering/selector pixel regressions remain separate.
"""
from pathlib import Path
import argparse,json,os,re,subprocess,time
from tools import smoke_ship_fleet_motion as rendering,validate_ship_fleet_input_cycle as cycle
menu,units,terrain,require=rendering.menu,rendering.units,rendering.terrain,rendering.require
ROOT=rendering.ROOT
STAGES=['initial','b-down','b-up','add-c-down','add-c-up','add-d-down','add-d-up','dispatch-down','dispatch-up']+['tick-'+str(n)for n in(1,3,10,25,50,80,120,160,200)]+['clear-point','clear-right-down','clear-right-up','recall-c-down','recall-c-up']
COUNTERS=(1,3,10,25,50,80,120,160,200)


def reference():
    data=cycle.load();base=rendering.load_reference(case_override=cycle.motion_case(data),counters=COUNTERS)
    checkpoints={}
    for i,stage in enumerate(STAGES):
        key='initial'if i<8 else'requests'if stage=='dispatch-up'else stage if stage.startswith('tick-')else'tick-200'
        cp=base['checkpoints'][key];checkpoints[stage]=dict(cp,queue=[dict(r,stage=stage)for r in cp['queue']])
    base['checkpoints']=checkpoints;base['packets']=data['packets'];return base


def provenance():
    r=rendering.provenance()
    for p in(Path(__file__),ROOT/'tests/fixtures/ship_fleet_input_cycle.json',ROOT/'tests/fixtures/ship_committed_selection.json',ROOT/'tools/probe_ship_fleet_input_cycle.py'):
        r[str(p.relative_to(ROOT))]={'path':str(p),'bytes':p.stat().st_size,'sha256':menu.file_sha256(p)}
    return r


def validate_log(log,ref):
    rows,_=rendering.parse(log,ref)
    packets=[]
    for m in re.finditer(r'^\[ShipFleetControl\] packet: id=(\d+); action=(\d+); payload=([0-9a-f]+)$',log,re.M):
        packets.append(dict(actor=int(m[1]),action=int(m[2]),payload_hex=m[3]))
    require(packets==ref['packets'][:len(packets)],'Fleet input packet order/payload differs')
    selections={}
    pattern=r'^\[ShipFleetSelection\] checkpoint: stage=([^;]+); members=([^;]+); pending=(True|False); selected=(True|False); counter=(\d+)$'
    for m in re.finditer(pattern,log,re.M):selections[m[1]]=dict(members=m[2],pending=m[3]=='True',selected=m[4]=='True',counter=int(m[5]))
    control={m[1]:(int(m[2]),int(m[3]),m[4]=='True')for m in re.finditer(r'^\[ShipFleetControl\] selection: stage=([^;]+); group=(-?\d+); temporary=(\d+); dispatched=(True|False)$',log,re.M)}
    done='[ShipFleetMoveReplay] complete:'in log
    for stage in rows:
        if not rows[stage]['ended']:continue
        require(stage in selections and stage in control,'Missing fleet selection checkpoint')
        index=STAGES.index(stage);members=[];pending=False;group=-1;sent=index>=8
        if 2<=index<=7:
            members=[11]+([12]if index>=4 else[])+([13]if index>=6 else[]);pending=True
        elif 8<=index<20 or stage=='recall-c-up':members=[11,12,13];group=0
        expected=','.join(format(i,'08x')for i in members)or'none'
        s=selections[stage];require((s['members'],s['pending'],s['selected'])==(expected,pending,bool(members)),'Fleet selection differs at '+stage)
        require(control[stage]==(group,len(members)if pending else 0,sent),'Committed/temporary group state differs at '+stage)
    if done:
        require(list(rows)==STAGES and all(r['ended']for r in rows.values()),'Fleet control replay incomplete')
        require(packets==ref['packets'],'Missing actual fleet packets')
    return rows,done


def run(output,*,reference_override=None,extra_args=(),extra_provenance=(),log_validator=validate_log,scope_override=None):
    output=Path(output).resolve();require(not output.exists(),'Use a fresh fleet control output');output.mkdir(parents=True)
    ref=reference()if reference_override is None else reference_override
    def current_provenance():
        result=provenance()
        for path in extra_provenance:
            p=Path(path);result[str(p.relative_to(ROOT))]=dict(path=str(p),bytes=p.stat().st_size,sha256=menu.file_sha256(p))
        return result
    baseline=current_provenance();env=os.environ.copy();env['DISPLAY']=menu.DISPLAY;env['LD_LIBRARY_PATH']=str(menu.TOOLCHAIN/'usr/lib/x86_64-linux-gnu')
    log=output/'player.log';launch=['bash',str(terrain.LAUNCHER),str(terrain.EXECUTABLE),'-logFile',str(log),'--ship-pointer-reference','--ship-pointer-fleet-selection','--ship-pointer-fleet-movement','--ship-pointer-fleet-movement-replay','--terrain-origin-x','9','--terrain-origin-y','0']
    launch.extend(map(str,extra_args))
    metadata=dict(launch=launch,provenance=baseline,scope='First normal3member order through synthetic InputSystem;Ctrl recall;explicit UI/body source-oracle handoff;no task scheduler,Shift group editing,busy replacement,OSmouse,fullUI pixel/nativeWin11/hardware/finalart claim')
    if scope_override is not None:metadata['scope']=scope_override
    menu.write_json(output/'launch.json',metadata);player=xvfb=wl=xl=None;failure=None;started=time.monotonic()
    try:
        require(not menu.DISPLAY_SOCKET.exists(),'Display79 is owned')
        xl=(output/'xvfb.log').open('w');xvfb=subprocess.Popen([str(menu.TOOLCHAIN/'usr/bin/Xvfb'),menu.DISPLAY,'-screen','0','1920x1080x24','-nolisten','tcp','-ac'],env=env,stdout=xl,stderr=subprocess.STDOUT);menu.wait_for_display(xvfb)
        wl=(output/'wine-launch.log').open('w');player=subprocess.Popen(launch,cwd=terrain.EXECUTABLE.parent,env=env,stdout=wl,stderr=subprocess.STDOUT)
        window=units.wait_for_ready(player,env,log);geometry=menu.xdotool(env,'getwindowgeometry','--shell',window);(output/'geometry.txt').write_text(geometry)
        g=dict(x.split('=',1)for x in geometry.splitlines()if'='in x);require(tuple(int(g[x])for x in('X','Y','WIDTH','HEIGHT'))==(0,0,1920,1080),'Fleet controls not fullscreen1920x1080')
        while player.poll()is None:
            log_validator(terrain.read_log(log),ref);require(time.monotonic()-started<160,'Fleet control runtime timeout');time.sleep(.05)
        final=terrain.read_log(log);rows,done=log_validator(final,ref)
        require(player.wait(timeout=10)==0 and done,'Fleet control did not finish');require('Exception'not in final,'Fleet control runtime exception')
        require('claimed_released=8; visual_refs_cleared=True'in final and 'cleanup: input_unsubscribed=True; visual_refs_cleared=True'in final and '[ShipFleetMotion] cleanup: pose_owners=3; visual_refs_cleared=True'in final,'Fleet control resources leaked')
        require(current_provenance()==baseline,'Fleet control source/build changed during QA')
    except Exception as error:failure=error
    finally:
        issues=[]
        for process,label in((player,'fleet control player'),(xvfb,'fleet control Xvfb')):
            issue=menu.stop_owned_process(process,label)
            if issue:issues.append(issue)
        for stream in(wl,xl):
            if stream is not None:stream.close()
        if issues and failure is None:failure=RuntimeError(str(issues))
    if failure:menu.write_json(output/'failure.json',dict(metadata,passed=False,error=str(failure)));raise failure
    r=dict(metadata,passed=True,checkpoints=len(rows),actor_rows=3*len(rows),component_rows=10*len(rows),actual_queue_reads=34*len(rows),packets=ref['packets'],publications=len(ref['publications']),exit_code=0,elapsed_seconds=time.monotonic()-started,pixel_comparison=False)
    menu.write_json(output/'report.json',r);return r


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=run(a.output);print({k:r[k]for k in('passed','checkpoints','actor_rows','component_rows','actual_queue_reads','publications','exit_code')})


if __name__=='__main__':main()
