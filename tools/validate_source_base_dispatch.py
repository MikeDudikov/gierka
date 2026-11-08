"""Fresh x86 comparison through original BaseSystem recipients and context reset."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
from tools import probe_source_base_dispatch as native
from tools import validate_boss_ai_gate as gate

FIXTURE = gate.ROOT / 'tests/fixtures/source_base_dispatch.json'
SHA = 'b3c30aefba0ceee812619cb3d33f5961d34c67fc3ebfbedc8f2e4d7f03776316'


def validate():
    raw = FIXTURE.read_bytes()
    gate.require(hashlib.sha256(raw).hexdigest() == SHA, 'Base dispatch fixture differs')
    data = json.loads(raw)
    gate.require(native.fixture() == data, 'Fresh BaseSystem execution differs')
    for case in data['rows']:
        previous = 0
        handlers = [0] if case['first_handler_flags'] & 1 else [0, 1]
        for row in case['operations']:
            reset = row['message'] == 0xc45e
            expected_stored = 0 if reset else row['value']
            gate.require(row['stored'] == expected_stored, 'C45E must reset actual stored state')
            delivered = case['active'] == 1 and (not reset or previous != 0)
            expected = [dict(handler=i, words=[0, 0, 256, 3, 0xc45d, expected_stored, 0, 0])
                        for i in handlers] if delivered else []
            gate.require(row['received'] == expected, 'Source handler ordering/gate/payload differs')
            gate.require(row['entries'].count('4eff00') == (2 if reset and previous else 1),
                         'Actual recursive vtable dispatch missing')
            previous = expected_stored
    for row in data['context_rows']:
        producer = row['gate'] == 0
        reset = producer and row['active'] == 1 and row['held'] != 0
        gate.require(row['root_gate'] == row['gate'], 'Root gate was mutated')
        gate.require(row['stored'] == (0 if reset else row['held']), 'Root and BaseSystem gates were conflated')
        expected = [dict(handler=i, words=[0, 0, 256, 3, 0xc45d, 0, 0, 0]) for i in (0, 1)] if reset else []
        gate.require(row['received'] == expected, 'Producer-to-recipient result differs')
        width, height = row['dimensions']
        messages = [dict(words=[0, 0, 0, 0, 0x17, None, 0, 0], route=[3, 1], rectangle=[0, 0, width, height]),
                    dict(words=[0, 0, 0, 15, 0x14a, 0, 0, 0])] if producer else []
        gate.require(row['messages'] == messages, 'Context sibling messages differ')
    mutations = {
        'wrong_virtual_recipient': [(0x59b604, struct.pack('<I', 0x4eff00), struct.pack('<I', 0x542490))],
        'lost_stored_reset': [(0x4f006e, b'\x89\x46\x20', b'\x90\x90\x90')],
        'ignored_handler_stop_bit': [(0x5420c3, b'\x01', b'\x00')],
        'inverted_root_gate': [(0x4ee90e, b'\x75', b'\x74')],
        'wrong_active_value': [(0x541fee, b'\x01', b'\x00')],
    }
    detected = []
    for name, patches in mutations.items():
        gate.require(native.fixture(patches) != data, 'Undetected x86 mutation: ' + name)
        detected.append(name)
    return dict(passed=True, fresh_x86=True, direct_operations=42, context_cases=108,
                negative_controls=detected, fixture_sha256=SHA, source_vtable='59b5e4',
                actual_recursive_recipient_executed=True, original_disk_patched=False,
                final_child_callbacks_are_boundaries=True, native_full_application=False,
                unity_integration=False, world_or_tick_executed=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = validate()
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(result)


if __name__ == '__main__':
    main()
