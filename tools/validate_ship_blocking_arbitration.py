"""Source-only blocking arbitration evidence;does not widen runtime support."""
from pathlib import Path
import hashlib,json
from tools import probe_ship_blocking_arbitration as native
ROOT=Path(__file__).resolve().parents[1]
SHA='4a96f382f5cd7ebc893850abc689b1492247de7e600243cbb6040f06a8deed82'


def load(path=None):
    raw=Path(path or ROOT/'tests/fixtures/ship_blocking_arbitration.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SHA:raise AssertionError('Blocking arbitration fixture SHA differs')
    return json.loads(raw)


def check(d):
    cancelled=discarded=stopped=0
    for c in d['cases']:
        before,after,promoted=c['before'],c['after'],c['promoted']
        assert after['target']==before['target']and after['claims']==before['claims']
        blocking=c['gate']!=0 and before['active']&128
        if blocking:
            cancelled+=1;assert c['arbitration_trace']==['0x4abe50','0x4abc60','0x4a6330']
            if c['pending_input']==128:
                discarded+=1;assert after['pending']==after['deferred']==0
                assert promoted['target']==before['target']
            if not c['same_last_plan_counter']and before['state']in(2,3):
                stopped+=1;assert after['state']==0
            if not c['same_last_plan_counter']and before['state']in(4,5):
                stopped+=1;assert after['state']==1 and after['cache']==[]
        else:
            assert c['arbitration_trace']==['0x4abe50']
        if c['same_last_plan_counter']:assert after['state']==before['state']
    assert discarded>0 and stopped>0
    return dict(cases=len(d['cases']),cancelled=cancelled,discarded_new_move=discarded,physical_stop=stopped)


def validate():
    d=load();assert d==native.fixture(),'Fresh source arbitration differs'
    origin=native.gate_initialization();assert origin==json.loads((ROOT/'artifacts/blocking-arbitration/constructor-gate-writes.json').read_text())
    assert set(origin['final'].values())=={0}
    return dict(passed=True,fresh_x86=True,**check(d),constructor_writes=len(origin['writes']),runtime_changed=False)
