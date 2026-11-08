"""First pending Shift:original UI+world and separate source marker-selection lifecycle."""
from pathlib import Path
import argparse,json,hashlib
from tools import probe_pending_queued_input as native,probe_queued_marker_lifecycle as graphics
from tools import validate_queued_world_integration as world
ROOT=world.ROOT
FIXTURE=ROOT/'tests/fixtures/pending_queued_input.json'
SHA='26e9fc2bd403dbb875822ff25b7e9c99cc680de17f189e92ac9be35323fd73c7'
LIFECYCLE=ROOT/'tests/fixtures/queued_marker_lifecycle.json'
LIFECYCLE_SHA='3dc3beb49a4b7290e079d2cf9f1826a02458ec318e471be461bf90077fddae66'


def load(path=FIXTURE,sha=SHA):
    raw=path.read_bytes();world.world.gate.require(hashlib.sha256(raw).hexdigest()==sha,'Pending Shift fixture differs:'+str(path));return json.loads(raw)


def validate(assembly=None,fresh=True):
    data=load();lifecycle=load(LIFECYCLE,LIFECYCLE_SHA);require=world.world.gate.require
    if fresh:
        require(json.loads(json.dumps(native.fixture()))==data,'Fresh pending Shift x86 differs')
        require(graphics.fixture()==lifecycle,'Fresh marker lifecycle x86 differs')
    counts=[sum(p['marker']is not None for p in r['route']['points'])for r in lifecycle['rows']]
    require(counts==[2,0,0,0,0,1,0,0,3,0],'Source marker selection lifecycle differs')
    require(all(r['task']['token']==1 for r in lifecycle['rows']),'Source selection unexpectedly replaced task')
    require(all(len(r['route']['points'])>=2 for r in lifecycle['rows']),'Source clear erased logical points')
    require(lifecycle['rows'][4]['destroyed']==[1,2],'Source duplicate recreated hidden marker')
    require(lifecycle['rows'][5]['route']['points'][2]['marker']['argument']==2,'Source append lost global ordinal')
    r=world.compare(assembly=assembly,data=data)
    return dict(r,fresh_x86=fresh,fixture_sha256=SHA,marker_lifecycle_sha256=LIFECYCLE_SHA,
        marker_lifecycle_states=len(counts),marker_counts=counts,first_ui_packet_count=len(data['initial_ui_steps'][0]['state']['packets']),
        initial_ui_packet_counts=[len(s['state']['packets'])for s in data['initial_ui_steps']],unity_input_adapter=False,
        explicit_show_hide_source_executed=True,explicit_show_hide_input_binding=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--assembly',type=Path);p.add_argument('--pinned',action='store_true');a=p.parse_args()
    r=validate(a.assembly,not a.pinned);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r)


if __name__=='__main__':main()
