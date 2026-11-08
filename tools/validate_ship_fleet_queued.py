"""Pinned independent x86 entry traces for bounded100/2;no C#port claim."""
from pathlib import Path
import argparse,hashlib,json
from tools import probe_ship_fleet_queued as native
from tools.validate_boss_ai_gate import require
ROOT=native.ROOT;FIXTURE=ROOT/'tests/fixtures/ship_fleet_queued.json'
SHA='8d0cab94992ccedce32b39d263923107b72bf2d5ecf9b56b9f0966ce7958913a'


def load(path=None):
    raw=Path(path or FIXTURE).read_bytes();require(hashlib.sha256(raw).hexdigest()==SHA,'Queued fixture SHA differs')
    return json.loads(raw)


def compare_cases(actual,expected):
    require(len(actual)==len(expected),'Queued x86 case count differs')
    for a,b in zip(actual,expected):
        require(a['label']==b['label'],'Queued x86 case order differs')
        require(len(a['rows'])==len(b['rows']),'Queued x86 row count differs')
        for index,(x,y)in enumerate(zip(a['rows'],b['rows'])):
            require(x==y,f"Queued x86 mismatch {a['label']} row{index} {y['operation']}")


def summarize(data):
    rows=[r for c in data['cases']for r in c['rows']]
    return dict(passed=True,cases=len(data['cases']),states=len(rows),paired_state_observations=2*len(rows),tracked_function_calls=2*sum(len(r['state']['calls'])for r in rows),
        ui_shift_requests=sum(r['operation'][0]=='shift'for r in rows),route_queries=sum(r['operation'][0]=='next'for r in rows),
        work_calls=sum(r['operation'][0]=='work'for r in rows),arrival_calls=sum(r['operation'][0]=='arrival'for r in rows),
        serialized_packets=sum(len(r['state']['packets'])for r in rows),fixture_sha256=SHA,source_ui_and_fleet_engines_separate=True,
        csharp_port=False,unity_runtime_queued=False,full_ship_life=False,graphical_marker_construction=False)


def validate():
    pinned=load();fresh=native.fixture();compare_cases(fresh['cases'],pinned['cases'])
    require({k:v for k,v in fresh.items()if k!='cases'}=={k:v for k,v in pinned.items()if k!='cases'},'Queued x86 provenance differs')
    return dict(summarize(pinned),fresh_x86=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();result=validate()
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':main()
