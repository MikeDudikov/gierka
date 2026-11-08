"""All local temporary-fleet hover subsets against original cursor/Fleet/Ship code."""
import argparse,json,hashlib,subprocess,tempfile
from pathlib import Path
from tools import validate_ship_pointer_hover as old,probe_ship_fleet_hover as native
ROOT=old.ROOT;PIN='482eba58964e0e453ea5b947f427e5491dbc14efd99b416d450f78df5e99758a'
FIXTURE=ROOT/'tests/fixtures/ship_fleet_hover.json'
def load(path=None):
 raw=Path(path or FIXTURE).read_bytes();old.gate.require(hashlib.sha256(raw).hexdigest()==PIN,'Fleet hover fixture SHA differs');return json.loads(raw)
def validate():
 f=load();old.gate.require(native.fixture()==f,'Fresh fleet hover differs');lines=[];expected=[]
 families,_=old.native.mask.mask_inputs(ROOT/'reference/raw/ancient-conquest')
 for family in families:
  if family['family']!='PAD':lines.append('\t'.join(map(str,['F',family['family'],family['width'],family['height'],b''.join(family['planes']).hex()])))
 for a in f['actors']:lines.append('\t'.join(map(str,['A',a['id'],a['family'],*a['world'],a['frame'],a['heading'],a['side'],a['player'],a['caps'],a['class'],*a['cell']])))
 lines.append('START')
 for i,op in enumerate(f['operations']):
  lines.append('MASK\t'+str(op['mask']))
  values=['MOVE',i,*op['point'],*op['point'],op['point'][0]//64,op['point'][1]//64,int(op['mask']!=0)]if op['operation']=='MOVE'else['REFRESH',i,int(op['mask']!=0)]
  lines.append('\t'.join(map(str,values)));expected.append(old.state_line(i,op['state']))
 _,_,runtime,compiler=old.gate.prerequisites();probe=ROOT/'tests/fixtures/ShipFleetHoverProbe.cs'
 with tempfile.TemporaryDirectory(prefix='fleet-hover-')as tmp:
  exe=Path(tmp)/'Probe.exe';cp=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/out:'+str(exe),*map(str,old.SOURCES),str(probe)],capture_output=True,text=True);old.gate.require(cp.returncode==0,cp.stdout+cp.stderr)
  rp=subprocess.run([str(runtime),str(exe),str(ROOT/'tests/fixtures/mission_cell_flags.bin')],input='\n'.join(lines)+'\n',capture_output=True,text=True);old.gate.require(rp.returncode==0,rp.stderr)
  actual=rp.stdout.splitlines();old.gate.require(len(actual)==len(expected),'Fleet hover result count differs')
  for i,(a,b)in enumerate(zip(actual,expected)):old.gate.require(a==b,'Fleet hover row'+str(i)+' actual:'+a+' expected:'+b)
 return {'passed':True,'states':len(expected),'selected_subsets':8,'fixture_sha256':PIN,'checked':True,'warnings_as_errors':True,'hover_sha256':old.gate.digest(old.SOURCES[-1])}
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=validate();a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
if __name__=='__main__':main()
