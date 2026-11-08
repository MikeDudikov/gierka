"""Controlled in-place record load,world continuation and real pose/depth readouts."""
from pathlib import Path
import argparse,re
from tools import smoke_ship_world_step as base,validate_cohort_world_restore as proof
ROOT=base.ROOT;require=base.require
COUNTERS=(1,3,10,11,25,50,80,100,125,150,200,201,202,212)


def reference():
    case=next(c for c in proof.load()['cases']if c['label']=='cohort-0-1,0,255')
    ops=[dict(kind='R',id=s['id'],counter=0,state=s)for s in case['initial']['actors']]
    for f in case['rows']:
        ops.extend(dict(kind='T',id=s['id'],counter=f['counter'],state=s)for s in f['actors'])
        if str(f['counter'])in case['restored']:
            ops.extend(dict(kind='L',id=s['id'],counter=f['counter'],state=s)for s in case['restored'][str(f['counter'])]['actors'])
    ref=base.rendering.load_reference(case_override=dict(initial=case['initial']['actors'],operations=ops),counters=COUNTERS)
    del ref['checkpoints']['requests'];ref['world']=case;ref['counters']=COUNTERS;return ref


def validate_log(log,ref):
    result=base.validate_log(log,ref);restores=[]
    for m in re.finditer(r'^\[ShipWorldRestore\] context: counter=(\d+); phase=(-?\d+); queued=(\d+); age=(\d+); prep=(\d+)$',log,re.M):
        counter,phase,queued,age,prep=map(int,m.groups());restores.append(counter);r=ref['world']['restored'][str(counter)]
        require((phase,queued,age,prep)==(r['phase'],len(r['outgoing']),r['group']['age'],r['mail_gate']),'Restored world context differs')
    require(restores==[1,10][:len(restores)],'Invalid restore order')
    if result[1]:require(restores==[1,10],'Missing cohort restore')
    return result


def run(output,records):
    records=Path(records).resolve();require(not records.exists(),'Use fresh source records directory');records.mkdir(parents=True)
    ref=reference()
    for counter,rows in ref['world']['records'].items():
        d=records/counter;d.mkdir()
        for identifier,raw in zip((11,12,13),rows):(d/(format(identifier,'08x')+'.bin')).write_bytes(bytes.fromhex(raw))
    paths=[Path(__file__),proof.PROBE,ROOT/'tests/fixtures/cohort_world_restore.json',ROOT/'tools/probe_cohort_world_restore.py',*sorted(records.rglob('*.bin'))]
    return base.run(output,True,reference_override=ref,extra_args=('--ship-fleet-world-restore-dir',records),extra_provenance=paths,log_validator=validate_log,
        scope_override='Controlled in-place cohort reload at1/10;source records,gates1/0/255,warm2 mail,explicit registry;source Life subset+CRT/graphics boundaries;existing pose/depth adapters;no whole-world save/load,original full graphics recreation,pixel/Win11/hardware proof')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--records',type=Path,required=True);a=p.parse_args();r=run(a.output,a.records)
    print({k:r[k]for k in('passed','checkpoints','actor_rows','component_rows','actual_queue_reads','publications','exit_code')})
