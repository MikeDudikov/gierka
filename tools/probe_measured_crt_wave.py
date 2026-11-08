"""Replay measured Wine32 CRT neighbor words through actual4ceab0/4cf550.

The source CRT sample and source fleet engine are separate;only the observed
signedword crosses this explicit boundary. Disconnected terrain is synthetic.
"""
from pathlib import Path
import argparse,hashlib,json
from tools import probe_queued_wave_boundary as wave
ROOT=wave.ROOT


def sample(path):
    rows=[json.loads(line)for line in Path(path).read_text().splitlines()]
    assert rows[0]==dict(kind='conditions',pointer_bits=32,heap_init_arg=0,source_threshold=1016,wave_request=1152,heap_compatibility=0)
    assert rows[-1]==dict(kind='complete',samples=256,game_entry_called=False)
    values=rows[1:-1];assert len(values)==256 and [r['sample']for r in values]==list(range(256))
    assert all(r['kind']=='wave'and r['usable']>=1152 and r['prefix_i16']==(r['prefix_u16']if r['prefix_u16']<32768 else r['prefix_u16']-65536)for r in values)
    return sorted({r['prefix_i16']for r in values})


def fixture():
    path=ROOT/'artifacts/queued-crt-context/vm-owned-pages/crt.jsonl';prefixes=sample(path);assert prefixes==[117]
    metadata=wave.queued.normal.source.membership.hover.source_metadata();cases=[]
    disconnected=[-1]*576
    for x,y in((16,2),(21,5),(19,4),(18,6),(16,4)):disconnected[y*24+x]=0
    for kind,terrain in(('mission',None),('disconnected',disconnected)):
        for prefix in(0,*prefixes):
            ui=wave.run(prefix,'ui',metadata,terrain);direct=wave.run(prefix,'fleet',metadata,terrain);assert ui==direct
            cases.append(dict(terrain=kind,adjacent_input=prefix,**ui))
    return dict(schema_version=1,original_exe_sha256=wave.queued.normal.source.pointer.gate.EXPECTED,cases=cases,
        measured_neighbor_words=prefixes,native_probe_log_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        synthetic_disconnected_map=True,native_Windows_verified=False,scope=__doc__)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();data=fixture()
    a.output.write_text(json.dumps(data,separators=(',',':'))+'\n')
    print([(c['terrain'],c['adjacent_input'],[p['actor']for p in c['state']['packets']],[r['candidate']for r in c['comparisons']])for c in data['cases']])


if __name__=='__main__':main()
