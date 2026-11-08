#!/usr/bin/env python3
"""Compare native normal0b selector transactions with checked actual C#."""
from __future__ import annotations
import argparse,json,hashlib,subprocess,tempfile
from pathlib import Path
if __package__:
 from . import probe_ship_selection_visuals as native
 from . import validate_boss_ai_gate as gate
else:
 import probe_ship_selection_visuals as native
 import validate_boss_ai_gate as gate
ROOT=gate.ROOT;MissingPrerequisite=gate.MissingPrerequisite
SOURCE=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipSelectionProgression.cs'
PROBE=ROOT/'tests/fixtures/ShipSelectionProgressionProbe.cs'
FIXTURE=ROOT/'tests/fixtures/ship_selection_visuals.json'
FIXTURE_SHA256='62b771352ae781b101a2e2bfe3ccd1edecc45b900e2c52863b45130e240b9067'
def expected(label,index,r):
 return list(map(str,[label,index,r['selection'],int(r['exists']),r['frame'],r['drawn_frame'],r['last_counter'],int(r['visible']),*r['world'],int(r['health_exists']),int(r['health_visible']),*r['health_world'],int(r['publishes']),int(r['deletes']),int(r['hides_health'])]))
def validate(fixture=None):
 frozen=json.loads(Path(fixture).read_text())if fixture else load_fixture();native.art.checked_sources()
 pe,uc,runtime,compiler=gate.prerequisites();actual=native.native_fixture();gate.require(actual==frozen,'Fresh native selector differs from fixture');lines=[];wanted=[]
 for c in frozen['cases']:
  lines.append('CASE\t'+c['label'])
  for i,(op,row)in enumerate(zip(c['operations'],c['rows'])):lines.append('\t'.join(map(str,op)));wanted.append(expected(c['label'],i,row))
 before={str(p.relative_to(ROOT)):gate.digest(p)for p in(SOURCE,PROBE,Path(native.__file__))}
 with tempfile.TemporaryDirectory(prefix='ship-selection-')as tmp:
  exe=Path(tmp)/'SelectionProbe.exe';cp=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/target:exe','/out:'+str(exe),str(SOURCE),str(PROBE)],capture_output=True,text=True,timeout=60);gate.require(cp.returncode==0,cp.stdout+cp.stderr)
  rp=subprocess.run([str(runtime),str(exe)],input='\n'.join(lines)+'\n',capture_output=True,text=True,timeout=60);gate.require(rp.returncode==0,rp.stdout[-1200:]+rp.stderr)
 rows=[];guards=None
 for line in rp.stdout.splitlines():
  fields=line.split('\t')
  if fields[0]=='ROW':rows.append(fields[1:])
  elif fields[0]=='GUARDS':guards=int(fields[1])
  else:raise AssertionError('Unknown selector probe output')
 gate.require(len(rows)==len(wanted),'Selector snapshot count differs')
 for i,(a,b)in enumerate(zip(rows,wanted)):gate.require(a==b,'Selector mismatch'+str(i)+' C#'+str(a)+' native'+str(b))
 gate.require(guards==5,'Selector guards differ');gate.require(all(gate.digest(ROOT/p)==sha for p,sha in before.items()),'Selector sources changed during proof')
 return {'passed':True,'cases':len(frozen['cases']),'snapshots':len(rows),'publications':sum(r['publishes']for c in frozen['cases']for r in c['rows']),'selector_deletions':sum(r['deletes']for c in frozen['cases']for r in c['rows']),'health_removals':sum(r['hides_health']for c in frozen['cases']for r in c['rows']),'guards':guards,'checked_compilation':True,'warnings_as_errors':True,'fixture_sha256':hashlib.sha256(Path(fixture or FIXTURE).read_bytes()).hexdigest(),'source_sha256':before,'limits':frozen['scope']}
def load_fixture():
 raw=FIXTURE.read_bytes();gate.require(hashlib.sha256(raw).hexdigest()==FIXTURE_SHA256,'Selector fixture SHA differs');return json.loads(raw)
def main():
 p=argparse.ArgumentParser();p.add_argument('--fixture',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=validate(a.fixture);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if isinstance(v,(int,bool))}))
if __name__=='__main__':main()
