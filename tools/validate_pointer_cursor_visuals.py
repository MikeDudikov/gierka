#!/usr/bin/env python3
"""Actual source cursor+confirm transactions versus checked C# temporal adapter."""
from __future__ import annotations
import argparse,json,hashlib,subprocess,tempfile
from pathlib import Path
if __package__:
 from . import probe_pointer_cursor_visuals as native
 from . import validate_boss_ai_gate as gate
else:
 import probe_pointer_cursor_visuals as native
 import validate_boss_ai_gate as gate
ROOT=gate.ROOT;MissingPrerequisite=gate.MissingPrerequisite
SOURCE=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/PointerCursorProgression.cs';PROBE=ROOT/'tests/fixtures/PointerCursorProgressionProbe.cs';FIXTURE=ROOT/'tests/fixtures/pointer_cursor_visuals.json';FIXTURE_SHA256='1cb33c999e98813329edf7b04c90d5f5def9dcadfe8ac5c158b3259a518b20d2'
def expected(label,index,r):return list(map(str,[label,index,r['type'],int(r['green']),r['frame'],*r['screen'],int(r['visible']),*r['draw_position'],r['last_tick'],r['interval'],int(r['confirm_exists']),r['confirm_frame'],r['confirm_drawn'],int(r['confirm_visible']),*r['confirm_world'],r['confirm_last_tick'],int(r['cursor_publishes']),int(r['confirm_publishes']),int(r['deletes_confirm'])]))
def load_fixture():
 raw=FIXTURE.read_bytes();gate.require(hashlib.sha256(raw).hexdigest()==FIXTURE_SHA256,'Cursor fixture SHA differs');return json.loads(raw)
def validate(fixture=None):
 frozen=json.loads(Path(fixture).read_text())if fixture else load_fixture();native.visual.art.checked_sources();_,uc,runtime,compiler=gate.prerequisites();gate.require(native.fixture()==frozen,'Fresh native cursor differs from fixture');lines=[];wanted=[]
 for c in frozen['cases']:
  lines.append('CASE\t'+c['label'])
  for i,(op,row)in enumerate(zip(c['operations'],c['rows'])):lines.append('\t'.join(str(int(v))if isinstance(v,bool)else str(v)for v in op));wanted.append(expected(c['label'],i,row))
 hashes={str(p.relative_to(ROOT)):gate.digest(p)for p in(SOURCE,PROBE,Path(native.__file__))}
 with tempfile.TemporaryDirectory(prefix='pointer-cursor-')as tmp:
  exe=Path(tmp)/'CursorProbe.exe';cp=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/target:exe','/out:'+str(exe),str(SOURCE),str(PROBE)],capture_output=True,text=True,timeout=60);gate.require(cp.returncode==0,cp.stdout+cp.stderr);rp=subprocess.run([str(runtime),str(exe)],input='\n'.join(lines)+'\n',capture_output=True,text=True,timeout=60);gate.require(rp.returncode==0,rp.stdout[-1500:]+rp.stderr)
 rows=[];guards=None
 for line in rp.stdout.splitlines():
  f=line.split('\t')
  if f[0]=='ROW':rows.append(f[1:])
  elif f[0]=='GUARDS':guards=int(f[1])
  else:raise AssertionError('Unknown cursor probe output')
 gate.require(len(rows)==len(wanted),'Cursor count differs')
 for i,(a,b)in enumerate(zip(rows,wanted)):gate.require(a==b,'Cursor mismatch'+str(i)+' C#'+str(a)+' native'+str(b))
 gate.require(guards==7,'Cursor guard count differs');gate.require(all(gate.digest(ROOT/p)==sha for p,sha in hashes.items()),'Cursor sources changed during proof')
 return {'passed':True,'cases':len(frozen['cases']),'snapshots':len(rows),'cursor_publication_operations':sum(r['cursor_publishes']for c in frozen['cases']for r in c['rows']),'confirm_publications':sum(r['confirm_publishes']for c in frozen['cases']for r in c['rows']),'confirm_deletions':sum(r['deletes_confirm']for c in frozen['cases']for r in c['rows']),'guards':guards,'checked_compilation':True,'warnings_as_errors':True,'source_sha256':hashes,'scope':frozen['scope']}
def main():
 p=argparse.ArgumentParser();p.add_argument('--fixture',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=validate(a.fixture);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if isinstance(v,(int,bool))}))
if __name__=='__main__':main()
