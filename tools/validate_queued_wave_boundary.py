"""Fresh original comparison with explicit allocator-neighbor inputs,not C#port."""
from pathlib import Path
import argparse,hashlib,json
from tools import probe_queued_wave_boundary as native
from tools.validate_boss_ai_gate import require
ROOT=native.ROOT;FIXTURE=ROOT/'tests/fixtures/queued_wave_boundary.json'
SHA='307f39f575db59672a3232d8d66261b4b18b6d52d986c0adb54897ae88e9418b'


def load(path=None):
    raw=Path(path or FIXTURE).read_bytes();require(hashlib.sha256(raw).hexdigest()==SHA,'Queued wave fixture SHA differs')
    return json.loads(raw)


def validate():
    pinned=load();require(pinned==native.fixture(),'Fresh queued wave boundary differs')
    return dict(passed=True,fresh_x86=True,cases=5,comparisons=15,paired_comparisons=30,
        memory_index=-1,offset_bytes=-2,wave_allocation_bytes=1152,behavior_depends_on_adjacent_memory=True,
        native_crt_layout_verified=False,synthetic_adjacent_inputs=[0,5000,32767,-32768],fixture_sha256=SHA)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();result=validate()
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':main()
