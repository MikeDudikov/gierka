"""Compare replacement request boundaries and subsequent world/body outputs to x86."""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,struct,subprocess,tempfile
from tools import probe_ship_fleet_ui_replace as native,validate_ship_world_step as world
ROOT=world.ROOT;PROBE=ROOT/'tests/fixtures/ShipFleetUiReplaceProbe.cs'
FIXTURE=ROOT/'tests/fixtures/ship_fleet_ui_replace.json'
SHA='944ac00954fbf02fc12b931bcd521e82e95a80827bf42e60e1d95f11fe82adae'


def load(path=None):
    raw=Path(path or FIXTURE).read_bytes()
    world.gate.require(hashlib.sha256(raw).hexdigest()==SHA,'UI replace fixture SHA differs');return json.loads(raw)


def compare(data,assembly=None,probe=PROBE):
    lines=['SEED\t'+identifier+'\t'+payload for identifier,payload in data['seed_payloads'].items()]
    lines.append('MAP\t'+base64.b64encode(struct.pack('<576h',*data['terrain'])).decode());required=[];labels=[]
    for case in data['cases']:
        lines.append('START\t2\t'+','.join(map(str,case['order']))+'\t11,12,13');consumed=0
        def row(frame,label):
            required.append(world.meta(frame,consumed));labels.append((case['label'],label,'world'))
            for state in frame['actors']:required.append(world.bodies.expected(state));labels.append((case['label'],label,state['id']))
            task=frame['group']['task'];required.append('\t'.join(map(str,['Q',1,task[2],task[3],task[4]])));labels.append((case['label'],label,'task'))
        for frame in case['rows']:
            lines.append('F\t'+str(frame['captured']));consumed+=sum(p['action']==41 for p in frame['received']);row(frame,frame['counter'])
            for request in case['requests']:
                if request['after']==frame['counter']:
                    lines.append('R\t'+'\t'.join(map(str,request['goal'])));row(request['snapshot'],'replace-'+str(request['goal']))
    _,_,runtime,compiler=world.gate.prerequisites()
    with tempfile.TemporaryDirectory(prefix='ship-ui-replace-')as directory:
        exe=Path(directory)/'Probe.exe';sources=list(dict.fromkeys([*world.bodies.legacy.SOURCES,world.membership.SOURCE,*world.membership.DEPENDENCIES,world.SIM/'SingleStepClock.cs',world.SOURCE]))
        files=[*map(str,sources),str(probe)]
        if assembly is not None:files=['/reference:'+str(assembly),'/reference:'+str(Path(assembly).parent/'netstandard.dll'),str(probe)]
        result=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/out:'+str(exe),*files],capture_output=True,text=True)
        world.gate.require(result.returncode==0,result.stdout+result.stderr)
        if assembly is not None:shutil.copy2(assembly,exe.parent/'Assembly-CSharp.dll')
        result=subprocess.run([str(runtime),str(exe)],input='\n'.join(lines)+'\n',capture_output=True,text=True,cwd=ROOT)
        world.gate.require(result.returncode==0,'UI replace execution failed:'+result.stderr)
        actual=result.stdout.splitlines();world.gate.require(len(actual)==len(required),'UI replace row count differs')
        for index,(a,b)in enumerate(zip(actual,required)):
            if a!=b:raise AssertionError('UI replace mismatch '+str(labels[index])+':'+str([(i,x,y)for i,(x,y)in enumerate(zip(a.split('\t'),b.split('\t')))if x!=y]))
        result=subprocess.run([str(runtime),str(exe),'--api'],input='\n'.join(lines[:4])+'\n',capture_output=True,text=True,cwd=ROOT)
        world.gate.require(result.returncode==0,'UI replace API execution failed:'+result.stdout+result.stderr)
        world.gate.require(result.stdout.strip()=='API\t28','UI replace API incomplete:'+result.stdout)
    frames=sum(len(c['rows'])for c in data['cases']);requests=sum(len(c['requests'])for c in data['cases'])
    return dict(passed=True,cases=len(data['cases']),frames=frames,requests=requests,actor_states=3*(frames+requests),world_rows=frames+requests,
        registration_orders=len({tuple(c['order'])for c in data['cases']}),api_controls=28,checked=True,warnings_as_errors=True)


def validate():
    data=load();world.gate.require(data==json.loads(json.dumps(native.fixture())),'Fresh UI replace source differs')
    return dict(compare(data),fresh_x86=True,fixture_sha256=SHA)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();result=validate()
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':main()
