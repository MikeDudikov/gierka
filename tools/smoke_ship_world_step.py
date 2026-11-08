"""World clock/mail/group/ship replay in the shipping player;no image capture.

Checks full actor state,source sprite IDs/positions,actual renderer queue and
deferred command receipts. Does not claim pixel validation or full Ship::Life.
"""
from pathlib import Path
import argparse,json,os,re,subprocess,time
from tools import smoke_ship_fleet_motion as rendering,validate_ship_world_step as world
menu,units,terrain,require=rendering.menu,rendering.units,rendering.terrain,rendering.require
ROOT=rendering.ROOT
COUNTERS=(1,3,10,25,50,80,100,125,150,200,201,202,212)


def reference(busy=False):
    from tools import validate_ship_busy_orders as repeated
    data=repeated.load_world()if busy else world.load()
    case=next(c for c in data['cases']if c['label']==('world-busy-0-10'if busy else'deferred-group-command--1-2'))
    counters=(1,3,10,11,25,50,80,100,125,150,200,201,202,212)if busy else COUNTERS
    native=world.native.WorldOracle(tuple(case['order']),case['warm']);native.request(tuple(case['members']))
    initial=native.frame(0)['actors']
    ops=[dict(kind='R',id=s['id'],counter=0,state=s)for s in initial]
    for f in case['rows']:
        expected=[[s['id'],p['frame'],*p['world'],p['depth']]for s in f['actors']for p in s['publications']]
        require(expected==f['publications'],'Renderer reference must preserve actual source publication order')
        ops.extend(dict(kind='T',id=s['id'],counter=f['counter'],state=s)for s in f['actors'])
    ref=rendering.load_reference(case_override=dict(initial=initial,operations=ops),counters=counters)
    del ref['checkpoints']['requests']
    ref['world']=case;ref['counters']=counters;return ref


def provenance():
    r=rendering.provenance()
    for p in(Path(__file__),world.SOURCE,world.PROBE,ROOT/'tests/fixtures/ship_world_step.json',ROOT/'tools/probe_ship_world_step.py',ROOT/'tests/fixtures/ship_busy_world.json'):
        r[str(p.relative_to(ROOT))]=dict(path=str(p),bytes=p.stat().st_size,sha256=menu.file_sha256(p))
    return r


def validate_log(log,ref):
    rows,_=rendering.parse(log,ref)
    frames=ref['world']['rows'];expected_receipts=[];expected_emissions=[]
    for f in frames:
        expected_receipts.extend((f['counter'],world.packet(p,True))for p in f['received'])
        expected_emissions.extend((f['counter'],world.packet(p))for p in f['emitted'])
    def packets(kind):
        return [(int(m[1]),m[2])for m in re.finditer(r'^\[ShipWorldStep\] '+kind+r': at=(\d+); packet=([^\r\n]+)$',log,re.M)]
    received,emitted=packets('received'),packets('emitted')
    require(received==expected_receipts[:len(received)],'World receipt order/payload/stamp differs')
    require(emitted==expected_emissions[:len(emitted)],'World task emission order/payload/stamp differs')
    checks=[]
    for m in re.finditer(r'^\[ShipWorldStep\] checkpoint: counter=(\d+); age=(\d+); consumed=(\d+); queued=(\d+); prep=(\d+)$',log,re.M):
        counter,age,consumed,queued,prep=map(int,m.groups());checks.append(counter)
        f=next(f for f in frames if f['counter']==counter)
        consumed_expected=sum(p['action']==41 for row in frames[:counter]for p in row['received'])
        require((age,consumed,queued,prep)==(f['group']['age'],consumed_expected,len(f['outgoing']),f['mail_gate']),'World checkpoint differs at '+str(counter))
    require(checks==list(ref['counters'][:len(checks)]),'World checkpoint order differs')
    done='[ShipWorldStep] complete: counter=212; full_game=False'in log
    if done:
        require(list(rows)==list(ref['checkpoints'])and all(r['ended']for r in rows.values()),'Incomplete world actor/render replay')
        require(checks==list(ref['counters'])and received==expected_receipts and emitted==expected_emissions,'Incomplete world mail replay')
        require(rows['tick-212']['publications']==ref['publications'],'Incomplete world publication stream')
    return rows,done,received,emitted


def run(output,busy=False,*,reference_override=None,extra_args=(),extra_provenance=(),log_validator=validate_log,scope_override=None):
    output=Path(output).resolve();require(not output.exists(),'Use a fresh world output');output.mkdir(parents=True)
    ref=reference(busy)if reference_override is None else reference_override
    def current_provenance():
        r=provenance()
        for path in extra_provenance:
            p=Path(path);r[str(p.relative_to(ROOT))]=dict(path=str(p),bytes=p.stat().st_size,sha256=menu.file_sha256(p))
        return r
    baseline=current_provenance();env=os.environ.copy();env['DISPLAY']=menu.DISPLAY;env['LD_LIBRARY_PATH']=str(menu.TOOLCHAIN/'usr/lib/x86_64-linux-gnu')
    log=output/'player.log'
    launch=['bash',str(terrain.LAUNCHER),str(terrain.EXECUTABLE),'-logFile',str(log),'--ship-fleet-motion-reference','--ship-fleet-world-step','--ship-fleet-world-registration','fleet,11,12,13','--terrain-origin-x','9','--terrain-origin-y','0','--terrain-reference-exit-after','1']
    if busy:launch.append('--ship-fleet-world-busy')
    launch.extend(map(str,extra_args))
    metadata=dict(launch=launch,provenance=baseline,scope='Explicit controlled registry/warm2 mail/local normal20+41/40ms clock;normal repeated20 with nonblocking58b0;original Life subset Promote+Work;no inferred mission registration,AI,blocking arbitration,35,full game,pixel/finalart/nativeWin11/hardware proof')
    if scope_override is not None:metadata['scope']=scope_override
    menu.write_json(output/'launch.json',metadata);player=xvfb=wl=xl=None;failure=None;started=time.monotonic()
    try:
        require(not menu.DISPLAY_SOCKET.exists(),'Display79 is owned')
        xl=(output/'xvfb.log').open('w');xvfb=subprocess.Popen([str(menu.TOOLCHAIN/'usr/bin/Xvfb'),menu.DISPLAY,'-screen','0','1920x1080x24','-nolisten','tcp','-ac'],env=env,stdout=xl,stderr=subprocess.STDOUT);menu.wait_for_display(xvfb)
        wl=(output/'wine-launch.log').open('w');player=subprocess.Popen(launch,cwd=terrain.EXECUTABLE.parent,env=env,stdout=wl,stderr=subprocess.STDOUT)
        window=units.wait_for_ready(player,env,log);geometry=menu.xdotool(env,'getwindowgeometry','--shell',window);(output/'geometry.txt').write_text(geometry)
        g=dict(x.split('=',1)for x in geometry.splitlines()if'='in x);require(tuple(int(g[x])for x in('X','Y','WIDTH','HEIGHT'))==(0,0,1920,1080),'World player not fullscreen1920x1080')
        while player.poll()is None:
            log_validator(terrain.read_log(log),ref);require(time.monotonic()-started<150,'World runtime timeout');time.sleep(.05)
        final=terrain.read_log(log);rows,done,received,emitted=log_validator(final,ref)
        require(player.wait(timeout=10)==0 and done,'World player did not finish');require('Exception'not in final,'World runtime exception')
        claims=len(ref['world']['rows'][-1]['actors'][-1]['claims'])
        require('claimed_released='+str(claims)+'; visual_refs_cleared=True'in final and '[ShipFleetMotion] cleanup: pose_owners=3; visual_refs_cleared=True'in final,'World resources/claims leaked')
        require(current_provenance()==baseline,'World source/build changed during QA')
    except Exception as error:failure=error
    finally:
        issues=[]
        for process,label in((player,'world player'),(xvfb,'world Xvfb')):
            issue=menu.stop_owned_process(process,label)
            if issue:issues.append(issue)
        for stream in(wl,xl):
            if stream is not None:stream.close()
        if issues and failure is None:failure=RuntimeError(str(issues))
    if failure:menu.write_json(output/'failure.json',dict(metadata,passed=False,error=str(failure)));raise failure
    r=dict(metadata,passed=True,checkpoints=len(rows),actor_rows=3*len(rows),component_rows=10*len(rows),actual_queue_reads=34*len(rows),received=received,emitted=emitted,publications=len(ref['publications']),exit_code=0,elapsed_seconds=time.monotonic()-started,pixel_comparison=False,image_capture=False)
    menu.write_json(output/'report.json',r);return r


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--busy',action='store_true');a=p.parse_args();r=run(a.output,a.busy)
    print({k:r[k]for k in('passed','checkpoints','actor_rows','component_rows','actual_queue_reads','publications','exit_code')})


if __name__=='__main__':main()
