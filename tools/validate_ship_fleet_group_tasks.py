"""Behavioral x86 fidelity of coupled membership/task ownership,not world scheduling."""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,subprocess,tempfile
from tools import probe_ship_fleet_group_tasks as native,validate_boss_ai_gate as gate
from tools import validate_ship_fleet_membership as membership

ROOT=gate.ROOT;SOURCE=membership.SOURCE;PROBE=ROOT/'tests/fixtures/ShipFleetGroupTasksProbe.cs'
FIXTURE_SHA='48832345adada86d26d2c5ed308d1dcb7dbf81a4646590fdd9f8314499e18719'


def load(path=None):
    raw=Path(path or ROOT/'tests/fixtures/ship_fleet_group_tasks.json').read_bytes()
    gate.require(hashlib.sha256(raw).hexdigest()==FIXTURE_SHA,'Group ownership fixture SHA differs')
    return json.loads(raw)


def packet(p):return f"{p['actor']}:{p['action']}:{p['payload_hex']}"


def expected(state):
    groups=[]
    for g in state['groups']:
        groups.append('~'.join(map(str,[g['mode'],g['serial'],g['age'],','.join(map(str,g['members'])),
            ','.join(map(str,g['slots'])),','.join(map(str,g['task']))if g['task']else'-',
            ';'.join(','.join(map(str,a))for a in g['assignments']),';'.join(g['events'])])))
    return '\t'.join([str(state['result'])if state['result']is not None else'-',str(state['current_group']),str(state['consumed']),
        '/'.join(groups),';'.join(','.join(str(a[k])for k in('id','ui_group','simulation_group','member_index'))for a in state['actors']),
        ';'.join(map(packet,state['membership_commands'])),';'.join(map(packet,state['commands']))])


def compare(data,source=SOURCE,assembly=None):
    lines=['MAP\tmission\t'+data['terrain_base64'],'MAP\tblocked\t'+base64.b64encode(b'\xff'*1152).decode()];required=[];labels=[]
    for case in data['cases']:
        lines.append('CASE')
        for step in case['states']:
            lines.append('\t'.join(map(str,step['operation'])));required.append(expected(step['after']));labels.append((case['label'],step['operation']))
    _,_,runtime,compiler=gate.prerequisites()
    with tempfile.TemporaryDirectory(prefix='fleet-group-ownership-')as directory:
        exe=Path(directory)/'Probe.exe';files=[str(source),str(PROBE),*map(str,membership.DEPENDENCIES)]
        if assembly is not None:files=['/reference:'+str(assembly),'/reference:'+str(Path(assembly).parent/'netstandard.dll'),str(PROBE)]
        r=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/out:'+str(exe),*files],capture_output=True,text=True)
        gate.require(r.returncode==0,r.stdout+r.stderr)
        if assembly is not None:shutil.copy2(assembly,exe.parent/'Assembly-CSharp.dll')
        r=subprocess.run([str(runtime),str(exe)],input='\n'.join(lines)+'\n',capture_output=True,text=True)
        gate.require(r.returncode==0,'Group ownership execution failed: '+r.stderr)
        actual=r.stdout.splitlines();gate.require(len(actual)==len(required),'Group ownership row count differs')
        for i,(a,b)in enumerate(zip(actual,required)):
            gate.require(a==b,f'Group ownership mismatch row{i} {labels[i]}\nactual: {a}\nexpected: {b}')
        r=subprocess.run([str(runtime),str(exe),'--api'],capture_output=True,text=True)
        gate.require(r.returncode==0,r.stdout+r.stderr)
        gate.require(r.stdout.strip()=='API\t26','Group ownership API controls incomplete: '+r.stdout)
    packets=[p for c in data['cases']for s in c['states']for p in s['after']['commands']]
    return dict(passed=True,cases=len(data['cases']),states=len(required),group_states=sum(len(s['after']['groups'])for c in data['cases']for s in c['states']),
        packets=len(packets),membership41=sum(p['action']==41 for p in packets),moves20=sum(p['action']==20 for p in packets),
        watch35=sum(p['action']==35 for p in packets),api_controls=26,checked=True,warnings_as_errors=True)


def validate():
    d=load();gate.require(d==native.fixture(),'Fresh source group ownership differs')
    return dict(compare(d),fresh_native=True,fixture_sha256=FIXTURE_SHA,
        sources={str(p.relative_to(ROOT)):gate.digest(p)for p in(SOURCE,PROBE,Path(native.__file__),Path(__file__))})


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=validate()
    a.output.write_text(json.dumps(r,indent=2)+'\n');print({k:v for k,v in r.items()if k!='sources'})


if __name__=='__main__':main()
