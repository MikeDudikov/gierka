"""Explicit C45E context replay at held50;actual InputSystem keys and unchanged x86 world.

This exercises the source-context entry point,not Unity focus callbacks or
physical OS activation. No screenshot capture or full-game claim.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
from tools import smoke_pending_queued_input as pending
from tools import probe_context_marker_lifecycle as native

ROOT = pending.ROOT
shared = pending.shared
require = pending.require
FIXTURE = ROOT / 'tests/fixtures/source_context_markers.json'
SHA = '5ba26f428a5a24ca595868c8ca0e7e1a03a12d90e3f4fe1013b32236097f31a4'
CONTEXT_STAGES = ['context-blocked', 'context-inactive', 'context-reset', 'context-repeat']
CONTEXT_EVENTS = [(50, 1, 1, 1, 1, False), (50, 0, 0, 1, 1, False),
                  (50, 0, 1, 1, 0, True), (50, 0, 1, 0, 0, False)]


def source_lifecycle():
    raw = FIXTURE.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == SHA, 'Source context-marker fixture differs')
    data = json.loads(raw)
    require(native.fixture() == data, 'Fresh producer-to-fleet source execution differs')
    rows = data['rows']
    require([[p['marker'] is not None for p in r['state']['route']['points']] for r in rows]
            == [[True, True], [True, True], [False, False], [False, False]], 'Source marker reset/gates differ')
    require([r['stored'] for r in rows] == [1, 1, 0, 0], 'Source stored-key context differs')
    require([len(r['forwarded']) for r in rows] == [0, 0, 1, 0], 'Source reset was duplicated/lost')
    require(rows[2]['forwarded'] == [[0, 0, 256, 3, 0xc45d, 0, 0, 0]], 'Actual fleet received a different reset envelope')
    first = rows[0]['state']
    for row in rows:
        state = row['state']
        require(state['task'] == first['task'] and state['membership'] == first['membership'], 'Source reset changed task/membership')
        require(state['age'] == first['age'] and state['events'] == first['events'], 'Source reset changed group age/events')
        require(state['route']['members'] == first['route']['members'], 'Source reset changed route member records')
        require([p['cell'] for p in state['route']['points']] == [p['cell'] for p in first['route']['points']], 'Source reset erased logical points')
        require(state['packets'] == [], 'Source graphics reset emitted ship commands')
    return data


def reference(position=0, right_shift=False):
    source_lifecycle()
    ref = pending.reference(position, source_keys=True)
    original = list(ref['stage_order'])
    stages = []
    for stage in original:
        stages.append(stage)
        if stage == 'tick-50':
            stages.extend(CONTEXT_STAGES)
    for key in ('checkpoints', 'contexts', 'taskstates', 'markers', 'selections'):
        values = ref[key]
        for stage in CONTEXT_STAGES:
            value = values['tick-50']
            if key == 'checkpoints':
                value = dict(value, queue=[dict(row, stage=stage) for row in value['queue']])
            elif key == 'markers' and stage in ('context-reset', 'context-repeat'):
                value = []
            values[stage] = value
        ref[key] = {stage: values[stage] for stage in stages if stage in values}
    ref['stage_order'] = stages
    physical_events = ref['key_events']
    ref['key_controls'] = [('RightShift' if right_shift else 'LeftShift', r[1]) for r in physical_events]
    ref['key_events'] = [physical_events[0], (50, False, 0, False), *physical_events[1:]]
    ref['context_events'] = CONTEXT_EVENTS
    return ref


def validate_log(log, ref):
    rows, done = shared.validate_log(log, ref)
    events = [(*map(int, m.groups()[:5]), m[6] == 'True') for m in re.finditer(
        r'^\[ShipFleetWaypoint\] context: counter=(\d+); gate=(\d+); registration=(\d+); before=(\d+); stored=(\d+); emitted=(True|False)$', log, re.M)]
    require(events == ref['context_events'][:len(events)], 'Source context gates/state/order differ')
    if done:
        require(events == ref['context_events'], 'Missing source context observations')
    return rows, done


def negative_controls(log, ref):
    validate_log(log, ref)
    detected = pending.negative_controls(log, ref)
    mutations = {
        'lost_context_record': re.sub(r'^\[ShipFleetWaypoint\] context: [^\n]*\n', '', log, count=1, flags=re.M),
        'wrong_context_gate': log.replace('context: counter=50; gate=1; registration=1;', 'context: counter=50; gate=0; registration=1;', 1),
        'context_advanced_tick': log.replace('context: counter=50;', 'context: counter=51;', 1),
        'reset_kept_key_state': log.replace('before=1; stored=0; emitted=True', 'before=1; stored=1; emitted=True', 1),
    }
    for name, mutant in mutations.items():
        require(mutant != log, 'Inactive context checker mutation: ' + name)
        try:
            validate_log(mutant, ref)
        except (AssertionError, RuntimeError, ValueError):
            detected.append(name)
        else:
            raise AssertionError('Context checker accepted: ' + name)
    return detected


def run(output, position=0, right_shift=False):
    ref = reference(position, right_shift)
    order = [11, 12, 13]
    order.insert(position, 'fleet')
    result = pending.control.run(output, reference_override=ref,
        extra_args=('--ship-pointer-fleet-world', '--ship-fleet-world-registration', ','.join(map(str, order)),
                    '--ship-fleet-wave-prefixes', '117,117,117', '--ship-pointer-fleet-pending-queued-replay',
                    '--ship-pointer-source-context-replay', *(('--ship-pointer-right-shift-replay',) if right_shift else ())),
        extra_provenance=(Path(__file__), FIXTURE, Path(native.__file__), Path(pending.__file__), Path(shared.__file__),
                          ROOT / 'Unity/AncientConquest/Assets/AncientConquest/Runtime/Simulation/SourceRouteKeyVisibility.cs',
                          ROOT / 'Unity/AncientConquest/Assets/AncientConquest/Runtime/ShipPointerReference.cs',
                          ROOT / 'Unity/AncientConquest/Assets/AncientConquest/Runtime/ShipFleetMoveInputReplay.cs'),
        log_validator=validate_log, scope_override=__doc__)
    result.update(context_events=len(CONTEXT_EVENTS), key_envelopes=len(ref['key_events']),
                  key_control_events=len(ref['key_controls']), right_shift_replay=right_shift,
                  marker_checkpoint_reads=sum(map(len, ref['markers'].values())),
                  fleet_position=position, explicit_source_context=True, physical_activation=False,
                  wave_prefixes=[117] * 3, constant_controlled_memory_profile=True, image_capture=False,
                  negative_controls=negative_controls((Path(output) / 'player.log').read_text(), ref))
    pending.control.menu.write_json(Path(output) / 'report.json', result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--fleet-position', type=int, choices=(0, 3), default=0)
    parser.add_argument('--right-shift', action='store_true')
    args = parser.parse_args()
    result = run(args.output, args.fleet_position, args.right_shift)
    print({k: result[k] for k in ('passed', 'checkpoints', 'actor_rows', 'publications', 'context_events', 'exit_code')})


if __name__ == '__main__':
    main()
