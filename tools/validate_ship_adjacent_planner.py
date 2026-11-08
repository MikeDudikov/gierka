#!/usr/bin/env python3
"""Closed source0b adjacent plans vs actual native planner; no generic pathfinding."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

if __package__:
    from . import probe_ship_adjacent_navigation as native, validate_boss_ai_gate as gate
    from . import validate_mission_ship_seed as ship
else:
    import probe_ship_adjacent_navigation as native
    import validate_boss_ai_gate as gate
    import validate_mission_ship_seed as ship

ROOT=gate.ROOT
MissingPrerequisite=gate.MissingPrerequisite
RUNTIME=ROOT/'Unity/AncientConquest/Assets/AncientConquest/Runtime'
SOURCES=[RUNTIME/name for name in ('MissionOccupancyGrid.cs','Simulation/ShipAdjacentQuery.cs','Simulation/ShipAdjacentPlanner.cs')]
PROBE=ROOT/'tests/fixtures/ShipAdjacentPlannerProbe.cs'
FIXTURE=ROOT/'tests/fixtures/ship_adjacent_planner.json'
FIXTURE_SHA256='73295e933946ffab36abb7282f4b51c280995f6a85aa29c37e448dffd3cf3c0a'
FLAGS=ROOT/'tests/fixtures/mission_cell_flags.bin'
OUTPUT=ROOT/'artifacts/navigation/adjacent/csharp-validation.json'


def compact(report):
    cases=[]
    for heading,case in enumerate(report['cases']):
        n=case['navigation']
        cases.append({'heading':heading,'target':case['target'],'flags':case['target_flags'],
                      'planned':bool(n['points']),'return_low_byte':n['return_low_byte'],
                      'points':n['points'],'path_hex':n['path_hex'],'path_count':len(n['points']),
                      'path_index':n['path_index'],'initial_state':n['state'],'center_gate':n['center_gate']})
    return {'schema_version':1,'original_source_hashes':report['source_hashes'],
            'source_cell_flags_sha256':report['source_cell_flags_sha256'],
            'source0b_payload_sha256':'fbcbf7c873f418fffdd9761954cea7b3844c2567b08baa85b0f3489faa51bbdb',
            'map_dimensions':[24,24],'origin':[16,2],'heading':5,'restriction':0,
            'source_fleet_cells':[[16,2],[21,5],[19,4],[11,18],[9,21],[10,22],[6,13],[6,14]],
            'local_flags':[[0x308,8,1],[1,1,1],[7,7,1]],'cases':cases}


def validate(mono_root=None):
    _,unicorn,runtime,compiler=gate.prerequisites(mono_root=mono_root)
    original=native.validate()
    gate.require(gate.digest(FIXTURE)==FIXTURE_SHA256,'Pinned adjacent planner fixture changed')
    fixture=json.loads(FIXTURE.read_text())
    gate.require(fixture==compact(original),'Fresh native adjacent plans differ from pinned fixture')
    gate.require(gate.digest(FLAGS)==fixture['source_cell_flags_sha256'],'Source flag bytes changed')
    gate.require(gate.digest(ship.FIXTURE)==ship.FIXTURE_SHA256,'Source ship fixture changed')
    seed=next(row for row in json.loads(ship.FIXTURE.read_text())['records'] if row['instance_id']==11)
    gate.require(seed['payload_sha256']==fixture['source0b_payload_sha256'],'Planner source0b recipe differs')
    before={str(path.relative_to(ROOT)):gate.digest(path) for path in [*SOURCES,PROBE]}
    with tempfile.TemporaryDirectory(prefix='ship-adjacent-planner-')as temporary:
        exe=Path(temporary)/'ShipAdjacentPlannerProbe.exe'
        build=subprocess.run(compiler+['/nologo','/checked+','/target:exe','/out:'+str(exe),*map(str,SOURCES),str(PROBE)],
                             text=True,capture_output=True,timeout=60)
        gate.require(build.returncode==0,'Adjacent planner C# compilation failed:\n'+build.stdout+build.stderr)
        run=subprocess.run([str(runtime),str(exe),str(FLAGS)],text=True,capture_output=True,timeout=60)
        gate.require(run.returncode==0,'Adjacent planner probe failed:\n'+run.stdout+run.stderr)
    rows=[];guards=[]
    for line in run.stdout.splitlines():
        fields=line.split('\t')
        if fields[0]=='ROW':rows.append(fields[1:])
        elif fields[0]=='GUARD':guards.append(fields[1])
        else:raise ValueError('Unknown planner probe output: '+line)
    gate.require(len(rows)==8,'C# planner returned a different adjacent case count')
    for case,actual in zip(fixture['cases'],rows):
        expected=[case['heading'],int(case['planned']),case['path_count'],case['path_index'],case['initial_state'],case['center_gate'],case['path_hex']]
        gate.require(actual==list(map(str,expected)),f'Adjacent planner differs for heading{case["heading"]}: x86 {expected} / C# {actual}')
    gate.require(len(guards)==len(set(guards)),'Duplicate planner guard declarations')
    gate.require(before=={str(path.relative_to(ROOT)):gate.digest(path) for path in [*SOURCES,PROBE]},'Planner source changed during validation')
    return {'passed':8,'case_count':8,'accepted':6,'source_blocked':2,'guard_count':len(guards),'guards':guards,
            'fixture_sha256':FIXTURE_SHA256,'original_source_hashes':fixture['original_source_hashes'],
            'source_sha256':before,'checked_compilation':True,'compiler_command':compiler,'mono_runtime':str(runtime),
            'unicorn_version':unicorn.__version__,'native_oracle_sha256':gate.digest(Path(native.__file__)),
            'validator_sha256':gate.digest(Path(__file__)),'native_evidence':original,
            'scope':'Initial source0b/staticfleet8/local3x3/original24map adjacent branch only',
            'limits':['No generic native wave/line planner, pathfinding for other origins, dynamic fleet or runtime integration',
                      'Native ProcPostMove lowbyte0 is shared by success/failure; installed native path determines the observed outcome',
                      'Init service and bounded heap/setjmp boundaries are explicit; no query/planner procedure is replaced',
                      'Failure directentry leaves the source exception-chain pointer linked; isolated probe executes no movement after that return']}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=OUTPUT);parser.add_argument('--mono-root',type=Path)
    args=parser.parse_args(argv)
    if args.output.exists():parser.error('Select a fresh output path')
    try:report=validate(args.mono_root)
    except MissingPrerequisite as error:parser.exit(2,str(error)+'\n')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x')as stream:stream.write(json.dumps(report,indent=2)+'\n')
    print(f"8 native/C# adjacent plans passed; {report['guard_count']} guards")
    return 0


if __name__=='__main__':raise SystemExit(main())
