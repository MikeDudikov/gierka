#!/usr/bin/env python3
"""Observe frozen mission-object reference pixels in a Windows Mono player.

Four isolated Wine/Xvfb sessions cover five reef references. No OS input,
original constructors, simulation or playable mission is exercised.
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

from PIL import Image, ImageChops, ImageStat

if __package__:
    from . import smoke_native_menu as menu, smoke_terrain as terrain
    from .validate_mission_reef_seed import load_fixture, FIXTURE
else:
    import smoke_native_menu as menu
    import smoke_terrain as terrain
    from validate_mission_reef_seed import load_fixture, FIXTURE

MANIFEST = menu.REPOSITORY / 'Unity/AncientConquest/Assets/Resources/MissionObjectsGenerated/MissionObjectsManifest.json'
EXECUTABLE, ASSEMBLY, LAUNCHER = terrain.EXECUTABLE, terrain.ASSEMBLY, terrain.LAUNCHER
SIZE, EXIT_AFTER = terrain.SIZE, terrain.EXIT_AFTER
READY = ('Mission object reference ready: reefs=5; reference_state=1; frame=0; '
         'empty_collision_reference=True; simulation=False')
PINNED_PAYLOADS = {
    'ObjectSeeds.bytes': (8356, '448ef43d4a625439bf4d853a4d1d37cc6845ada22d6274a57be0a4ebf4383539'),
    'ReefFramesRgba.bytes': (32768, '6b033ca9c2068fa50823823066661bedff8a5a7226404c070f911142ff98707d'),
    'MissionDescriptor.bytes': (1788, '458dac3b5942c5dff55d0640cb354a3761be9c824074cb99c29a939856a03ded'),
    'SavedViews.bytes': (80, 'b8a17a6b40efc364c44dc2a1470a1ace8188de20e6cf057edd6865eff04800f8'),
}
CASES = (
    {'name': 'reef-00000009', 'requested': (0, 4), 'actual': (0, 4), 'visible_ids': (9,)},
    {'name': 'reef-0000000a', 'requested': (9, 8), 'actual': (9, 8), 'visible_ids': (10,)},
    {'name': 'reefs-00000005-00000006', 'requested': (9, 15), 'actual': (9, 15), 'visible_ids': (5, 6)},
    {'name': 'reef-00000021', 'requested': (0, 15), 'actual': (0, 15), 'visible_ids': (33,)},
)
LIMITATIONS = [
    'Windows Mono player under Wine/Xvfb; native Windows11 and target laptop not tested',
    'Five frozen state1/frame0 reef references with empty collision cells; not complete initial mission state',
    '45 source seeds selected/parsed, zero original constructors executed by C#; no full spawning or simulation',
    'Diagnostic Point2x camera is unchanged; saved source origin15,0/view9x8 is reported, not imposed as modern FOV',
    'No OS input, navigation, panning, animation, AI, mission audio or gameplay validated',
    'Timed diagnostic Application.Quit(0) is not product/menu Quit evidence',
    'Source base-palette graphics remain a fidelity reference, not final2026art or hardware performance proof',
]
require = menu.require


def provenance():
    result = terrain.provenance()
    for label, path in {'objects_manifest': MANIFEST, 'reef_native_fixture': FIXTURE,
                        **{name: MANIFEST.parent / name for name in PINNED_PAYLOADS}}.items():
        require(path.is_file() and not path.is_symlink(), 'Missing/symbolic reference: ' + str(path))
        result[label] = {'path': str(path), 'bytes': path.stat().st_size, 'sha256': menu.file_sha256(path)}
    return result


def load_reference():
    world, payloads = terrain.load_reference()
    manifest = json.loads(MANIFEST.read_text())
    require((manifest['schema_version'], manifest['mission'], manifest['record_count'],
             manifest['native_canvas_width'], manifest['native_canvas_height'],
             manifest['reef_atlas_width'], manifest['reef_atlas_height'], manifest['format'], manifest['row_order'])
            == (1, 'miss000', 45, 1920, 1080, 128, 64, 'RGBA32', 'bottom-to-top'), 'Object manifest contract changed')
    raw_payloads = {}
    for name, (length, expected) in PINNED_PAYLOADS.items():
        path = MANIFEST.parent / name
        require(path.is_file() and not path.is_symlink(), 'Missing/symbolic object payload: ' + name)
        raw = path.read_bytes(); actual = hashlib.sha256(raw).hexdigest()
        require(len(raw) == length == manifest['payloads'][name]['bytes'], 'Object payload size differs: ' + name)
        require(actual == expected == manifest['payloads'][name]['sha256'], 'Object payload hash differs: ' + name)
        raw_payloads[name] = raw
        payloads[name] = {'bytes': len(raw), 'sha256': actual}
    records, end = {}, 0
    require(len(manifest['records']) == 45, 'Object record list changed')
    for record in manifest['records']:
        require(record['payload_offset'] == end and record['payload_length'] >= 16, 'Object record contiguity changed')
        end += record['payload_length']
        raw = raw_payloads['ObjectSeeds.bytes'][record['payload_offset']:end]
        require(hashlib.sha256(raw).hexdigest() == record['payload_sha256'], 'Object record content differs')
        require(record['resource_name'] not in records, 'Duplicate object record')
        records[record['resource_name']] = raw
    require(end == len(raw_payloads['ObjectSeeds.bytes']), 'Object payload has unreferenced bytes')
    native = load_fixture()['records']
    for reef in native:
        require(records[reef['name']].hex() == reef['payload_hex'], 'Staged reef differs from native initialization fixture')
    atlas = Image.frombytes('RGBA', (128, 64), raw_payloads['ReefFramesRgba.bytes']).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    frames = {}
    require(len(manifest['reef_frames']) == 2, 'Reef frame table changed')
    for frame in manifest['reef_frames']:
        variant = frame['variant']
        require(variant in (2, 3) and variant not in frames and frame['reference_state'] == 1
                and frame['reference_frame_index'] == 0 and frame['atlas_x'] == (variant - 2) * 64
                and frame['atlas_y'] == 0 and (frame['width'], frame['height']) == (64, 64), 'Reef atlas mapping changed')
        image = atlas.crop(((variant - 2) * 64, 0, (variant - 1) * 64, 64))
        require(hashlib.sha256(image.tobytes()).hexdigest() == frame['rgba_sha256'], 'Reef full-plane hash differs')
        require(set(image.getchannel('A').getdata()) == {0, 255}, 'Unexpected fractional reef alpha')
        frames[variant] = image
    composed = world.convert('RGBA')
    for reef in native:
        composed.alpha_composite(frames[reef['variant']], tuple(reef['world_pixel']))
    return {'terrain': world, 'world': composed.convert('RGB'), 'frames': frames, 'reefs': native, 'payloads': payloads}


def expected_image(reference, case):
    return terrain.expected_image(reference['world'], case)


def reef_regions(reference, case):
    result = []
    source_x, source_y, _, _ = terrain.source_rect(case)
    for reef in reference['reefs']:
        if reef['instance_id'] not in case['visible_ids']: continue
        world_x, world_y = reef['world_pixel']
        left, top = (world_x - source_x) * 2, (world_y - source_y) * 2
        rect = (left, top, left + 128, top + 128)
        require(left >= 0 and top >= 0 and rect[2] <= SIZE[0] and rect[3] <= SIZE[1], 'Expected reef not fully inside diagnostic frame')
        result.append({'instance_id': reef['instance_id'], 'rect': rect,
                       'alpha': reference['frames'][reef['variant']].getchannel('A').resize((128, 128), Image.Resampling.NEAREST)})
    require(len(result) == len(case['visible_ids']), 'Missing expected reef regions')
    return result


def frame_metrics(actual, expected, regions):
    matched, global_metrics = terrain.frame_metrics(actual, expected)
    rois = []
    if actual.size != SIZE or expected.size != SIZE:
        return False, {'global': global_metrics, 'reef_regions': [], 'matched': False}
    for region in regions:
        crop = actual.convert('RGB').crop(region['rect'])
        wanted = expected.convert('RGB').crop(region['rect'])
        diff = ImageChops.difference(crop, wanted)
        mean = sum(ImageStat.Stat(diff).mean) / 3
        # Test full128x128 tile AND source-covered pixels, so small objects cannot
        # disappear inside the whole-frame pixel tolerance.
        covered_mean = sum(ImageStat.Stat(diff, region['alpha']).mean) / 3
        roi_matched = mean < 1.0 and covered_mean < 1.0
        rois.append({'instance_id': region['instance_id'], 'rect': list(region['rect']),
                     'mean_rgb_error': mean, 'covered_pixel_mean_rgb_error': covered_mean,
                     'max_channel_error': max(v[1] for v in diff.getextrema()),
                     'matched': roi_matched})
        matched = matched and roi_matched
    return matched, {'global': global_metrics, 'reef_regions': rois, 'matched': matched}


def validate_log(log, case, reference):
    terrain.validate_log(log, case)
    require('Mission object reference seeds: source=45; selected=45; source_constructors_executed=0' in log,
            'Source/selected seed count or zero-constructor scope not logged')
    require('Mission object reference setup: player=1,1; source_saved_origin=15,0; source_view_cells=9,8; diagnostic_camera_unchanged=True' in log,
            'Bounded source player/view setup not logged')
    require(READY in log, 'Frozen empty-collision reef readiness not logged')
    pattern = re.compile(r'Mission object reference reef: id=([0-9a-f]{8}); cell=(-?\d+),(-?\d+); variant=(\d+)')
    actual = []
    for line in log.splitlines():
        if line.startswith('Mission object reference reef:'):
            match = pattern.fullmatch(line)
            require(match is not None, 'Malformed reef declaration')
            actual.append(tuple(int(value, 16 if i == 0 else 10) for i, value in enumerate(match.groups())))
    expected = [(reef['instance_id'], *reef['cell'], reef['variant']) for reef in reference['reefs']]
    require(sorted(actual) == sorted(expected), 'Reef declarations are missing, duplicated or differ from native fixture')


def wait_for_ready(player, environment, player_log):
    deadline = time.monotonic() + 50
    while time.monotonic() < deadline:
        require(player.poll() is None, 'Player exited before object readiness: ' + str(player.returncode))
        log = terrain.read_log(player_log)
        require('Exception' not in log, 'Player exception before object readiness')
        if READY in log:
            result = subprocess.run([str(menu.TOOLCHAIN / 'usr/bin/xdotool'), 'search', '--name', '^AncientConquest$'],
                                    env=environment, capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip(): return result.stdout.strip().splitlines()[-1]
        time.sleep(.1)
    raise AssertionError('No ready mission-object reference/player window within50seconds')


def observe_pixels(player, environment, output, expected, regions):
    attempts = []
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and len(attempts) < 12:
        require(player.poll() is None, 'Player exited before matching object framebuffer')
        path = menu.capture(environment, output, f'frame-{len(attempts) + 1:02d}')
        with Image.open(path) as actual: matched, metrics = frame_metrics(actual, expected, regions)
        attempts.append({'screenshot': path.name, **metrics})
        menu.write_json(output / 'frame-attempts.json', attempts)
        if matched: return path, metrics, attempts
        time.sleep(.15)
    if attempts:
        with Image.open(output / attempts[-1]['screenshot']) as actual:
            if actual.size == SIZE: ImageChops.difference(actual.convert('RGB'), expected).save(output / 'difference.png')
    raise AssertionError('Object framebuffer or reef regions never matched; inspect frame-attempts.json')


def run_case(output, case, reference, baseline):
    output.mkdir()
    expected = expected_image(reference, case); regions = reef_regions(reference, case)
    expected.save(output / 'expected.png', compress_level=0)
    environment = os.environ.copy(); environment['DISPLAY'] = menu.DISPLAY
    environment['LD_LIBRARY_PATH'] = str(menu.TOOLCHAIN / 'usr/lib/x86_64-linux-gnu')
    player_log = output / 'player.log'
    launch = ['bash', str(LAUNCHER), str(EXECUTABLE), '-logFile', str(player_log), '--mission-object-reference',
              '--terrain-origin-x', str(case['requested'][0]), '--terrain-origin-y', str(case['requested'][1]),
              '--terrain-reference-exit-after', str(EXIT_AFTER)]
    metadata = {'case': case['name'], 'requested_origin_cells': list(case['requested']),
                'clamped_origin_cells': list(case['actual']), 'source_rect': list(terrain.source_rect(case)),
                'expected_visible_reef_ids': list(case['visible_ids']), 'display_size': list(SIZE), 'scale': 2,
                'launch': launch, 'provenance': baseline, 'verified_payloads': reference['payloads'],
                'runtime': 'Windows Mono player under Wine11/Xvfb', 'input_injection': 'none',
                'diagnostic_exit_after_seconds': EXIT_AFTER,
                'thresholds': {'global': {'mean_rgb_error_strictly_below': 1, 'bad_pixel_channel_error_above': 4,
                                          'bad_pixel_fraction_at_most': .005},
                               'each_reef_roi_mean_rgb_error_strictly_below': 1,
                               'each_reef_covered_pixel_mean_rgb_error_strictly_below': 1}}
    menu.write_json(output / 'launch.json', metadata)
    player = xvfb = wine_log = xvfb_log = None
    failure = None; cleanup_failures = []; report = None; stage = 'preflight'; started = time.monotonic()
    try:
        require(provenance() == baseline, 'Build or staged source changed between object cases')
        require(not menu.DISPLAY_SOCKET.exists(), 'Display79 already owned; refuse reuse')
        stage = 'Xvfb startup'; xvfb_log = (output / 'xvfb.log').open('w')
        xvfb = subprocess.Popen([str(menu.TOOLCHAIN / 'usr/bin/Xvfb'), menu.DISPLAY, '-screen', '0', '1920x1080x24',
                                 '-nolisten', 'tcp', '-ac'], env=environment, stdout=xvfb_log, stderr=subprocess.STDOUT)
        menu.wait_for_display(xvfb)
        stage = 'player startup'; wine_log = (output / 'wine-launch.log').open('w')
        player = subprocess.Popen(launch, cwd=EXECUTABLE.parent, env=environment, stdout=wine_log, stderr=subprocess.STDOUT)
        window = wait_for_ready(player, environment, player_log); ready_at = time.monotonic()
        stage = 'fullscreen geometry'; geometry = menu.xdotool(environment, 'getwindowgeometry', '--shell', window)
        (output / 'geometry.txt').write_text(geometry + '\n')
        values = dict(line.split('=', 1) for line in geometry.splitlines() if '=' in line)
        require(tuple(int(values[k]) for k in ('X', 'Y', 'WIDTH', 'HEIGHT')) == (0, 0, *SIZE), 'Player does not fill1920x1080')
        validate_log(terrain.read_log(player_log), case, reference)
        stage = 'actual pixels and individual reef regions'
        screenshot, metrics, attempts = observe_pixels(player, environment, output, expected, regions)
        stage = 'diagnostic timed exit'; code = player.wait(timeout=20); exited_at = time.monotonic()
        require(code == 0, 'Object diagnostic did not exit0: ' + str(code))
        log = terrain.read_log(player_log); validate_log(log, case, reference)
        require(terrain.DIAGNOSTIC_EXIT in log, 'Diagnostic timed exit marker missing')
        require(exited_at - ready_at >= EXIT_AFTER - 2, 'Object player exited before diagnostic timer')
        require(provenance() == baseline, 'Build or source changed during object validation')
        report = dict(metadata, passed=True, geometry=geometry, framebuffer=metrics,
                      matched_screenshot=screenshot.name, capture_attempt_count=len(attempts), exit_code=code,
                      termination='diagnostic timed Application.Quit(0)', ready_to_observed_exit_seconds=exited_at-ready_at,
                      elapsed_seconds=exited_at-started,
                      screenshots={p.name:menu.file_sha256(p) for p in sorted(output.glob('*.png'))},
                      player_log_sha256=menu.file_sha256(player_log), limitations=LIMITATIONS)
    except Exception as error: failure = error
    finally:
        for process, label in ((player, 'player'), (xvfb, 'Xvfb')):
            issue = menu.stop_owned_process(process, label)
            if issue: cleanup_failures.append(issue)
        for stream in (wine_log, xvfb_log):
            if stream is not None: stream.close()
    if cleanup_failures:
        menu.write_json(output/'cleanup-failure.json', cleanup_failures)
        if failure is None: stage='cleanup'; failure=RuntimeError('Could not stop own process')
    if failure is not None:
        menu.write_json(output/'failure.json', dict(metadata, stage=stage, failure_type=type(failure).__name__,
                        failure=str(failure), player_returncode_after_cleanup=player.returncode if player is not None else None))
        raise failure
    report['player_returncode_after_cleanup'] = player.returncode
    menu.write_json(output/'report.json', report)
    return report


def run_smoke(output):
    output = Path(output).resolve(); require(not output.exists(), 'Select a fresh output directory')
    output.mkdir(parents=True); reports=[]; stage='reference preflight'
    try:
        baseline = provenance(); reference = load_reference()
        for case in CASES:
            stage=case['name']; reports.append(run_case(output/case['name'], case, reference, baseline))
        require(provenance()==baseline, 'Build/source changed during object validation')
        report = {'passed':True, 'runtime':'Windows Mono player under Wine11/Xvfb', 'provenance':baseline,
                  'verified_payloads':reference['payloads'], 'cases':reports, 'limitations':LIMITATIONS}
        menu.write_json(output/'report.json', report); return report
    except Exception as error:
        menu.write_json(output/'failure.json', {'passed':False,'stage':stage,'completed_cases':[r['case'] for r in reports],
                        'failure_type':type(error).__name__,'failure':str(error),'limitations':LIMITATIONS})
        raise


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    if args.output.resolve().exists(): parser.error('Select a fresh output directory')
    report=run_smoke(args.output)
    print(json.dumps({'passed':report['passed'],'output':str(args.output.resolve()),'cases':[r['case'] for r in report['cases']]},indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
