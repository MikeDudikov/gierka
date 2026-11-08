#!/usr/bin/env python3
"""Fresh source global-map hover, fleet/ship responses and checked C# state parity."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,tempfile
from pathlib import Path
try:from . import probe_ship_pointer_hover as native,validate_boss_ai_gate as gate
except ImportError:import probe_ship_pointer_hover as native,validate_boss_ai_gate as gate
ROOT=gate.ROOT;MissingPrerequisite=gate.MissingPrerequisite
FIXTURE=ROOT/'tests/fixtures/ship_pointer_hover.json';FIXTURE_SHA256='8b6378752fed97d06f5890e6ed4de07646f96b0c14860971ad2ffa7d010ba547'
RUNTIME=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime'
SOURCES=[RUNTIME/'MissionOccupancyGrid.cs',*[RUNTIME/('Simulation/'+name+'.cs')for name in('ShipPointerMask','ShipWorldPicker','ShipPointerHover')]]
PROBE=ROOT/'tests/fixtures/ShipPointerHoverProbe.cs';OUTPUT=ROOT/'artifacts/world-input/hover-csharp-validation.json'

def load_fixture(path=FIXTURE):
 raw=Path(path).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA256:raise ValueError('Original pointer-hover fixture SHA256 differs')
 d=json.loads(raw)
 if d['original_exe_sha256']!=gate.EXPECTED:raise ValueError('Original pointer-hover executable differs')
 return d

def state_line(index,s):
 values=['STATE',index,int(s['has_map']),*s['screen'],*s['world'],*s['cell'],'-'if s['hovered_id']is None else s['hovered_id'],s['cursor_type'],s['action_mask'],s['action_bit'],int(s['blocked']),s['selector'],int(s['last_query']),','.join(map(str,s['visits']))or'-']
 return '\t'.join(map(str,values))

def validate(mono_root=None):
 frozen=load_fixture()
 if not gate.ORIGINAL.is_file():raise MissingPrerequisite('Private original executable unavailable')
 if gate.digest(gate.ORIGINAL)!=gate.EXPECTED:raise ValueError('Original executable SHA256 differs')
 _,unicorn,runtime,compiler=gate.prerequisites(mono_root=mono_root)
 paths=[*SOURCES,PROBE,Path(native.__file__),Path(native.picking.__file__),Path(native.mask.__file__)]
 hashes={str(p.relative_to(ROOT)):gate.digest(p)for p in paths}
 fresh=json.loads(json.dumps(native.original_cases()));gate.require(fresh==frozen,'Fresh original pointer-hover execution differs from pinned fixture')
 families,_=native.mask.mask_inputs(ROOT/'reference/raw/ancient-conquest');lines=[]
 for f in families:
  if f['family']=='PAD':continue
  lines.append('\t'.join(map(str,('F',f['family'],f['width'],f['height'],b''.join(f['planes']).hex()))))
 for a in frozen['actors']:
  lines.append('\t'.join(map(str,('A',a['id'],a['family'],*a['world'],a['frame'],a['heading'],a['side'],a['player'],a['caps'],a['class'],*a['cell']))))
 lines.append('START');expected=[]
 for op in frozen['operations']:
  k=op['op'];i=op['index']
  if k=='MOVE':line=[k,i,*op['screen'],*op['world'],op['world'][0]//64,op['world'][1]//64,int(op['selected'])]
  elif k=='REFRESH':line=[k,i,int(op['selected'])]
  elif k=='CAPS':line=[k,i,op['id'],op['value']]
  elif k=='POSE':line=[k,i,op['id'],*op['world'],op['frame'],op['heading']]
  elif k=='CLAIMS':line=[k,i,','.join(str(a)+':'+str(b)for a,b in op['claims'])]
  elif k=='IMPORT':line=[k,i,op['type'],op['mask'],op['bit'],int(op['blocked'])]
  elif k=='INVALIDATE':line=[k,i]
  else:raise ValueError('Unknown hover operation')
  lines.append('\t'.join(map(str,line)))
  if op['state']is not None:expected.append(state_line(i,op['state']))
 with tempfile.TemporaryDirectory(prefix='ship-pointer-hover-')as td:
  exe=Path(td)/'ShipPointerHoverProbe.exe';cp=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/target:exe','/out:'+str(exe),*map(str,SOURCES),str(PROBE)],capture_output=True,text=True,timeout=60)
  gate.require(cp.returncode==0,'Hover C# compilation failed:\n'+cp.stdout+cp.stderr)
  run=subprocess.run([str(runtime),str(exe),str(ROOT/'tests/fixtures/mission_cell_flags.bin')],input='\n'.join(lines)+'\n',capture_output=True,text=True,timeout=60)
  gate.require(run.returncode==0,'Hover C# execution failed:\n'+run.stdout[-1000:]+run.stderr)
 actual=[line for line in run.stdout.splitlines()if line.startswith('STATE\t')]
 gate.require(len(actual)==len(expected),'Hover state count differs')
 for i,(a,b)in enumerate(zip(actual,expected)):
  if a!=b:raise AssertionError('Hover state mismatch at'+str(i)+'\nC#:'+a+'\nx86:'+b)
 guards=[line.split('\t')[1]for line in run.stdout.splitlines()if line.startswith('GUARD\t')];totals=[int(line.split('\t')[1])for line in run.stdout.splitlines()if line.startswith('GUARDS\t')]
 gate.require(totals==[15]and len(guards)==len(set(guards))==15,'Hover guard count differs')
 gate.require(all(gate.digest(ROOT/p)==v for p,v in hashes.items()),'Hover source changed during comparison')
 return {'passed':True,'state_count':len(actual),'operation_count':len(frozen['operations']),'visited_predicate_count':sum(len(o['state']['visits'])for o in frozen['operations']if o['state']is not None),'source_query_count':sum(o['state']['last_query']for o in frozen['operations']if o['state']is not None),'guard_count':len(guards),'guards':guards,'fixture_sha256':FIXTURE_SHA256,'original_exe_sha256':gate.EXPECTED,'source_sha256':hashes,'validator_sha256':gate.digest(Path(__file__)),'checked_compilation':True,'warnings_as_errors':True,'mono_runtime':str(runtime),'compiler_command':compiler,'unicorn_version':unicorn.__version__,'native_boundaries':frozen['boundaries'],'scope':frozen['scope'],'excluded':frozen['excluded']}

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=OUTPUT);p.add_argument('--mono-root',type=Path);a=p.parse_args(argv);d=validate(a.mono_root);a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('x')as f:f.write(json.dumps(d,indent=2)+'\n')
 print(json.dumps({k:d[k]for k in('passed','state_count','source_query_count','visited_predicate_count','guard_count')}));return 0
if __name__=='__main__':main()
