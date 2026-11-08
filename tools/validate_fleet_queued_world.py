"""Independent source100/2 world corpus and pure actor arrival projection.

C#100/2 world scheduling remains guarded. Actor comparison replays actual
x86 mail in source registry order,not a second world/task implementation.
"""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,struct,subprocess,tempfile
from tools import probe_fleet_queued_world as native
from tools import validate_ship_world_step as world
ROOT=world.ROOT;SIM=world.SIM;FIXTURE=ROOT/'tests/fixtures/fleet_queued_world.json'
SHA='5d36373f7cf9e95fd2f66e338af1cdc6c0c6ad6526cd58610bf3217cfe98d885'


def load(path=None):
    raw=Path(path or FIXTURE).read_bytes()
    world.gate.require(hashlib.sha256(raw).hexdigest()==SHA,'Queued world fixture SHA differs')
    return json.loads(raw)


def compare_cases(actual,expected):
    actual=json.loads(json.dumps(actual))
    world.gate.require(len(actual)==len(expected),'Queued world case count differs')
    for a,b in zip(actual,expected):
        world.gate.require(a['label']==b['label'],'Queued world case order differs')
        world.gate.require(len(a['rows'])==len(b['rows']),'Queued world frame count differs')
        for i,(x,y)in enumerate(zip(a['rows'],b['rows'])):
            world.gate.require(x==y,f"Queued world x86 mismatch {b['label']} frame{i} counter{y['counter']}")
        world.gate.require({k:v for k,v in a.items()if k!='rows'}=={k:v for k,v in b.items()if k!='rows'},'Queued world input/handoff differs')


def summarize(d):
    rows=[r for c in d['cases']for r in c['rows']];arrivals=[a for r in rows for a in r['arrivals']]
    return dict(passed=True,cases=len(d['cases']),frames=len(rows),accepted_steps=sum(bool(r['trace'])for r in rows),
        actor_states=3*len(rows)+sum(len(c['initial'])for c in d['cases']),
        registration_orders=len({tuple(c['order'])for c in d['cases']}),independent_ui_handoffs=len(d['ui_handoffs']),
        arrival_calls=len(arrivals),near_arrival_calls=sum(a['return_address']=='0x4a4a6c'for a in arrivals),
        exact_arrival_calls=sum(a['return_address']=='0x4a49b4'for a in arrivals),
        wave_reads=sum(len(r['wave_reads'])for r in rows),group_visits=sum(len(r['group_visits'])for r in rows),
        received=sum(len(r['received'])for r in rows),emitted=sum(len(r['emitted'])for r in rows),
        publications=sum(len(r['publications'])for r in rows),fixture_sha256=SHA,
        csharp_queued_world_integrated=False,full_ship_life=False,native_crt_executed=False,ui_shift_enabled=False)


def actor_inputs(d):
    lines=['SEED\t'+i+'\t'+p for i,p in d['seed_payloads'].items()]
    lines.append('MAP\t'+base64.b64encode(struct.pack('<576h',*d['terrain'])).decode())
    required=[];labels=[]
    for c in d['cases']:
        lines.append('QSTART\t'+','.join(map(str,c['order']))+'\t'+','.join(map(str,c['members'])))
        for state in c['initial']:
            required.extend([world.bodies.expected(state),f"A\t{state['id']}\t"]);labels.extend([(c['label'],0,state['id'],'body'),(c['label'],0,state['id'],'arrival')])
        for frame in c['rows']:
            received=';'.join(f"{p['actor']}:{p['action']}:{p['payload_hex']}"for p in frame['received'])or'-'
            lines.append(f"QFRAME\t{frame['counter']}\t{int(bool(frame['trace']))}\t{received}")
            for state in frame['actors']:
                entries=[a for a in frame['arrivals']if a['id']==state['id']]
                expected=';'.join(f"{a['counter']},{a['cell']}"for a in entries)
                required.extend([world.bodies.expected(state),f"A\t{state['id']}\t{expected}"])
                labels.extend([(c['label'],frame['counter'],state['id'],'body'),(c['label'],frame['counter'],state['id'],'arrival')])
    return lines,required,labels


def compare_actor(d,assembly=None,source=None):
    lines,required,labels=actor_inputs(d);_,_,runtime,compiler=world.gate.prerequisites()
    with tempfile.TemporaryDirectory(prefix='queued-world-arrival-')as directory:
        exe=Path(directory)/'Probe.exe'
        sources=list(dict.fromkeys([*world.bodies.legacy.SOURCES,world.membership.SOURCE,
            *world.membership.DEPENDENCIES,SIM/'SingleStepClock.cs',world.SOURCE,world.PROBE]))
        if source is not None:sources=[Path(source)if p.name=='ShipMoveOrder.cs'else p for p in sources]
        files=list(map(str,sources))
        if assembly is not None:files=['/reference:'+str(assembly),'/reference:'+str(Path(assembly).parent/'netstandard.dll'),str(world.PROBE)]
        built=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/out:'+str(exe),*files],capture_output=True,text=True)
        world.gate.require(built.returncode==0,built.stdout+built.stderr)
        if assembly is not None:shutil.copy2(assembly,exe.parent/'Assembly-CSharp.dll')
        run=subprocess.run([str(runtime),str(exe)],input='\n'.join(lines)+'\n',capture_output=True,text=True,cwd=ROOT)
        world.gate.require(run.returncode==0,'Queued arrival C# execution failed:'+run.stderr)
        actual=run.stdout.splitlines();world.gate.require(len(actual)==len(required),'Queued arrival row count differs')
        for i,(a,b)in enumerate(zip(actual,required)):
            world.gate.require(a==b,f'Queued arrival C# mismatch row{i} {labels[i]}\nactual:{a}\nexpected:{b}')
        api=subprocess.run([str(runtime),str(exe),'--arrival-api'],input='\n'.join(lines[:4])+'\n',capture_output=True,text=True,cwd=ROOT)
        world.gate.require(api.returncode==0,api.stdout+api.stderr)
        world.gate.require(api.stdout.strip()=='ARRIVAL_API\t2','Queued arrival API incomplete:'+api.stdout)
    return dict(passed=True,states=len(required)//2,arrival_observation_rows=len(required)//2,
        api_controls=2,checked=True,warnings_as_errors=True,source_packets_replayed=True,
        csharp_task_or_world_execution=False)


def validate(fresh=True):
    data=load()
    if fresh:
        observed=json.loads(json.dumps(native.fixture()));compare_cases(observed['cases'],data['cases'])
        world.gate.require({k:v for k,v in observed.items()if k!='cases'}=={k:v for k,v in data.items()if k!='cases'},'Queued world provenance differs')
    return dict(summarize(data),fresh_x86=fresh,actor_port=compare_actor(data))


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--pinned',action='store_true');p.add_argument('--assembly',type=Path);a=p.parse_args()
    r=dict(summarize(load()),actor_port=compare_actor(load(),assembly=a.assembly))if a.assembly else validate(not a.pinned)
    a.output.write_text(json.dumps(r,indent=2)+'\n');print(r)


if __name__=='__main__':main()
