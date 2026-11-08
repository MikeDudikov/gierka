"""Native source selector families/progression/health pixels against project C# and staging."""
import argparse,json,hashlib,subprocess,tempfile
from pathlib import Path
from tools import validate_boss_ai_gate as gate,probe_ship_fleet_visuals as native,validate_ship_selection_visuals as old
ROOT=gate.ROOT;FIXTURE=ROOT/'tests/fixtures/ship_fleet_visuals.json';PIN='3472e5e2e1de78273722357588805c08f67ddaa5369fa4e938b3e06076e65de7'
def load(path=None):
    raw=Path(path or FIXTURE).read_bytes();gate.require(hashlib.sha256(raw).hexdigest()==PIN,'Fleet visual fixture SHA differs');return json.loads(raw)
def validate():
    f=load();gate.require(native.fixture()==f,'Fresh sized selector differs');lines=[];expected=[]
    for index,c in enumerate(f['cases']):
        label=str(index);lines.append('CASE\t'+label+'\t'+str(c['logical_size']))
        for j,(op,row)in enumerate(zip(c['operations'],c['rows'])):lines.append('\t'.join(map(str,op)));expected.append(old.expected(label,j,row))
    _,_,runtime,compiler=gate.prerequisites();source=old.SOURCE;probe=ROOT/'tests/fixtures/ShipFleetProgressionProbe.cs'
    with tempfile.TemporaryDirectory(prefix='sized-selection-')as tmp:
        exe=Path(tmp)/'Probe.exe';cp=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/out:'+str(exe),str(source),str(probe)],capture_output=True,text=True);gate.require(cp.returncode==0,cp.stdout+cp.stderr)
        rp=subprocess.run([str(runtime),str(exe)],input='\n'.join(lines)+'\n',capture_output=True,text=True);gate.require(rp.returncode==0,rp.stderr)
        rows=[line.split('\t')[1:]for line in rp.stdout.splitlines()if line.startswith('ROW\t')];gate.require(rows==expected,'Sized selector C# differs');gate.require('GUARDS\t5'in rp.stdout,'Missing progression guards')
    return {'passed':True,'cases':len(f['cases']),'states':len(rows),'rle_frames':f['rle']['frames'],'rle_buffers':f['rle']['comparisons'],'health_buffers':len(f['health']['records']),'source_sha256':gate.digest(source),'fixture_sha256':PIN,'checked':True,'warnings_as_errors':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=validate();a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
if __name__=='__main__':main()
