#!/usr/bin/env python3
"""Validate bounded Unity C# ownership and source flag queries against real x86.

The frozen576 flags came from original grid creation with only setjmp/malloc
hooks. Small claim/release/query functions execute without hooks here. Owner
objects replace opaque native pointers by reference identity, including ID0.
No pathfinding, spawning, full grid object slots or gameplay are implemented.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile

if __package__:
    from .validate_boss_ai_gate import ROOT, EXPECTED, MissingPrerequisite, digest, prerequisites, require
else:
    from validate_boss_ai_gate import ROOT, EXPECTED, MissingPrerequisite, digest, prerequisites, require

SOURCE=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime/MissionOccupancyGrid.cs'
PROBE=ROOT/'tests/fixtures/MissionOccupancyGridProbe.cs'
FIXTURE=ROOT/'tests/fixtures/mission_cell_flags.bin'
PROVENANCE=FIXTURE.with_suffix('.json')
FIXTURE_SHA256='eb8c22b2dc3a3d6de5be5c5a28560701333cbc8610e8dd687052f4f93b260283'
PROVENANCE_SHA256='61c63dcfa2822effa4e28c75ea7962421c1cbd446d5342d0d369a07661257606'
OUTPUT=ROOT/'artifacts/units/collision/occupancy-csharp-validation.json'
GRID,END,STACK=0x70000000,0x700ff000,0x7ff00000
OWNER_POINTERS=(0,0x71000000,0x72000000,0x73000000)
GUARDS={'geometry','flags_clone','flags_null','claim_null','release_null','reference_identity','spatial_identity'}|{f'{axis}_{v}' for axis in ('width','height') for v in (-1,0,32768,-0x80000000,0x7fffffff)}|{f'flags_length_{v}' for v in (0,575,577)}|{f'bounds_{method}_{v}' for method in ('flags','owner','claim','release','terrain','enter') for v in range(8)}


def load_fixture(fixture=FIXTURE,provenance=PROVENANCE):
    raw=Path(fixture).read_bytes();metadata=Path(provenance).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA256:raise ValueError('Frozen source cell flags hash differs')
    if hashlib.sha256(metadata).hexdigest()!=PROVENANCE_SHA256:raise ValueError('Frozen source grid provenance hash differs')
    evidence=json.loads(metadata)
    if len(raw)!=2304 or evidence['original_exe_sha256']!=EXPECTED or evidence['grid_create']['cell_count']!=576:
        raise ValueError('Frozen source grid geometry differs')
    return raw,list(struct.unpack('<576I',raw)),evidence


def input_cases():
    queries=[{'kind':'Q','flags':0xa5a50000|(high<<4)|low,'restriction':restriction,'owner':owner}
             for low in range(16) for high in range(16) for restriction in (0,1,255) for owner in (0,1)]
    owners=[{'kind':'C','before':before,'claim':claim,'release':release}
            for before in range(4) for claim in (1,2,3) for release in (1,2,3)]
    return queries+owners


def original_cases(image,image_size,cases):
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
    from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_ESP,UC_X86_REG_EIP
    uc=Uc(UC_ARCH_X86,UC_MODE_32);uc.mem_map(0x400000,(image_size+4095)&~4095);uc.mem_write(0x400000,image)
    uc.mem_map(GRID,0x100000);uc.mem_map(STACK,0x100000)
    def write(address,value):uc.mem_write(address,struct.pack('<I',value&0xffffffff))
    def read(address):return struct.unpack('<I',uc.mem_read(address,4))[0]
    write(0x5c74fc,GRID);write(0x5c74ec,24)
    def call(address,args):
        sp=STACK+0xff000;write(sp,END)
        for i,value in enumerate(args,1):write(sp+4*i,value)
        uc.reg_write(UC_X86_REG_ESP,sp);uc.emu_start(address,END,count=1000)
        require(uc.reg_read(UC_X86_REG_EIP)==END,'Original occupancy helper did not return')
        return uc.reg_read(UC_X86_REG_EAX)
    results=[];slot=GRID+8+24*(12*24+7)
    for case in cases:
        if case['kind']=='Q':
            write(slot,case['flags']);write(slot+4,OWNER_POINTERS[case['owner']])
            results.append(('QUERY',call(0x4999e0,[7,12,case['restriction']]),call(0x499a40,[7,12,case['restriction']])))
        else:
            write(slot+4,OWNER_POINTERS[case['before']]);call(0x499800,[0,OWNER_POINTERS[case['claim']],7,12])
            after=OWNER_POINTERS.index(read(slot+4));call(0x499860,[7,12,OWNER_POINTERS[case['release']]])
            results.append(('OWNER',after,OWNER_POINTERS.index(read(slot+4))))
    return results


def validate(mono_root=None,fixture=FIXTURE,provenance=PROVENANCE):
    raw,flags,evidence=load_fixture(fixture,provenance)
    pefile,_unicorn,runtime,compiler=prerequisites(mono_root=mono_root)
    original=ROOT/'reference/raw/ancient-conquest/installed/ancient.exe';binary=original.read_bytes()
    require(hashlib.sha256(binary).hexdigest()==EXPECTED,'Original executable hash differs')
    pe=pefile.PE(data=binary);cases=input_cases();native=original_cases(pe.get_memory_mapped_image(),pe.OPTIONAL_HEADER.SizeOfImage,cases)
    lines=[]
    for case in cases:
        if case['kind']=='Q':lines.append(f"Q\t{case['flags']}\t{case['restriction']}\t{case['owner']}")
        else:lines.append(f"C\t{case['before']}\t{case['claim']}\t{case['release']}")
    source_sha,probe_sha=digest(SOURCE),digest(PROBE)
    with tempfile.TemporaryDirectory(prefix='mission-occupancy-csharp-') as folder:
        executable=Path(folder)/'MissionOccupancyGridProbe.exe';payload=Path(folder)/'CellFlags.bin';payload.write_bytes(raw)
        compiled=subprocess.run(compiler+['/nologo','/checked+','/target:exe','/out:'+str(executable),str(SOURCE),str(PROBE)],capture_output=True,text=True,timeout=60)
        require(compiled.returncode==0,'C# occupancy compilation failed:\n'+compiled.stdout+compiled.stderr)
        result=subprocess.run([str(runtime),str(executable),str(payload)],input='\n'.join(lines)+'\n',capture_output=True,text=True,timeout=60)
        require(result.returncode==0,'C# occupancy probe failed:\n'+result.stdout+result.stderr)
    require(digest(SOURCE)==source_sha and digest(PROBE)==probe_sha,'Occupancy source/probe changed during validation')
    guards=[];actual_flags=[];rows=[]
    for line in result.stdout.splitlines():
        fields=line.split('\t')
        if len(fields)==2 and fields[0]=='CHECK':guards.append(fields[1])
        elif len(fields)==4 and fields[0]=='FLAG':actual_flags.append(tuple(int(value) for value in fields[1:]))
        elif len(fields)==3 and fields[0] in ('QUERY','OWNER'):rows.append((fields[0],int(fields[1]),int(fields[2])))
        else:raise ValueError('Unexpected C# occupancy probe output: '+line)
    require(len(guards)==len(GUARDS) and set(guards)==GUARDS,'Missing/duplicated C# occupancy guards')
    require(actual_flags==[(index%24,index//24,value) for index,value in enumerate(flags)],'C# flags differ from original grid creation')
    require(len(rows)==len(native),'Unexpected C# occupancy row count')
    for index,(expected,actual) in enumerate(zip(native,rows)):
        require(expected==actual,f'Occupancy mismatch at{index}: original{expected}; C#{actual}')
    return {'kind':'Original grid fixture and unhooked x86 helpers vs actual C# bounded occupancy','original_sha256':EXPECTED,
            'source_flags_sha256':FIXTURE_SHA256,'provenance_sha256':PROVENANCE_SHA256,'grid_creation_evidence':evidence['grid_create'],
            'cell_flags_compared':len(flags),'query_cases':1536,'query_result_comparisons':3072,'owner_sequences':36,
            'case_count':len(rows),'passed':len(rows),'intercepted_functions':[],
            'original_entries':{'claim':'0x499800','release':'0x499860','terrain_query':'0x4999e0','with_occupant_query':'0x499a40'},
            'checked_compilation':True,'csharp_guard_count':len(guards),'csharp_guards':guards,
            'csharp_source_sha256':source_sha,'probe_sha256':probe_sha,'validator_sha256':digest(Path(__file__)),
            'identity_control':'Distinct owners with equal InstanceId0/Equals cannot release each other; native pointers map to reference identities',
            'excluded':['Original helpers lack defensive C# bounds/null/length guards; these are API policy, not native equivalence',
                        'TryClaim/Release bool return values are API outcomes; original void helpers compared by state only',
                        'Object slot population, paths, movement, orders, collisions for all classes, world lifecycle and gameplay']}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mono-root',type=Path);parser.add_argument('--output',type=Path,default=OUTPUT)
    args=parser.parse_args(argv)
    if args.output.exists():parser.error('Select a fresh output report')
    report=validate(args.mono_root);args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as stream:stream.write(json.dumps(report,indent=2)+'\n')
    print(f"{report['passed']} actual C#/x86 cases, {report['cell_flags_compared']} original cell flags, {report['csharp_guard_count']} C# guards passed")
    return 0

if __name__=='__main__':raise SystemExit(main())
