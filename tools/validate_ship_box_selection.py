"""Actual original box predicates/policy/line pixels vs checked project C#."""
from pathlib import Path
import json,subprocess,tempfile,argparse,hashlib
from tools import validate_boss_ai_gate as gate,probe_ship_box_selection as native
ROOT=gate.ROOT;FIXTURE=ROOT/'tests/fixtures/ship_box_selection.json';FIXTURE_SHA256='7a4187a4ab10a92c09244045dc2a4ebe79782e244f3f627aa3262a23c937f2d0'
def validate(fixture=None):
 frozen=load_fixture(fixture)
 fresh=native.fixture();gate.require(fresh==frozen,'Fresh original box fixture differs')
 _,_,runtime,compiler=gate.prerequisites();r=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime'
 paths=[r/'MissionOccupancyGrid.cs']+[r/'Simulation'/name for name in ['ShipPointerMask.cs','ShipWorldPicker.cs','ShipPointerHover.cs','ShipPointerCommands.cs','ShipBoxSelection.cs','ShipBoxOutline.cs','ShipBoxGesture.cs']]+[ROOT/'tests/fixtures/ShipBoxSelectionProbe.cs']
 lines=[];expected=[]
 for a in frozen['actors']:lines.append('\t'.join(map(str,['A',a['id'],a['side'],a['player'],a['class']])))
 for i,q in enumerate(frozen['queries']):
  claims=q.get('claims',frozen['claims']);lines.append('\t'.join(map(str,['Q',i,*q['rect'],q['owner'],q['reserved'],','.join(str(c)+':'+str(v)for c,v in claims)])))
  expected.append('Q\t'+str(i)+'\t'+','.join(map(str,q['result']['members'])))
 for i,p in enumerate(frozen['policies']):
  x,y,w,h=p['rect'];contains=x<=16<x+w and y<=2<y+h
  lines.append('\t'.join(map(str,['P',i,p['initial'],p['kind'],p['flags'],w,h,int(contains)])))
  s=p['after'];keys=['selected','pending','current_group','ui_group','sim_group','visual','group_count']
  vals=[int(s[k])for k in keys]+[len(s['commands']),s['cursor_type'],int(0 in p['selection_calls']),int(1 in p['selection_calls'])]
  expected.append('\t'.join(map(str,['P',i,*vals])))
 for i,q in enumerate(frozen['raster']['cases']):
  lines.append('\t'.join(map(str,['R',i,*[q[k]for k in('x','y','width','height','phase','thickness')]])))
  expected.append('R\t'+str(i)+'\t'+q['bitmap_hex'])
 lines.append('G');expected.append('G\t25')
 with tempfile.TemporaryDirectory(prefix='ship-box-')as tmp:
  exe=Path(tmp)/'Probe.exe';cp=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/out:'+str(exe),*map(str,paths)],capture_output=True,text=True);gate.require(cp.returncode==0,cp.stdout+cp.stderr)
  rp=subprocess.run([str(runtime),str(exe)],input='\n'.join(lines)+'\n',capture_output=True,text=True);gate.require(rp.returncode==0,rp.stdout[-200:]+rp.stderr)
  actual=rp.stdout.splitlines();gate.require(len(actual)==len(expected),'Box result count differs')
  for i,(a,b)in enumerate(zip(actual,expected)):
   if a!=b:raise AssertionError('Box mismatch row'+str(i)+' actual:'+a[:160]+' expected:'+b[:160])
 return {'passed':True,'queries':len(frozen['queries']),'policies':len(frozen['policies']),'raster_cases':len(frozen['raster']['cases']),'native_pixel_comparisons':len(frozen['raster']['cases'])*4096,'guard_count':25,'checked_compilation':True,'warnings_as_errors':True,'sources':{str(p.relative_to(ROOT)):gate.digest(p)for p in paths},'fixture_sha256':hashlib.sha256(Path(fixture or FIXTURE).read_bytes()).hexdigest()}
def load_fixture(path=None):
 raw=Path(path or FIXTURE).read_bytes();gate.require(hashlib.sha256(raw).hexdigest()==FIXTURE_SHA256,'Box fixture SHA differs');return json.loads(raw)
def main():
 p=argparse.ArgumentParser();p.add_argument('--fixture',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=validate(a.fixture);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k!='sources'}))
if __name__=='__main__':main()
