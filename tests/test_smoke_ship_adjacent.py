import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from tools import smoke_ship_adjacent as adjacent


EXPECTED_CALLS = {
    (17, 2): [('initial', 0), ('turn-start', 1), ('turn-published', 2), ('turn-complete', 26),
              ('reserved', 27), ('first-pixel', 30), ('transferred', 50), ('arrived', 61)],
    (17, 1): [('initial', 0), ('turn-start', 1), ('turn-published', 2), ('turn-complete', 35),
              ('reserved', 36), ('first-pixel', 40), ('transferred', 65), ('arrived', 79)],
    (16, 1): [('initial', 0), ('rejected', 0)],
    (15, 1): [('initial', 0), ('rejected', 0)],
    (15, 2): [('initial', 0), ('turn-start', 1), ('turn-published', 2), ('turn-complete', 8),
              ('reserved', 9), ('first-pixel', 12), ('transferred', 32), ('arrived', 43)],
    (15, 3): [('initial', 0), ('reserved', 1), ('first-pixel', 5), ('transferred', 30), ('arrived', 44)],
    (16, 3): [('initial', 0), ('turn-start', 1), ('turn-published', 2), ('turn-complete', 8),
              ('reserved', 9), ('first-pixel', 12), ('transferred', 32), ('arrived', 43)],
    (17, 3): [('initial', 0), ('turn-start', 1), ('turn-published', 2), ('turn-complete', 17),
              ('reserved', 18), ('first-pixel', 22), ('transferred', 46), ('arrived', 62)],
}


def stage_line(record):
    def encode(key, value):
        if key in adjacent.PAIR_FIELDS:
            return ','.join(map(str, value))
        return str(value)
    return adjacent.PREFIX + ' '.join(key + '=' + encode(key, record[key]) for key in adjacent.STAGE_FIELDS)


def checkpoint_metadata(case):
    pose_proof = adjacent.units.pinned_json(adjacent.movement.POSE_FIXTURE,
                                            adjacent.movement.POSE_FIXTURE_SHA256)
    poses = {row['frame_index']: row for row in pose_proof['frames']}
    checkpoints = {}
    for stage, row in adjacent.stage_plan(case):
        parts = poses[row['drawn_frame']]['components']
        # The pinned native34-component queue places source0b shadow at17 and
        # its two inline parts at23/24 for every bounded adjacent route.
        checkpoints[stage] = {'checkpoint': adjacent.expected_stage(case, stage, row),
            'expected_parts': [{'source_index': source_index, 'sprite': part['name'], 'order': order,
                                'position': [row['render_world'][0] + part['offset_x'],
                                             row['render_world'][1] + part['offset_y']]}
                               for source_index, order, part in zip((0, 1, 7), (17, 23, 24), parts)]}
    return checkpoints


def valid_log(case, checkpoints, stop_at=None):
    lines = [adjacent.conditions_line(case), adjacent.command_line(case)]
    for stage, checkpoint in checkpoints.items():
        lines.append(stage_line(checkpoint['checkpoint']))
        for part in checkpoint['expected_parts']:
            lines.append(adjacent.PREFIX + 'part: stage=' + stage +
                         f"; source_index={part['source_index']}; sprite={part['sprite']}; order={part['order']}; " +
                         'position=' + ','.join(map(str, part['position'])))
    lines.append(adjacent.completion_line(case, stop_at))
    row = case['trace'][min(stop_at, len(case['trace']) - 1) if stop_at is not None else -1]
    lines.append(f"Mission unit reference cleanup: claimed_released={row['occupied_cell_count']}; visual_refs_cleared=True")
    lines.append(adjacent.movement.DIAGNOSTIC_EXIT)
    return '\n'.join(lines) + '\n'


class AdjacentNativeCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = adjacent.units.pinned_json(adjacent.FIXTURE, adjacent.FIXTURE_SHA256)
        cls.cases = adjacent.native_cases(cls.native)

    def test_native_event_schedule_has_49_full_and_four_early_halt_captures(self):
        captures = 0
        for goal, expected in EXPECTED_CALLS.items():
            plan = adjacent.stage_plan(self.cases[goal])
            self.assertEqual([(stage, row['tick']) for stage, row in plan], expected)
            self.assertTrue(all(row['stamp'] == row['tick'] + 1 for _, row in plan))
            captures += len(plan)
        self.assertEqual(captures, 49)
        for goal, second in (((17, 2), 'turn-start'), ((15, 3), 'reserved')):
            plan = adjacent.stage_plan(self.cases[goal], 1)
            self.assertEqual([(stage, row['tick']) for stage, row in plan], [('initial', 0), (second, 1)])
            captures += len(plan)
        self.assertEqual(captures, 53)
        plan = dict(adjacent.stage_plan(self.cases[17, 2]))
        self.assertEqual((plan['turn-start']['frame'], plan['turn-start']['drawn_frame'],
                          plan['turn-start']['pose_published']), (47, 20, False))
        self.assertEqual((plan['turn-published']['frame'], plan['turn-published']['drawn_frame']), (48, 48))
        with self.assertRaises(AssertionError):
            adjacent.stage_plan(self.cases[17, 2], -1)

    def test_all_native_stage_logs_pass_and_corrupted_state_or_renderer_fields_fail(self):
        for goal, case in self.cases.items():
            checkpoints = checkpoint_metadata(case)
            log = valid_log(case, checkpoints)
            result = adjacent.validate_stage_log(log, {}, case, checkpoints, complete=True)
            self.assertEqual(len(result['stages']), len(EXPECTED_CALLS[goal]))
        case = self.cases[17, 2]
        checkpoints = checkpoint_metadata(case)
        log = valid_log(case, checkpoints)
        initial = stage_line(checkpoints['initial']['checkpoint'])
        turn = stage_line(checkpoints['turn-start']['checkpoint'])
        mutations = {
            'wrong-counter': log.replace('stage=turn-start call=1 counter=2', 'stage=turn-start call=1 counter=1'),
            'draw-stored-before-publication': log.replace(turn, turn.replace('drawn_frame=20', 'drawn_frame=47')),
            'wrong-published-world': log.replace(turn, turn.replace('published_world=1028,132', 'published_world=1029,132')),
            'wrong-source-cell': log.replace(turn, turn.replace('cell=16,2', 'cell=17,2')),
            'wrong-last-state-counter': log.replace(turn, turn.replace('last_state_counter=2', 'last_state_counter=0')),
            'missing-stage': log.replace(initial + '\n', ''),
            'duplicated-stage': log.replace(initial, initial + '\n' + initial),
            'unknown-stage-field': log.replace(initial, initial + ' extra=0'),
            'missing-stage-field': log.replace(initial, initial.replace(' path_count=2', '')),
            'invalid-boolean': log.replace(initial, initial.replace('accepted=True', 'accepted=1')),
            'duplicated-stage-key': log.replace(initial, initial + ' counter=1'),
            'invalid-command': log.replace('opaque_byte=255', 'opaque_byte=0'),
            'duplicated-command': log + adjacent.command_line(case) + '\n',
            'missing-command': log.replace(adjacent.command_line(case) + '\n', ''),
            'invalid-conditions': log.replace('planner_counter=1', 'planner_counter=0'),
            'wrong-renderer-order': log.replace('; order=23;', '; order=24;'),
            'wrong-renderer-anchor': log.replace('; position=1028,132', '; position=1029,132'),
            'wrong-renderer-source': log.replace('; sprite=BLB1A020;', '; sprite=BLB1A000;'),
            'missing-renderer-part': '\n'.join(line for line in log.splitlines()
                                              if not line.startswith(adjacent.PREFIX + 'part: stage=initial; source_index=7;')),
            'part-outside-own-stage': log.replace('part: stage=initial;', 'part: stage=turn-start;', 1),
            'wrong-ending-counter': log.replace('complete: goal=17,2; calls=61; counter=62;',
                                               'complete: goal=17,2; calls=61; counter=61;'),
            'wrong-cleanup-claims': log.replace('claimed_released=8;', 'claimed_released=9;'),
            'missing-exit-marker': log.replace(adjacent.movement.DIAGNOSTIC_EXIT, ''),
        }
        first_part = next(line for line in log.splitlines() if line.startswith(adjacent.PREFIX + 'part:'))
        mutations['duplicate-renderer-part'] = log.replace(first_part, first_part + '\n' + first_part)
        for label, changed in mutations.items():
            with self.subTest(label=label), self.assertRaises((AssertionError, ValueError)):
                adjacent.validate_stage_log(changed, {}, case, checkpoints, complete=True)


class AdjacentPixelReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not all((adjacent.units.SOURCE_ROOT / name).is_file() for name in adjacent.units.SOURCE_HASHES):
            raise unittest.SkipTest('Private original game inputs are not installed')
        cls.reference = adjacent.load_reference()

    def test_native_publication_pixels_match_and_wrong_frame_anchor_or_extra_sprite_fail(self):
        case = self.reference['native_adjacent'][17, 2]
        plan = dict(adjacent.stage_plan(case))
        initial = adjacent.checkpoint_reference(self.reference, case, 'initial', plan['initial'])
        turn = adjacent.checkpoint_reference(self.reference, case, 'turn-start', plan['turn-start'])
        published = adjacent.checkpoint_reference(self.reference, case, 'turn-published', plan['turn-published'])
        self.assertEqual(initial['expected_image'].tobytes(), turn['expected_image'].tobytes())
        for checkpoint in (initial, turn, published):
            self.assertTrue(adjacent.frame_metrics(checkpoint['expected_image'], checkpoint['expected_image'],
                                                   checkpoint['regions'])[0])
        wrong_frame = dict(plan['turn-start'], drawn_frame=plan['turn-start']['frame'])
        wrong = adjacent.checkpoint_reference(self.reference, case, 'turn-start', wrong_frame)
        self.assertFalse(adjacent.frame_metrics(wrong['expected_image'], turn['expected_image'], turn['regions'])[0])
        shifted_row = dict(plan['turn-published'], render_world=[1029, 132])
        shifted = adjacent.checkpoint_reference(self.reference, case, 'turn-published', shifted_row)
        self.assertFalse(adjacent.frame_metrics(shifted['expected_image'], published['expected_image'], published['regions'])[0])
        wrong_pixel = published['expected_image'].copy()
        wrong_pixel.putpixel((0, 0), tuple((value + 8) % 256 for value in wrong_pixel.getpixel((0, 0))))
        passed, metrics = adjacent.frame_metrics(wrong_pixel, published['expected_image'], published['regions'])
        self.assertFalse(passed)
        self.assertFalse(metrics['global']['matched'])  # Outside every ship ROI.
        missing_shadow = [draw for draw in published['draws']
                          if not (draw['kind'] == 'ship' and draw['instance_id'] == 11 and draw['source_index'] == 0)]
        changed = adjacent.units.expected_image(dict(published, world=adjacent.units.compose_world(published, missing_shadow)),
                                                 adjacent.CASE)
        self.assertFalse(adjacent.frame_metrics(changed, published['expected_image'], published['regions'])[0])
        extra = dict(next(draw for draw in published['draws']
                          if draw['kind'] == 'ship' and draw['instance_id'] == 11 and draw['source_index'] == 1),
                     x=600, y=400)
        extra_image = adjacent.units.expected_image(dict(published, world=adjacent.units.compose_world(
            published, published['draws'] + [extra])), adjacent.CASE)
        self.assertFalse(adjacent.frame_metrics(extra_image, published['expected_image'], published['regions'])[0])


class AdjacentPresentationFenceTests(unittest.TestCase):
    def fixture(self, root):
        initial = Image.new('RGB', adjacent.terrain.SIZE)
        current = initial.copy(); current.putpixel((0, 0), (8, 8, 8))
        stale_path, current_path = root / 'stale.png', root / 'current.png'
        initial.save(stale_path); current.save(current_path)
        checkpoints = {'initial': {'expected_image': initial, 'regions': []},
                       'turn-published': {'expected_image': current, 'regions': []}}
        observed = {'stages': [{'stage': 'initial'}, {'stage': 'turn-published'}],
                    'parts': {'initial': [{}, {}, {}], 'turn-published': [{}, {}, {}]}}
        return stale_path, current_path, checkpoints, observed

    def test_stale_frame_retries_within_the_same_stage_and_one_second_bound(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            stale, current, checkpoints, observed = self.fixture(root)
            with patch.object(adjacent.terrain, 'read_log', return_value='log'), \
                 patch.object(adjacent, 'validate_stage_log', return_value=observed), \
                 patch.object(adjacent.menu, 'capture', side_effect=[stale, current]), \
                 patch.object(adjacent.time, 'monotonic', side_effect=[0, .1, .2, .3]), \
                 patch.object(adjacent.time, 'sleep'):
                player = type('Player', (), {'poll': lambda self: None})()
                result = adjacent.capture_checkpoint(player, {}, root, root / 'player.log', {}, {},
                                                     'turn-published', checkpoints, None)
            self.assertEqual(result['presentation_attempt_count'], 2)
            self.assertEqual(result['failed_presentation_attempt_count'], 1)
            self.assertEqual(result['presentation_attempts'][0]['exact_previous_checkpoint_matches'], ['initial'])
            self.assertEqual(result['capture_seconds'], .3)
            self.assertTrue(result['first_attempt_failed'])

    def test_stage_changes_and_slow_correct_capture_are_rejected(self):
        for problem in ('stage-changed', 'capture-too-slow'):
            with self.subTest(problem=problem), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                _stale, current, checkpoints, observed = self.fixture(root)
                after = copy.deepcopy(observed)
                if problem == 'stage-changed':
                    after['stages'].append({'stage': 'turn-complete'})
                times = [0, 1.01 if problem == 'capture-too-slow' else .2]
                with patch.object(adjacent.terrain, 'read_log', return_value='log'), \
                     patch.object(adjacent, 'validate_stage_log', side_effect=[observed, after]), \
                     patch.object(adjacent.menu, 'capture', return_value=current), \
                     patch.object(adjacent.time, 'monotonic', side_effect=times):
                    player = type('Player', (), {'poll': lambda self: None})()
                    with self.assertRaisesRegex(AssertionError, 'changed during capture|exceeded1second'):
                        adjacent.capture_checkpoint(player, {}, root, root / 'player.log', {}, {},
                                                    'turn-published', checkpoints, None)


if __name__ == '__main__':
    unittest.main()
