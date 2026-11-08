"""Separate VM/control/probe outcomes and verify measured-word x86 replays."""
from pathlib import Path
import argparse,hashlib,json,re
from tools import probe_measured_crt_wave as native
from tools.validate_boss_ai_gate import require
ROOT=native.ROOT;FIXTURE=ROOT/'tests/fixtures/measured_crt_wave.json'
SHA='fda96fcd9758c18c716b9f664737564145124ad131957029e7115dbf6d20ce8d'


def load(path=None):
    raw=Path(path or FIXTURE).read_bytes();require(hashlib.sha256(raw).hexdigest()==SHA,'Measured CRT fixture SHA differs')
    return json.loads(raw)


def inspect_vm(directory):
    directory=Path(directory);serial=(directory/'serial.log').read_text();host=json.loads((directory/'host-status.json').read_text())
    ia32='IA32_PROBE_OK'in serial and 'IA32_EXIT=0'in serial
    c=re.search(r'^CONTROL32_EXIT=(\d+)$',serial,re.M);crt=re.search(r'^CRT_EXIT=(\d+)$',serial,re.M)
    control=c is not None and c[1]=='0'and(directory/'control32.stdout').read_text().strip()=='PE32_CONTROL_OK'
    passed=False;words=[]
    if control and crt is not None and crt[1]=='0':
        words=native.sample(directory/'crt.jsonl');passed=True
    return dict(passed=passed,ia32_passed=ia32,pe32_control_passed=control,control_exit=None if c is None else int(c[1]),
        crt_exit=None if crt is None else int(crt[1]),neighbor_words=words,qemu_exit=host['qemu_exit_code'],host_timeout=host['timed_out'])


def validate():
    pinned=load();require(pinned==native.fixture(),'Fresh measured CRT wave replay differs')
    out=ROOT/'artifacts/queued-crt-context';runs={name:inspect_vm(out/name)for name in('vm-run','vm-desktop','vm-crt-pages','vm-topdown','vm-owned-pages','vm-owned-repeat')}
    for name in('vm-owned-pages','vm-owned-repeat'):
        r=runs[name];require(r['passed']and r['ia32_passed']and r['qemu_exit']==0 and not r['host_timeout']and r['neighbor_words']==[117],'Native original CRT run did not pass:'+name)
    require(not runs['vm-run']['passed']and not runs['vm-run']['pe32_control_passed'],'Timeout incorrectly passed')
    require(runs['vm-desktop']['pe32_control_passed']and not runs['vm-desktop']['passed'],'Mapping failure incorrectly passed')
    return dict(passed=True,fresh_x86_replay=True,vm_runs=runs,native_crt_samples=512,native_crt_words=[117],replay_cases=4,replay_comparisons=12,paired_comparisons=24,
        original_crt_entrypoints=['0x58ec07','0x589bf5','0x589bc6'],original_heap_init_arg=0,original_game_entry_called=False,
        native_windows_verified=False,full_game_heap_history_verified=False,fixture_sha256=SHA)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();result=validate()
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':main()
