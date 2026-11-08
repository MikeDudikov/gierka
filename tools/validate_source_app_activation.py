"""Validate original activation ordering through C45E with x86 negative controls."""
from pathlib import Path
import argparse
import hashlib
import json
from tools import probe_source_app_activation as native
from tools import validate_boss_ai_gate as gate

FIXTURE = gate.ROOT / 'tests/fixtures/source_app_activation.json'
SHA = '3adb0d50be439d43c942aa32b66735a97336b4c75409b9322532f26119e0db17'


def validate():
    raw = FIXTURE.read_bytes()
    gate.require(hashlib.sha256(raw).hexdigest() == SHA, 'App activation fixture differs')
    data = json.loads(raw)
    gate.require(native.fixture() == data, 'Fresh AppProc execution differs')
    for row in data['rows']:
        active = row['activity'] != 0
        producer = not active and row['gate'] == 0
        reset = producer and row['registration'] == 1 and row['held'] != 0
        held = 0 if reset else row['held']
        gate.require(row['stored'] == held and row['root_gate'] == row['gate'], 'Activation key/gate state differs')
        gate.require(row['result'] == 0 and row['active'] == int(active), 'Activation result/flag differs')
        flags = (0xa5a5ffff & ~0x100) if active else 0xa5a5ffff
        gate.require(row['graphics_flags'] == (flags if row['graphics'] else None), 'Graphics activity bit differs')
        services = []
        if active and row['scene']:
            services.append(dict(kind='scene-restore', window=0x10203040, rectangle_is_app=True, mode=0))
        services += [dict(kind='LoadCursorA', resource=0x835 if active else 0x7f00, instance=0x400000),
                     dict(kind='SetCursor', cursor=0x12345678, active=int(active), held=held)]
        gate.require(row['services'] == services, 'Activation service order/parameters differ')
        received = [dict(handler=i, words=[0, 0, 256, 3, 0xc45d, 0, 0, 0]) for i in (0, 1)] if reset else []
        gate.require(row['received'] == received, 'Activation reset envelope/order differs')
        messages = [dict(words=[0, 0, 0, 0, 0x17, None, 0, 0], route=[3, 1], rectangle=[0, 0, 1920, 1080]),
                    dict(words=[0, 0, 0, 15, 0x14a, 0, 0, 0])] if producer else []
        gate.require(row['messages'] == messages, 'Activation sibling message order differs')
        gate.require(row['entries'].count('4ee900') == int(not active), 'Producer must run only on deactivation')
        gate.require(row['entries'].count('4eff00') == (2 if reset else int(producer and row['registration'] == 1)),
                     'Recursive receiver lifecycle differs')
        gate.require('540b00' in row['entries'], 'Original empty decoder did not execute')
    mutations = {
        'inverted_activity_branch': [(0x4eeb31, b'\x74', b'\x75')],
        'missing_reset_producer': [(0x4eebe3, b'\xe8\x18\xfd\xff\xff', b'\x90' * 5)],
        'wrong_deactivated_flag': [(0x4eebf9, bytes(4), b'\x01\0\0\0')],
        'wrong_deactivated_cursor': [(0x4eebee, b'\x68\0\x7f\0\0', b'\x68\x35\x08\0\0')],
    }
    detected = []
    for name, patches in mutations.items():
        gate.require(native.fixture(patches) != data, 'Undetected activation mutation: ' + name)
        detected.append(name)
    return dict(passed=True, fresh_x86=True, cases=len(data['rows']), fixture_sha256=SHA,
                negative_controls=detected, source_message='WM_ACTIVATEAPP/1C',
                actual_context_producer_and_recipient_executed=True,
                physical_os_events_executed=False, world_or_tick_executed=False,
                unity_lifecycle_integrated=False, audio_and_directdraw_configuration_disabled=True,
                cursor_imports_and_scene_restore_are_boundaries=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = validate()
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(result)


if __name__ == '__main__':
    main()
