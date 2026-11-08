#!/usr/bin/env python3
"""Observe one bounded source0b movement in a real Windows Mono player.

Seven checkpoints compare native movement state and independent source pixels.
The diagnostic has controlled wind0/heading5, upgrade0 and one prepared route;
it does not test OS input, general navigation, full AI or the complete game.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from PIL import Image, ImageChops

if __package__:
    from . import smoke_mission_units as units
    from .decode_composite_sprite import decode_composite_frame
    from .decode_sprite import dib_palette, resource_payload
    from .inspect_dkx import inspect_pair
    from .inspect_world_reference import base_palette_sprite
else:
    import smoke_mission_units as units
    from decode_composite_sprite import decode_composite_frame
    from decode_sprite import dib_palette, resource_payload
    from inspect_dkx import inspect_pair
    from inspect_world_reference import base_palette_sprite

menu, terrain, require = units.menu, units.terrain, units.require
ROOT = menu.REPOSITORY
MANIFEST = ROOT / 'Unity/AncientConquest/Assets/Resources/ShipMovementGenerated/ShipMovementManifest.json'
MANIFEST_SHA256 = '6aa1c312fa979993dc950df862bea69ee8e1522a3c7d1197dfe9583fc64ab5fc'
ATLAS_SHA256 = '9b204db564030e808e6ef067aa64caef8f3f462ae555d186b55b04916193fb82'
MOVEMENT_FIXTURE = ROOT / 'tests/fixtures/prepared_ship_movement.json'
MOVEMENT_FIXTURE_SHA256 = '28931c2849e05f46c7fd005c0f7b923f1d19bf26c045148a1a2388191cf2d374'
POSE_FIXTURE = ROOT / 'tests/fixtures/ship_a_pose_selection.json'
POSE_FIXTURE_SHA256 = 'b1bc3be7a6db713b4055eddf949c07340436cb644fcccb1aa97c834a93b362a0'
PUBLICATION_FIXTURE = ROOT / 'tests/fixtures/ship_forward_publication.json'
PUBLICATION_FIXTURE_SHA256 = '9567c1a18cd894892af9a97841ff5c73399a0b0030847a7a562a064b2f42b666'
STAGES = (('initial', 0), ('reserved', 1), ('animation-only', 3), ('first-pixel', 5),
          ('before-transfer', 29), ('transferred', 30), ('arrived', 44))
CASE = {'name': 'source0b-adjacent-move', 'requested': (9, 0), 'actual': (9, 0), 'visible_ids': (11, 12, 13)}
EXIT_AFTER = 1
DIAGNOSTIC_EXIT = 'Terrain reference diagnostic exit: requested_seconds=1; code=0'
CONDITIONS = ('[ShipMovementReference] conditions: id=0000000b; route=16,2>15,3; path=prepared-native-two-point; '
              'wind_force=0; wind_heading=5; owner_upgrade=0; quantum_ms=40; pending_steps=1; '
              'clock=bounded-single-step; input=domain-reference; full_simulation=False')
COMMAND = ('[ShipMovementReference] command: copied_bytes=26; target=15,3; opaque_byte=255; '
           'promotion=Promoted; active_flags=128; pending_flags=0; route_byte=0')
COMPLETE = '[ShipMovementReference] complete: calls=44; counter=44; frame=22; frozen_after_arrival=True; idle_rng=False'
HALTED = '[ShipMovementReference] halted: calls=1; counter=1; diagnostic_only=True'
LIMITATIONS = [
    'Windows Mono player under Wine/Xvfb; native Windows11 and target i5/RTX3050Ti laptop not tested',
    'One explicitly prepared source0b route16,2 to15,3, wind0/heading5, upgrade0, fullhealth and seven stationary source ships',
    'No OS input, general pathfinding, full command collection, combat, AI, idle RNG or complete mission simulation',
    'Harness checkpoint holds freeze diagnostic time; they do not reproduce the original pause mode or establish real-time cadence',
    'Whole1920x1080 viewport and complete source0b/c/d planes at origin9,0 scale2; other source ships remain outside this crop',
    'Known34-component cohort order only; no dynamic full-world sorter or other source classes',
    'Base-palette source art is a fidelity reference, not final2026art or a performance claim',
    'Diagnostic Application.Quit(0) is not evidence for the product/menu Quit callback',
]


def provenance():
    result = units.provenance()
    paths = {'movement_qa_helper': Path(__file__).resolve(), 'movement_manifest': MANIFEST,
             'movement_atlas': MANIFEST.parent / 'ShipMovementRgba.bytes',
             'native_movement_fixture': MOVEMENT_FIXTURE, 'native_pose_fixture': POSE_FIXTURE,
             'native_publication_fixture': PUBLICATION_FIXTURE}
    for name in ('ShipMovementReference.cs', 'MissionShipReference.cs', 'TerrainReferenceFrame.cs',
                 'Simulation/PreparedShipMovement.cs', 'Simulation/ShipFrameProgression.cs',
                 'Simulation/ShipMoveRequestInbox.cs', 'Simulation/SingleStepClock.cs'):
        paths['runtime_source:' + name] = ROOT / 'Unity/AncientConquest/Assets/AncientConquest/Runtime' / name
    for label, path in paths.items():
        require(path.is_file() and not path.is_symlink(), 'Missing/symbolic movement evidence: ' + str(path))
        result[label] = {'path': str(path), 'bytes': path.stat().st_size, 'sha256': menu.file_sha256(path)}
    return result


def load_reference():
    reference = units.load_reference()
    native = units.pinned_json(MOVEMENT_FIXTURE, MOVEMENT_FIXTURE_SHA256)
    pose_proof = units.pinned_json(POSE_FIXTURE, POSE_FIXTURE_SHA256)
    publication = units.pinned_json(PUBLICATION_FIXTURE, PUBLICATION_FIXTURE_SHA256)
    manifest = units.pinned_json(MANIFEST, MANIFEST_SHA256)
    require((manifest['instance_id'], manifest['descriptor_resource'], manifest['component_mask'], manifest['pose_count'],
             manifest['plane_count'], manifest['atlas_width'], manifest['atlas_height']) == (11, 'SHIP_A1110', 0x83, 88, 152, 2128, 224),
            'Movement pose manifest left its verified scope')
    atlas_raw = (MANIFEST.parent / 'ShipMovementRgba.bytes').read_bytes()
    require(len(atlas_raw) == 1906688 and hashlib.sha256(atlas_raw).hexdigest() == ATLAS_SHA256 ==
            manifest['payloads']['ShipMovementRgba.bytes']['sha256'], 'Movement atlas SHA/length differs')
    atlas = Image.frombytes('RGBA', (2128, 224), atlas_raw).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    source = {name: (units.SOURCE_ROOT / name).read_bytes() for name in units.SOURCE_HASHES}
    require(all(hashlib.sha256(raw).hexdigest() == units.SOURCE_HASHES[name] for name, raw in source.items()),
            'Source files changed while loading movement reference')
    data = source['files/DATA/OBJECTS.DKD']
    entries = inspect_pair(source['files/DATA/OBJECTS.DKX'], data)
    descriptor = next(entry for entry in entries if (entry['type'], entry['name']) == (8, 'SHIP_A1110'))
    map_data = source['installed/missions/maplib.dkd']
    maps = inspect_pair(source['installed/missions/maplib.dkx'], map_data)
    palette = dib_palette(resource_payload(next(entry for entry in maps
                  if (entry['type'], entry['name']) == (1, 'PALETTE')), map_data))
    require(hashlib.sha256(palette).hexdigest() == manifest['base_palette_sha256'], 'Movement palette changed')
    saved = {row['name']: row for row in manifest['planes']}
    proof = {row['frame_index']: row for row in pose_proof['frames']}
    poses = {}
    for index in range(88):
        frame = decode_composite_frame(descriptor, data, entries, index, 0x83)
        parts = [{key: part[key] for key in ('name', 'offset_x', 'offset_y', 'depth')} for part in frame['components']]
        require(parts == proof[index]['components'] and [p['name'] for p in frame['inline_components']] == proof[index]['inline_names'],
                'Movement decoder selection/order differs from actual native pose fixture')
        require((frame['width'], frame['height']) == (56, 56), 'Movement pose plane changed')
        staged = manifest['poses'][index]
        require(staged['frame_index'] == index and staged['inline_draw_order'] == [1, 7] and
                [{k: p[k] for k in ('source_index', 'name', 'offset_x', 'offset_y', 'depth')} for p in staged['components']] ==
                [{k: p[k] for k in ('source_index', 'name', 'offset_x', 'offset_y', 'depth')} for p in frame['components']],
                'Staged movement pose differs from source/native proof')
        decoded = {}
        for part in frame['components']:
            image = base_palette_sprite(part['sprite'], palette)
            plane = saved[part['name']]
            left, top = plane['atlas_x'], 224 - plane['atlas_y'] - plane['height']
            require(atlas.crop((left, top, left+56, top+56)).tobytes() == image.tobytes(),
                    'Movement atlas plane differs from original source decoder')
            require(hashlib.sha256(image.tobytes()).hexdigest() == plane['rgba_sha256'], 'Movement plane hash differs')
            decoded[part['source_index']] = dict(part, image=image)
        poses[index] = decoded
    case = next(case for case in native['cases'] if case['label'] == 'southwest_pending1')
    require(case['controlled_inputs'] == {'pending_steps_each_call': 1, 'wind_strength': 0, 'wind_heading': 5,
            'owner_upgrade_byte': 0, 'blocked_target_with_source0c_pointer': False}, 'Native movement conditions differ')
    require(case['active_path_hex'] == '10000200050f00030005' and len(case['trace']) == 45, 'Native prepared route changed')
    require(case['source_payload_sha256'] == next(row['payload_sha256'] for row in
            units.pinned_json(units.SHIP_FIXTURE, units.SHIP_FIXTURE_SHA256)['records'] if row['instance_id'] == 11),
            'Movement trace used a different source ship payload')
    require(publication['movement_fixture_sha256'] == MOVEMENT_FIXTURE_SHA256 and
            publication['movement_case'] == 'southwest_pending1' and publication['hooked_callees'] == {} and
            len(publication['rows']) == 45, 'Native publication fixture scope changed')
    # Independent source forward-tail arithmetic, not the C# helper. Validate
    # every stored frame in the pinned full native trace, not just checkpoints.
    last_tick, frame = 0, 20
    last_ticks = {}
    for row, published in zip(case['trace'], publication['rows']):
        if row['animation_tail_reached'] and ((row['stamp'] - last_tick) & 0xffffffff) > 2:
            frame = 20 if frame + 1 >= 24 else frame + 1
            last_tick = row['stamp']
        require(frame == row['frame'], 'Native trace frame disagrees with verified unsigned forward-tail rule')
        require(published['call'] == row['tick'] and published['stamp'] == row['stamp'] and published['stored_frame'] == frame,
                'Native movement/publication counter or stored frame disagrees')
        last_ticks[row['tick']] = last_tick
    reference.update(poses=poses, native_trace=case['trace'], native_last_ticks=last_ticks,
                     native_publication=publication['rows'],
                     movement_manifest=manifest, movement_payloads={'ShipMovementRgba.bytes': {'bytes': len(atlas_raw), 'sha256': ATLAS_SHA256}})
    return reference


def checkpoint_reference(reference, stage_name):
    cache = reference.setdefault('_checkpoint_cache', {})
    if stage_name in cache: return cache[stage_name]
    tick = dict(STAGES)[stage_name]
    row = reference['native_trace'][tick]
    require(row['tick'] == row['stamp'] == tick, 'Checkpoint counter phase changed')
    published = reference['native_publication'][tick]
    frame = published['drawn_frame']
    parts = reference['poses'][frame]
    world_x, world_y = published['render_world_x'], published['render_world_y']
    depth = max(10000, 20000 - 56 - world_y)
    draws = []
    for draw in reference['draws']:
        if draw['kind'] != 'ship' or draw['instance_id'] != 11:
            draws.append(draw)
        else:
            part = parts[draw['source_index']]
            draws.append(dict(draw, name=part['name'], image=part['image'], x=world_x+part['offset_x'],
                              y=world_y+part['offset_y'], depth=21000 if part['source_index'] == 0 else depth))
    require(depth > reference['ships'][13]['reference_depth'], 'Movement changed the verified body queue rank')
    alpha = Image.new('L', (56, 56))
    for part in parts.values(): alpha = ImageChops.lighter(alpha, part['image'].getchannel('A'))
    ship = dict(reference['ships'][11], world_pixel=(world_x, world_y), cell=tuple(row['cell']), alpha=alpha,
                frame_index=frame, reference_depth=depth)
    ship['parts'] = [draw for draw in draws if draw['kind'] == 'ship' and draw['instance_id'] == 11]
    ships = dict(reference['ships']); ships[11] = ship
    result = {key:value for key,value in reference.items() if key != '_checkpoint_cache'}
    result.update(ships=ships, draws=draws)
    result['world'] = units.compose_world(result)
    result['expected_image'] = units.expected_image(result, CASE)
    result['regions'] = units.ship_regions(result, CASE)
    result['checkpoint'] = {'stage': stage_name, 'call': tick, 'counter': row['stamp'], 'cell': row['cell'],
        'world': row['world'], 'frame': row['frame'], 'drawn_frame': frame,
        'occupied': row['occupied_cell_count'], 'reserved': row['reserved'],
        'complete': tick == 44, 'state': row['state'], 'speed': row['speed'], 'remainder': row['remainder'],
        'deceleration': row['deceleration'], 'next': row['next_cell'], 'center_gate': bool(row['center_gate']),
        'last_tick': reference['native_last_ticks'][tick]}
    result['expected_parts'] = [{'source_index': draw['source_index'], 'sprite': draw['name'],
                                 'order': index+10, 'position': [draw['x'], draw['y']]}
                                for index, draw in enumerate(draws) if draw['kind'] == 'ship' and draw['instance_id'] == 11]
    cache[stage_name] = result
    return result


def stage_records(log):
    records = []
    for line in log.splitlines():
        if not line.startswith('[ShipMovementReference] stage='): continue
        values = {}
        for token in line[len('[ShipMovementReference] '):].split(' '):
            require('=' in token, 'Malformed movement stage token')
            key, value = token.split('=', 1)
            require(key not in values, 'Duplicated movement stage field')
            if key in ('cell', 'world'): value = [int(v) for v in value.split(',')]
            elif key in ('complete', 'center_gate'):
                require(value in ('True', 'False'), 'Invalid movement stage boolean'); value = value == 'True'
            elif key != 'stage': value = int(value)
            values[key] = value
        records.append(values)
    return records


def validate_stage_log(log, reference, *, complete=False, stop_at=44):
    require(stop_at in (1,44), 'QA supports only full44 and reserved1 lifecycle cases')
    require('Exception' not in log and '[ShipMovementReference] failed' not in log, 'Movement player reported an exception/failure')
    require(log.count(CONDITIONS) == 1, 'Missing/duplicated source movement conditions')
    require(sum(line.startswith('[ShipMovementReference] conditions:') for line in log.splitlines()) == 1,
            'Unexpected extra movement conditions declaration')
    commands = [line for line in log.splitlines() if line.startswith('[ShipMovementReference] command:')]
    require(commands in ([], [COMMAND]), 'Invalid/duplicated movement command')
    records = stage_records(log)
    expected_names = [name for name, tick in STAGES if tick <= stop_at]
    names = [record['stage'] for record in records]
    require(names == expected_names[:len(names)] and len(names) <= len(expected_names), 'Missing, duplicated or unordered movement checkpoint')
    for record in records:
        expected = checkpoint_reference(reference, record['stage'])['checkpoint']
        require(record == expected, 'Movement checkpoint differs from pinned native state: ' + record['stage'])
    pattern = re.compile(r'\[ShipMovementReference\] part: stage=([a-z-]+); source_index=(\d+); sprite=([^;]+); order=(-?\d+); position=(-?\d+),(-?\d+)')
    parts = {name: [] for name in names}
    current_stage = None
    for line in log.splitlines():
        if line.startswith('[ShipMovementReference] stage='):
            current_stage = line.split('stage=',1)[1].split(' ',1)[0]
        if not line.startswith('[ShipMovementReference] part:'): continue
        match = pattern.fullmatch(line); require(match is not None, 'Malformed movement renderer part declaration')
        name, index, sprite, order, x, y = match.groups()
        require(name in parts and name == current_stage, 'Movement renderer part precedes or leaves its stage')
        parts[name].append({'source_index': int(index), 'sprite': sprite, 'order': int(order), 'position': [int(x), int(y)]})
    for index, name in enumerate(names):
        expected = checkpoint_reference(reference, name)['expected_parts']
        actual = parts[name]
        require(len({p['source_index'] for p in actual}) == len(actual), 'Duplicate movement part declaration')
        require(all(part in expected for part in actual), 'Movement renderer part differs from native pose/order/anchor')
        if complete or index < len(names)-1:
            require(sorted(actual, key=lambda p:p['source_index']) == sorted(expected, key=lambda p:p['source_index']), 'Missing movement part declaration')
    if complete:
        require(names == expected_names, 'Incomplete movement checkpoint sequence')
        require(log.count(COMMAND) == 1, 'Missing movement command contract')
        endings = [line for line in log.splitlines() if line.startswith('[ShipMovementReference] complete:') or
                   line.startswith('[ShipMovementReference] halted:')]
        if stop_at == 44:
            require(endings == [COMPLETE], 'Missing/invalid full movement completion')
        else:
            require(endings == [HALTED], 'Missing/invalid early movement halt')
        released = 8 if stop_at == 44 else 9
        cleanup = f'Mission unit reference cleanup: claimed_released={released}; visual_refs_cleared=True'
        require([line for line in log.splitlines() if line.startswith('Mission unit reference cleanup:')] == [cleanup],
                'Movement did not release its8/9source claims and clear visual references')
        require(DIAGNOSTIC_EXIT in log, 'Movement timed diagnostic exit marker missing')
    return {'stages': records, 'parts': parts}


def frame_metrics(actual, expected, regions):
    matched, metrics = units.frame_metrics(actual, expected, regions)
    # This diagnostic has point-sampled source art and no text/AA. A small
    # duplicate sprite outside the current ship planes must also fail.
    maximum = metrics['global'].get('max_channel_error')
    strict_global = maximum is not None and maximum <= 4
    metrics['global']['max_channel_error_at_most'] = 4
    metrics['global']['matched'] = bool(metrics['global'].get('matched', False) and strict_global)
    metrics['matched'] = matched and strict_global
    return metrics['matched'], metrics


def capture_checkpoint(player, environment, output, player_log, reference, current, checkpoints, stop_at):
    """Fence X presentation within this same1.25s checkpoint; never borrow a later state."""
    attempts=[]
    started=time.monotonic()
    deadline=started+1.0
    while True:
        require(player.poll() is None,'Player exited while awaiting checkpoint presentation')
        before_log=terrain.read_log(player_log)
        before=validate_stage_log(before_log,reference,stop_at=stop_at)
        before_names=[row['stage'] for row in before['stages']]
        require(before_names and before_names[-1]==current and len(before['parts'][current])==3,
                'Movement changed before checkpoint capture: '+current)
        path=menu.capture(environment,output,f'{current}-attempt-{len(attempts)+1:02d}')
        with Image.open(path) as image:
            rgb=image.convert('RGB')
            passed,metrics=frame_metrics(rgb,checkpoints[current]['expected_image'],checkpoints[current]['regions'])
            stale=[]
            if not passed:
                raw=rgb.tobytes()
                for name,_ in STAGES:
                    if name==current:break
                    if name in checkpoints and raw==checkpoints[name]['expected_image'].tobytes():stale.append(name)
        after_log=terrain.read_log(player_log)
        after_records=stage_records(after_log)
        elapsed=time.monotonic()-started
        attempts.append({'screenshot':path.name,'elapsed_seconds':elapsed,'metrics':metrics,
                         'observed_stages_before':before_names,'observed_stages_after':[row['stage'] for row in after_records],
                         'exact_previous_checkpoint_matches':stale})
        menu.write_json(output/(current+'-attempts.json'),attempts)
        after=validate_stage_log(after_log,reference,stop_at=stop_at)
        require(before==after,'Movement fields/stage changed during checkpoint capture: '+current)
        require(elapsed<=1.0,'Checkpoint presentation exceeded1second within its1.25second hold: '+current)
        if passed:
            menu.write_json(output/(current+'-metrics.json'),metrics)
            return {'screenshot':path.name,'metrics':metrics,'capture_seconds':elapsed,'presentation_attempt_count':len(attempts),
                    'failed_presentation_attempt_count':len(attempts)-1,'presentation_attempts':attempts,
                    'observed_stage_before':current,'observed_stage_after':current,
                    'presentation_deadline_seconds':1.0,'first_attempt_failed':not attempts[0]['metrics']['matched']}
        require(time.monotonic()<deadline,'Movement framebuffer persistently differs during checkpoint: '+current)
        time.sleep(.02)


def observe(player, environment, output, player_log, reference, checkpoints, stop_at):
    captured = {}
    deadline = time.monotonic() + 40
    while True:
        log = terrain.read_log(player_log)
        if CONDITIONS not in log:
            require(player.poll() is None and time.monotonic() < deadline and 'Exception' not in log,
                    'Movement conditions did not follow bootstrap readiness')
            time.sleep(.02)
            continue
        parsed = validate_stage_log(log, reference, stop_at=stop_at)
        names = [row['stage'] for row in parsed['stages']]
        if names:
            current = names[-1]
            for name in names[:-1]: require(name in captured, 'Missed movement capture checkpoint: ' + name)
            if current not in captured and len(parsed['parts'][current]) == 3:
                captured[current]=capture_checkpoint(player,environment,output,player_log,reference,current,checkpoints,stop_at)
                menu.write_json(output / 'captures.json', captured)
        if player.poll() is not None: break
        require(time.monotonic() < deadline, 'Movement player did not exit in40seconds')
        time.sleep(.02)
    require(player.wait(timeout=10) == 0, 'Movement diagnostic did not exit0')
    require(set(captured) == {name for name,tick in STAGES if tick<=stop_at}, 'Not all required movement checkpoints were captured')
    parsed = validate_stage_log(terrain.read_log(player_log), reference, complete=True, stop_at=stop_at)
    return captured, parsed


def run_case(output, baseline, reference, stop_at):
    output = Path(output).resolve()
    require(not output.exists(), 'Select a fresh movement output directory')
    output.mkdir(parents=True)
    checkpoints = {name: checkpoint_reference(reference, name) for name,tick in STAGES if tick<=stop_at}
    for name, value in checkpoints.items(): value['expected_image'].save(output / (name+'-expected.png'), compress_level=0)
    environment = os.environ.copy()
    environment['DISPLAY'] = menu.DISPLAY
    environment['LD_LIBRARY_PATH'] = str(menu.TOOLCHAIN / 'usr/lib/x86_64-linux-gnu')
    player_log = output / 'player.log'
    launch = ['bash',str(terrain.LAUNCHER),str(terrain.EXECUTABLE),'-logFile',str(player_log),'--ship-movement-reference',
              '--terrain-origin-x','9','--terrain-origin-y','0','--terrain-reference-exit-after',str(EXIT_AFTER)]
    launch.extend(('--ship-movement-stop-at',str(stop_at)))
    metadata = {'launch':launch,'provenance':baseline,'conditions':CONDITIONS,'camera_origin_cells':[9,0],
                'display_size':list(terrain.SIZE),'scale':2,'input_injection':'none','stage_harness_hold_seconds':1.25,'stop_at_call':stop_at,
                'presentation_deadline_seconds':1.0,'presentation_retry_poll_seconds':.02,
                'expected_native_states':[value['checkpoint'] for value in checkpoints.values()],
                'thresholds':{'global_mean_rgb_error_strictly_below':1,'global_bad_pixel_fraction_at_most':.005,
                              'global_max_channel_error_at_most':4,
                              'each_full_ship_plane_mean_rgb_error_strictly_below':1,
                              'each_source_coverage_mean_rgb_error_strictly_below':1,'each_full_ship_plane_max_channel_error_at_most':4},
                'limitations':LIMITATIONS}
    menu.write_json(output/'launch.json',metadata)
    player=xvfb=wine_log=xvfb_log=None
    failure=None; cleanup=[]; stage='preflight'; started=time.monotonic(); report=None
    try:
        require(provenance()==baseline,'Build/source changed during movement preflight')
        require(not menu.DISPLAY_SOCKET.exists(),'Display79 already owned; refuse reuse')
        stage='Xvfb startup';xvfb_log=(output/'xvfb.log').open('w')
        xvfb=subprocess.Popen([str(menu.TOOLCHAIN/'usr/bin/Xvfb'),menu.DISPLAY,'-screen','0','1920x1080x24','-nolisten','tcp','-ac'],
                              env=environment,stdout=xvfb_log,stderr=subprocess.STDOUT)
        menu.wait_for_display(xvfb)
        stage='player startup';wine_log=(output/'wine-launch.log').open('w')
        player=subprocess.Popen(launch,cwd=terrain.EXECUTABLE.parent,env=environment,stdout=wine_log,stderr=subprocess.STDOUT)
        window=units.wait_for_ready(player,environment,player_log)
        stage='fullscreen geometry';geometry=menu.xdotool(environment,'getwindowgeometry','--shell',window)
        (output/'geometry.txt').write_text(geometry+'\n')
        values=dict(line.split('=',1) for line in geometry.splitlines() if '=' in line)
        require(tuple(int(values[key]) for key in ('X','Y','WIDTH','HEIGHT'))==(0,0,*terrain.SIZE),'Movement player does not fill1920x1080')
        units.validate_log(terrain.read_log(player_log),CASE,reference)
        stage='native checkpoints and actual framebuffer';captures,parsed=observe(player,environment,output,player_log,reference,checkpoints,stop_at)
        require(provenance()==baseline,'Build/source changed during movement run')
        report=dict(metadata,passed=True,geometry=geometry,captures=captures,native_stage_log=parsed,exit_code=0,
                    source_claims_released=8 if stop_at==44 else 9,elapsed_seconds=time.monotonic()-started,
                    player_log_sha256=menu.file_sha256(player_log),
                    screenshots={p.name:menu.file_sha256(p) for p in sorted(output.glob('*.png'))})
    except Exception as error:failure=error
    finally:
        for process,label in ((player,'player'),(xvfb,'Xvfb')):
            issue=menu.stop_owned_process(process,label)
            if issue:cleanup.append(issue)
        for stream in (wine_log,xvfb_log):
            if stream is not None:stream.close()
    if cleanup:
        menu.write_json(output/'cleanup-failure.json',cleanup)
        if failure is None:failure=RuntimeError('Could not stop own movement process');stage='cleanup'
    if failure is not None:
        menu.write_json(output/'failure.json',dict(metadata,passed=False,stage=stage,failure_type=type(failure).__name__,failure=str(failure)))
        raise failure
    report['player_returncode_after_cleanup']=player.returncode
    menu.write_json(output/'report.json',report)
    return report


def run_smoke(output):
    output=Path(output).resolve()
    require(not output.exists(),'Select a fresh movement output directory')
    output.mkdir(parents=True)
    reports=[]
    try:
        baseline,reference=provenance(),load_reference()
        for name,stop in (('full-route',44),('halt-reserved',1)):
            reports.append(run_case(output/name,baseline,reference,stop))
        require(provenance()==baseline,'Build/source changed between movement lifecycle cases')
        report={'passed':True,'provenance':baseline,'cases':reports,'limitations':LIMITATIONS}
        menu.write_json(output/'report.json',report)
        return report
    except Exception as error:
        menu.write_json(output/'failure.json',{'passed':False,'completed_cases':len(reports),
                        'failure_type':type(error).__name__,'failure':str(error),'limitations':LIMITATIONS})
        raise


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    report=run_smoke(args.output)
    print(json.dumps({'passed':report['passed'],'output':str(args.output.resolve()),
                      'case_stops':[case['stop_at_call'] for case in report['cases']]}))
    return 0


if __name__=='__main__':raise SystemExit(main())
