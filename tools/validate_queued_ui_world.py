"""UI/1001->1002->1001 request boundaries and full deterministic C#world."""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,struct,subprocess,tempfile
from tools import probe_queued_ui_world as native,validate_queued_world_integration as integrated
world=integrated.world;ROOT=world.ROOT;FIXTURE=ROOT/'tests/fixtures/queued_ui_world.json'
SHA='7431c964531c4a15472404c3612795cf974f9218c3e9ef922a36a248a2087b0c'


def load():
    raw=FIXTURE.read_bytes();world.gate.require(hashlib.sha256(raw).hexdigest()==SHA,'Queued UI fixture SHA differs');return json.loads(raw)


def compare(assembly=None,data=None):
    d=load()if data is None else data;lines=['SEED\t'+i+'\t'+p for i,p in d['seed_payloads'].items()]
    lines.append('MAP\t'+base64.b64encode(struct.pack('<576h',*d['terrain'])).decode());required=[];labels=[]
    for c in d['cases']:
        lines.append('USTART\t2\t'+','.join(map(str,c['order']))+'\t11,12,13\t'+','.join(map(str,c['prefixes'])));consumed=0
        def row(f,label):
            required.append(integrated.expected(f,consumed));labels.append((c['label'],label,'world'))
            for state in f['actors']:
                required.append(world.bodies.expected(state));labels.append((c['label'],label,state['id'],'body'))
                calls=[a for a in f['arrivals']if a['id']==state['id']]
                required.append(f"A\t{state['id']}\t"+';'.join(f"{a['counter']},{a['cell']}"for a in calls));labels.append((c['label'],label,state['id'],'arrival'))
        for f in c['rows']:
            lines.append('WF\t'+str(f['captured']));consumed+=sum(p['action']==41 for p in f['received']);row(f,f['counter'])
            for request in c['requests']:
                if request['after']==f['counter']:
                    lines.append('UR\t'+request['kind']+'\t'+'\t'.join(map(str,request['goal'])));row(request['snapshot'],request['kind'])
    _,_,runtime,compiler=world.gate.prerequisites()
    with tempfile.TemporaryDirectory(prefix='queued-ui-world-')as directory:
        exe=Path(directory)/'Probe.exe';sources=list(dict.fromkeys([*world.bodies.legacy.SOURCES,world.membership.SOURCE,
            *world.membership.DEPENDENCIES,world.SIM/'SingleStepClock.cs',world.SOURCE,world.PROBE]));files=list(map(str,sources))
        if assembly is not None:files=['/reference:'+str(assembly),'/reference:'+str(Path(assembly).parent/'netstandard.dll'),str(world.PROBE)]
        r=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/out:'+str(exe),*files],capture_output=True,text=True)
        world.gate.require(r.returncode==0,r.stdout+r.stderr)
        if assembly is not None:shutil.copy2(assembly,exe.parent/'Assembly-CSharp.dll')
        r=subprocess.run([str(runtime),str(exe)],input='\n'.join(lines)+'\n',capture_output=True,text=True,cwd=ROOT)
        world.gate.require(r.returncode==0,r.stderr);actual=r.stdout.splitlines();world.gate.require(len(actual)==len(required),'Queued UI row count differs')
        for i,(a,b)in enumerate(zip(actual,required)):
            world.gate.require(a==b,f'Queued UI mismatch row{i} {labels[i]}\nactual:{a}\nexpected:{b}')
    frames=sum(len(c["rows"])for c in d["cases"]);requests=sum(len(c["requests"])for c in d["cases"])
    return dict(passed=True,cases=len(d["cases"]),frames=frames,requests=requests,actor_states=3*(frames+requests),world_rows=frames+requests,
        explicit_memory_inputs=True,full_event_records=True,unity_input_adapter=False)


def validate():
    d=load();world.gate.require(d==json.loads(json.dumps(native.fixture())),'Fresh source queued UI differs');return dict(compare(),fresh_x86=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--pinned',action='store_true');p.add_argument('--assembly',type=Path);a=p.parse_args()
    r=compare(a.assembly)if a.assembly or a.pinned else validate();a.output.write_text(json.dumps(r,indent=2)+'\n');print(r)


if __name__=='__main__':main()
