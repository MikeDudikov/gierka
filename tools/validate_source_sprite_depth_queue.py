#!/usr/bin/env python3
"""Actual original normal-node registration/depth updates vs checked C#.
No callbacks, deleted/recycled nodes, pixels, Unity or OS services are executed.
"""
from __future__ import annotations
import argparse,hashlib,json,random,struct,subprocess,tempfile
from pathlib import Path
if __package__:
 from .validate_boss_ai_gate import ROOT,EXPECTED,ORIGINAL,MissingPrerequisite,digest,prerequisites,require
else:
 from validate_boss_ai_gate import ROOT,EXPECTED,ORIGINAL,MissingPrerequisite,digest,prerequisites,require
SOURCE=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime/SourceSpriteDepthQueue.cs'
PROBE=ROOT/'tests/fixtures/SourceSpriteDepthQueueProbe.cs'
COHORT=ROOT/'tests/fixtures/mission_ship_world_order.json'
COHORT_SHA256='0ee61b970675c19a0cdfc021ba223752d6694721074cbba0c900dd428f2be0c6'
FIXTURE=ROOT/'tests/fixtures/source_sprite_depth_queue.json'
FIXTURE_SHA256='9be3038d93fc54330f509c5652293bd52e6f716800f667bd4dcd0bb186d8593b'
OUTPUT=ROOT/'artifacts/long-routes/depth/csharp-validation.json'
M,DATA,IDS,ORDER,OUT,END,STACK=(0x70000000,0x70010000,0x70040000,0x70050000,0x70060000,0x700f0000,0x71000000)
GUARDS={'empty-copies','empty-update','empty-get','empty-draw','negative-draw','past-end-draw','max-draw','negative-update','past-end-update','max-update','min-get','past-end-get','copy-isolation','invalid-operation-immutability'}

def checked_image(original=ORIGINAL):
 original=Path(original)
 if not original.is_file():raise MissingPrerequisite('Optional original executable missing: '+str(original))
 raw=original.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=EXPECTED:raise ValueError('Original executable SHA-256 differs from verified depth queue')
 import pefile
 pe=pefile.PE(data=raw)
 require(pe.OPTIONAL_HEADER.ImageBase==0x400000,'Unexpected original base')
 return pe.get_memory_mapped_image(),pe.OPTIONAL_HEADER.SizeOfImage

class NativeQueue:
 def __init__(self,image,image_size):
  from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
  self.u=Uc(UC_ARCH_X86,UC_MODE_32);self.u.mem_map(0x400000,(image_size+4095)&~4095);self.u.mem_write(0x400000,image);self.u.mem_map(M,0x100000);self.u.mem_map(STACK,0x20000)
  for off,v in ((0x1a4,64),(0x1a8,DATA),(0x1ac,ORDER),(0x1b0,IDS)):self.w(M+off,v)
 def w(self,a,v):self.u.mem_write(a,struct.pack('<I',v&0xffffffff))
 def r(self,a):return struct.unpack('<I',self.u.mem_read(a,4))[0]
 def s(self,a):return struct.unpack('<i',self.u.mem_read(a,4))[0]
 def call(self,a,args):
  from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP
  sp=STACK+0x1f000
  for i,v in enumerate((END,*args)):self.w(sp+4*i,v)
  self.u.reg_write(UC_X86_REG_ESP,sp);self.u.emu_start(a,END,count=20000)
  require(self.u.reg_read(UC_X86_REG_EIP)==END,'Native depth call did not return')
 def register(self,depth):
  require(self.r(M+0x1a0)<64,'Bounded original node capacity exceeded')
  self.call(0x55d670,(M,OUT,depth,1,0,0,1,1,0,0));return self.r(OUT)
 def update(self,node,depth):self.call(0x55d960,(M,node,depth))
 def snapshot(self):
  n=self.r(M+0x1a0);ascending=[self.r(self.r(ORDER+4*i)+0x40)for i in range(n)]
  require(sorted(ascending)==list(range(n)),'Native IDs were lost or duplicated')
  depths=[self.s(self.r(IDS+4*i)+0x44)for i in range(n)]
  for i,node in enumerate(ascending):
   require(self.r(self.r(IDS+4*node)+0x48)==i,'Native cached position disagrees')
   require(not(self.r(self.r(IDS+4*node))&0x4000),'Callback nodes are outside scope')
  require([depths[i]for i in ascending]==sorted(depths),'Native queue is not ascending signed depths')
  return {'depths':depths,'ascending':ascending,'draw_order':ascending[::-1]}

def cohort_registration():
 raw=COHORT.read_bytes();require(hashlib.sha256(raw).hexdigest()==COHORT_SHA256,'Pinned source cohort changed')
 groups=json.loads(raw)['groups_back_to_front'];require(len(groups)==21,'Source cohort count differs')
 groups=sorted(groups,key=lambda g:(int(g['resource_name'][4:],16),0 if g['kind']=='inline_parent' else 1))
 return [{'node_id':i,'resource_name':g['resource_name'],'kind':g['kind'],'depth':g['depth']}for i,g in enumerate(groups)]

def original_cohort_trace(world_ys,original=ORIGINAL):
 """Consume EVERY source publication Y, in order, including duplicate Ys.
 Returns retained native registration IDs and full back-to-front group order.
 """
 original=Path(original);image,size=checked_image(original);native=NativeQueue(image,size);registration=cohort_registration()
 for node in registration:require(native.register(node['depth'])==node['node_id'],'Source registration ID changed')
 moving=next(n['node_id']for n in registration if n['resource_name']=='OBJ_0000000b'and n['kind']=='inline_parent')
 initial=native.snapshot()['draw_order'];states=[]
 expected_groups=json.loads(COHORT.read_text())['groups_back_to_front']
 require([(registration[i]['resource_name'],registration[i]['kind']) for i in initial]==[(g['resource_name'],g['kind']) for g in expected_groups],'Fresh native queue differs from pinned static cohort order')
 for y in world_ys:
  require(isinstance(y,int)and 0<=y<=1535,'Cohort API requires a source map worldY in0..1535')
  depth=max(10000,20000-56-y);native.update(moving,depth)
  states.append({'world_y':y,'depth':depth,'draw_order':native.snapshot()['draw_order']})
 require(digest(original)==EXPECTED,'Original changed during depth trace')
 return {'original_sha256':EXPECTED,'cohort_sha256':COHORT_SHA256,'registration':registration,'moving_node_id':moving,'initial_draw_order':initial,'states':states,'native_entries':['0x55d670','0x55d960','0x571eb0'],'native_hooks':[],'scope':'Fresh normal21node cohort, retained IDs, every publication in supplied order; no callback/recycled-node/pixel/fullworld contract'}

def input_cases():
 registration=cohort_registration();regs=[['R',g['depth']]for g in registration]
 moving=next(g['node_id']for g in registration if g['resource_name']=='OBJ_0000000b'and g['kind']=='inline_parent')
 cases=[{'label':'source_cohort_tie_crossings','operations':regs+[['U',moving,19944-y]for y in(132,267,268,268,269,268,267,323,324,325,324,323,540,0,1535,132)]},
        {'label':'source_cohort_dense_forward_reverse','operations':regs+[['U',moving,19944-y]for y in list(range(132,541))+[540,540]+list(range(539,-1,-1))+list(range(1,541))]}]
 for i,n in enumerate((1,2,3,4,8,13,21,32,48,63)):
  rng=random.Random(0x55d960+i);pool=[-2147483648,-1,0,1,4,10,30,19620,19676,19812,20200,21000,2147483646,2147483647]
  ops=[['R',rng.choice(pool)]for _ in range(n)]
  for j in range(192):
   node=rng.randrange(n);value=rng.choice(pool)if j%3 else rng.randint(-2147483648,2147483647)
   ops.append(['U',node,value])
   if j%17==0:ops.append(['U',node,value])
  cases.append({'label':'signed_update_stress_'+str(n),'operations':ops})
 cases.extend([{'label':'all_equal_and_reverse','operations':[['R',10]for _ in range(8)]+[['U',i,v]for v in(0,10,20,10)for i in range(7,-1,-1)]},
               {'label':'negative_registration_sentinel','operations':[['R',v]for v in(-2147483648,-10,-1,0,2147483647)]+[['U',i,v]for v in(-2147483648,-1,0,2147483647)for i in range(5)]}])
 return cases

def original_cases(image,image_size,cases):
 results=[]
 for case in cases:
  q=NativeQueue(image,image_size);rows=[]
  for op in case['operations']:
   if op[0]=='R':node=q.register(op[1])
   else:node=op[1];q.update(node,op[2])
   rows.append({'node_id':node,**q.snapshot()})
  results.append({'label':case['label'],'rows':rows})
 return results

def fixture_object(original=ORIGINAL):
 image,size=checked_image(original);cases=input_cases();native=original_cases(image,size,cases)
 return {'schema_version':1,'original_exe_sha256':EXPECTED,'cohort_sha256':COHORT_SHA256,'scope':'Fresh normal-node registration and SetDepth updates only; no callback bit4000 or recycled slots','native_entries':['0x55d670','0x55d960','0x571eb0'],'native_hooks':[],'cases':[dict(c,native_rows=r['rows'])for c,r in zip(cases,native)]}

def load_fixture(path=FIXTURE):
 raw=Path(path).read_bytes();require(hashlib.sha256(raw).hexdigest()==FIXTURE_SHA256,'Depth queue fixture SHA-256 differs')
 data=json.loads(raw);require(data['original_exe_sha256']==EXPECTED and data['cohort_sha256']==COHORT_SHA256,'Depth fixture source differs');return data

def validate(original=ORIGINAL,mono_root=None):
 image,size=checked_image(original);fixture=load_fixture();cases=input_cases();native=original_cases(image,size,cases)
 require([dict(c,native_rows=r['rows'])for c,r in zip(cases,native)]==fixture['cases'],'Fresh native execution differs from pinned depth fixture')
 pefile,unicorn,runtime,compiler=prerequisites(Path(original),mono_root)
 before={str(p):digest(p)for p in(Path(original),SOURCE,PROBE,COHORT,FIXTURE)}
 with tempfile.TemporaryDirectory(prefix='source-depth-csharp-')as temporary:
  executable=Path(temporary)/'SourceSpriteDepthQueueProbe.exe'
  built=subprocess.run(compiler+['/nologo','/checked+','/target:exe','/out:'+str(executable),str(SOURCE),str(PROBE)],capture_output=True,text=True,timeout=60)
  require(built.returncode==0,'Depth C# compilation failed:\n'+built.stdout+built.stderr)
  lines=[]
  for c in cases:
   lines.append('CASE\t'+c['label']);lines.extend('\t'.join(map(str,op))for op in c['operations'])
  output=subprocess.run([str(runtime),str(executable)],input='\n'.join(lines)+'\n',check=True,capture_output=True,text=True,timeout=60)
 rows=[];guards=[]
 for line in output.stdout.splitlines():
  f=line.split('\t')
  if f[0]=='GUARD':guards.append(f[1]);continue
  require(f[0]=='ROW'and len(f)==7,'Malformed depth probe result')
  rows.append((f[1],int(f[2]),{'node_id':int(f[3]),'depths':[int(x)for x in f[4].split(',')],'ascending':[int(x)for x in f[5].split(',')],'draw_order':[int(x)for x in f[6].split(',')]}))
 expected=[(c['label'],i,row)for c in native for i,row in enumerate(c['rows'])]
 require(rows==expected,'Actual checked C# depth queue differs from native execution')
 require(len(guards)==len(GUARDS)and set(guards)==GUARDS,'Depth contract checks missing or duplicated')
 require(before=={str(p):digest(p)for p in(Path(original),SOURCE,PROBE,COHORT,FIXTURE)},'Depth inputs changed during validation')
 return {'passed':len(rows),'case_count':len(cases),'operation_count':len(rows),'register_operations':sum(op[0]=='R'for c in cases for op in c['operations']),'update_operations':sum(op[0]=='U'for c in cases for op in c['operations']),'guard_count':len(guards),'guards':guards,'checked_compilation':True,'original_exe_sha256':EXPECTED,'fixture_sha256':FIXTURE_SHA256,'cohort_sha256':COHORT_SHA256,'source_sha256':digest(SOURCE),'probe_sha256':digest(PROBE),'validator_sha256':digest(Path(__file__)),'native_entries':['0x55d670','0x55d960','0x571eb0'],'native_hooks':[],'scope':'Exact normal fresh-node depth insertion/update order including signed extrema, ties, repeats, reversals and retained IDs; no callback/deletion/recycling/world lifecycle/pixels','cases':[{'label':c['label'],'operation_count':len(c['operations'])}for c in cases]}

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path,default=ORIGINAL);p.add_argument('--mono-root',type=Path);p.add_argument('--output',type=Path,default=OUTPUT);args=p.parse_args(argv)
 if args.output.exists():p.error('Refusing to replace existing report')
 try:report=validate(args.original,args.mono_root)
 except MissingPrerequisite as e:p.exit(2,str(e)+'\n')
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n');print(f"{report['passed']} native/C# depth queue operations PASS; {report['guard_count']} guards")
 return 0
if __name__=='__main__':raise SystemExit(main())
