"""First Shift commits pending selection,source41 then100/2's20;append and duplicate.

Original518070 UI and independent49ca60/4cf2c0 world with actual4a1700.
Controlled prefix117 input,not a universalWindows allocation contract.
"""
from pathlib import Path
import argparse,json
from tools import probe_fleet_queued_world as native


def fixture():
    specifications=[]
    for position,order in ((0,(-1,11,12,13)),(3,(11,12,13,-1))):
        specifications.append(dict(label='pending-queued-'+str(position),order=order,warm=2,members=(11,12,13),
            points=((18,6),(16,4),(18,6)),prefixes=[117]*3,age_input=None,terrain='mission',times=[40*i for i in range(1,201)]))
    data=native.fixture(specifications);data['scope']=__doc__
    ui=native.fleet.QueuedOracle(native.fleet.normal.source.membership.hover.source_metadata(),'ui')
    ui.run(('select',11,12,13));steps=[]
    for label,x,y in (('dispatch',18,6),('pending-append',16,4),('pending-duplicate',18,6)):
        steps.append(dict(label=label,state=ui.run(('shift',x,y,0))))
    data['initial_ui_steps']=steps;return data


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();d=fixture()
    a.output.write_text(json.dumps(d,separators=(',',':'))+'\n');print(dict(cases=len(d['cases']),frames=sum(len(c['rows'])for c in d['cases'])))


if __name__=='__main__':main()
