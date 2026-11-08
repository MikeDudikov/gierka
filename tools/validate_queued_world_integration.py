"""Full C#100/2 world vs original clock/mail/task/actor corpus,including310.

Unlike the earlier actor replay,no source packets are injected after startup.
The shared C#world must itself reproduce task routing and mailbox timing.
"""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,struct,subprocess,tempfile
from tools import validate_fleet_queued_world as proof
from tools import probe_queued_world_integration as native
from tools import validate_ship_world_step as world
ROOT=world.ROOT
HASHES={'queued_world_mixed':'318e79be7d5af12ea4bc6e783a2263268cc662396ce574515dbb0a251184ee95',
    'normal_world_arrivals':'b3259f41b711fc7739eb920803aefdf7f248ef16a4f2a84c4ce62150be22e8d1'}


def load(name):
    p=ROOT/'tests/fixtures'/f'{name}.json';raw=p.read_bytes()
    world.gate.require(hashlib.sha256(raw).hexdigest()==HASHES[name],'Integrated world fixture SHA differs:'+name)
    return json.loads(raw)


def expected(frame,consumed):
    group=frame['group'];route=group.get('route')or dict(registered=0,points=[],members=[])
    visits=[-1 if s=='fleet:0'else int(s.split(':')[1])for s in frame['trace']if s.startswith(('fleet:','ship:'))]
    return '\t'.join(map(str,['K',frame['counter'],frame['phase'],frame['mail_gate'],','.join(map(str,visits)),
        ';'.join(world.packet(p,True)for p in frame['received']),';'.join(world.packet(p)for p in frame['emitted']),
        ';'.join(world.packet(p)for p in frame['outgoing']),';'.join(','.join(map(str,p))for p in frame['publications']),
        group['age'],consumed,','.join(map(str,group['task'])),','.join(map(str,group['members'])),';'.join(group['events']),
        ';'.join(','.join(map(str,p))for p in route['points']),route['registered'],
        ';'.join(','.join(map(str,[m['id'],m['mode'],*m['target']]))for m in route['members']),
        ';'.join(','.join(map(str,a))for a in group.get('assignments',[]))]))


def compare(assembly=None,source=None,data=None):
    if data is None:
        data=proof.load();mixed=load('queued_world_mixed');cases=[*data['cases'],*mixed['cases']]
    else:cases=data['cases']
    lines=['SEED\t'+i+'\t'+p for i,p in data['seed_payloads'].items()]
    lines+=['MAP\t'+base64.b64encode(struct.pack('<576h',*data['terrain'])).decode()]
    required=[];labels=[]
    for c in cases:
        lines.append('\t'.join(map(str,['WSTART',c['warm'],','.join(map(str,c['order'])),','.join(map(str,c['members'])),
            ','.join(map(str,c['prefixes'])),';'.join(','.join(map(str,p))for p in c['points']),
            '-'if c['age_input']is None else c['age_input']])))
        consumed=0
        if c['terrain']=='islands':
            terrain=[0 if (x,y)in((16,2),(21,5),(19,4),(18,6),(16,4))else-1 for y in range(24)for x in range(24)]
        else:terrain=data['terrain']
        lines.append('MAP\t'+base64.b64encode(struct.pack('<576h',*terrain)).decode())
        for f in c['rows']:
            lines.append('WF\t'+str(f['captured']));consumed+=sum(p['action']==41 for p in f['received'])
            required.append(expected(f,consumed));labels.append((c['label'],f['counter'],'world'))
            for state in f['actors']:
                required.append(world.bodies.expected(state));labels.append((c['label'],f['counter'],state['id'],'body'))
                calls=[a for a in f['arrivals']if a['id']==state['id']]
                required.append(f"A\t{state['id']}\t"+';'.join(f"{a['counter']},{a['cell']}"for a in calls));labels.append((c['label'],f['counter'],state['id'],'arrival'))
    _,_,runtime,compiler=world.gate.prerequisites()
    with tempfile.TemporaryDirectory(prefix='queued-world-integration-')as directory:
        exe=Path(directory)/'Probe.exe';sources=list(dict.fromkeys([*world.bodies.legacy.SOURCES,world.membership.SOURCE,
            *world.membership.DEPENDENCIES,world.SIM/'SingleStepClock.cs',Path(source or world.SOURCE),world.PROBE]))
        files=list(map(str,sources))
        if assembly is not None:files=['/reference:'+str(assembly),'/reference:'+str(Path(assembly).parent/'netstandard.dll'),str(world.PROBE)]
        built=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/out:'+str(exe),*files],capture_output=True,text=True)
        world.gate.require(built.returncode==0,built.stdout+built.stderr)
        if assembly is not None:shutil.copy2(assembly,exe.parent/'Assembly-CSharp.dll')
        run=subprocess.run([str(runtime),str(exe)],input='\n'.join(lines)+'\n',capture_output=True,text=True,cwd=ROOT)
        world.gate.require(run.returncode==0,'Integrated world execution failed:'+run.stderr)
        actual=run.stdout.splitlines();world.gate.require(len(actual)==len(required),'Integrated world output count differs')
        for i,(a,b)in enumerate(zip(actual,required)):
            world.gate.require(a==b,f'Integrated world mismatch row{i} {labels[i]}\nactual:{a}\nexpected:{b}')
        api=subprocess.run([str(runtime),str(exe),'--integrated-api'],input='\n'.join(lines[:4])+'\n',capture_output=True,text=True,cwd=ROOT)
        world.gate.require(api.returncode==0,api.stdout+api.stderr)
        world.gate.require(api.stdout.strip()=='INTEGRATED_API\t10','Integrated API controls incomplete:'+api.stdout)
    return dict(passed=True,cases=len(cases),frames=sum(len(c['rows'])for c in cases),
        actor_states=sum(len(c['rows'])*3 for c in cases),strict_event_records=True,
        csharp_world_executes_task_and_mail=True,source_packets_injected_after_startup=False,
        checked=True,warnings_as_errors=True,api_controls=10)


def validate(fresh=True):
    if fresh:
        proof.compare_cases(native.mixed_fixture()['cases'],load('queued_world_mixed')['cases'])
        world.gate.require(json.loads(json.dumps(native.normal_fixture()))==load('normal_world_arrivals'),'Fresh normal-world310 differs')
    return dict(compare(),normal_world=world.compare(load('normal_world_arrivals'),observe_arrivals=True),fresh_x86_additional=fresh)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--pinned',action='store_true');p.add_argument('--assembly',type=Path);a=p.parse_args()
    r=dict(compare(assembly=a.assembly),normal_world=world.compare(load('normal_world_arrivals'),assembly=a.assembly,observe_arrivals=True))if a.assembly else validate(not a.pinned)
    a.output.write_text(json.dumps(r,indent=2)+'\n');print(r)


if __name__=='__main__':main()
