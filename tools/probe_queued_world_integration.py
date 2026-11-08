"""Additional mixed-prefix/member-order cases and normal100/1 with real310.

Original46case fixture remains immutable. Normal source probes now execute
4a1700 for the strict comparison;old ret-notification fixtures remain historical.
"""
from pathlib import Path
import argparse,json
from tools import probe_fleet_queued_world as queued
ROOT=queued.ROOT;world=queued.world


def mixed_specs():
    for order in((-1,11,12,13),(11,12,13,-1)):
        for members in((13,11),(13,12,11)):
            yield dict(label=f'mixed-{order.index(-1)}-'+','.join(map(str,members)),order=order,warm=0,
                members=members,points=((16,2),(18,6),(16,4)),prefixes=[32767,117,-32768],
                age_input=101,terrain='mission',times=[40*i for i in range(1,31)])


def mixed_fixture():return queued.fixture(list(mixed_specs()))


def normal_fixture():
    cases=[]
    for spec in world.specifications():
        # Normal100/1 never uses4ceab0;these explicit inputs must remain unused.
        n=queued.QueuedWorldOracle(spec['order'],spec['warm'],{11:0,12:0,13:0})
        n.request(spec['members']);rows=[]
        for t in spec['times']:
            notified=t==spec.get('notify_at',-1)*40
            if notified:n.notify()
            row=n.frame(t);assert not row['wave_reads'];rows.append(dict(row,notified=notified))
        cases.append(dict(spec,rows=rows))
    return dict(schema_version=2,original_exe_sha256=world.original.EXPECTED,cases=cases,
        seed_payloads={str(i):n.records[i].hex()for i in world.live.LOCAL},
        terrain=list(queued.fleet.normal.source.formation.mission_terrain()),
        arrival_notifications_executed=True,scope=__doc__)


def main():
    p=argparse.ArgumentParser();p.add_argument('--mixed-output',type=Path,required=True);p.add_argument('--normal-output',type=Path,required=True);a=p.parse_args()
    mixed=mixed_fixture();a.mixed_output.write_text(json.dumps(mixed,separators=(',',':'))+'\n')
    print('MIXED',len(mixed['cases']),flush=True)
    normal=normal_fixture();a.normal_output.write_text(json.dumps(normal,separators=(',',':'))+'\n')
    print('NORMAL',len(normal['cases']),sum(len(c['rows'])for c in normal['cases']),flush=True)


if __name__=='__main__':main()
