#!/usr/bin/env python3
"""Compare actual Unity ship-only world queries with original49a580 and source art.

Scripted source0b movement supplies frozen poses/claims. No pointer input,
selection, fog or complete mission picking is exercised.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import time
from PIL import Image

if __package__:
    from . import smoke_ship_order as order
    from . import probe_ship_world_picker as native
    from . import probe_ship_pointer_mask as mask_source
else:
    import smoke_ship_order as order
    import probe_ship_world_picker as native
    import probe_ship_pointer_mask as mask_source

menu, terrain, units, require = order.menu, order.terrain, order.units, order.require
ROOT = menu.REPOSITORY
PREFIX = '[ShipPickingReference] '
MASK_MANIFEST = ROOT / 'Unity/AncientConquest/Assets/Resources/ShipPickingGenerated/ShipPickingManifest.json'
MASK_MANIFEST_SHA256 = 'b3dd42407980032faab9f534bfb1d42f63572947c2d248205cbdfb9ddfd33e67'
MASK_PAYLOAD = MASK_MANIFEST.parent / 'ShipHitMasks.bytes'
MASK_PAYLOAD_SHA256 = '60f3696904880fa4c4a51da2094f96145b30859013463369d1b953aebf3ba240'
PICKER_FIXTURE = ROOT / 'tests/fixtures/ship_world_picker.json'
PICKER_FIXTURE_SHA256 = 'cee2e9f5c46c2de4db20068a78b63f3090428534f3d67948f2056abbb92a720b'
ACTOR_IDS = (11, 12, 13, 16, 39, 40, 41, 42)
CASES = order.CASES
READY = (PREFIX + 'ready: families=4; masks=96; payload_bytes=52800; payload_sha256=' + MASK_PAYLOAD_SHA256 +
         '; actors=8; fog=False; other_object_slots=empty; selection=False; mouse=False')
LIMITATIONS = order.LIMITATIONS + [
    'World query diagnostic only: no InputSystem events, player selection, cursors, healthbar or OS mouse',
    'NoFog and empty nonship object slots are explicit inputs, not defaults of a new mission',
    'Current/reservation ownership and stored frame come from the source0b order fixture; seven fleet actors remain static',
    'All seven frozen order traces have identical stored/drawn mask indices and equal physics/published positions; these runtime cases cannot discriminate those substitutions',
    'Dedicated mask native proof plus static binding review establish stored-frame and published-position choices',
    'Query coordinates may be offscreen; this is not screen-to-world or original viewport/FOV validation',
]


def provenance():
    result = order.provenance()
    files = {'picking_qa_helper': Path(__file__).resolve(), 'native_world_picker_oracle': Path(native.__file__),
             'native_mask_oracle': Path(mask_source.__file__), 'native_world_picker_fixture': PICKER_FIXTURE,
             'picking_manifest': MASK_MANIFEST, 'picking_mask_payload': MASK_PAYLOAD}
    for key, path in files.items():
        require(path.is_file() and not path.is_symlink(), 'Missing/symbolic picking evidence: ' + str(path))
        result[key] = {'path': str(path), 'bytes': path.stat().st_size, 'sha256': menu.file_sha256(path)}
    return result


def load_reference():
    reference = order.load_reference()
    manifest = units.pinned_json(MASK_MANIFEST, MASK_MANIFEST_SHA256)
    fixture = units.pinned_json(PICKER_FIXTURE, PICKER_FIXTURE_SHA256)
    require(fixture['original_exe_sha256'] == units.SOURCE_HASHES['installed/ancient.exe'] and
            fixture['query_count'] == 1206 and fixture['intercepted_callees'] == [], 'Native picker scope changed')
    require(MASK_PAYLOAD.is_file() and menu.file_sha256(MASK_PAYLOAD) == MASK_PAYLOAD_SHA256 and
            MASK_PAYLOAD.stat().st_size == 52800, 'Staged mask payload changed')
    families, metadata = mask_source.mask_inputs(ROOT / 'reference/raw/ancient-conquest')
    families = {row['family']: row for row in families if row['kind'] == 'original type18'}
    require(manifest['family_count'] == 4 and manifest['mask_count'] == 96 and
            manifest['sources'] == metadata['sources'], 'Original mask staging provenance differs')
    descriptor_families = {row['geometry_resource']: families[row['family']] for row in manifest['families']}
    require(tuple(sorted(reference['ships'])) == ACTOR_IDS, 'Actual source fleet changed')
    for ship in reference['ships'].values():
        family = descriptor_families[ship['descriptor']]
        require((family['width'], family['height']) == (ship['width'], ship['height']), 'Source mask/sprite geometry differs')
    reference.update(picking_manifest=manifest, picking_families=descriptor_families)
    return reference


def actor_rows(reference, stage, sample):
    rows = []
    for identifier in ACTOR_IDS:
        ship = reference['ships'][identifier]
        moving = identifier == 11
        rows.append({'stage': stage, 'id': identifier, 'descriptor': ship['descriptor'], 'class': 200 + ship['model'],
                     'heading': sample['heading'] if moving else ship['heading'],
                     'stored_frame': sample['frame'] if moving else ship['frame_index'],
                     'sprite': list(sample['render_world'] if moving else ship['world_pixel']),
                     'claims': list(sample['owned_cells']) if moving else [ship['cell'][1] * 24 + ship['cell'][0]]})
    return rows


def query_specs(reference, actors, sample):
    result = []
    def add(label, world, precise):
        x, y = world
        require(0 <= x < 1536 and 0 <= y < 1536, 'Canonical query left the reference world')
        result.append({'index': len(result), 'label': label, 'world': [x, y], 'cell': [x // 64, y // 64], 'precise': precise})
    for actor in actors:
        ship = reference['ships'][actor['id']]
        center = (actor['sprite'][0] + ship['width'] // 2, actor['sprite'][1] + ship['height'] // 2)
        for precise in (False, True):
            add(f"actor-{actor['id']:08x}-center-" + ('precise' if precise else 'coarse'), center, precise)
    moving = actors[0]; ship = reference['ships'][11]; x, y = moving['sprite']; w, h = ship['width'], ship['height']
    add('source0b-published-origin', (x, y), True)
    add('source0b-right-edge', (x + w, y + h // 2), True)
    add('source0b-bottom-edge', (x + w // 2, y + h), True)
    for precise in (False, True):
        add('source0b-current-center-' + ('precise' if precise else 'coarse'),
            (sample['cell'][0] * 64 + 32, sample['cell'][1] * 64 + 32), precise)
    if sample['reserved'] >= 0:
        for precise in (False, True):
            add('source0b-reservation-center-' + ('precise' if precise else 'coarse'),
                (sample['reserved'] % 24 * 64 + 32, sample['reserved'] // 24 * 64 + 32), precise)
    for label, point in (('map-top-left', (0, 0)), ('map-top-right', (1535, 0)),
                         ('map-bottom-left', (0, 1535)), ('map-bottom-right', (1535, 1535))):
        add(label, point, True)
    require(len(result) == (27 if sample['reserved'] >= 0 else 25), 'Canonical query template count changed')
    return result


def checkpoints(reference, case, stop_at=None):
    engine = native.NativeShipWorldPicker()
    result = {}
    for stage, sample in order.stage_plan(case, stop_at):
        cp = order.checkpoint_reference(reference, case, stage, sample)
        actors = actor_rows(reference, stage, sample)
        claims = {}
        for actor in actors:
            engine.set_actor(actor['id'], actor['sprite'], actor['stored_frame'], actor['heading'],
                             reference['picking_families'][actor['descriptor']], actor['class'])
            for index in actor['claims']:
                require(index not in claims, 'Two source actors claim the same cell')
                claims[index] = actor['id']
        engine.set_claims(claims)
        queries, native_queries = [], []
        for query in query_specs(reference, actors, sample):
            hit = engine.query(*query['world'], *query['cell'], query['precise'])
            require(all(call['args'] == [*query['world'], int(query['precise']), 0, 0] for call in hit['calls']),
                    'Native virtual predicate argument boundary changed')
            queries.append(dict(query, stage=stage, sample=sample['sample_index'], picked=hit['hit_id'], visited=hit['visits']))
            native_queries.append(dict(query, **hit))
        cp.update(expected_actors=actors, expected_queries=queries, native_queries=native_queries)
        result[stage] = cp
    return result


ACTOR_FIELDS = ('stage', 'id', 'descriptor', 'class', 'heading', 'stored_frame', 'sprite', 'claims')
QUERY_FIELDS = ('stage', 'sample', 'index', 'label', 'world', 'cell', 'precise', 'picked', 'visited')
COMPLETE_FIELDS = ('stage', 'sample', 'query_count', 'grid_unchanged')
ID = re.compile(r'[0-9a-f]{8}')


def decode_list(value, kind):
    if not value:
        return []
    pieces = value.split(',')
    if kind == 'ids':
        require(all(ID.fullmatch(item) for item in pieces), 'Malformed source owner ID list')
        return [int(item, 16) for item in pieces]
    require(all(re.fullmatch(r'\d+', item) for item in pieces), 'Malformed source cell index list')
    return [int(item) for item in pieces]


def picking_records(log):
    actors, queries, completions, events, current = {}, {}, {}, {}, None
    for line in log.splitlines():
        if line.startswith(order.PREFIX + 'stage='):
            current = line.split('stage=', 1)[1].split(' ', 1)[0]
        kind = ('actor' if line.startswith(PREFIX + 'actor: ') else 'query' if line.startswith(PREFIX + 'query: ')
                else 'checkpoint_complete' if line.startswith(PREFIX + 'checkpoint_complete: ') else None)
        if kind is None:
            require(not line.startswith(PREFIX) or line.startswith(PREFIX + 'ready:'), 'Unknown picking diagnostic line')
            continue
        fields = {}
        for token in line.split(': ', 1)[1].split('; '):
            require('=' in token, 'Malformed picking token')
            key, value = token.split('=', 1)
            require(key not in fields, 'Duplicate picking field')
            fields[key] = value
        require(set(fields) == set(ACTOR_FIELDS if kind == 'actor' else QUERY_FIELDS if kind == 'query' else COMPLETE_FIELDS), 'Missing/unknown picking field')
        require(fields['stage'] == current and current is not None, 'Picking row precedes/leaves source stage')
        for key in tuple(fields):
            value = fields[key]
            if key in ('stage', 'descriptor', 'label'):
                require(re.fullmatch(r'[a-zA-Z0-9_-]+', value), 'Malformed picking label')
            elif key in ('world', 'cell', 'sprite'):
                require(re.fullmatch(r'-?\d+,-?\d+', value), 'Malformed picking coordinate pair')
                fields[key] = [int(v) for v in value.split(',')]
            elif key in ('precise', 'grid_unchanged'):
                require(value in ('True', 'False'), 'Malformed picking precision')
                fields[key] = value == 'True'
            elif key == 'picked':
                require(value == 'none' or ID.fullmatch(value), 'Malformed picked owner')
                fields[key] = None if value == 'none' else int(value, 16)
            elif key == 'id':
                require(ID.fullmatch(value), 'Malformed actor owner')
                fields[key] = int(value, 16)
            elif key in ('claims', 'visited'):
                fields[key] = decode_list(value, 'ids' if key == 'visited' else 'cells')
            else:
                fields[key] = int(value)
        target = actors if kind == 'actor' else queries if kind == 'query' else completions
        target.setdefault(current, []).append(fields)
        events.setdefault(current, []).append((kind, fields))
    return actors, queries, completions, events


def validate_log(log, reference, case, expected, *, complete=False, stop_at=None):
    ready = [line for line in log.splitlines() if line.startswith(PREFIX + 'ready:')]
    require(ready == [READY], 'Missing/duplicated/invalid source picking readiness')
    parsed = order.validate_stage_log(log, reference, case, expected, complete=complete, stop_at=stop_at)
    actors, queries, completions, events = picking_records(log)
    stages = [row['stage'] for row in parsed['stages']]
    require(all(name in stages for name in actors) and all(name in stages for name in queries) and all(name in stages for name in completions), 'Picking row references unknown stage')
    for index, stage in enumerate(stages):
        wanted_actors, actual_actors = expected[stage]['expected_actors'], actors.get(stage, [])
        wanted_queries, actual_queries = expected[stage]['expected_queries'], queries.get(stage, [])
        require(actual_actors == wanted_actors[:len(actual_actors)] and len(actual_actors) <= len(wanted_actors),
                'Actual actor pose, resource family or occupancy binding differs from source')
        require(actual_queries == wanted_queries[:len(actual_queries)] and len(actual_queries) <= len(wanted_queries),
                'Actual world hit or ordered predicate traversal differs from original49a580')
        wanted_complete = {'stage': stage, 'sample': expected[stage]['checkpoint']['sample_index'],
                           'query_count': len(wanted_queries), 'grid_unchanged': True}
        wanted_events = []
        for position, actor in enumerate(wanted_actors):
            wanted_events.append(('actor', actor))
            wanted_events.extend(('query', q) for q in wanted_queries[position * 2:position * 2 + 2])
        wanted_events.extend(('query', q) for q in wanted_queries[16:])
        wanted_events.append(('checkpoint_complete', wanted_complete))
        actual_events = events.get(stage, [])
        require(actual_events == wanted_events[:len(actual_events)] and len(actual_events) <= len(wanted_events),
                'Picking bindings, queries or completion marker are out of order')
        if complete or index < len(stages) - 1:
            require(actual_actors == wanted_actors and actual_queries == wanted_queries and
                    completions.get(stage, []) == [wanted_complete], 'Incomplete picking checkpoint')
    return dict(parsed, actors=actors, queries=queries, completions=completions)


def capture_checkpoint(player, environment, output, player_log, reference, case, stage, expected, stop_at):
    attempts = []; started = time.monotonic()
    while True:
        require(player.poll() is None, 'Picking player exited during capture')
        before = validate_log(terrain.read_log(player_log), reference, case, expected, stop_at=stop_at)
        require(before['stages'] and before['stages'][-1]['stage'] == stage and len(before['parts'][stage]) == 3 and
                len(before['queue'].get(stage, [])) == 34 and len(before['actors'].get(stage, [])) == 8 and
                len(before['queries'].get(stage, [])) == len(expected[stage]['expected_queries']) and
                len(before['completions'].get(stage, [])) == 1,
                'Picking checkpoint changed or is incomplete before capture')
        path = menu.capture(environment, output, f'{stage}-attempt-{len(attempts) + 1:02d}')
        with Image.open(path) as image:
            rgb = image.convert('RGB')
            passed, metrics = order.frame_metrics(rgb, expected[stage]['expected_image'], expected[stage]['regions'])
            matches = []
            if not passed:
                raw = rgb.tobytes()
                for previous in expected:
                    if previous == stage: break
                    if raw == expected[previous]['expected_image'].tobytes(): matches.append(previous)
        after = validate_log(terrain.read_log(player_log), reference, case, expected, stop_at=stop_at)
        elapsed = time.monotonic() - started
        attempts.append({'screenshot': path.name, 'elapsed_seconds': elapsed, 'metrics': metrics,
                         'observed_stages_before': [v['stage'] for v in before['stages']],
                         'observed_stages_after': [v['stage'] for v in after['stages']],
                         'exact_previous_checkpoint_matches': matches})
        menu.write_json(output / (stage + '-attempts.json'), attempts)
        require(before == after, 'Motion, actor binding, picking result or traversal changed during capture')
        require(elapsed <= 1.0, 'Picking presentation exceeded1second inside its1.25second hold')
        if passed:
            menu.write_json(output / (stage + '-metrics.json'), metrics)
            return {'screenshot': path.name, 'metrics': metrics, 'capture_seconds': elapsed,
                    'presentation_attempt_count': len(attempts), 'failed_presentation_attempt_count': len(attempts) - 1,
                    'presentation_attempts': attempts, 'observed_stage_before': stage, 'observed_stage_after': stage,
                    'presentation_deadline_seconds': 1.0, 'first_attempt_failed': not attempts[0]['metrics']['matched']}
        require(time.monotonic() - started < 1.0, 'Picking framebuffer persistently differs')
        time.sleep(.02)


def observe(player, environment, output, player_log, reference, case, expected, stop_at):
    captured = {}; deadline = time.monotonic() + 90
    while True:
        log = terrain.read_log(player_log)
        if READY not in log or order.conditions_line(case) not in log:
            require(player.poll() is None and time.monotonic() < deadline and 'Exception' not in log, 'Picking bootstrap did not become ready')
            time.sleep(.02); continue
        parsed = validate_log(log, reference, case, expected, stop_at=stop_at)
        names = [row['stage'] for row in parsed['stages']]
        if names:
            stage = names[-1]
            require(all(name in captured for name in names[:-1]), 'Missed picking checkpoint')
            if stage not in captured and len(parsed['parts'][stage]) == 3 and len(parsed['queue'].get(stage, [])) == 34 and \
                    len(parsed['actors'].get(stage, [])) == 8 and len(parsed['queries'].get(stage, [])) == len(expected[stage]['expected_queries']) and len(parsed['completions'].get(stage, [])) == 1:
                captured[stage] = capture_checkpoint(player, environment, output, player_log, reference, case, stage, expected, stop_at)
                menu.write_json(output / 'captures.json', captured)
        if player.poll() is not None: break
        require(time.monotonic() < deadline, 'Picking player did not exit in90seconds')
        time.sleep(.02)
    require(player.wait(timeout=10) == 0 and set(captured) == set(expected), 'Picking exit/capture sequence failed')
    parsed = validate_log(terrain.read_log(player_log), reference, case, expected, complete=True, stop_at=stop_at)
    return captured, parsed


def run_case(output, baseline, reference, specification):
    output = Path(output).resolve(); require(not output.exists(), 'Choose a fresh picking output directory'); output.mkdir(parents=True)
    case = reference['native_order'][specification['label']]; stop_at = specification['stop_at']
    expected = checkpoints(reference, case, stop_at)
    for stage, cp in expected.items(): cp['expected_image'].save(output / (stage + '-expected.png'), compress_level=0)
    environment = os.environ.copy(); environment['DISPLAY'] = menu.DISPLAY
    environment['LD_LIBRARY_PATH'] = str(menu.TOOLCHAIN / 'usr/lib/x86_64-linux-gnu')
    player_log = output / 'player.log'; gx, gy = specification['goal']
    launch = ['bash', str(terrain.LAUNCHER), str(terrain.EXECUTABLE), '-logFile', str(player_log),
              '--ship-picking-reference', '--ship-order-target-x', str(gx), '--ship-order-target-y', str(gy),
              '--terrain-origin-x', '9', '--terrain-origin-y', '0', '--terrain-reference-exit-after', '1',
              '--ship-order-session-seed', str(case['session_seed'])]
    if stop_at is not None: launch.extend(('--ship-order-stop-at', str(stop_at)))
    if specification['next_goal'] is not None:
        launch.extend(('--ship-order-next-x', str(specification['next_goal'][0]), '--ship-order-next-y', str(specification['next_goal'][1])))
    metadata = {'launch': launch, 'provenance': baseline, 'goal': list(specification['goal']), 'stop_at_call': stop_at,
                'conditions': order.conditions_line(case), 'picking_ready': READY, 'display_size': list(terrain.SIZE),
                'camera_origin_cells': [9, 0], 'input_injection': 'none', 'scope': 'source ship-only world query with actual poses/claims',
                'expected_native_states': [cp['checkpoint'] for cp in expected.values()],
                'expected_actor_bindings': {name: cp['expected_actors'] for name, cp in expected.items()},
                'expected_native_queries': {name: cp['native_queries'] for name, cp in expected.items()},
                'limitations': LIMITATIONS}
    menu.write_json(output / 'launch.json', metadata)
    player = xvfb = wine_log = xvfb_log = None; failure = None; cleanup = []; report = None; phase = 'preflight'; started = time.monotonic()
    try:
        require(provenance() == baseline and not menu.DISPLAY_SOCKET.exists(), 'Picking source changed or display79 already owned')
        xvfb_log = (output / 'xvfb.log').open('w')
        xvfb = subprocess.Popen([str(menu.TOOLCHAIN / 'usr/bin/Xvfb'), menu.DISPLAY, '-screen', '0', '1920x1080x24', '-nolisten', 'tcp', '-ac'],
                                env=environment, stdout=xvfb_log, stderr=subprocess.STDOUT)
        menu.wait_for_display(xvfb); phase = 'player startup'; wine_log = (output / 'wine-launch.log').open('w')
        player = subprocess.Popen(launch, cwd=terrain.EXECUTABLE.parent, env=environment, stdout=wine_log, stderr=subprocess.STDOUT)
        window = units.wait_for_ready(player, environment, player_log)
        geometry = menu.xdotool(environment, 'getwindowgeometry', '--shell', window); (output / 'geometry.txt').write_text(geometry+'\n')
        values = dict(line.split('=', 1) for line in geometry.splitlines() if '=' in line)
        require(tuple(int(values[k]) for k in ('X', 'Y', 'WIDTH', 'HEIGHT')) == (0, 0, *terrain.SIZE), 'Picking player does not fill1920x1080')
        units.validate_log(terrain.read_log(player_log), order.CASE, reference); phase = 'source queries and actual rendering'
        captured, parsed = observe(player, environment, output, player_log, reference, case, expected, stop_at)
        require(provenance() == baseline, 'Picking build/source changed during run')
        last = order.stage_plan(case, stop_at)[-1][1]
        report = dict(metadata, passed=True, geometry=geometry, captures=captured, native_stage_log=parsed,
                      exit_code=0, source_claims_released=last['occupied_cell_count'], elapsed_seconds=time.monotonic()-started,
                      query_count=sum(len(cp['expected_queries']) for cp in expected.values()),
                      actor_binding_count=sum(len(cp['expected_actors']) for cp in expected.values()),
                      player_log_sha256=menu.file_sha256(player_log),
                      screenshots={p.name: menu.file_sha256(p) for p in sorted(output.glob('*.png'))})
    except Exception as error: failure = error
    finally:
        for process, label in ((player, 'player'), (xvfb, 'Xvfb')):
            issue = menu.stop_owned_process(process, label)
            if issue: cleanup.append(issue)
        for stream in (wine_log, xvfb_log):
            if stream is not None: stream.close()
    if cleanup:
        menu.write_json(output/'cleanup-failure.json', cleanup)
        if failure is None: failure = RuntimeError('Own picking process cleanup failed'); phase = 'cleanup'
    if failure is not None:
        menu.write_json(output/'failure.json', dict(metadata, passed=False, stage=phase, failure_type=type(failure).__name__, failure=str(failure)))
        raise failure
    report['player_returncode_after_cleanup'] = player.returncode; menu.write_json(output/'report.json', report); return report


def run_smoke(output, selected=None):
    output = Path(output).resolve(); require(not output.exists(), 'Choose a fresh picking output directory')
    specifications = [case for case in CASES if selected is None or case['name'] in selected]
    require(specifications and (selected is None or len(specifications) == len(selected) == len(set(selected))), 'Invalid picking case selection')
    output.mkdir(parents=True); reports = []
    try:
        baseline, reference = provenance(), load_reference()
        for specification in specifications: reports.append(run_case(output/specification['name'], baseline, reference, specification))
        require(provenance() == baseline, 'Picking sources changed between runs')
        report = {'passed': True, 'provenance': baseline, 'cases': reports, 'case_count': len(reports),
                  'capture_count': sum(len(c['captures']) for c in reports), 'query_count': sum(c['query_count'] for c in reports),
                  'actor_binding_count': sum(c['actor_binding_count'] for c in reports), 'limitations': LIMITATIONS}
        menu.write_json(output/'report.json', report); return report
    except Exception as error:
        menu.write_json(output/'failure.json', {'passed': False, 'completed_cases': len(reports), 'failure_type': type(error).__name__, 'failure': str(error)})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', action='append', choices=[case['name'] for case in CASES]); args = parser.parse_args(argv)
    report = run_smoke(args.output, args.case)
    print(json.dumps({k: report[k] for k in ('passed', 'case_count', 'capture_count', 'query_count', 'actor_binding_count')})); return 0


if __name__ == '__main__': raise SystemExit(main())
