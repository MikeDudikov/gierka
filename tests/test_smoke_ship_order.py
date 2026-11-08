import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from tools import smoke_ship_order as order


def stage_line(record):
    def encode(key, value):
        return ','.join(map(str, value)) if key in order.PAIR_FIELDS else str(value)
    return order.PREFIX + ' '.join(key + '=' + encode(key, record[key]) for key in order.STAGE_FIELDS)


def valid_log(reference, case, checkpoints, stop_at=None):
    lines = [order.conditions_line(case)]
    for r in order.expected_registration(reference, case):
        lines.append(order.PREFIX + f"registration: node={r['node']}; kind={r['kind']}; id={r['id']:08x}; " +
                     f"depth={r['depth']}; components={r['components']}")
    for stage, cp in checkpoints.items():
        lines.append(stage_line(cp['checkpoint']))
        path = cp['expected_path']
        lines.append(order.PREFIX + f"path: stage={stage}; count={path['count']}; points_hex={path['points_hex']}")
        for part in cp['expected_parts']:
            lines.append(order.PREFIX + 'part: stage=' + stage +
                f"; source_index={part['source_index']}; sprite={part['sprite']}; order={part['order']}; " +
                'position=' + ','.join(map(str, part['position'])))
        for r in cp['expected_queue_rows']:
            lines.append(order.PREFIX + f"queue: stage={stage}; node={r['node']}; kind={r['kind']}; " +
                         f"id={r['id']:08x}; part={r['part']}; depth={r['depth']}; order={r['order']}")
    lines.append(order.completion_line(case, stop_at))
    sample = order.stage_plan(case, stop_at)[-1][1]
    lines.append(f"Mission unit reference cleanup: claimed_released={sample['occupied_cell_count']}; visual_refs_cleared=True")
    lines.append(order.movement.DIAGNOSTIC_EXIT)
    return '\n'.join(lines) + '\n'


class NormalOrderSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not all((order.units.SOURCE_ROOT / n).is_file() for n in order.units.SOURCE_HASHES):
            raise unittest.SkipTest('Private original game inputs are not installed')
        cls.reference = order.load_reference()
        cls.cases = cls.reference['native_order']

    def checkpoints(self, case, stop_at=None):
        return {name: order.checkpoint_reference(self.reference, case, name, sample)
                for name, sample in order.stage_plan(case, stop_at)}

    def test_source_normal_cycle_has_same_counter_work_and_deferred_stop_before_idle(self):
        case = self.cases['reach18_5']
        expected = [('initial', 0), ('request-1', 0), ('promoted-1', 1), ('path-1', 1), ('turn-1', 3),
                    ('reserved-1', 19), ('moving-1', 23), ('transferred-1', 47), ('path-complete-1', 87),
                    ('stop-request-1', 98), ('active-cleared-1', 99), ('idle-published-1', 101)]
        plan = order.stage_plan(case)
        self.assertEqual([(n, s['counter']) for n, s in plan], expected)
        stages = dict(plan)
        self.assertEqual((stages['promoted-1']['last_plan'], stages['promoted-1']['state'],
                          stages['promoted-1']['frame'], stages['promoted-1']['drawn_frame']), (1, 2, 47, 20))
        self.assertEqual(stages['stop-request-1']['pending'] & 8, 8)
        self.assertEqual(stages['stop-request-1']['active'] & 0x80, 0x80)
        self.assertEqual(stages['active-cleared-1']['active'], 0x400)
        idle = stages['idle-published-1']
        self.assertEqual((idle['frame'], idle['drawn_frame'], idle['random_state']), (81, 80, 639546082))
        self.assertTrue(order.can_request(idle))
        self.assertEqual(idle['cache_cells'], [115, 141])
        total = sum(len(order.stage_plan(self.cases[s['label']], s['stop_at'])) for s in order.CASES)
        self.assertEqual(total, 53)

    def test_nearest_endpoint_is_not_requested_arrival_and_second_request_does_not_advance_time(self):
        case = self.cases['nearest18_2']
        stages = dict(order.stage_plan(case, 180))
        end = stages['halted']
        self.assertTrue(order.path_complete(end))
        self.assertFalse(order.requested_reached(end))
        self.assertFalse(order.can_request(end))
        self.assertEqual((end['path_endpoint'], end['requested_goal'], end['active_target']),
                         ([17, 2], [18, 2], [18, 2]))
        self.assertEqual(end['active'] & 0x80, 0x80)
        two = self.cases['two18_5_then16_4']
        samples = two['samples']; before, request = samples[102], samples[103]
        self.assertEqual((before['counter'], request['counter'], request['operation'], request['epoch']),
                         (101, 101, 'request', 2))
        self.assertNotEqual(before['sample_index'], request['sample_index'])
        self.assertEqual(request['publications'], [])
        self.assertFalse(request['animation_tail_reached'])
        for key in ('frame', 'drawn_frame', 'world', 'render_world', 'random_state', 'last_frame_tick'):
            self.assertEqual(request[key], before[key])
        self.assertEqual(request['pending'] & 0x80, 0x80)
        self.assertEqual(len(order.stage_plan(two)), 23)
        self.assertEqual(order.stage_plan(two)[-1][1]['counter'], 197)
        self.assertEqual(len(two['_native_queue']['rows']), len(samples))

    def test_stop_bound_precedes_idle_completion_and_following_request(self):
        for label in ('reach18_5', 'two18_5_then16_4'):
            with self.subTest(case=label, stop_at=101):
                plan = order.stage_plan(self.cases[label], 101)
                name, sample = plan[-1]
                self.assertEqual((name, sample['sample_index'], sample['counter'], sample['operation']),
                                 ('halted', 102, 101, 'tick'))
                self.assertEqual(plan[-2][0], 'idle-published-1')
                self.assertNotIn('request-2', [stage for stage, _ in plan])
                self.assertEqual(order.completion_line(self.cases[label], 101),
                                 order.PREFIX + 'halted: calls=101; counter=101; diagnostic_only=True')
        with self.subTest(stop_at=0):
            plan = order.stage_plan(self.cases['reach18_5'], 0)
            self.assertEqual([stage for stage, _ in plan], ['initial', 'request-1', 'halted'])
            self.assertEqual((plan[-1][1]['counter'], plan[-1][1]['operation']), (0, 'request'))
        with self.subTest(stop_at=100):
            stage, sample = order.stage_plan(self.cases['reach18_5'], 100)[-1]
            self.assertEqual((stage, sample['counter']), ('halted', 100))
        with self.subTest(stop_at=102):
            stage, sample = order.stage_plan(self.cases['reach18_5'], 102)[-1]
            self.assertEqual((stage, sample['counter']), ('idle-published-1', 101))

    def test_order_flags_rng_path_cache_and_terminal_corruptions_are_rejected(self):
        case = self.cases['reach18_5']; cp = self.checkpoints(case)
        log = valid_log(self.reference, case, cp)
        self.assertEqual(len(order.validate_stage_log(log, self.reference, case, cp, complete=True)['stages']), 12)
        initial = stage_line(cp['initial']['checkpoint']); request = stage_line(cp['request-1']['checkpoint'])
        idle = stage_line(cp['idle-published-1']['checkpoint']); stop = stage_line(cp['stop-request-1']['checkpoint'])
        path = next(line for line in log.splitlines() if line.startswith(order.PREFIX + 'path: stage=path-1;'))
        queue = next(line for line in log.splitlines() if line.startswith(order.PREFIX + 'queue:'))
        mutations = {
            'fake-synchronous-stop': log.replace(stop, stop.replace('active_flags=1152', 'active_flags=1024')),
            'lost-pending-stop': log.replace(stop, stop.replace('pending_flags=8', 'pending_flags=0')),
            'rng-not-updated': log.replace(idle, idle.replace('random_state=639546082', 'random_state=0')),
            'stored-idle-rendered-too-soon': log.replace(idle, idle.replace('drawn_frame=80', 'drawn_frame=81')),
            'request-advances-counter': log.replace(request, request.replace('counter=0', 'counter=1')),
            'request-stale-pubs': log.replace(request, request.replace('publication_count=0', 'publication_count=1')),
            'wrong-operation': log.replace(request, request.replace('operation=request', 'operation=tick')),
            'sample-counter-conflated': log.replace(idle, idle.replace('sample_index=102', 'sample_index=101')),
            'wrong-requested-goal': log.replace(request, request.replace('requested_goal=18,5', 'requested_goal=17,2')),
            'fake-ready-before-clear': log.replace(stop, stop.replace('can_request=False', 'can_request=True')),
            'missing-cache': log.replace(idle, idle.replace('cache_count=2 cache_hex=0073008d', 'cache_count=0 cache_hex=')),
            'cache-order-changed': log.replace(idle, idle.replace('cache_hex=0073008d', 'cache_hex=008d0073')),
            'invalid-cache-length': log.replace(idle, idle.replace('cache_hex=0073008d', 'cache_hex=73')),
            'wrong-seed-contract': log.replace('session_seed=0;', 'session_seed=1;'),
            'duplicate-conditions': log + order.conditions_line(case) + '\n',
            'duplicate-state': log.replace(initial, initial + '\n' + initial),
            'unknown-state-field': log.replace(initial, initial + ' extra=0'),
            'duplicate-state-field': log.replace(initial, initial + ' epoch=1'),
            'wrong-source-path': log.replace(path, path + 'ff'),
            'missing-source-path': log.replace(path + '\n', ''),
            'duplicate-source-path': log.replace(path, path + '\n' + path),
            'wrong-queue-order': log.replace(queue, queue.replace('order=10', 'order=11')),
            'duplicate-queue': log.replace(queue, queue + '\n' + queue),
            'wrong-end-active': log.replace('epochs=1; target_reached=True; active_flags=1024;',
                                           'epochs=1; target_reached=True; active_flags=0;'),
            'contradictory-terminal': log + order.PREFIX + 'complete: calls=0; counter=0\n',
            'wrong-cleanup': log.replace('claimed_released=8;', 'claimed_released=9;'),
        }
        for label, value in mutations.items():
            self.assertNotEqual(value, log, label)
            with self.subTest(label=label), self.assertRaises((AssertionError, ValueError)):
                order.validate_stage_log(value, self.reference, case, cp, complete=True)

    def test_idle_pixels_reject_stored_frame_ghosts_and_global_five_but_accept_four(self):
        case = self.cases['reach18_5']; name, sample = order.stage_plan(case)[-1]
        cp = order.checkpoint_reference(self.reference, case, name, sample)
        wrong_sample = dict(sample, drawn_frame=sample['frame'])
        wrong = order.checkpoint_reference(self.reference, case, name, wrong_sample)
        image, regions = cp['expected_image'], cp['regions']
        self.assertTrue(order.frame_metrics(image, image, regions)[0])
        self.assertFalse(order.frame_metrics(wrong['expected_image'], image, regions)[0])
        for error, accepted in ((4, True), (5, False)):
            changed = image.copy(); pixel = changed.getpixel((0, 0))
            changed.putpixel((0, 0), tuple(v + error if v + error <= 255 else v - error for v in pixel))
            self.assertEqual(order.frame_metrics(changed, image, regions)[0], accepted)
        ghost = dict(next(d for d in cp['draws'] if d['kind'] == 'ship' and d['instance_id'] == 11 and
                          d['source_index'] == 1), x=600, y=400)
        extra = order.units.expected_image(dict(cp, world=order.units.compose_world(cp, cp['draws'] + [ghost])), order.CASE)
        self.assertFalse(order.frame_metrics(extra, image, regions)[0])


class NormalOrderFenceTests(unittest.TestCase):
    def fixture(self, root):
        a = Image.new('RGB', order.terrain.SIZE); b = a.copy(); b.putpixel((0, 0), (8, 8, 8))
        stale, ready = root / 'stale.png', root / 'ready.png'; a.save(stale); b.save(ready)
        cp = {'initial': {'expected_image': a, 'regions': []}, 'idle-published-1': {'expected_image': b, 'regions': []}}
        parsed = {'stages': [{'stage': 'initial'}, {'stage': 'idle-published-1'}],
                  'parts': {'initial': [{}, {}, {}], 'idle-published-1': [{}, {}, {}]},
                  'queue': {'initial': [{}] * 34, 'idle-published-1': [{}] * 34}, 'registration': [{}] * 21}
        return stale, ready, cp, parsed

    def test_stale_frame_retries_with_same_state_epoch_and_full_queue(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); stale, ready, cp, parsed = self.fixture(root)
            with patch.object(order.terrain, 'read_log', return_value='log'), \
                 patch.object(order, 'validate_stage_log', return_value=parsed), \
                 patch.object(order.menu, 'capture', side_effect=[stale, ready]), \
                 patch.object(order.time, 'monotonic', side_effect=[0, .1, .2, .3]), patch.object(order.time, 'sleep'):
                player = type('Player', (), {'poll': lambda self: None})()
                result = order.capture_checkpoint(player, {}, root, root / 'player.log', {}, {}, 'idle-published-1', cp, None)
            self.assertEqual(result['presentation_attempt_count'], 2)
            self.assertEqual(result['presentation_attempts'][0]['exact_previous_checkpoint_matches'], ['initial'])

    def test_epoch_change_and_late_correct_frame_fail_capture_fence(self):
        for problem in ('epoch-changed', 'late'):
            with self.subTest(problem=problem), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); _, ready, cp, parsed = self.fixture(root); after = copy.deepcopy(parsed)
                if problem == 'epoch-changed':
                    after['stages'][-1]['epoch'] = 2
                with patch.object(order.terrain, 'read_log', return_value='log'), \
                     patch.object(order, 'validate_stage_log', side_effect=[parsed, after]), \
                     patch.object(order.menu, 'capture', return_value=ready), \
                     patch.object(order.time, 'monotonic', side_effect=[0, 1.01 if problem == 'late' else .2]):
                    player = type('Player', (), {'poll': lambda self: None})()
                    with self.assertRaisesRegex(AssertionError, 'changed during capture|exceeded1second'):
                        order.capture_checkpoint(player, {}, root, root / 'player.log', {}, {}, 'idle-published-1', cp, None)


if __name__ == '__main__':
    unittest.main()
