"""Pinned UI packets plus one source world engine per explicit registry/mail case."""
from pathlib import Path
import argparse,hashlib,json
from tools import probe_ship_fleet_ui_world as native,validate_ship_world_step as world
ROOT=world.ROOT
SHA='9ffb6a782dce24639a0b59cba50fc70c5b1f9e980185eee886242f224b8f1728'
FIXTURE=ROOT/'tests/fixtures/ship_fleet_ui_world.json'


def load(path=None):
    raw=Path(path or FIXTURE).read_bytes()
    world.gate.require(hashlib.sha256(raw).hexdigest()==SHA,'UI world fixture SHA differs')
    return json.loads(raw)


def validate():
    data=load();world.gate.require(data==json.loads(json.dumps(native.fixture())),'Fresh source UI world boundary differs')
    return dict(world.compare(data),fresh_native=True,fixture_sha256=SHA,ui_packets=6,source_ui_world_engines_separate=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=validate();a.output.write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':main()
