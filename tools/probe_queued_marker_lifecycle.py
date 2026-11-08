"""Source selection hides graphics independently of100/2 logical ownership."""
import json,argparse
from pathlib import Path
from tools import probe_ship_fleet_queued as native


def fixture():
    n=native.QueuedOracle(native.normal.source.membership.hover.source_metadata(),'ui');rows=[]
    def capture(label):
        s=n.snapshot_queued();rows.append(dict(label=label,task=s['task'],route=s['route'],destroyed=s['marker_destroyed'],
            packets=s['packets'],selection=n.snapshot_pending()))
    n.run(('select',11,12,13));n.run(('shift',18,6,0));n.run(('shift',16,4,0));capture('created')
    for label,call in (
        ('clear',lambda:n.release(7,None,message=100)),
        ('recall',lambda:n.release(5,12,flags=8)),
        ('work',lambda:n.run(('work',1,1))),
        ('hidden-duplicate',lambda:n.run(('shift',18,6,1))),
        ('append',lambda:n.run(('shift',18,5,1))),
        ('clear-again',lambda:n.release(7,None,message=100)),
        ('recall-again',lambda:n.release(5,12,flags=8)),
        ('explicit-show',lambda:n.invoke_fleet(0x4a2050,(5,1))),
        ('explicit-hide',lambda:n.invoke_fleet(0x4a2050,(5,0)))):
        n.commands.clear();n.selection_events.clear();call();capture(label)
    return dict(schema_version=1,original_exe_sha256=native.pointer.gate.EXPECTED,rows=rows,scope=__doc__,
        lower_graphics_constructor_destructor_boundaries=True,source_task_selection_and_route_executed=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();d=fixture()
    a.output.write_text(json.dumps(d,separators=(',',':'))+'\n');print([(r['label'],[p['marker']is not None for p in r['route']['points']])for r in d['rows']])


if __name__=='__main__':main()
