"""Compare the single-owner bounded C#100/2 port with pinned independent x86 traces."""
from pathlib import Path
import argparse,base64,hashlib,json,shutil,struct,subprocess,tempfile
from tools import validate_ship_fleet_queued as queued
from tools import validate_queued_wave_boundary as boundary
from tools import validate_crt_context as crt
from tools import validate_ship_fleet_normal_task as normal
from tools import validate_boss_ai_gate as gate
ROOT=gate.ROOT;SIM=normal.SIMULATION
PROBE=ROOT/'tests/fixtures/ShipFleetQueuedPortProbe.cs'
INPUTS=['ShipFleetNormalTask.cs','ShipFleetMembership.cs','SourceWaveField.cs',
        'ShipFleetMoveCommands.cs','SourceFleetFormation.cs','ShipMoveRequestInbox.cs']


def expected(state):
    route=state['route'];m=state['membership']
    return '\t'.join(map(str,[state['age'],','.join(map(str,state['task']['header']))if state['task']else'-',
        ';'.join(','.join(map(str,p['cell']))for p in route['points'])if route else'',
        ';'.join(','.join(map(str,[p['id'],p['mode'],*p['target']]))for p in route['members'])if route else'',
        ';'.join(state.get('events',[])),m['current_group'],
        '/'.join(f"{g['mode']}:{g['serial']}:"+','.join(map(str,g['members']))for g in m['groups']),
        ';'.join(','.join(map(str,[a['id'],a['ui_group'],a['simulation_group'],a['member_index']]))for a in m['actors']),
        m['consumed'],';'.join(f"{p['actor']}:{p['action']}:{p['payload_hex']}"for p in state['packets']),
        f"{state['value']['cell']},{state['value']['end']}"if state['value']is not None else'-']))


def inputs():
    mission=normal.load()['terrain_base64'];disconnected=[-1]*576
    for x,y in((16,2),(21,5),(19,4),(18,6),(16,4)):disconnected[y*24+x]=0
    maps={'mission':mission,'disconnected':base64.b64encode(struct.pack('<576h',*disconnected)).decode()}
    lines=['MAP\t'+name+'\t'+raw for name,raw in maps.items()];wanted=[];labels=[]
    for case in queued.load()['cases']:
        lines.append('CASE')
        for row in case['rows']:
            lines.append('\t'.join(map(str,row['operation'])));wanted.append(expected(row['state']));labels.append((case['label'],row['operation']))
    # These corpora differ only in explicit memory/map inputs. No expected output
    # is calculated by a second managed/Python behavioral implementation.
    for kind,data in(('boundary',boundary.load()),('crt',crt.load())):
        for i,case in enumerate(data['cases']):
            lines.append('CASE')
            for op in(('select',11,12,13),('shift',18,6,0),('shift',16,4,1),('age',101)):
                lines.append('\t'.join(map(str,op)));wanted.append(None);labels.append((kind,i,'setup'))
            prefix=case['comparisons'][0]['adjacent_used']
            lines.append('\t'.join(map(str,['CONTEXT',case.get('terrain','mission'),prefix,prefix,prefix])))
            lines.append('work\t1\t2');wanted.append(expected(case['state']));labels.append((kind,i,'work'))
    return lines,wanted,labels


def compare(assembly=None,overrides=None):
    lines,wanted,labels=inputs();_,_,runtime,compiler=gate.prerequisites()
    with tempfile.TemporaryDirectory(prefix='fleet-queued-port-')as directory:
        exe=Path(directory)/'Probe.exe'
        sources=[str((overrides or{}).get(name,SIM/name))for name in INPUTS]+[str(PROBE)]
        if assembly is not None:
            sources=['/reference:'+str(assembly),'/reference:'+str(Path(assembly).parent/'netstandard.dll'),str(PROBE)]
        built=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/out:'+str(exe),*sources],capture_output=True,text=True)
        gate.require(built.returncode==0,built.stdout+built.stderr)
        if assembly is not None:shutil.copy2(assembly,exe.parent/'Assembly-CSharp.dll')
        result=subprocess.run([str(runtime),str(exe)],input='\n'.join(lines)+'\n',capture_output=True,text=True)
        gate.require(result.returncode==0,'Queued port execution failed: '+result.stderr)
        actual=result.stdout.splitlines();gate.require(len(actual)==len(wanted),'Queued port row count differs')
        for i,(observed,required)in enumerate(zip(actual,wanted)):
            if required is not None:
                gate.require(observed==required,f'Queued port mismatch row{i} {labels[i]}\nactual:{observed}\nexpected:{required}')
        api=subprocess.run([str(runtime),str(exe),'--api'],capture_output=True,text=True)
        gate.require(api.returncode==0,api.stdout+api.stderr);gate.require(api.stdout.strip()=='API\t19','Queued API controls incomplete:'+api.stdout)
    return dict(passed=True,cases=64,canonical_states=1121,setup_rows=36,api_controls=19,
        full_logical_projection=True,opaque_graphical_pointers_excluded=True,checked=True,warnings_as_errors=True,
        world_queued_integration=False,ui_shift_enabled=False)


def wave_compare(assembly=None):
    """Full fields from actual4a1e90/545960,including blocked seeds and islands."""
    from unicorn.x86_const import UC_X86_REG_EAX
    _,_,runtime,compiler=gate.prerequisites();oracle=queued.native.QueuedOracle()
    raw=base64.b64decode(normal.load()['terrain_base64']);mission=list(struct.unpack('<576h',raw))
    maps={'mission':mission,'open':[0]*576,'blocked':[-1]*576,
        'islands':[0 if (x,y)in((16,2),(21,5),(19,4),(18,6),(16,4))else-1 for y in range(24)for x in range(24)]}
    lines=[];wanted=[];hashes=[]
    for name,terrain in maps.items():
        raw=struct.pack('<576h',*terrain);lines.append('MAP\t'+name+'\t'+base64.b64encode(raw).decode())
        oracle.u.mem_write(oracle.r(0x5c93bc),raw)
        for x,y in((0,0),(23,23),(16,2),(21,5),(19,4)):
            oracle.invoke_fleet(0x4a1e90,(0,x,y,5000));address=oracle.u.reg_read(UC_X86_REG_EAX)
            field=bytes(oracle.u.mem_read(address,1152));wanted.append(base64.b64encode(field).decode())
            hashes.append(dict(map=name,x=x,y=y,sha256=hashlib.sha256(field).hexdigest()))
            lines.append(f'WAVE\t{name}\t{x}\t{y}')
    with tempfile.TemporaryDirectory(prefix='queued-wave-port-')as directory:
        exe=Path(directory)/'Probe.exe';sources=[str(SIM/n)for n in INPUTS]+[str(PROBE)]
        if assembly is not None:sources=['/reference:'+str(assembly),'/reference:'+str(Path(assembly).parent/'netstandard.dll'),str(PROBE)]
        result=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/out:'+str(exe),*sources],capture_output=True,text=True)
        gate.require(result.returncode==0,result.stdout+result.stderr)
        if assembly is not None:shutil.copy2(assembly,exe.parent/'Assembly-CSharp.dll')
        result=subprocess.run([str(runtime),str(exe)],input='\n'.join(lines)+'\n',capture_output=True,text=True)
        gate.require(result.returncode==0,result.stderr);gate.require(result.stdout.splitlines()==wanted,'Queued descending full wave differs from x86')
    return dict(passed=True,fields=len(wanted),signed_words=len(wanted)*576,source='4a1e90/545db0/545960',hashes=hashes)


def world_guard(assembly=None):
    from tools import validate_ship_world_step as world
    d=world.load();lines=['SEED\t'+i+'\t'+p for i,p in d['seed_payloads'].items()]
    lines.append('MAP\t'+base64.b64encode(struct.pack('<576h',*d['terrain'])).decode())
    _,_,runtime,compiler=gate.prerequisites()
    with tempfile.TemporaryDirectory(prefix='queued-world-guard-')as directory:
        exe=Path(directory)/'Probe.exe';sources=list(dict.fromkeys([*world.bodies.legacy.SOURCES,world.membership.SOURCE,
            *world.membership.DEPENDENCIES,SIM/'SingleStepClock.cs',world.SOURCE,world.PROBE]))
        files=list(map(str,sources))
        if assembly is not None:files=['/reference:'+str(assembly),'/reference:'+str(Path(assembly).parent/'netstandard.dll'),str(world.PROBE)]
        result=subprocess.run(compiler+['/nologo','/checked+','/warnaserror+','/out:'+str(exe),*files],capture_output=True,text=True)
        gate.require(result.returncode==0,result.stdout+result.stderr)
        if assembly is not None:shutil.copy2(assembly,exe.parent/'Assembly-CSharp.dll')
        result=subprocess.run([str(runtime),str(exe),'--queued-guard'],input='\n'.join(lines)+'\n',capture_output=True,text=True,cwd=ROOT)
        gate.require(result.returncode==0,result.stderr);gate.require(result.stdout.strip()=='QUEUED_WORLD_GUARD_OK','World guard incomplete')
    return dict(passed=True,counter_phase_mail_actors_grid_unchanged=True)


def validate(fresh=True):
    proofs={}
    if fresh:
        proofs={'queued':queued.validate(),'boundary':boundary.validate(),'crt':crt.validate()}
    return dict(compare(),wave=wave_compare(),world_guard=world_guard(),fresh_x86=fresh,x86_proofs=proofs,
        sources={str(p.relative_to(ROOT)):gate.digest(p)for p in [PROBE,Path(__file__),*[SIM/n for n in INPUTS]]})


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--pinned',action='store_true');p.add_argument('--assembly',type=Path);a=p.parse_args()
    result=dict(compare(a.assembly),wave=wave_compare(a.assembly),world_guard=world_guard(a.assembly))if a.assembly else validate(not a.pinned)
    a.output.write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items()if k not in('sources','x86_proofs')})


if __name__=='__main__':main()
