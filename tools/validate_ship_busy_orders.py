"""Pinned x86 normal repeated20 receipt and its original world phase integration."""
from pathlib import Path
import argparse,hashlib,json
from tools import validate_ship_live_fleet as live,validate_ship_world_step as world,probe_ship_busy_orders as native
ROOT=live.ROOT;PROBE=ROOT/'tests/fixtures/ShipBusyOrdersProbe.cs'
FIXTURE_SHA='30268bff1368c805d01419f8513cf343f99517c542ecf3dd7c6d00928fdbc6f3'
WORLD_SHA='2d1dc4597711ddde7bfbaf84c66e6bbd58b7d8e9e7a6eb678b2f44c2f25f46dd'


def load(path=None):
    raw=Path(path or ROOT/'tests/fixtures/ship_busy_orders.json').read_bytes()
    live.legacy.gate.require(hashlib.sha256(raw).hexdigest()==FIXTURE_SHA,'Busy order fixture SHA differs');return json.loads(raw)


def load_world(path=None):
    raw=Path(path or ROOT/'tests/fixtures/ship_busy_world.json').read_bytes()
    live.legacy.gate.require(hashlib.sha256(raw).hexdigest()==WORLD_SHA,'Busy world fixture SHA differs');return json.loads(raw)


def compare(data,source=live.SOURCE,assembly=None):
    return live.compare(data,source=source,assembly=assembly,probe=PROBE,api_controls=12)


def validate():
    d=load();w=load_world();live.legacy.gate.require(d==native.fixture(),'Fresh busy actor differs')
    live.legacy.gate.require(w==native.world_fixture(),'Fresh busy world differs')
    return dict(actor=compare(d),world=world.compare(w),fresh_native=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=validate();a.output.write_text(json.dumps(r,indent=2)+'\n');print(r)


if __name__=='__main__':main()
