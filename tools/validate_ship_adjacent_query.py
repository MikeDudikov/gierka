#!/usr/bin/env python3
"""Compare bounded adjacent-cell source x86 queries with the actual Unity C#.

No planner, constructors, movement, Life, AI or renderer executes here.
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
    from . import validate_mission_object_selection as selection
    from . import validate_mission_ship_seed as ship
else:
    import validate_mission_object_selection as selection
    import validate_mission_ship_seed as ship

gate=selection.gate
ROOT=gate.ROOT
MissingPrerequisite=selection.MissingPrerequisite
GRID_SOURCE=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime/MissionOccupancyGrid.cs'
SOURCE=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/ShipAdjacentQuery.cs'
PROBE=ROOT/'tests/fixtures/ShipAdjacentQueryProbe.cs'
FIXTURE=ROOT/'tests/fixtures/ship_adjacent_query.json'
FLAGS=ROOT/'tests/fixtures/mission_cell_flags.bin'
FIXTURE_SHA256='98cefc9c6544f52e929943ad22fe511b5abac23a7f5e1332ffa18b76ed761d3e'
OUTPUT=ROOT/'artifacts/navigation/query-review/csharp-validation.json'


def original_cases(source_root=selection.SOURCE_ROOT):
    try:
        import pefile
        from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EIP,UC_X86_REG_ESP
    except ModuleNotFoundError as error:
        raise MissingPrerequisite('Install tools/requirements-analysis.txt for x86 query validation') from error
    GRID,SELF,A,B,LINK,TARGET=0x70000000,0x70010000,0x70012000,0x70014000,0x70016000,0x70018000
    WIDTH,HEIGHT,COUNT=24,24,576
    DIRECTIONS=((1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1),(0,1),(1,1))
    flags_raw=(ROOT/'tests/fixtures/mission_cell_flags.bin').read_bytes()
    assert hashlib.sha256(flags_raw).hexdigest()=='eb8c22b2dc3a3d6de5be5c5a28560701333cbc8610e8dd687052f4f93b260283'
    source_flags=struct.unpack('<576I',flags_raw)
    sources=selection.checked_sources(source_root)
    pe=pefile.PE(data=sources['installed/ancient.exe'])
    uc=selection.new_engine(pe.get_memory_mapped_image(),pe.OPTIONAL_HEADER.SizeOfImage)
    put=lambda addr,val:selection.put(uc,addr,val)
    current_spec={}
    cases=[]
    identities={SELF:1,A:2,B:3,TARGET:4,**{0x70020000+n*0x1000:5+n for n in range(8)}}
    def token(pointer):return identities[pointer] if pointer else 0
    get=lambda addr:selection.get(uc,addr)
    for addr,value in ((0x5c74fc,GRID),(0x5c74ec,WIDTH),(0x5c74f0,HEIGHT),(0x5c74e8,COUNT)):
        put(addr,value)
    for pointer in (SELF,A,B,TARGET):
        put(pointer+0x50,200);put(pointer+0x4c,11)
        uc.mem_write(pointer+0x58c,b'\0');put(pointer+0x8e6,0)

    def index(x,y):return y*WIDTH+x
    def owner(cell,value):
        put(GRID+12+24*cell,value);current_spec['owners'][str(cell)]=token(value)
    def flag(cell,value):
        put(GRID+8+24*cell,value);current_spec['flags'][str(cell)]=value
    def reset(native_flags=False,fill_owner=0):
        rows=bytearray(8+24*COUNT)
        struct.pack_into('<hhhh',rows,0,WIDTH,HEIGHT,64,64)
        for cell in range(COUNT):
            struct.pack_into('<II',rows,8+24*cell,source_flags[cell] if native_flags else 1,fill_owner)
        uc.mem_write(GRID,bytes(rows))
        current_spec.clear();current_spec.update(source_flags=native_flags,owner_fill=token(fill_owner),flags={},owners={})
        for pointer in (SELF,A,B,TARGET):
            put(pointer+0x50,200);put(pointer+0x4c,11);put(pointer+0x8e6,0)
            uc.mem_write(pointer+0x58c,b'\0')

    def call(address,*args):
        top=selection.STACK+selection.STACK_SIZE-0x1000
        for n,value in enumerate((selection.END,*args)):put(top+4*n,value)
        uc.reg_write(UC_X86_REG_ESP,top)
        uc.emu_start(address,selection.END,count=10000)
        assert uc.reg_read(UC_X86_REG_EIP)==selection.END
        result=uc.reg_read(UC_X86_REG_EAX)
        if address==0x499aa0:
            requester,cell,heading,restriction=args
            required={requester}
            required.update(pointer for pointer,identity in identities.items() if identity in
                            [current_spec['owner_fill'],*current_spec['owners'].values()])
            descriptors=[]
            for pointer in sorted(required,key=token):
                linked=get(pointer+0x8e6)
                linked_target=get(linked+5) if linked else 0
                xy=[struct.unpack('<i',uc.mem_read(linked_target+offset,4))[0] for offset in (0x5a3,0x5a7)] if linked else [0,0]
                descriptors.append([token(pointer),get(pointer+0x50),bytes(uc.mem_read(pointer+0x58c,1))[0],
                                    int(bool(linked)),get(linked) if linked else 0,*xy])
            cases.append({'source_flags':current_spec['source_flags'],'owner_fill':current_spec['owner_fill'],
                          'flags':dict(current_spec['flags']),'owners':dict(current_spec['owners']),
                          'occupants':descriptors,'target_index':cell,'heading':heading,'restriction':restriction,
                          'expected':result})
        return result

    def terrain(bits,restriction=0):
        low,high=bits&15,(bits>>4)&15
        return low<8 and high not in (4,5,6) and (not restriction or high!=3)

    def corners(cell,heading):
        if heading==1:return cell-1,cell+WIDTH
        if heading==3:return cell+WIDTH,cell+1
        if heading==5:return cell+1,cell-WIDTH
        if heading==7:return cell-WIDTH,cell-1
        return None

    records=ship.source_records(sources)
    report={'scope':'actual unhooked499aa0/499990/4999e0 predicate only; no planner/MoveShip/Life/AI/full world',
            'source_hashes':selection.SOURCE_HASHES,'source_cell_flags_sha256':hashlib.sha256(flags_raw).hexdigest(),
            'hooks':[],'source_neighbors':[],'flag_owner_cases':[],'corner_owner_cases':[],
            'corner_flag_cases':[],'linked_state_cases':[],'boundary_cases':[]}

    # Explicit partial source cohort: source records provide class/coordinates,
    # pointers are opaque test identities and do not claim source construction.
    for heading,(dx,dy) in enumerate(DIRECTIONS):
        for restriction in (0,1):
            for target_owner in (0,SELF,A):
                reset(native_flags=True)
                for n,(entry,payload) in enumerate(records):
                    pointer=SELF if entry['name']=='OBJ_0000000b' else 0x70020000+n*0x1000
                    x,y=struct.unpack_from('<ii',payload,36)
                    put(pointer+0x50,struct.unpack_from('<I',payload,28)[0]+200)
                    put(pointer+0x5a3,x);put(pointer+0x5a7,y)
                    owner(index(x,y),pointer)
                x,y=16+dx,2+dy;cell=index(x,y);owner(cell,target_owner)
                actual=call(0x499aa0,SELF,cell,heading,restriction)
                expected=terrain(source_flags[cell],restriction) and target_owner in (0,SELF)
                assert actual==int(expected)
                report['source_neighbors'].append({'heading':heading,'target':[x,y],'index':cell,
                    'flags':source_flags[cell],'restriction':restriction,'target_owner':hex(target_owner),
                    'result':bool(actual),'corner_indices':corners(cell,heading)})

    # Exact target mask/owner gate, exhaustively covering both nibbles, all three
    # restriction bytes, with empty/same/distinct-but-equal-ID owner identities.
    reset();cell=index(17,2)
    for high in range(16):
        for low in range(16):
            bits=0xa5a50000|(high<<4)|low;flag(cell,bits)
            for restriction in (0,1,255):
                expected=terrain(bits,restriction)
                flat=call(0x499990,cell,restriction);xy=call(0x4999e0,17,2,restriction)
                assert flat==xy==int(expected)
                for target_owner in (0,SELF,A):
                    owner(cell,target_owner)
                    actual=call(0x499aa0,SELF,cell,0,restriction)
                    assert actual==int(expected and target_owner in (0,SELF))
                    report['flag_owner_cases'].append({'flags':bits,'restriction':restriction,'target_owner':hex(target_owner),
                        'flat_result':flat,'xy_result':xy,'result':actual})

    for heading in (1,3,5,7):
        dx,dy=DIRECTIONS[heading];cell=index(16+dx,2+dy);ca,cb=corners(cell,heading)
        for oa in (0,SELF,A,B):
            for ob in (0,SELF,A,B):
                reset();owner(ca,oa);owner(cb,ob)
                actual=call(0x499aa0,SELF,cell,heading,0)
                expected=not(oa and ob and oa==ob)
                assert actual==int(expected)
                report['corner_owner_cases'].append({'heading':heading,'target':cell,'corners':[ca,cb],
                    'owners':[hex(oa),hex(ob)],'result':bool(actual)})
        for fa,fb in ((8,1),(1,8),(8,8),(0x41,1),(1,0x51),(0x61,0x41),(0x31,0x31)):
            reset();flag(ca,fa);flag(cb,fb)
            actual=call(0x499aa0,SELF,cell,heading,1)
            assert actual==1
            report['corner_flag_cases'].append({'heading':heading,'corner_flags':[fa,fb],
                'corner_terrain_queries':[call(0x499990,ca,1),call(0x499990,cb,1)],'result':bool(actual)})

    # The special link branch is asymmetric: only cornerA is examined. It does
    # not require foreignownership, a matching cornerB occupant or target class.
    for heading in (1,3,5,7):
        dx,dy=DIRECTIONS[heading];cell=index(16+dx,2+dy);ca,cb=corners(cell,heading)
        scenarios=[('base',A,0,200,6,200,cb,True,True),
                   ('self-cornerA',SELF,0,200,6,200,cb,True,True),
                   ('different-owner-cornerB',A,B,200,6,200,cb,True,True),
                   ('no-link',A,0,200,6,200,cb,False,False),
                   ('wrong-record-type',A,0,200,6,201,cb,True,False),
                   ('linked-target-othercell',A,0,200,6,200,ca,True,False)]
        for tag in (199,200,207,211,212):scenarios.append(('class:'+str(tag),A,0,tag,6,200,cb,True,200<=tag<=211))
        for state in (0,4,5,6,7):scenarios.append(('state:'+str(state),A,0,200,state,200,cb,True,state==6))
        for label,oa,ob,tag,state,kind,linked_cell,has_link,blocked in scenarios:
            reset();owner(ca,oa);owner(cb,ob);put(oa+0x50,tag);uc.mem_write(oa+0x58c,bytes((state,)))
            put(oa+0x8e6,LINK if has_link else 0);put(LINK,kind)
            uc.mem_write(LINK+4,b'\xff');put(LINK+5,TARGET)
            put(TARGET+0x50,999)  # no category/class check of the linked target
            put(TARGET+0x5a3,linked_cell%WIDTH);put(TARGET+0x5a7,linked_cell//WIDTH)
            actual=call(0x499aa0,SELF,cell,heading,0)
            assert actual==int(not blocked)
            report['linked_state_cases'].append({'heading':heading,'case':label,'cornerA_owner':hex(oa),
                'cornerB_owner':hex(ob),'owner_runtime_tag':tag,'movement_state':state,'link_record_type':kind,
                'has_link':has_link,'linked_cell':linked_cell,'result':bool(actual)})
        reset();owner(cb,A);put(A+0x50,200);uc.mem_write(A+0x58c,b'\x06');put(A+0x8e6,LINK)
        put(LINK,200);put(LINK+5,TARGET);put(TARGET+0x5a3,ca%WIDTH);put(TARGET+0x5a7,ca//WIDTH)
        actual=call(0x499aa0,SELF,cell,heading,0);assert actual==1
        report['linked_state_cases'].append({'heading':heading,'case':'reversed-link-only-in-cornerB','result':True})

    # Every valid target and heading with one foreign object claiming all other
    # cells: only source boundary earlyreturns or cardinal parity can allow this.
    for heading in range(8):
        for cell in range(COUNT):
            reset(fill_owner=A);owner(cell,0)
            actual=call(0x499aa0,SELF,cell,heading,0)
            x,y=cell%WIDTH,cell//WIDTH
            boundary=((heading==1 and (x==0 or y==HEIGHT-1)) or
                      (heading==3 and (y==HEIGHT-1 or x==WIDTH-1)) or
                      (heading==5 and (y==0 or x==WIDTH-1)) or
                      (heading==7 and (y==0 or x==0)))
            assert actual==int(heading%2==0 or boundary)
            report['boundary_cases'].append({'heading':heading,'target':cell,'boundary_early_allow':bool(boundary),'result':bool(actual)})

    report['case_counts']={key:len(report[key]) for key in ('source_neighbors','flag_owner_cases','corner_owner_cases',
                              'corner_flag_cases','linked_state_cases','boundary_cases')}
    report['case_count']=sum(report['case_counts'].values())
    report['inputs']=cases
    start=0
    for group,count in report['case_counts'].items():
        for case in cases[start:start+count]:case['group']=group
        start+=count
    assert start==len(cases)==7120
    return report


GUARDS={'null_grid','null_requester','null_resolver','value_projection','terrain_resolver_gate',
        'target_resolver_gate','cardinal_resolver_gate','boundary_resolver_gate',
        'empty_corner_resolver_gate','only_first_corner_resolved','all_case_grids_unchanged'}|{
        'heading_'+str(value) for value in (8,127,128,255)}|{'bounds_'+str(index) for index in range(8)}


def fixture_data(original):
    return {'source_hashes':selection.SOURCE_HASHES,
            'source_cell_flags_sha256':original['source_cell_flags_sha256'],
            'case_counts':original['case_counts'],'case_count':original['case_count'],
            'scope':'499aa0 target/corner query only, identity-token projections; no planner/world construction',
            'cases':original['inputs']}


def encode(case):
    mapping=lambda rows:';'.join(str(key)+':'+str(value) for key,value in sorted(rows.items(),key=lambda row:int(row[0]))) or '-'
    views=';'.join(':'.join(map(str,row)) for row in case['occupants'])
    return '\t'.join(map(str,[int(case['source_flags']),case['owner_fill'],case['target_index'],
                               case['heading'],case['restriction'],mapping(case['flags']),mapping(case['owners']),views]))


def validate(source_root=selection.SOURCE_ROOT,mono_root=None):
    _,unicorn,runtime,compiler=gate.prerequisites(Path(source_root)/'installed/ancient.exe',mono_root)
    original=original_cases(source_root)
    gate.require(gate.digest(FIXTURE)==FIXTURE_SHA256,'Pinned adjacent-query fixture differs')
    gate.require(json.loads(FIXTURE.read_text())==fixture_data(original),'Actual x86 differs from adjacent-query fixture')
    pinned={str(path.relative_to(ROOT)):gate.digest(path) for path in (GRID_SOURCE,SOURCE,PROBE)}
    with tempfile.TemporaryDirectory(prefix='ship-adjacent-query-') as temporary:
        executable=Path(temporary)/'ShipAdjacentQueryProbe.exe'
        build=subprocess.run(compiler+['/nologo','/checked+','/target:exe','/out:'+str(executable),
                                      str(GRID_SOURCE),str(SOURCE),str(PROBE)],text=True,capture_output=True,timeout=60)
        gate.require(build.returncode==0,'Adjacent-query C# compilation failed:\n'+build.stdout+build.stderr)
        result=subprocess.run([str(runtime),str(executable),str(FLAGS)],
                              input='\n'.join(encode(case) for case in original['inputs'])+'\n',
                              text=True,capture_output=True,timeout=90)
        gate.require(result.returncode==0,'Adjacent-query C# probe failed:\n'+result.stdout+result.stderr)
    gate.require(pinned=={str(path.relative_to(ROOT)):gate.digest(path) for path in (GRID_SOURCE,SOURCE,PROBE)},
                 'Adjacent-query source/probe changed during validation')
    rows=[];guards=[]
    for line in result.stdout.splitlines():
        fields=line.split('\t')
        if len(fields)==2 and fields[0]=='CHECK':guards.append(fields[1])
        elif len(fields)==2 and fields[0]=='RESULT':rows.append(int(fields[1]))
        else:raise AssertionError('Unexpected adjacent-query probe output: '+line)
    gate.require(len(guards)==len(GUARDS) and set(guards)==GUARDS,'Missing/duplicate adjacent-query contract checks')
    expected=[case['expected'] for case in original['inputs']]
    gate.require(len(rows)==len(expected),'Adjacent-query C# case count differs')
    for index,(native,managed) in enumerate(zip(expected,rows)):
        gate.require(native==managed,f'Adjacent-query mismatch {index}: x86 {native}, C# {managed}')
    neighbors=[row for row in original['source_neighbors'] if row['restriction']==0 and row['target_owner']=='0x0']
    return {'passed':len(rows),'case_count':len(rows),'case_groups':original['case_counts'],
            'scope':fixture_data(original)['scope'],'source_hashes':selection.SOURCE_HASHES,
            'source_cell_flags_sha256':original['source_cell_flags_sha256'],'source_neighbors':neighbors,
            'checked_compilation':True,'csharp_contract_checks':len(guards),'csharp_guards':guards,
            'fixture_sha256':FIXTURE_SHA256,'source_sha256':pinned,'validator_sha256':gate.digest(Path(__file__)),
            'native_function_intercepts':[],'native_entries':['0x499aa0','0x499990','0x4999e0','0x50e590'],
            'compiler_command':compiler,'mono_runtime':str(runtime),'unicorn_version':unicorn.__version__,
            'original_cases':original,
            'limits':['No constructors, full grid population, planner, movement, Life, AI or Unity/player is executed',
                      'Source group uses explicit eight-owner partial grid; other class lifecycle remains outside scope',
                      'Null input/heading/bounds rejection is defensive C# policy, not native equivalence',
                      'Occupant struct describes valid native link graphs; malformed linked pointers are unrepresentable',
                      'Resolver exposes only cornerA fields and must itself be read-only; identity is by object reference']}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,default=selection.SOURCE_ROOT)
    parser.add_argument('--mono-root',type=Path)
    parser.add_argument('--output',type=Path,default=OUTPUT)
    args=parser.parse_args(argv)
    if args.output.exists():parser.error('Select a fresh output path; previous evidence is preserved')
    try:report=validate(args.source_root,args.mono_root)
    except MissingPrerequisite as error:parser.exit(2,str(error)+'\n')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as stream:stream.write(json.dumps(report,indent=2)+'\n')
    print(f"{report['passed']} actual x86/C# adjacent-query cases; {report['csharp_contract_checks']} contract checks")
    return 0


if __name__=='__main__':raise SystemExit(main())
