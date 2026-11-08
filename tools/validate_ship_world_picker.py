#!/usr/bin/env python3
"""Fresh original normal-ship picker queries and exact visit order vs checked C#."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,tempfile
from pathlib import Path
try:from . import probe_ship_world_picker as native,validate_boss_ai_gate as gate
except ImportError:import probe_ship_world_picker as native,validate_boss_ai_gate as gate
ROOT=gate.ROOT;MissingPrerequisite=gate.MissingPrerequisite
FIXTURE=ROOT/'tests/fixtures/ship_world_picker.json'
FIXTURE_SHA256='cee2e9f5c46c2de4db20068a78b63f3090428534f3d67948f2056abbb92a720b'
RUNTIME=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime'
SOURCES=[RUNTIME/'MissionOccupancyGrid.cs',RUNTIME/'Simulation/ShipPointerMask.cs',RUNTIME/'Simulation/ShipWorldPicker.cs']
PROBE=ROOT/'tests/fixtures/ShipWorldPickerProbe.cs'
OUTPUT=ROOT/'artifacts/world-input/picking/world-picker-csharp-validation.json'

def load_fixture(path=FIXTURE):
 raw=Path(path).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA256:raise ValueError('Original world-picker fixture SHA256 differs')
 d=json.loads(raw)
 if d['original_exe_sha256']!=gate.EXPECTED:raise ValueError('Original world-picker executable differs')
 return d

def validate(mono_root=None):
 frozen=load_fixture()
 if not gate.ORIGINAL.is_file():raise MissingPrerequisite('Optional original executable unavailable')
 if gate.digest(gate.ORIGINAL)!=gate.EXPECTED:raise ValueError('Original executable SHA256 differs')
 _,unicorn,runtime,compiler=gate.prerequisites(mono_root=mono_root)
 paths=[*SOURCES,PROBE,Path(native.__file__)];hashes={str(p.relative_to(ROOT)):gate.digest(p)for p in paths}
 fresh=native.original_cases();gate.require(fresh==frozen,'Fresh original world-picker execution differs from pinned fixture')
 lines=[];expected=[]
 for row in frozen['cases']:
  hits=','.join(map(str,row['hit_ids']))or'-';aliases=','.join(str(a)+':'+str(b)for a,b in row['aliases'])or'-'
  lines.append('\t'.join(map(str,('Q',row['label'],*row['world'],*row['cell'],int(row['precise']),hits,aliases))))
  expected.append('\t'.join(('ROW',row['label'],'-'if row['hit_id']is None else str(row['hit_id']),','.join(map(str,row['visits']))or'-')))
 with tempfile.TemporaryDirectory(prefix='ship-world-picker-')as td:
  exe=Path(td)/'ShipWorldPickerProbe.exe';cp=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/target:exe','/out:'+str(exe),*map(str,SOURCES),str(PROBE)],capture_output=True,text=True,timeout=60)
  gate.require(cp.returncode==0,'Picker C# compilation failed:\n'+cp.stdout+cp.stderr)
  run=subprocess.run([str(runtime),str(exe)],input='\n'.join(lines)+'\n',capture_output=True,text=True,timeout=60)
  gate.require(run.returncode==0,'Picker C# execution failed:\n'+run.stdout[-1000:]+run.stderr)
 actual=[line for line in run.stdout.splitlines()if line.startswith('ROW\t')]
 gate.require(actual==expected,'C# world-picker hit or visitation sequence differs from original')
 guards=[line.split('\t')[1]for line in run.stdout.splitlines()if line.startswith('GUARD\t')]
 totals=[int(line.split('\t')[1])for line in run.stdout.splitlines()if line.startswith('GUARDS\t')]
 gate.require(totals==[21]and len(guards)==len(set(guards))==21,'Picker API guard count differs')
 gate.require(all(gate.digest(ROOT/p)==sha for p,sha in hashes.items()),'Picker source changed during validation')
 return {'passed':True,'query_count':len(expected),'visited_predicate_count':sum(len(r['visits'])for r in frozen['cases']),'all_map_cells':576,'first_hit_cases':49,'duplicate_occupant_cases':1,'overlapping_masks_cases':4,'guard_count':len(guards),'guards':guards,'fixture_sha256':FIXTURE_SHA256,'original_exe_sha256':gate.EXPECTED,'source_sha256':hashes,'validator_sha256':gate.digest(Path(__file__)),'checked_compilation':True,'warnings_as_errors':True,'mono_runtime':str(runtime),'compiler_command':compiler,'unicorn_version':unicorn.__version__,'native_intercepted_callees':[],'scope':frozen['scope'],'excluded':frozen['excluded']}

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=OUTPUT);p.add_argument('--mono-root',type=Path);args=p.parse_args(argv);d=validate(args.mono_root);args.output.parent.mkdir(parents=True,exist_ok=True)
 with args.output.open('x')as f:f.write(json.dumps(d,indent=2)+'\n')
 print(json.dumps({k:d[k]for k in('passed','query_count','visited_predicate_count','guard_count')}));return 0
if __name__=='__main__':main()
