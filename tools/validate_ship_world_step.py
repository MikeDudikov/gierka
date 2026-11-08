"""Compare clock/mail/fleet/actor phases and full bodies with one original engine."""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,struct,subprocess,tempfile
from tools import probe_ship_world_step as native,validate_ship_live_fleet as bodies,validate_ship_fleet_membership as membership
from tools import validate_boss_ai_gate as gate
ROOT=gate.ROOT;SIM=membership.SOURCE.parent;SOURCE=SIM/'ShipWorldStep.cs';PROBE=ROOT/'tests/fixtures/ShipWorldStepProbe.cs'
FIXTURE_SHA='d4fe29c10cbbf7a86232754748d9c52f654bc2792f5be6808071a7972b74f66f'


def load(path=None):
    raw=Path(path or ROOT/'tests/fixtures/ship_world_step.json').read_bytes()
    gate.require(hashlib.sha256(raw).hexdigest()==FIXTURE_SHA,'World step fixture SHA differs');return json.loads(raw)


def packet(p,received=False):
    return ':'.join(map(str,[p['actor'],p['action'],p['queued_at']if received else p['counter'],p['payload_hex']]))


def meta(frame,consumed):
    visits=[-1 if s=='fleet:0'else int(s.split(':')[1])for s in frame['trace']if s.startswith(('fleet:','ship:'))]
    g=frame['group']
    return '\t'.join(map(str,['W',frame['counter'],frame['phase'],frame['mail_gate'],','.join(map(str,visits)),
        ';'.join(packet(p,True)for p in frame['received']),';'.join(map(packet,frame['emitted'])),';'.join(map(packet,frame['outgoing'])),
        ';'.join(','.join(map(str,p))for p in frame['publications']),g['age'],consumed,
        ';'.join(','.join(map(str,a))for a in g['assignments']),';'.join(g['events'])]))


def compare(data,source=SOURCE,assembly=None,observe_arrivals=False):
    lines=['SEED\t'+i+'\t'+p for i,p in data['seed_payloads'].items()]
    lines+=['MAP\t'+base64.b64encode(struct.pack('<576h',*data['terrain'])).decode()];required=[];labels=[]
    if observe_arrivals:lines.append('TRACE310')
    for case in data['cases']:
        lines.append('\t'.join(map(str,['START',case['warm'],','.join(map(str,case['order'])),','.join(map(str,case['members']))])))
        consumed=0
        for frame in case['rows']:
            if frame['notified']:lines.append('N')
            lines.append('F\t'+str(frame['captured']));consumed+=sum(p['action']==41 for p in frame['received'])
            required.append(meta(frame,consumed));labels.append((case['label'],frame['counter'],'world'))
            for state in frame['actors']:required.append(bodies.expected(state));labels.append((case['label'],frame['counter'],state['id']))
    _,_,runtime,compiler=gate.prerequisites()
    with tempfile.TemporaryDirectory(prefix='ship-world-step-')as directory:
        exe=Path(directory)/'Probe.exe';sources=list(dict.fromkeys([*bodies.legacy.SOURCES,membership.SOURCE,*membership.DEPENDENCIES,SIM/'SingleStepClock.cs',Path(source)]))
        files=[*map(str,sources),str(PROBE)]
        if assembly is not None:files=['/reference:'+str(assembly),'/reference:'+str(Path(assembly).parent/'netstandard.dll'),str(PROBE)]
        r=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/out:'+str(exe),*files],capture_output=True,text=True);gate.require(r.returncode==0,r.stdout+r.stderr)
        if assembly is not None:shutil.copy2(assembly,exe.parent/'Assembly-CSharp.dll')
        r=subprocess.run([str(runtime),str(exe)],input='\n'.join(lines)+'\n',capture_output=True,text=True,cwd=ROOT)
        gate.require(r.returncode==0,'World step execution failed: '+r.stderr)
        actual=r.stdout.splitlines();gate.require(len(actual)==len(required),f'World step row count differs:{len(actual)}/{len(required)}')
        for i,(a,b)in enumerate(zip(actual,required)):
            if a!=b:
                diff=[(n,x,y)for n,(x,y)in enumerate(zip(a.split('\t'),b.split('\t')))if x!=y]
                raise AssertionError(f'World step mismatch row{i} {labels[i]}: {diff[:12]}')
        seed_input='\n'.join(lines[:4])+'\n'
        r=subprocess.run([str(runtime),str(exe),'--api'],input=seed_input,capture_output=True,text=True,cwd=ROOT)
        gate.require(r.returncode==0,r.stdout+r.stderr);gate.require(r.stdout.strip()=='API\t20','World API controls incomplete:'+r.stdout)
    frames=[f for c in data['cases']for f in c['rows']]
    return dict(passed=True,cases=len(data['cases']),frames=len(frames),actor_states=3*len(frames),registration_orders=len({tuple(c['order'])for c in data['cases']}),
        accepted_steps=sum(bool(f['trace'])for f in frames),received=sum(len(f['received'])for f in frames),
        emitted=sum(len(f['emitted'])for f in frames),publications=sum(len(f['publications'])for f in frames),
        api_controls=20,checked=True,warnings_as_errors=True)


def validate():
    d=load();gate.require(d==json.loads(json.dumps(native.fixture())),'Fresh original world step differs')
    return dict(compare(d),fresh_native=True,fixture_sha256=FIXTURE_SHA)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=validate()
    a.output.write_text(json.dumps(r,indent=2)+'\n');print(r)


if __name__=='__main__':main()
