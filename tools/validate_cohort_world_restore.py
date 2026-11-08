"""Source-ordered world steps with in-place cohort restore and unchanged context."""
from pathlib import Path
import base64,hashlib,json,struct,subprocess,tempfile,shutil
from tools import validate_ship_world_step as world,probe_cohort_world_restore as native
ROOT=world.ROOT;SOURCE=world.SOURCE;PROBE=ROOT/'tests/fixtures/CohortWorldRestoreProbe.cs'
SHA='bb8bf6f462d8fe88a3af24e785c870c93826d944fd0e4a16eac05ec7a743b225'


def load(path=None):
 raw=Path(path or ROOT/'tests/fixtures/cohort_world_restore.json').read_bytes()
 world.gate.require(hashlib.sha256(raw).hexdigest()==SHA,'Cohort restore fixture SHA differs');return json.loads(raw)


def compare(data,source=SOURCE,assembly=None):
 lines=['SEED\t'+i+'\t'+p for i,p in data['seed_payloads'].items()]
 lines.append('MAP\t'+base64.b64encode(struct.pack('<576h',*data['terrain'])).decode());required=[];labels=[]
 for c in data['cases']:
  lines.append('START\t2\t'+','.join(map(str,c['order']))+'\t11,12,13');consumed=0
  def row(f,label):
   required.append(world.meta(f,consumed));labels.append((c['label'],label,'world'))
   for s in f['actors']:required.append(world.bodies.expected(s));labels.append((c['label'],label,s['id']))
  for f in c['rows']:
   if f['notified']:lines.append('N')
   lines.append('F\t'+str(f['captured']));consumed+=sum(p['action']==41 for p in f['received']);row(f,f['counter'])
   key=str(f['counter'])
   if key in c['restored']:
    lines.append('B\t'+'\t'.join(c['records'][key]));r=c['restored'][key]
    row(dict(f,actors=r['actors'],group=r['group'],outgoing=r['outgoing']),f'restore-{key}')
 _,_,runtime,compiler=world.gate.prerequisites()
 with tempfile.TemporaryDirectory(prefix='cohort-world-')as d:
  exe=Path(d)/'Probe.exe';sources=list(dict.fromkeys([*world.bodies.legacy.SOURCES,world.membership.SOURCE,*world.membership.DEPENDENCIES,world.SIM/'SingleStepClock.cs',Path(source)]))
  files=[*map(str,sources),str(PROBE)]
  if assembly is not None:files=['/reference:'+str(assembly),'/reference:'+str(Path(assembly).parent/'netstandard.dll'),str(PROBE)]
  r=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/out:'+str(exe),*files],capture_output=True,text=True);world.gate.require(r.returncode==0,r.stdout+r.stderr)
  if assembly is not None:shutil.copy2(assembly,exe.parent/'Assembly-CSharp.dll')
  r=subprocess.run([str(runtime),str(exe)],input='\n'.join(lines)+'\n',capture_output=True,text=True,cwd=ROOT)
  world.gate.require(r.returncode==0,'Cohort execution failed:'+r.stderr);actual=r.stdout.splitlines();world.gate.require(len(actual)==len(required),'Cohort row count differs')
  for i,(a,b)in enumerate(zip(actual,required)):
   if a!=b:raise AssertionError('Cohort mismatch '+str(labels[i])+':'+str([(j,x,y)for j,(x,y)in enumerate(zip(a.split('\t'),b.split('\t')))if x!=y]))
  #One warm/source record batch is needed by the additional API controls.
  c=data['cases'][0];api=lines[:4]+['START\t2\t-1,11,12,13\t11,12,13','F\t40','B\t'+'\t'.join(c['records']['1'])]
  r=subprocess.run([str(runtime),str(exe),'--api'],input='\n'.join(api)+'\n',capture_output=True,text=True,cwd=ROOT)
  world.gate.require(r.returncode==0,'Cohort API execution failed:'+r.stderr);world.gate.require(r.stdout.splitlines()[-1]=='API\t29','Cohort API incomplete')
 return dict(passed=True,cases=len(data['cases']),frames=sum(len(c['rows'])for c in data['cases']),restores=sum(len(c['restored'])for c in data['cases']),
  actor_states=sum((len(c['rows'])+len(c['restored']))*3 for c in data['cases']),world_rows=len(required)//4,api_controls=29,checked=True,warnings_as_errors=True)


def validate():
 d=load();world.gate.require(d==native.fixture(),'Fresh cohort source differs');return dict(compare(d),fresh_x86=True)
