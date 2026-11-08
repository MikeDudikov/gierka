"""Re-execute original export/restore and compare subsequent Work with native control."""
import hashlib,json
from pathlib import Path
from tools import probe_ship_state_restore as native
ROOT=Path(__file__).resolve().parents[1]
SHA='dd8827df6031a4f080f48cca0e042cd1135fd1aa9b3b513172d980508d6609e0'


def load(path=None):
    raw=Path(path or ROOT/'tests/fixtures/ship_state_restore.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SHA:raise AssertionError('Restore fixture SHA differs')
    return json.loads(raw)


def check(data):
    discarded=0
    for c in data['cases']:
        assert c['before']==c['restored']
        assert c['exported_gate']==0 and c['imported_gate']==c['gate']
        assert len(c['rows'])==32
        if c['gate']==0:assert c['rows'][0]['target']==[16,4]
        elif c['rows'][0]['target']==c['before']['target']:discarded+=1
        assert '0x50cb80'in c['boundaries']and '0x50d4f0'in c['boundaries']
    assert discarded==20
    return dict(cases=len(data['cases']),future_states=sum(len(c['rows'])for c in data['cases']),discarded_new_move=discarded,
        unmodified_buffers=sum(c['gate']==0 for c in data['cases']),patched_buffers=sum(c['gate']!=0 for c in data['cases']))


def validate():
    d=load();assert d==native.fixture(),'Fresh original restore differs'
    return dict(passed=True,fresh_x86=True,native_controls=True,**check(d),production_changed=False)
