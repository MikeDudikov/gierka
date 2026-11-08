"""Fresh original accelerator serialization and BaseSystemC45D/C45E envelopes."""
from pathlib import Path
import argparse,json,hashlib,struct
from tools import probe_source_key_visibility as native,validate_boss_ai_gate as gate
ROOT=gate.ROOT;FIXTURE=ROOT/'tests/fixtures/source_key_visibility.json'
SHA='470fbee7542cf8f5552447f0cf1ee24ff9e4b871a5d17e9bea3b67e9c17f033e'


def validate():
    raw=FIXTURE.read_bytes();gate.require(hashlib.sha256(raw).hexdigest()==SHA,'Source keyboard fixture differs')
    data=json.loads(raw);gate.require(native.fixture()==data,'Fresh source key bindings/envelopes differ')
    registrations=data['rows'][0]['bindings'];removed=data['rows'][-1]['bindings'];decoded=[]
    for row in registrations:
        b=bytes.fromhex(row['payload_hex']);gate.require(len(b)==74 and row['kind']==16,'Source74-byte accelerator differs')
        decoded.append(dict(key=b[4],secondary_key=b[5],pressed=[struct.unpack_from('<I',b,k)[0]for k in(26,30)],released=[struct.unpack_from('<I',b,k)[0]for k in(58,62)]))
    gate.require([d['key']for d in decoded]==[29,42,54],'Source accelerator order differs')
    for key in decoded[1:]:gate.require(key['pressed']==[0xc45d,1]and key['released']==[0xc45d,0],'Source Shift down/up message differs')
    gate.require([r['payload_hex']for r in removed]==[r['payload_hex']for r in registrations][::-1]and all(r['kind']==17 for r in removed),'Source unregister must reverse registrations')
    for row in data['rows'][1:6]+data['rows'][7:8]:
        gate.require(row['stored']==row['value']and row['forwarded'][0]['slot']==24,'Source C45D storage/dispatch differs')
        gate.require(row['forwarded'][0]['words']==[0,0,256,3,0xc45d,row['value'],0,0],'Source C45D envelope differs')
    gate.require(data['rows'][6]['stored']==1 and data['rows'][6]['forwarded']==[dict(slot=32,words=[0,0,0,0,0xc45d,0,0,0])],'Source C45E effect differs')
    gate.require(data['rows'][8]['stored']==0 and data['rows'][8]['forwarded']==[],'Source C45E gate differs')
    return dict(passed=True,fresh_x86=True,operations=len(data['rows']),accelerators=decoded,fixture_sha256=SHA,
        original_set_accelerator_executed=True,os_keyboard_polling=False,global_registry_dispatch_boundary=True,
        source_key_visibility_unity_integrated=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=validate()
    a.output.write_text(json.dumps(r,indent=2)+'\n');print(r)


if __name__=='__main__':main()
