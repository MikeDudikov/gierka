"""Tenth resource set:original0d H1110/A3 movement,turn and idle planes."""
from pathlib import Path
import argparse,json
from tools import stage_ship_movement as movement
ROOT=movement.ROOT
MANIFEST_NAME='ShipHeavyMovementManifest.json'


def compose(source_root=ROOT/'reference/raw/ancient-conquest'):
    return movement.compose(source_root,heavy=True)


def stage(source_root,project,replace_generated=False):
    payloads,metadata,_=compose(source_root)
    return movement.write_payloads(Path(project)/'Assets/Resources/ShipHeavyMovementGenerated',payloads,metadata,
                                   replace_generated=replace_generated,manifest_name=MANIFEST_NAME)


def main():
    p=argparse.ArgumentParser();p.add_argument('--source-root',type=Path,default=ROOT/'reference/raw/ancient-conquest')
    p.add_argument('--project',type=Path,default=ROOT/'Unity/AncientConquest');p.add_argument('--replace-generated',action='store_true');a=p.parse_args()
    r=stage(a.source_root,a.project,a.replace_generated)
    print(json.dumps({k:r[k]for k in('pose_count','plane_count','atlas_width','atlas_height','payloads')},indent=2))


if __name__=='__main__':main()
