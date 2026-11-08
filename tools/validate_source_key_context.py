"""Validate source4ee900 producer,including negative gates and x86 byte mutations."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
from tools import probe_source_key_context as native
from tools import validate_boss_ai_gate as gate

ROOT = gate.ROOT
FIXTURE = ROOT / 'tests/fixtures/source_key_context.json'
SHA = 'd62e5d4304a9327aa5f50fbf384c664f2adc0a20830970a6c9eac91321c5ff0e'


def validate():
    raw = FIXTURE.read_bytes()
    gate.require(hashlib.sha256(raw).hexdigest() == SHA, 'Source context fixture differs')
    data = json.loads(raw)
    gate.require(native.fixture() == data, 'Fresh source context producer differs')
    for row in data['rows']:
        if row['gate'] != 0:
            gate.require(row['messages'] == [], 'Nonzero source context gate emitted messages')
            continue
        width, height = row['dimensions']
        expected = [
            dict(route=[3, 1], words=[0, 0, 0, 0, 0x17, None, 0, 0], rectangle=[0, 0, width, height]),
            dict(route=None, words=[0, 0, 0, 0, 0xc45e, 0, 0, 0]),
            dict(route=None, words=[0, 0, 0, 15, 0x14a, 0, 0, 0]),
        ]
        gate.require(row['messages'] == expected, 'Source context message order/payload differs')
    mutations = {
        'inverted_gate': [(0x4ee90e, b'\x75', b'\x74')],
        'swapped_message_codes': [
            (0x4ee93b, struct.pack('<I', 0xc45e), struct.pack('<I', 0x14a)),
            (0x4ee954, struct.pack('<I', 0x14a), struct.pack('<I', 0xc45e)),
        ],
        'lost_group15': [(0x4ee94a, struct.pack('<I', 15), bytes(4))],
    }
    detected = []
    for name, patches in mutations.items():
        mutant = native.fixture(patches)
        gate.require(mutant != data, 'Source context mutation escaped:' + name)
        detected.append(name)
    return dict(passed=True, fresh_x86=True, cases=len(data['rows']),
                messages=sum(len(row['messages']) for row in data['rows']),
                negative_controls=detected, fixture_sha256=SHA,
                native_recipient_execution=False, csharp_integration=False,
                tick_or_world_executed=False, dimensions_are_source_input=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = validate()
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(result)


if __name__ == '__main__':
    main()
