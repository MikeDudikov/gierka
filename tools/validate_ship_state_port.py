"""Exact original source-record restore and blocking normal80 C# projection."""
from pathlib import Path
import hashlib,json,subprocess,tempfile,shutil
from tools import validate_ship_live_fleet as live,probe_ship_state_port as native
ROOT=live.ROOT;SOURCE=live.SOURCE;PROBE=ROOT/'tests/fixtures/ShipStatePortProbe.cs'
SHA='4de52138da52a6a330c2f16f2cd173f5d43c63ee6b9020506e155cb5ac025bac'

def load(path=None):
 raw=Path(path or ROOT/'tests/fixtures/ship_state_port.json').read_bytes()
 live.legacy.gate.require(hashlib.sha256(raw).hexdigest()==SHA,'State port fixture SHA differs');return json.loads(raw)

def compare(data,source=SOURCE,assembly=None):
 lines=['SEED\t'+i+'\t'+p for i,p in data['seed_payloads'].items()];expected=[];labels=[]
 for c in data['cases']:
  lines+=['START\t0','WARM\t'+str(c['actor'])+'\t'+str(c['warmup'])+'\t'+'\t'.join(map(str,c['goal']))]
  #Replay twice;second import rewinds motion after explicit cohort-grid restore.
  for repeat in range(2):
   if repeat:lines.append('CONTEXT\t'+';'.join(','.join(map(str,p))for p in c['restored']['claims']))
   lines.append('DEFER\t'+str(c['actor'])+'\t'+str(c['deferred']))
   lines.append('RESTORE\t'+str(c['actor'])+'\t'+str(c['warmup'])+'\t'+c['raw_hex'])
   states=[c['restored'],c['received'],*c['rows']]
   lines.append('R\t'+str(c['actor'])+'\t16\t4\t255')
   for t in range(c['warmup']+1,c['warmup']+33):lines.append('T\t'+str(c['actor'])+'\t'+str(t)+'\t1')
   for t,s in enumerate(states):expected.append(live.expected(s)+'\t'+str(s['gate']));labels.append((c['actor'],c['warmup'],c['gate'],repeat,t))
 _,_,runtime,compiler=live.legacy.gate.prerequisites()
 with tempfile.TemporaryDirectory(prefix='ship-state-port-')as d:
  exe=Path(d)/'Probe.exe';inputs=[str(source)if p==SOURCE else str(p)for p in live.legacy.SOURCES]+[str(PROBE)]
  if assembly is not None:inputs=['/reference:'+str(assembly),'/reference:'+str(Path(assembly).parent/'netstandard.dll'),str(PROBE)]
  r=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/out:'+str(exe),*inputs],capture_output=True,text=True);live.legacy.gate.require(r.returncode==0,r.stdout+r.stderr)
  if assembly is not None:shutil.copy2(assembly,exe.parent/'Assembly-CSharp.dll')
  r=subprocess.run([str(runtime),str(exe),'--api'],input='\n'.join(lines)+'\n',capture_output=True,text=True,cwd=ROOT)
  live.legacy.gate.require(r.returncode==0,'State port execution failed:'+r.stderr)
  rows=r.stdout.splitlines();live.legacy.gate.require(rows[-1]=='API\t10','State port API incomplete:'+rows[-1]);rows=rows[:-1]
  live.legacy.gate.require(len(rows)==len(expected),'State port row count differs')
  for i,(a,b)in enumerate(zip(rows,expected)):
   if a!=b:raise AssertionError('State port mismatch '+str(labels[i])+':'+str([(j,x,y)for j,(x,y)in enumerate(zip(a.split('\t'),b.split('\t')))if x!=y]))
 return dict(passed=True,cases=len(data['cases']),states=len(expected),replays=2,api_controls=10,checked=True,warnings_as_errors=True)

def validate():
 d=load();live.legacy.gate.require(d==native.fixture(),'Fresh state port source differs');return dict(compare(d),fresh_x86=True)
