#!/usr/bin/env python3
"""Observe source0b's eight bounded adjacent requests in a Windows Mono player.

Native whole-MoveShip traces, including actual sprite publication boundaries,
choose every expected state and source pixel plane. The diagnostic freezes
time at semantic checkpoints; this is not a complete mission or OS-input test.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import time

from PIL import Image, ImageChops

if __package__:
    from . import smoke_ship_movement as movement
else:
    import smoke_ship_movement as movement

units, menu, terrain, require = movement.units, movement.menu, movement.terrain, movement.require
ROOT = menu.REPOSITORY
FIXTURE = ROOT / 'tests/fixtures/ship_adjacent_movement.json'
FIXTURE_SHA256 = '2ffc6d70e131770dc065b252e88818e02aca203f681ea1ff373875883f8e9075'
PREFIX = '[ShipAdjacentReference] '
CASE = {'name': 'source0b-adjacent', 'requested': (9, 0), 'actual': (9, 0), 'visible_ids': (11, 12, 13)}
GOALS = ((17, 2), (17, 1), (16, 1), (15, 1), (15, 2), (15, 3), (16, 3), (17, 3))
EVENT_ORDER = ('turn-start', 'turn-published', 'turn-complete', 'reserved', 'first-pixel', 'transferred', 'arrived')
CASES = tuple({'name': 'h' + str(index), 'goal': goal, 'stop_at': None} for index, goal in enumerate(GOALS)) + (
    {'name': 'halt-turn', 'goal': GOALS[0], 'stop_at': 1},
    {'name': 'halt-reserved', 'goal': GOALS[5], 'stop_at': 1},
)
PAIR_FIELDS = {'goal', 'cell', 'world', 'published_world'}
BOOL_FIELDS = {'accepted', 'center_gate', 'complete', 'publishes_pose', 'forward_tail'}
STAGE_FIELDS = ('stage', 'call', 'counter', 'goal', 'accepted', 'cell', 'world', 'published_world', 'heading',
                'target_heading', 'state', 'frame', 'drawn_frame', 'last_tick', 'last_state_counter', 'turn_step',
                'center_gate', 'speed', 'remainder', 'deceleration', 'reserved', 'next', 'path_index', 'path_count',
                'occupied', 'complete', 'publishes_pose', 'forward_tail')
LIMITATIONS = [
    'Windows Mono player under Wine/Xvfb; native Windows11 and target i5/RTX3050Ti laptop not tested',
    'Only eight adjacent requests from source0b16,2/heading5: six source routes and two source terrain rejections',
    'Controlled wind0/heading5, owner upgrade0, quantum40 and pending_steps1; not complete mission world initialization',
    'No OS input, distant routes, combat, enemy AI, fog lifecycle or complete gameplay validated',
    'Planner at counter1 then movement at counters2.. is an explicit diagnostic schedule; full source Life may plan/move at the same counter',
    'Checkpoint holds freeze diagnostic source time; they do not establish wall-clock cadence or original pause behavior',
    'Whole1920x1080 viewport and full source0b/c/d planes at camera9,0 scale2; other seven ships remain frozen',
    'Known34-component cohort order only; no general dynamic full-world sorter',
    'Source base-palette art is a fidelity reference, not final2026art or target hardware performance proof',
    'Diagnostic Application.Quit(0) is not evidence for the product/menu Quit callback',
]


def provenance():
    result = movement.provenance()
    files = {'adjacent_qa_helper': Path(__file__).resolve(), 'native_adjacent_fixture': FIXTURE}
    for name in ('ShipAdjacentReference.cs', 'SourceShipPoseReference.cs', 'Simulation/ShipTurnProgression.cs',
                 'Simulation/ShipAdjacentMovement.cs', 'Simulation/ShipAdjacentQuery.cs',
                 'Simulation/ShipAdjacentPlanner.cs'):
        files['runtime_source:' + name] = ROOT / 'Unity/AncientConquest/Assets/AncientConquest/Runtime' / name
    for label, path in files.items():
        require(path.is_file() and not path.is_symlink(), 'Missing/symbolic adjacent evidence: ' + str(path))
        result[label] = {'path': str(path), 'bytes': path.stat().st_size, 'sha256': menu.file_sha256(path)}
    return result


def native_cases(fixture):
    cases = [case for case in fixture['cases'] if re.fullmatch(r'h[0-7]_pending1', case['label'])]
    require(len(cases) == 8 and {tuple(case['goal']) for case in cases} == set(GOALS),
            'Native adjacent fixture does not contain exactly eight distinct pending1 goals')
    by_goal = {tuple(case['goal']): case for case in cases}
    require([by_goal[goal]['accepted'] for goal in GOALS] == [True, True, False, False, True, True, True, True],
            'Native adjacent accepted/rejected cohort changed')
    for heading, goal in enumerate(GOALS):
        case = by_goal[goal]
        require(case['requested_heading'] == heading and case['source_resource'] == 'OBJ_0000000b',
                'Native adjacent request identity changed')
        require(case['scenario'] == 'source_static' and case['controlled_inputs'] == {
                'pending_steps_each_call': 1, 'wind_strength': 0, 'wind_heading': 5, 'owner_upgrade_byte': 0,
                'blocked_target_with_source0c_pointer_before_plan': False,
                'occupied_target_after_plan_with_source0c_pointer': False},
                'Native adjacent controlled conditions changed')
        require(case['trace'][0]['stamp'] == 1 and case['trace'][0]['tick'] == 0 and
                case['trace'][0]['world'] == [1028, 132] and case['trace'][0]['drawn_frame'] == 20,
                'Native adjacent initial counter/publication phase changed')
        for index, row in enumerate(case['trace']):
            require(row['tick'] == index and row['stamp'] == index + 1,
                    'Native adjacent call and source-counter relationship changed')
            require(0 <= row['drawn_frame'] < 88 and row['occupied_cell_count'] in (8, 9),
                    'Native adjacent sprite/occupancy trace exceeds diagnostic scope')
        if case['accepted']:
            require(case['native_navigation']['points'] == [[16, 2, heading], [*goal, heading]],
                    'Native adjacent planner path is not its observed two-point route')
            require(case['trace'][-1]['state'] == 0 and case['trace'][-1]['cell'] == list(goal),
                    'Native adjacent route did not arrive')
        else:
            require(len(case['trace']) == 1 and not case['active_path_hex'],
                    'Rejected native adjacent request acquired movement steps/path')
    return by_goal


def load_reference():
    fixture = units.pinned_json(FIXTURE, FIXTURE_SHA256)
    reference = movement.load_reference()
    require(fixture['original_exe_sha256'] == units.SOURCE_HASHES['installed/ancient.exe'],
            'Native adjacent trace used a different executable')
    by_goal = native_cases(fixture)
    seed = next(row for row in units.pinned_json(units.SHIP_FIXTURE, units.SHIP_FIXTURE_SHA256)['records']
                if row['instance_id'] == 11)
    require(all(case['source_payload_sha256'] == seed['payload_sha256'] for case in by_goal.values()),
            'Native adjacent trace used a different source0b seed')
    for key in ('native_trace', 'native_last_ticks', 'native_publication', '_checkpoint_cache'):
        reference.pop(key, None)
    reference.update(native_adjacent=by_goal, adjacent_fixture=fixture)
    return reference


def stage_plan(case, stop_at=None):
    require(stop_at is None or isinstance(stop_at, int) and not isinstance(stop_at, bool) and 0 <= stop_at <= 512,
            'Adjacent stop count must be0..512 or absent')
    trace = case['trace']
    result = [('initial', trace[0])]
    if not case['accepted']:
        return result + [('rejected', trace[0])]
    seen = set()
    previous = trace[0]
    for row in trace[1:]:
        if stop_at is not None and row['tick'] > stop_at:
            break
        conditions = (
            32 <= row['frame'] <= 55,
            bool(row['pose_published']) and row['state'] == 2,
            previous['state'] == 2 and row['state'] == 3,
            row['reserved'] >= 0,
            row['world'] != [1028, 132],
            row['cell'] != [16, 2],
            row['state'] == 0,
        )
        for event, condition in zip(EVENT_ORDER, conditions):
            if condition and event not in seen:
                seen.add(event)
                result.append((event, row))
        previous = row
    return result


def expected_stage(case, stage, row):
    return {'stage': stage, 'call': row['tick'], 'counter': row['stamp'], 'goal': list(case['goal']),
            'accepted': case['accepted'], 'cell': row['cell'], 'world': row['world'],
            'published_world': row['render_world'], 'heading': row['heading'], 'target_heading': row['target_heading'],
            'state': row['state'], 'frame': row['frame'], 'drawn_frame': row['drawn_frame'],
            'last_tick': row['last_frame_tick'], 'last_state_counter': row['last_state_counter'],
            'turn_step': row['turn_step'], 'center_gate': bool(row['center_gate']), 'speed': row['speed'],
            'remainder': row['remainder'], 'deceleration': row['deceleration'], 'reserved': row['reserved'],
            'next': row['next_cell'], 'path_index': row['path_index'], 'path_count': row['path_count'],
            'occupied': row['occupied_cell_count'], 'complete': bool(case['accepted'] and row['tick'] > 0 and row['state'] == 0),
            'publishes_pose': bool(row['pose_published']), 'forward_tail': bool(row['animation_tail_reached'])}


def checkpoint_reference(reference, case, stage, row):
    frame, (world_x, world_y) = row['drawn_frame'], row['render_world']
    parts = reference['poses'][frame]
    depth = max(10000, 20000 - 56 - world_y)
    require(depth > reference['ships'][13]['reference_depth'], 'Adjacent move crossed the verified source body rank')
    draws = []
    for draw in reference['draws']:
        if draw['kind'] != 'ship' or draw['instance_id'] != 11:
            draws.append(draw)
        else:
            part = parts[draw['source_index']]
            draws.append(dict(draw, name=part['name'], image=part['image'], x=world_x + part['offset_x'],
                              y=world_y + part['offset_y'], depth=21000 if part['source_index'] == 0 else depth))
    alpha = Image.new('L', (56, 56))
    for part in parts.values():
        alpha = ImageChops.lighter(alpha, part['image'].getchannel('A'))
    ship = dict(reference['ships'][11], world_pixel=(world_x, world_y), cell=tuple(row['cell']), alpha=alpha,
                frame_index=frame, reference_depth=depth)
    ship['parts'] = [draw for draw in draws if draw['kind'] == 'ship' and draw['instance_id'] == 11]
    ships = dict(reference['ships']); ships[11] = ship
    result = {key: value for key, value in reference.items() if key != '_checkpoint_cache'}
    result.update(ships=ships, draws=draws)
    result['world'] = units.compose_world(result)
    result['expected_image'] = units.expected_image(result, CASE)
    result['regions'] = units.ship_regions(result, CASE)
    result['checkpoint'] = expected_stage(case, stage, row)
    result['expected_parts'] = [{'source_index': draw['source_index'], 'sprite': draw['name'], 'order': index + 10,
                                 'position': [draw['x'], draw['y']]} for index, draw in enumerate(draws)
                                if draw['kind'] == 'ship' and draw['instance_id'] == 11]
    return result


def stage_records(log):
    result = []
    for line in log.splitlines():
        if not line.startswith(PREFIX + 'stage='):
            continue
        values = {}
        for token in line[len(PREFIX):].split(' '):
            require('=' in token, 'Malformed adjacent stage token')
            key, value = token.split('=', 1)
            require(key not in values, 'Duplicated adjacent stage field')
            if key in PAIR_FIELDS:
                require(re.fullmatch(r'-?\d+,-?\d+', value) is not None, 'Invalid adjacent pair')
                value = [int(part) for part in value.split(',')]
            elif key in BOOL_FIELDS:
                require(value in ('True', 'False'), 'Invalid adjacent boolean')
                value = value == 'True'
            elif key != 'stage':
                value = int(value)
            values[key] = value
        require(set(values) == set(STAGE_FIELDS), 'Missing/unknown adjacent stage field')
        result.append(values)
    return result


def conditions_line(case):
    return (PREFIX + 'conditions: id=0000000b; origin=16,2; goal=' + ','.join(map(str, case['goal'])) +
            '; planner=bounded-source-adjacent; planner_counter=1; wind_force=0; wind_heading=5; '
            'owner_upgrade=0; quantum_ms=40; pending_steps=1; clock=bounded-single-step; '
            'input=domain-reference; full_simulation=False')


def command_line(case):
    return (PREFIX + 'command: copied_bytes=26; target=' + ','.join(map(str, case['goal'])) +
            '; opaque_byte=255; promotion=Promoted; active_flags=128; pending_flags=0; route_byte=0; has_route=' +
            str(case['accepted']))


def completion_line(case, stop_at=None):
    if not case['accepted']:
        return PREFIX + 'rejected: goal=' + ','.join(map(str, case['goal'])) + '; calls=0; counter=1; no_route=True; frozen=True'
    last = case['trace'][-1]
    if stop_at is not None and stop_at < last['tick']:
        row = case['trace'][stop_at]
        return PREFIX + f"halted: calls={row['tick']}; counter={row['stamp']}; diagnostic_only=True"
    return (PREFIX + 'complete: goal=' + ','.join(map(str, case['goal'])) +
            f"; calls={last['tick']}; counter={last['stamp']}; frame={last['frame']}; drawn_frame={last['drawn_frame']}" +
            '; frozen_after_arrival=True; idle_rng=False')


def validate_stage_log(log, reference, case, checkpoints, *, complete=False, stop_at=None):
    require('Exception' not in log and PREFIX + 'failed' not in log, 'Adjacent player reported an exception/failure')
    command_seen = False
    for label, expected in (('conditions:', conditions_line(case)), ('command:', command_line(case))):
        lines = [line for line in log.splitlines() if line.startswith(PREFIX + label)]
        if label == 'command:' and not complete:
            require(lines in ([], [expected]), 'Duplicated/invalid adjacent ' + label)
            command_seen = bool(lines)
        else:
            require(lines == [expected], 'Missing/duplicated/invalid adjacent ' + label)
            if label == 'command:':
                command_seen = True
    records = stage_records(log)
    expected_names = list(checkpoints)
    names = [record['stage'] for record in records]
    require(not names or command_seen, 'Adjacent checkpoint precedes its command')
    require(names == expected_names[:len(names)] and len(names) <= len(expected_names),
            'Missing, duplicated or unordered adjacent checkpoint')
    for record in records:
        require(record == checkpoints[record['stage']]['checkpoint'],
                'Adjacent checkpoint differs from pinned native state: ' + record['stage'])
    pattern = re.compile(re.escape(PREFIX) + r'part: stage=([a-z-]+); source_index=(\d+); sprite=([^;]+); order=(-?\d+); position=(-?\d+),(-?\d+)')
    parts = {name: [] for name in names}
    current_stage = None
    for line in log.splitlines():
        if line.startswith(PREFIX + 'stage='):
            current_stage = line.split('stage=', 1)[1].split(' ', 1)[0]
        if not line.startswith(PREFIX + 'part:'):
            continue
        match = pattern.fullmatch(line)
        require(match is not None, 'Malformed adjacent renderer part declaration')
        name, index, sprite, order, x, y = match.groups()
        require(name in parts and name == current_stage, 'Adjacent renderer part precedes/leaves its stage')
        parts[name].append({'source_index': int(index), 'sprite': sprite, 'order': int(order), 'position': [int(x), int(y)]})
    for index, name in enumerate(names):
        expected, actual = checkpoints[name]['expected_parts'], parts[name]
        require(len({part['source_index'] for part in actual}) == len(actual), 'Duplicate adjacent part declaration')
        require(all(part in expected for part in actual), 'Adjacent part differs from native pose/order/anchor')
        if complete or index < len(names) - 1:
            require(sorted(actual, key=lambda part: part['source_index']) == sorted(expected, key=lambda part: part['source_index']),
                    'Missing adjacent renderer part declaration')
    if complete:
        require(names == expected_names, 'Incomplete adjacent checkpoint sequence')
        endings = [line for line in log.splitlines() if any(line.startswith(PREFIX + label)
                   for label in ('complete:', 'halted:', 'rejected:'))]
        require(endings == [completion_line(case, stop_at)], 'Missing/invalid adjacent ending')
        row = case['trace'][min(stop_at, len(case['trace']) - 1) if stop_at is not None else -1]
        cleanup = f"Mission unit reference cleanup: claimed_released={row['occupied_cell_count']}; visual_refs_cleared=True"
        require([line for line in log.splitlines() if line.startswith('Mission unit reference cleanup:')] == [cleanup],
                'Adjacent run did not release its native source claims and visual references')
        require(movement.DIAGNOSTIC_EXIT in log, 'Adjacent timed diagnostic exit marker missing')
    return {'stages': records, 'parts': parts}


frame_metrics = movement.frame_metrics


def capture_checkpoint(player, environment, output, player_log, reference, case, current, checkpoints, stop_at):
    """Fence presentation inside the same1.25s hold; never accept another stage."""
    attempts = []
    started = time.monotonic()
    deadline = started + 1.0
    while True:
        require(player.poll() is None, 'Player exited while awaiting adjacent presentation')
        before = validate_stage_log(terrain.read_log(player_log), reference, case, checkpoints, stop_at=stop_at)
        before_names = [row['stage'] for row in before['stages']]
        require(before_names and before_names[-1] == current and len(before['parts'][current]) == 3,
                'Adjacent checkpoint changed before capture: ' + current)
        path = menu.capture(environment, output, f'{current}-attempt-{len(attempts) + 1:02d}')
        with Image.open(path) as image:
            rgb = image.convert('RGB')
            passed, metrics = frame_metrics(rgb, checkpoints[current]['expected_image'], checkpoints[current]['regions'])
            stale = []
            if not passed:
                raw = rgb.tobytes()
                for name in checkpoints:
                    if name == current:
                        break
                    if raw == checkpoints[name]['expected_image'].tobytes():
                        stale.append(name)
        after_log = terrain.read_log(player_log)
        after = validate_stage_log(after_log, reference, case, checkpoints, stop_at=stop_at)
        elapsed = time.monotonic() - started
        attempts.append({'screenshot': path.name, 'elapsed_seconds': elapsed, 'metrics': metrics,
                         'observed_stages_before': before_names,
                         'observed_stages_after': [row['stage'] for row in after['stages']],
                         'exact_previous_checkpoint_matches': stale})
        menu.write_json(output / (current + '-attempts.json'), attempts)
        require(before == after, 'Adjacent fields/stage changed during capture: ' + current)
        require(elapsed <= 1.0, 'Adjacent presentation exceeded1second within its1.25second hold: ' + current)
        if passed:
            menu.write_json(output / (current + '-metrics.json'), metrics)
            return {'screenshot': path.name, 'metrics': metrics, 'capture_seconds': elapsed,
                    'presentation_attempt_count': len(attempts), 'failed_presentation_attempt_count': len(attempts) - 1,
                    'presentation_attempts': attempts, 'observed_stage_before': current, 'observed_stage_after': current,
                    'presentation_deadline_seconds': 1.0, 'first_attempt_failed': not attempts[0]['metrics']['matched']}
        require(time.monotonic() < deadline, 'Adjacent framebuffer persistently differs during checkpoint: ' + current)
        time.sleep(.02)


def observe(player, environment, output, player_log, reference, case, checkpoints, stop_at):
    captured = {}
    deadline = time.monotonic() + 50
    while True:
        log = terrain.read_log(player_log)
        if conditions_line(case) not in log:
            require(player.poll() is None and time.monotonic() < deadline and 'Exception' not in log,
                    'Adjacent conditions did not follow bootstrap readiness')
            time.sleep(.02)
            continue
        parsed = validate_stage_log(log, reference, case, checkpoints, stop_at=stop_at)
        names = [row['stage'] for row in parsed['stages']]
        if names:
            current = names[-1]
            for name in names[:-1]:
                require(name in captured, 'Missed adjacent capture checkpoint: ' + name)
            if current not in captured and len(parsed['parts'][current]) == 3:
                captured[current] = capture_checkpoint(player, environment, output, player_log, reference, case,
                                                       current, checkpoints, stop_at)
                menu.write_json(output / 'captures.json', captured)
        if player.poll() is not None:
            break
        require(time.monotonic() < deadline, 'Adjacent player did not exit in50seconds')
        time.sleep(.02)
    require(player.wait(timeout=10) == 0, 'Adjacent diagnostic did not exit0')
    require(set(captured) == set(checkpoints), 'Not all required adjacent checkpoints were captured')
    parsed = validate_stage_log(terrain.read_log(player_log), reference, case, checkpoints, complete=True, stop_at=stop_at)
    return captured, parsed


def run_case(output, baseline, reference, specification):
    output = Path(output).resolve()
    require(not output.exists(), 'Select a fresh adjacent output directory')
    output.mkdir(parents=True)
    case = reference['native_adjacent'][tuple(specification['goal'])]
    stop_at = specification['stop_at']
    checkpoints = {stage: checkpoint_reference(reference, case, stage, row) for stage, row in stage_plan(case, stop_at)}
    for stage, checkpoint in checkpoints.items():
        checkpoint['expected_image'].save(output / (stage + '-expected.png'), compress_level=0)
    environment = os.environ.copy()
    environment['DISPLAY'] = menu.DISPLAY
    environment['LD_LIBRARY_PATH'] = str(menu.TOOLCHAIN / 'usr/lib/x86_64-linux-gnu')
    player_log = output / 'player.log'
    goal_x, goal_y = specification['goal']
    launch = ['bash', str(terrain.LAUNCHER), str(terrain.EXECUTABLE), '-logFile', str(player_log),
              '--ship-adjacent-reference', '--ship-adjacent-target-x', str(goal_x), '--ship-adjacent-target-y', str(goal_y),
              '--terrain-origin-x', '9', '--terrain-origin-y', '0', '--terrain-reference-exit-after', '1']
    if stop_at is not None:
        launch.extend(('--ship-adjacent-stop-at', str(stop_at)))
    metadata = {'launch': launch, 'provenance': baseline, 'goal': list(specification['goal']),
                'requested_heading': case['requested_heading'], 'accepted': case['accepted'], 'stop_at_call': stop_at,
                'conditions': conditions_line(case), 'camera_origin_cells': [9, 0], 'display_size': list(terrain.SIZE),
                'scale': 2, 'input_injection': 'none', 'stage_harness_hold_seconds': 1.25,
                'presentation_deadline_seconds': 1.0, 'presentation_retry_poll_seconds': .02,
                'expected_native_states': [checkpoint['checkpoint'] for checkpoint in checkpoints.values()],
                'thresholds': {'global_mean_rgb_error_strictly_below': 1, 'global_bad_pixel_fraction_at_most': .005,
                               'global_max_channel_error_at_most': 4, 'each_full_ship_plane_mean_rgb_error_strictly_below': 1,
                               'each_source_coverage_mean_rgb_error_strictly_below': 1,
                               'each_full_ship_plane_max_channel_error_at_most': 4}, 'limitations': LIMITATIONS}
    menu.write_json(output / 'launch.json', metadata)
    player = xvfb = wine_log = xvfb_log = None
    failure = None; cleanup = []; stage = 'preflight'; started = time.monotonic(); report = None
    try:
        require(provenance() == baseline, 'Build/source changed during adjacent preflight')
        require(not menu.DISPLAY_SOCKET.exists(), 'Display79 already owned; refuse reuse')
        stage = 'Xvfb startup'; xvfb_log = (output / 'xvfb.log').open('w')
        xvfb = subprocess.Popen([str(menu.TOOLCHAIN / 'usr/bin/Xvfb'), menu.DISPLAY, '-screen', '0', '1920x1080x24',
                                 '-nolisten', 'tcp', '-ac'], env=environment, stdout=xvfb_log, stderr=subprocess.STDOUT)
        menu.wait_for_display(xvfb)
        stage = 'player startup'; wine_log = (output / 'wine-launch.log').open('w')
        player = subprocess.Popen(launch, cwd=terrain.EXECUTABLE.parent, env=environment,
                                  stdout=wine_log, stderr=subprocess.STDOUT)
        window = units.wait_for_ready(player, environment, player_log)
        stage = 'fullscreen geometry'; geometry = menu.xdotool(environment, 'getwindowgeometry', '--shell', window)
        (output / 'geometry.txt').write_text(geometry + '\n')
        values = dict(line.split('=', 1) for line in geometry.splitlines() if '=' in line)
        require(tuple(int(values[key]) for key in ('X', 'Y', 'WIDTH', 'HEIGHT')) == (0, 0, *terrain.SIZE),
                'Adjacent player does not fill1920x1080')
        units.validate_log(terrain.read_log(player_log), CASE, reference)
        stage = 'native checkpoints and actual framebuffer'
        captures, parsed = observe(player, environment, output, player_log, reference, case, checkpoints, stop_at)
        require(provenance() == baseline, 'Build/source changed during adjacent run')
        cleanup_row = case['trace'][min(stop_at, len(case['trace']) - 1) if stop_at is not None else -1]
        report = dict(metadata, passed=True, geometry=geometry, captures=captures, native_stage_log=parsed, exit_code=0,
                      source_claims_released=cleanup_row['occupied_cell_count'], elapsed_seconds=time.monotonic() - started,
                      player_log_sha256=menu.file_sha256(player_log),
                      screenshots={path.name: menu.file_sha256(path) for path in sorted(output.glob('*.png'))})
    except Exception as error:
        failure = error
    finally:
        for process, label in ((player, 'player'), (xvfb, 'Xvfb')):
            issue = menu.stop_owned_process(process, label)
            if issue:
                cleanup.append(issue)
        for stream in (wine_log, xvfb_log):
            if stream is not None:
                stream.close()
    if cleanup:
        menu.write_json(output / 'cleanup-failure.json', cleanup)
        if failure is None:
            failure = RuntimeError('Could not stop own adjacent process'); stage = 'cleanup'
    if failure is not None:
        menu.write_json(output / 'failure.json', dict(metadata, passed=False, stage=stage,
                        failure_type=type(failure).__name__, failure=str(failure)))
        raise failure
    report['player_returncode_after_cleanup'] = player.returncode
    menu.write_json(output / 'report.json', report)
    return report


def run_smoke(output, selected=None):
    output = Path(output).resolve()
    require(not output.exists(), 'Select a fresh adjacent output directory')
    reports = []
    specifications = [case for case in CASES if selected is None or case['name'] in selected]
    require(specifications and (selected is None or len(specifications) == len(selected) == len(set(selected))),
            'Unknown, duplicated or empty adjacent case selection')
    output.mkdir(parents=True)
    try:
        baseline, reference = provenance(), load_reference()
        for specification in specifications:
            reports.append(run_case(output / specification['name'], baseline, reference, specification))
        require(provenance() == baseline, 'Build/source changed between adjacent cases')
        report = {'passed': True, 'provenance': baseline, 'cases': reports,
                  'case_count': len(reports), 'capture_count': sum(len(case['captures']) for case in reports),
                  'limitations': LIMITATIONS}
        menu.write_json(output / 'report.json', report)
        return report
    except Exception as error:
        menu.write_json(output / 'failure.json', {'passed': False, 'completed_cases': len(reports),
                        'failure_type': type(error).__name__, 'failure': str(error), 'limitations': LIMITATIONS})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', action='append', choices=[case['name'] for case in CASES])
    args = parser.parse_args(argv)
    report = run_smoke(args.output, args.case)
    print(json.dumps({'passed': report['passed'], 'output': str(args.output.resolve()),
                      'case_count': report['case_count'], 'capture_count': report['capture_count']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
