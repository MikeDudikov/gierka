import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from tools import smoke_ship_route as route


EXPECTED_CALLS = {
    (14, 4): [('initial', 0), ('reserved-1', 1), ('first-pixel-1', 5), ('reserved-2', 30),
              ('transferred-1', 30), ('waypoint-1', 40), ('first-pixel-2', 41), ('transferred-2', 50), ('arrived', 59)],
    (18, 5): [('initial', 0), ('turn-start-1', 1), ('turn-published-1', 2), ('turn-complete-1', 17),
              ('reserved-1', 18), ('first-pixel-1', 22), ('reserved-2', 46), ('transferred-1', 46),
              ('waypoint-1', 57), ('first-pixel-2', 58), ('reserved-3', 67), ('transferred-2', 67),
              ('waypoint-2', 74), ('first-pixel-3', 75), ('transferred-3', 81), ('arrived', 86)],
    (20, 4): [('initial', 0), ('turn-start-1', 1), ('turn-published-1', 2), ('turn-complete-1', 26),
              ('reserved-1', 27), ('first-pixel-1', 30), ('reserved-2', 50), ('transferred-1', 50),
              ('waypoint-1', 59), ('first-pixel-2', 60), ('reserved-3', 71), ('transferred-2', 71),
              ('waypoint-2', 78), ('first-pixel-3', 79), ('reserved-4', 85), ('transferred-3', 85),
              ('waypoint-3', 89), ('first-pixel-4', 90), ('transferred-4', 98), ('arrived', 107)],
    (20, 6): [('initial', 0), ('turn-start-1', 1), ('turn-published-1', 2), ('turn-complete-1', 17),
              ('reserved-1', 18), ('first-pixel-1', 22), ('reserved-2', 46), ('transferred-1', 46),
              ('waypoint-1', 57), ('first-pixel-2', 58), ('reserved-3', 67), ('transferred-2', 67),
              ('waypoint-2', 74), ('first-pixel-3', 75), ('reserved-4', 83), ('transferred-3', 83),
              ('waypoint-3', 90), ('first-pixel-4', 91), ('transferred-4', 99), ('arrived', 108)],
    (16, 1): [('initial', 0), ('rejected', 0)],
    (19, 4): [('initial', 0), ('turn-start-1', 1), ('turn-published-1', 2), ('turn-complete-1', 26),
              ('reserved-1', 27), ('first-pixel-1', 30), ('reserved-2', 50), ('transferred-1', 50),
              ('waypoint-1', 59), ('first-pixel-2', 60), ('transferred-2', 71), ('waypoint-2', 80), ('stalled', 130)],
}


def stage_line(record):
    def encode(key, value):
        return ','.join(map(str, value)) if key in route.PAIR_FIELDS else str(value)
    return route.PREFIX + ' '.join(key + '=' + encode(key, record[key]) for key in route.STAGE_FIELDS)


def valid_log(reference, case, checkpoints, stop_at=None):
    lines = [route.conditions_line(case), route.command_line(case), route.path_line(case)]
    for part in route.expected_registration(reference, case):
        lines.append(route.PREFIX + f"registration: node={part['node']}; kind={part['kind']}; " +
                     f"id={part['id']:08x}; depth={part['depth']}; components={part['components']}")
    for stage, checkpoint in checkpoints.items():
        lines.append(stage_line(checkpoint['checkpoint']))
        for part in checkpoint['expected_parts']:
            lines.append(route.PREFIX + 'part: stage=' + stage +
                f"; source_index={part['source_index']}; sprite={part['sprite']}; order={part['order']}; " +
                'position=' + ','.join(map(str, part['position'])))
        for part in checkpoint['expected_queue_rows']:
            lines.append(route.PREFIX + f"queue: stage={stage}; node={part['node']}; kind={part['kind']}; " +
                         f"id={part['id']:08x}; part={part['part']}; depth={part['depth']}; order={part['order']}")
    lines.append(route.completion_line(case, stop_at))
    row = case['trace'][min(stop_at, len(case['trace']) - 1) if stop_at is not None else -1]
    lines.append(f"Mission unit reference cleanup: claimed_released={row['occupied_cell_count']}; visual_refs_cleared=True")
    lines.append(route.movement.DIAGNOSTIC_EXIT)
    return '\n'.join(lines) + '\n'


class RouteSourceReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not all((route.units.SOURCE_ROOT / name).is_file() for name in route.units.SOURCE_HASHES):
            raise unittest.SkipTest('Private original game inputs are not installed')
        cls.reference = route.load_reference()
        cls.cases = cls.reference['native_route']

    def checkpoints(self, case, stop_at=None):
        return {name: route.checkpoint_reference(self.reference, case, name, row)
                for name, row in route.stage_plan(case, stop_at)}

    def test_native_event_schedule_preserves_segment_and_reservation_order(self):
        count = 0
        for goal, expected in EXPECTED_CALLS.items():
            case = self.cases[goal]
            plan = route.stage_plan(case)
            self.assertEqual([(name, row['tick']) for name, row in plan], expected)
            self.assertTrue(all(row['stamp'] == row['tick'] + 1 for _, row in plan))
            count += len(plan)
        self.assertEqual(count, 80)
        case = self.cases[18, 5]
        early = route.stage_plan(case, 46)
        self.assertEqual(len(early), 8)
        self.assertEqual([(name, row['tick']) for name, row in early[-2:]], [('reserved-2', 46), ('transferred-1', 46)])
        row = early[-1][1]
        self.assertEqual((row['path_index'], row['cell'], row['waypoint'], row['next_waypoint']),
                         (1, [17, 3], [17, 3], [18, 4]))
        self.assertEqual(count + len(early), 88)
        stalled = self.cases[19, 4]['trace'][-1]
        self.assertEqual(stalled['state'], 0)
        self.assertFalse(route.is_complete(self.cases[19, 4], stalled))
        self.assertTrue(route.completion_line(self.cases[19, 4]).startswith(route.PREFIX + 'stalled:'))

    def test_state_queue_and_terminal_log_corruptions_are_rejected(self):
        case = self.cases[18, 5]
        checkpoints = self.checkpoints(case)
        log = valid_log(self.reference, case, checkpoints)
        self.assertEqual(len(route.validate_stage_log(log, self.reference, case, checkpoints, complete=True)['stages']), 16)
        initial = stage_line(checkpoints['initial']['checkpoint'])
        two = stage_line(checkpoints['first-pixel-3']['checkpoint'])
        part = next(line for line in log.splitlines() if line.startswith(route.PREFIX + 'part:'))
        queue = next(line for line in log.splitlines() if line.startswith(route.PREFIX + 'queue:'))
        registration = next(line for line in log.splitlines() if line.startswith(route.PREFIX + 'registration:'))
        mutations = {
            'stored-as-drawn': log.replace('stage=turn-start-1 call=1 counter=2', 'stage=turn-start-1 call=1 counter=1'),
            'drop-intermediate-publication': log.replace(two, two.replace('publication_count=2', 'publication_count=1')),
            'wrong-waypoint': log.replace(initial, initial.replace('waypoint=17,3', 'waypoint=18,4', 1)),
            'wrong-next-waypoint': log.replace(initial, initial.replace('next_waypoint=18,4', 'next_waypoint=18,5')),
            'missing-state-field': log.replace(initial, initial.replace(' path_count=4', '')),
            'extra-state-field': log.replace(initial, initial + ' extra=0'),
            'duplicate-state-field': log.replace(initial, initial + ' counter=1'),
            'duplicate-stage': log.replace(initial, initial + '\n' + initial),
            'missing-part': log.replace(part + '\n', ''),
            'duplicate-part': log.replace(part, part + '\n' + part),
            'wrong-part-order': log.replace(part, part.replace('order=17', 'order=18')),
            'missing-queue-entry': log.replace(queue + '\n', ''),
            'duplicate-queue-entry': log.replace(queue, queue + '\n' + queue),
            'wrong-queue-order': log.replace(queue, queue.replace('order=10', 'order=11')),
            'wrong-queue-depth': log.replace(queue, queue.replace('depth=21000', 'depth=20999')),
            'wrong-node-mapping': log.replace(queue, queue.replace('node=20', 'node=19')),
            'missing-registration': log.replace(registration + '\n', ''),
            'duplicate-registration': log.replace(registration, registration + '\n' + registration),
            'duplicate-command': log + route.command_line(case) + '\n',
            'wrong-path-bytes': log.replace(route.path_line(case), route.path_line(case) + 'ff'),
            'missing-path': log.replace(route.path_line(case) + '\n', ''),
            'missing-command': log.replace(route.command_line(case) + '\n', ''),
            'contradictory-complete': log + route.PREFIX + 'complete: goal=0,0; calls=0\n',
            'contradictory-stalled': log + route.PREFIX + 'stalled: goal=0,0; calls=0\n',
            'wrong-claims': log.replace('claimed_released=8;', 'claimed_released=9;'),
            'missing-exit': log.replace(route.movement.DIAGNOSTIC_EXIT, ''),
        }
        for label, value in mutations.items():
            self.assertNotEqual(value, log, label)
            with self.subTest(label=label), self.assertRaises((AssertionError, ValueError)):
                route.validate_stage_log(value, self.reference, case, checkpoints, complete=True)

    def test_all_publications_affect_history_dependent_native_depth_ties(self):
        # Queue control, independent of ship physics: two writes in the same
        # call cross a tie and return to it. Keeping only the final write loses
        # the source's retained side of that tie.
        case = {'trace': [
            {'tick': 0, 'render_world': [1028, 132], 'publications': []},
            {'tick': 1, 'render_world': [1028, 268], 'publications': [
                {'frame': 20, 'world': [1028, 269], 'depth': 19675},
                {'frame': 20, 'world': [1028, 268], 'depth': 19676}]}]}
        history = route.native_queue_history(case)
        actual = history['rows'][1]['draw_order']
        wrong = route.depth_queue.original_cohort_trace([268])['states'][-1]['draw_order']
        self.assertNotEqual(actual, wrong)
        self.assertEqual(history['publication_count'], 2)

    def test_source_pixels_reject_old_cohort_order_ghosts_and_outside_roi_errors(self):
        case = self.cases[20, 6]
        plan = dict(route.stage_plan(case))
        checkpoint = route.checkpoint_reference(self.reference, case, 'reserved-4', plan['reserved-4'])
        image, regions = checkpoint['expected_image'], checkpoint['regions']
        self.assertTrue(route.frame_metrics(image, image, regions)[0])
        def key(draw):
            return draw['kind'], draw['instance_id'], draw.get('source_index', -1)
        current = {key(draw): draw for draw in checkpoint['draws']}
        wrong_order = [current[key(draw)] for draw in self.reference['draws']]
        wrong = route.units.expected_image(dict(checkpoint, world=route.units.compose_world(checkpoint, wrong_order)), route.CASE)
        self.assertFalse(route.frame_metrics(wrong, image, regions)[0])
        for error, accepted in ((4, True), (5, False)):
            changed = image.copy(); pixel = changed.getpixel((0, 0))
            changed.putpixel((0, 0), tuple(value + error if value + error <= 255 else value - error for value in pixel))
            self.assertEqual(route.frame_metrics(changed, image, regions)[0], accepted)
        ghost = dict(next(draw for draw in checkpoint['draws'] if draw['kind'] == 'ship' and
                          draw['instance_id'] == 11 and draw['source_index'] == 1), x=600, y=400)
        wrong = route.units.expected_image(dict(checkpoint, world=route.units.compose_world(
            checkpoint, checkpoint['draws'] + [ghost])), route.CASE)
        self.assertFalse(route.frame_metrics(wrong, image, regions)[0])


class RoutePresentationFenceTests(unittest.TestCase):
    def setup_case(self, root):
        image = Image.new('RGB', route.terrain.SIZE)
        current = image.copy(); current.putpixel((0, 0), (8, 8, 8))
        stale, ready = root / 'stale.png', root / 'ready.png'
        image.save(stale); current.save(ready)
        checkpoints = {'initial': {'expected_image': image, 'regions': []},
                       'first-pixel-2': {'expected_image': current, 'regions': []}}
        observed = {'stages': [{'stage': 'initial'}, {'stage': 'first-pixel-2'}],
                    'parts': {'initial': [{}, {}, {}], 'first-pixel-2': [{}, {}, {}]},
                    'queue': {'initial': [{}] * 34, 'first-pixel-2': [{}] * 34}, 'registration': [{}] * 21}
        return stale, ready, checkpoints, observed

    def test_stale_presentation_retries_only_inside_same_complete_state_and_queue(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); stale, ready, checkpoints, observed = self.setup_case(root)
            with patch.object(route.terrain, 'read_log', return_value='log'), \
                 patch.object(route, 'validate_stage_log', return_value=observed), \
                 patch.object(route.menu, 'capture', side_effect=[stale, ready]), \
                 patch.object(route.time, 'monotonic', side_effect=[0, .1, .2, .3]), patch.object(route.time, 'sleep'):
                player = type('Player', (), {'poll': lambda self: None})()
                result = route.capture_checkpoint(player, {}, root, root / 'player.log', {}, {}, 'first-pixel-2', checkpoints, None)
            self.assertEqual(result['presentation_attempt_count'], 2)
            self.assertEqual(result['presentation_attempts'][0]['exact_previous_checkpoint_matches'], ['initial'])
            self.assertEqual(result['capture_seconds'], .3)

    def test_changed_queue_and_late_correct_frame_are_rejected(self):
        for problem in ('queue-changed', 'slow-capture'):
            with self.subTest(problem=problem), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); _, ready, checkpoints, observed = self.setup_case(root)
                after = copy.deepcopy(observed)
                if problem == 'queue-changed':
                    after['queue']['first-pixel-2'][0] = {'order': 99}
                with patch.object(route.terrain, 'read_log', return_value='log'), \
                     patch.object(route, 'validate_stage_log', side_effect=[observed, after]), \
                     patch.object(route.menu, 'capture', return_value=ready), \
                     patch.object(route.time, 'monotonic', side_effect=[0, 1.01 if problem == 'slow-capture' else .2]):
                    player = type('Player', (), {'poll': lambda self: None})()
                    with self.assertRaisesRegex(AssertionError, 'changed during capture|exceeded1second'):
                        route.capture_checkpoint(player, {}, root, root / 'player.log', {}, {}, 'first-pixel-2', checkpoints, None)


if __name__ == '__main__':
    unittest.main()
