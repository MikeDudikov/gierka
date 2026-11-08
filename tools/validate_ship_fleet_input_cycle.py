"""Pinned first fleet UI packets handed to the actual three-body C# core."""
from pathlib import Path
import argparse,hashlib,json
from tools import validate_ship_live_fleet as live,probe_ship_fleet_input_cycle as native
ROOT=live.ROOT
FIXTURE_SHA='944dfe8904be35dc60af6083ed78dccaf5b7b1e421a5f435ecf111fbbd30cd26'


def load(path=None):
    raw=Path(path or ROOT/'tests/fixtures/ship_fleet_input_cycle.json').read_bytes()
    live.legacy.gate.require(hashlib.sha256(raw).hexdigest()==FIXTURE_SHA,'Fleet input cycle fixture SHA differs');return json.loads(raw)


def motion_case(data):
    ops=[]
    for r in data['received']:
        p=r['packet'];raw=bytes.fromhex(p['payload_hex'])
        if p['action']==41:
            import struct
            ops.append(dict(kind='G',id=p['actor'],group=struct.unpack_from('<i',raw,1)[0],state=r['state']))
        else:ops.append(dict(kind='R',id=p['actor'],goal=r['state']['requested'],argument=raw[-1],state=r['state']))
    ops +=[dict(kind='T',id=r['state']['id'],counter=r['counter'],pending=1,state=r['state'])for r in data['rows']]
    return dict(seed=0,initial=data['initial'],operations=ops,label='first-fleet-ui')


def validate():
    data=load();live.legacy.gate.require(data==native.fixture(),'Fresh fleet UI/body handoff differs')
    result=live.compare(dict(seed_payloads=data['seed_payloads'],cases=[motion_case(data)]));result.update(fresh_native=True,fixture_sha256=FIXTURE_SHA)
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=validate();a.output.write_text(json.dumps(r,indent=2)+'\n');print(r)


if __name__=='__main__':main()
