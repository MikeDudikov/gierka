"""Checked C# vs fresh original pending-fleet transactions and sprite slot lifecycle."""
from pathlib import Path
import argparse,hashlib,json,subprocess,tempfile
from tools import validate_boss_ai_gate as gate,probe_ship_pending_selection as pending,probe_source_sprite_slots as slots
ROOT=gate.ROOT
FILES={'ship_pending_selection.json':'3cbcc65ebb9ed8db1af562592938b1ee6b68b4b546eb9e4252c6a527f7a4990a','source_sprite_slots.json':'a9069f4b1a0ebb95e1f38b3c1067a46e8283e70e6632f0d213618db3c41c3217'}
def load(name,path=None):
    p=Path(path or ROOT/'tests/fixtures'/name);raw=p.read_bytes();gate.require(hashlib.sha256(raw).hexdigest()==FILES[name],'Fleet fixture SHA differs: '+name);return json.loads(raw)
def validate():
    p=load('ship_pending_selection.json');q=load('source_sprite_slots.json')
    gate.require(p==pending.fixture(),'Fresh pending selection differs');gate.require(q==slots.fixture(),'Fresh slot lifecycle differs')
    lines=[];expected=[]
    for i,c in enumerate(p['cases']):
        rect=c.get('rect',[0,0,1,1]);members=','.join(map(str,c.get('candidates',[])))or'-'
        values=['P',i,c['initial_mask'],int(c['initial_pending']),c['operation'],c['kind'],c.get('target')or 0,c['flags'],c.get('message',98),int(c.get('blocked',False)),int(c.get('enabled',True)),*rect[2:],members]
        lines.append('\t'.join(map(str,values)));s=c['after'];events=','.join(str(a)+':'+str(b)for a,b in s['events'])
        expected.append('\t'.join(map(str,['P',i,','.join(map(str,s['members'])),int(s['selected']),int(s['pending']),','.join(map(str,s['visuals'])),events,s['cursor'],s['mask'],s['bit'],int(s['blocked'])])))
    for i,c in enumerate(q['cases']):
        lines.append('CASE\t'+str(i))
        for op,s in zip(c['operations'],c['rows']):
            lines.append('\t'.join(str(int(v))if isinstance(v,bool)else str(v)for v in op))
            expected.append('\t'.join(map(str,['Q',s['result']if s['result']is not None else-1,','.join(map(str,s['depths'])),','.join(str(int(v))for v in s['alive']),','.join(map(str,s['draw_order']))])))
    _,_,runtime,compiler=gate.prerequisites();r=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime'
    paths=[r/'Simulation/ShipPointerCommands.cs',r/'Simulation/ShipPendingSelection.cs',r/'SourceSpriteSlotQueue.cs',ROOT/'tests/fixtures/ShipPendingSelectionProbe.cs']
    with tempfile.TemporaryDirectory(prefix='pending-selection-')as tmp:
        exe=Path(tmp)/'Probe.exe';cp=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/out:'+str(exe),*map(str,paths)],capture_output=True,text=True);gate.require(cp.returncode==0,cp.stdout+cp.stderr)
        rp=subprocess.run([str(runtime),str(exe)],input='\n'.join(lines)+'\n',capture_output=True,text=True);gate.require(rp.returncode==0,rp.stderr)
        actual=rp.stdout.splitlines();gate.require(len(actual)==len(expected),'Fleet output count differs')
        for i,(a,b)in enumerate(zip(actual,expected)):gate.require(a==b,'Fleet mismatch row'+str(i)+' actual:'+a+' expected:'+b)
    return {'passed':True,'pending_cases':len(p['cases']),'slot_cases':len(q['cases']),'slot_states':sum(len(c['rows'])for c in q['cases']),'checked':True,'warnings_as_errors':True,'sources':{str(p.relative_to(ROOT)):gate.digest(p)for p in paths}}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);a=parser.parse_args();result=validate();a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='sources'}))
if __name__=='__main__':main()
