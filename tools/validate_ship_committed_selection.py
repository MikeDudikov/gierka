"""Exact Ctrl recall/plain selection/right blank with committed normal groups."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,tempfile
from tools import validate_boss_ai_gate as gate,probe_ship_committed_selection as native
ROOT=gate.ROOT
SOURCE=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipPendingSelection.cs'
PROBE=ROOT/'tests/fixtures/ShipCommittedSelectionProbe.cs'
FIXTURE_SHA='28a8a56c05ed88823dc075f41b6da73f9609272e68392ee2006a0d806537ef90'


def load(path=None):
    raw=Path(path or ROOT/'tests/fixtures/ship_committed_selection.json').read_bytes()
    gate.require(hashlib.sha256(raw).hexdigest()==FIXTURE_SHA,'Committed selection fixture SHA differs');return json.loads(raw)


def compare(data,source=SOURCE,assembly=None):
    lines=[];expected=[]
    for case in data['cases']:
        lines.append('CASE')
        for group in case['groups']:lines.append('G\t'+','.join(map(str,group)))
        for step in case['steps']:
            lines.append(step['action']+'\t'+str(step['target']));s=step['after']
            expected.append('\t'.join(map(str,[','.join(map(str,step['effective_members'])),len(s['members']),int(s['selected']),int(s['pending']),s['current_group'],','.join(map(str,s['visuals'])),','.join(str(a)+':'+str(b)for a,b in s['events']),s['cursor'],s['mask'],s['bit'],int(s['blocked'])])))
    _,_,runtime,compiler=gate.prerequisites()
    with tempfile.TemporaryDirectory()as directory:
        exe=Path(directory)/'Probe.exe';runtime_root=SOURCE.parent
        files=[str(source),str(runtime_root/'ShipFleetMembership.cs'),str(runtime_root/'ShipPointerCommands.cs'),str(PROBE),
               *[str(runtime_root/n)for n in('ShipFleetNormalTask.cs','ShipFleetMoveCommands.cs','SourceFleetFormation.cs','SourceWaveField.cs','ShipMoveRequestInbox.cs')]]
        if assembly is not None:files=['/reference:'+str(assembly),'/reference:'+str(Path(assembly).parent/'netstandard.dll'),str(PROBE)]
        r=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/out:'+str(exe),*files],capture_output=True,text=True)
        gate.require(r.returncode==0,r.stdout+r.stderr)
        if assembly is not None:shutil.copy2(assembly,exe.parent/'Assembly-CSharp.dll')
        r=subprocess.run([str(runtime),str(exe)],input='\n'.join(lines)+'\n',capture_output=True,text=True);gate.require(r.returncode==0,r.stderr)
        actual=r.stdout.splitlines();gate.require(len(actual)==len(expected),'Committed selection row count differs')
        for i,(a,b)in enumerate(zip(actual,expected)):gate.require(a==b,'Committed selection mismatch row'+str(i)+' actual:'+a+' expected:'+b)
    return dict(passed=True,cases=len(data['cases']),states=len(expected),checked=True,warnings_as_errors=True)


def validate():
    data=load();gate.require(data==native.fixture(),'Fresh committed selection differs');r=compare(data);r.update(fresh_native=True,fixture_sha256=FIXTURE_SHA);return r


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--assembly',type=Path);a=p.parse_args()
    r=compare(load(),assembly=a.assembly)if a.assembly else validate();a.output.write_text(json.dumps(r,indent=2)+'\n');print(r)


if __name__=='__main__':main()
