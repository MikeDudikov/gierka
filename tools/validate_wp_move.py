"""Original WPMOVE constructor masks,4ced10 position writes and staged source pixels."""
from pathlib import Path
import argparse,json,hashlib
from tools import probe_wp_move as native,compose_wp_move as composer,stage_ship_fleet_visuals as stage
from tools import validate_boss_ai_gate as gate
ROOT=gate.ROOT


def validate():
    path=ROOT/'tests/fixtures/wp_move.json';raw=path.read_bytes()
    gate.require(hashlib.sha256(raw).hexdigest()==composer.FIXTURE_SHA,'WPMOVE fixture SHA differs')
    data=json.loads(raw);gate.require(native.fixture()==data,'Fresh x86 WPMOVE masks/config differ')
    positions=native.position_fixture()
    def signed(v):return(v+2**31)%2**32-2**31
    for row in positions:gate.require(row['world']==[signed(row['cell'][0]*64+14),signed(row['cell'][1]*64+18)],'Fresh4ced10 pixel position differs')
    payloads,manifest=stage.compose();folder=ROOT/'Unity/AncientConquest/Assets/Resources/ShipFleetVisualsGenerated'
    for name,payload in payloads.items():gate.require((folder/name).read_bytes()==payload,'Staged pixels differ:'+name)
    staged=json.loads((folder/stage.MANIFEST_NAME).read_text())
    gate.require(all(staged[k]==v for k,v in manifest.items()),'Staged WPMOVE table differs')
    wp=manifest['wp_move'];gate.require(len(wp['frames'])==100 and len(wp['ordinal_frames'])==256,'WPMOVE ordinal coverage differs')
    gate.require(wp['frames'][wp['ordinal_frames'][99]]['mask']==0x100000,'Original ordinal99 must hide both digits')
    gate.require(wp['ordinal_frames'][255]==wp['ordinal_frames'][99],'Original narrowed-byte wrap must hide both digits')
    gate.require(wp['ordinal_frames'][0]!=wp['ordinal_frames'][1],'Negative control:lost unit digit')
    gate.require(wp['ordinal_frames'][8]!=wp['ordinal_frames'][9],'Negative control:lost tens transition')
    return dict(passed=True,fresh_x86=True,constructor_cases=256,unique_frames=100,position_cases=positions,
        fixture_sha256=composer.FIXTURE_SHA,original_renderer_executed=False,source_palette=True,
        payloads={k:hashlib.sha256(v).hexdigest()for k,v in payloads.items()})


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=validate()
    a.output.write_text(json.dumps(r,indent=2)+'\n');print(r)


if __name__=='__main__':main()
