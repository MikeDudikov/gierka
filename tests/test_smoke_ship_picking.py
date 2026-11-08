import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
from tools import smoke_ship_picking as picking

order = picking.order


def row_line(kind, row):
    fields = picking.ACTOR_FIELDS if kind == 'actor' else picking.QUERY_FIELDS if kind == 'query' else picking.COMPLETE_FIELDS
    def encode(key, value):
        if key == 'id': return f'{value:08x}'
        if key == 'picked': return 'none' if value is None else f'{value:08x}'
        if key == 'visited': return ','.join(f'{v:08x}' for v in value)
        if isinstance(value, list): return ','.join(map(str, value))
        return str(value)
    return picking.PREFIX + kind + ': ' + '; '.join(key + '=' + encode(key, row[key]) for key in fields)


def order_stage(row):
    return order.PREFIX + ' '.join(key + '=' + (','.join(map(str, row[key])) if key in order.PAIR_FIELDS else str(row[key]))
                                   for key in order.STAGE_FIELDS)


def valid_log(reference, case, expected, stop_at=None):
    lines = [picking.READY, order.conditions_line(case)]
    for r in order.expected_registration(reference, case):
        lines.append(order.PREFIX + f"registration: node={r['node']}; kind={r['kind']}; id={r['id']:08x}; depth={r['depth']}; components={r['components']}")
    for stage, cp in expected.items():
        lines.extend((order_stage(cp['checkpoint']), order.PREFIX + f"path: stage={stage}; count={cp['expected_path']['count']}; points_hex={cp['expected_path']['points_hex']}"))
        for part in cp['expected_parts']:
            lines.append(order.PREFIX + f"part: stage={stage}; source_index={part['source_index']}; sprite={part['sprite']}; order={part['order']}; position=" + ','.join(map(str, part['position'])))
        for r in cp['expected_queue_rows']:
            lines.append(order.PREFIX + f"queue: stage={stage}; node={r['node']}; kind={r['kind']}; id={r['id']:08x}; part={r['part']}; depth={r['depth']}; order={r['order']}")
        for index, actor in enumerate(cp['expected_actors']):
            lines.append(row_line('actor', actor))
            lines.extend(row_line('query', q) for q in cp['expected_queries'][index * 2:index * 2 + 2])
        lines.extend(row_line('query', q) for q in cp['expected_queries'][16:])
        lines.append(row_line('checkpoint_complete', {'stage': stage, 'sample': cp['checkpoint']['sample_index'],
                                                      'query_count': len(cp['expected_queries']), 'grid_unchanged': True}))
    sample = order.stage_plan(case, stop_at)[-1][1]
    lines.extend((order.completion_line(case, stop_at),
                  f"Mission unit reference cleanup: claimed_released={sample['occupied_cell_count']}; visual_refs_cleared=True",
                  order.movement.DIAGNOSTIC_EXIT))
    return '\n'.join(lines) + '\n'


class PickingReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = picking.ROOT / 'reference/raw/ancient-conquest'
        if not all((root / name).is_file() for name in picking.mask_source.staging.SOURCE_HASHES):
            raise unittest.SkipTest('Private original ship inputs unavailable')
        cls.reference = picking.load_reference()
        cls.expected = {}
        for spec in picking.CASES:
            case = cls.reference['native_order'][spec['label']]
            cls.expected[spec['name']] = picking.checkpoints(cls.reference, case, spec['stop_at'])

    def normal(self):
        return self.reference['native_order']['reach18_5'], self.expected['normal']

    def test_fresh_native_world_queries_cover_actual_poses_claims_and_reservation_alias(self):
        count = 0
        for spec in picking.CASES:
            case = self.reference['native_order'][spec['label']]; expected = self.expected[spec['name']]
            parsed = picking.validate_log(valid_log(self.reference, case, expected, spec['stop_at']),
                                           self.reference, case, expected, complete=True, stop_at=spec['stop_at'])
            self.assertEqual(len(parsed['actors']), len(expected))
            self.assertEqual(sum(len(v) for v in parsed['actors'].values()), len(expected) * 8)
            self.assertTrue(all(len(v) == 1 for v in parsed['completions'].values()))
            count += len(expected)
        self.assertEqual(count, 53)
        case, expected = self.normal(); reserved = expected['reserved-1']; queries = {q['label']: q for q in reserved['expected_queries']}
        coarse, precise = queries['source0b-reservation-center-coarse'], queries['source0b-reservation-center-precise']
        self.assertEqual((coarse['picked'], coarse['visited']), (11, [11]))
        self.assertEqual((precise['picked'], precise['visited']), (None, [11, 11]))
        self.assertEqual(reserved['expected_actors'][0]['claims'], [64, 89])
        idle = expected['idle-published-1']['expected_actors'][0]
        self.assertEqual((idle['stored_frame'], idle['sprite'], idle['claims']), (81, [1156, 324], [138]))
        self.assertEqual(idle['stored_frame'], case['samples'][102]['frame'])
        self.assertNotEqual(idle['stored_frame'], case['samples'][102]['drawn_frame'])

    def test_actor_query_and_completion_corruptions_are_rejected(self):
        case, expected = self.normal(); good = valid_log(self.reference, case, expected)
        actor = row_line('actor', expected['idle-published-1']['expected_actors'][0])
        query = row_line('query', expected['initial']['expected_queries'][0])
        precise = next(q for q in expected['reserved-1']['expected_queries'] if q['label'] == 'source0b-reservation-center-precise')
        precise_line = row_line('query', precise)
        complete = row_line('checkpoint_complete', {'stage': 'initial', 'sample': 0, 'query_count': 25, 'grid_unchanged': True})
        actor_initial = row_line('actor', expected['initial']['expected_actors'][0])
        mutations = {
            'missing-ready': good.replace(picking.READY + '\n', ''),
            'duplicate-ready': picking.READY + '\n' + good,
            'wrong-payload': good.replace(picking.MASK_PAYLOAD_SHA256, '0' * 64),
            'mouse-claim': good.replace('selection=False; mouse=False', 'selection=False; mouse=True'),
            'wrong-id': good.replace(actor, actor.replace('id=0000000b', 'id=0000000c')),
            'wrong-descriptor': good.replace(actor, actor.replace('SHIP_A1110', 'SHIP_H1110')),
            'wrong-class': good.replace(actor, actor.replace('class=200', 'class=207')),
            'wrong-heading': good.replace(actor, actor.replace('heading=6', 'heading=5')),
            'drawn-used-as-stored': good.replace(actor, actor.replace('stored_frame=81', 'stored_frame=80')),
            'wrong-sprite': good.replace(actor, actor.replace('sprite=1156,324', 'sprite=1157,324')),
            'lost-claim': good.replace(actor, actor.replace('claims=138', 'claims=')),
            'wrong-reservation-alias': good.replace('claims=64,89', 'claims=64,90'),
            'duplicate-actor': good.replace(actor, actor + '\n' + actor),
            'query-before-actor': good.replace(actor_initial + '\n' + query, query + '\n' + actor_initial),
            'wrong-sample': good.replace(query, query.replace('sample=0', 'sample=1')),
            'wrong-index': good.replace(query, query.replace('index=0', 'index=1')),
            'wrong-label': good.replace(query, query.replace('center-coarse', 'center-precise')),
            'wrong-world': good.replace(query, query.replace('world=1056,160', 'world=1057,160')),
            'wrong-cell': good.replace(query, query.replace('cell=16,2', 'cell=17,2')),
            'wrong-precision': good.replace(query, query.replace('precise=False', 'precise=True')),
            'wrong-hit': good.replace(query, query.replace('picked=0000000b', 'picked=none')),
            'missing-visit': good.replace(query, query.replace('visited=0000000b', 'visited=')),
            'deduplicated-owner': good.replace(precise_line, precise_line.replace('visited=0000000b,0000000b', 'visited=0000000b')),
            'wrong-hit-on-precise-miss': good.replace(precise_line, precise_line.replace('picked=none', 'picked=0000000b')),
            'duplicate-query': good.replace(query, query + '\n' + query),
            'missing-query': good.replace(query + '\n', ''),
            'unknown-query-field': good.replace(query, query + '; extra=1'),
            'duplicate-query-field': good.replace(query, query + '; index=0'),
            'invalid-owner-width': good.replace(query, query.replace('picked=0000000b', 'picked=b')),
            'missing-completion': good.replace(complete + '\n', ''),
            'duplicate-completion': good.replace(complete, complete + '\n' + complete),
            'wrong-completion-sample': good.replace(complete, complete.replace('sample=0', 'sample=1')),
            'wrong-completion-count': good.replace(complete, complete.replace('query_count=25', 'query_count=24')),
            'mutated-grid': good.replace(complete, complete.replace('grid_unchanged=True', 'grid_unchanged=False')),
            'premature-completion': good.replace(actor_initial, complete + '\n' + actor_initial),
            'unknown-picking-line': good + picking.PREFIX + 'mystery: value=1\n',
        }
        for name, bad in mutations.items():
            self.assertNotEqual(good, bad, name)
            with self.subTest(name=name), self.assertRaises((AssertionError, ValueError)):
                picking.validate_log(bad, self.reference, case, expected, complete=True)

    def test_last_stage_can_be_partial_but_completed_capture_requires_marker(self):
        case, expected = self.normal(); good = valid_log(self.reference, case, expected)
        complete = row_line('checkpoint_complete', {'stage': 'idle-published-1', 'sample': 102,
                                                   'query_count': 25, 'grid_unchanged': True})
        partial = good[:good.index(complete)]
        parsed = picking.validate_log(partial, self.reference, case, expected)
        self.assertEqual(len(parsed['queries']['idle-published-1']), 25)
        self.assertNotIn('idle-published-1', parsed['completions'])
        with self.assertRaises(AssertionError):
            picking.validate_log(partial, self.reference, case, expected, complete=True)

    def test_zero_owner_identity_and_duplicate_visits_are_preserved_by_parser(self):
        log = order.PREFIX + 'stage=zero\n' + row_line('query', {'stage': 'zero', 'sample': 0, 'index': 0,
                'label': 'zero', 'world': [0, 0], 'cell': [0, 0], 'precise': True, 'picked': 0, 'visited': [0, 0]})
        _, rows, _, _ = picking.picking_records(log)
        self.assertEqual(rows['zero'][0]['picked'], 0)
        self.assertEqual(rows['zero'][0]['visited'], [0, 0])
        self.assertNotEqual(rows['zero'][0]['picked'], None)


class PickingFenceTests(unittest.TestCase):
    def exercise(self, changed=False, incomplete=False):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory); image = Image.new('RGB', (8, 8)); png = output/'frame.png'; image.save(png)
            expected = {'held': {'expected_image': image, 'regions': [], 'expected_queries': [{}] * 25}}
            parsed = {'stages': [{'stage': 'held'}], 'parts': {'held': [{}] * 3}, 'queue': {'held': [{}] * 34},
                      'actors': {'held': [{}] * 8}, 'queries': {'held': [{'picked': 11}] * 25},
                      'completions': {} if incomplete else {'held': [{'grid_unchanged': True}]}}
            after = copy.deepcopy(parsed)
            if changed: after['queries']['held'][0]['picked'] = None
            player = type('Player', (), {'poll': lambda self: None})()
            with patch.object(picking, 'validate_log', side_effect=[parsed, after]), \
                    patch.object(picking.terrain, 'read_log', return_value='log'), \
                    patch.object(picking.menu, 'capture', return_value=png), \
                    patch.object(picking.order, 'frame_metrics', return_value=(True, {'matched': True})):
                return picking.capture_checkpoint(player, {}, output, output/'player.log', {}, {}, 'held', expected, None)

    def test_capture_accepts_complete_constant_query_state(self):
        self.assertEqual(self.exercise()['presentation_attempt_count'], 1)

    def test_capture_rejects_query_mutation_when_motion_and_pixels_stay_constant(self):
        with self.assertRaisesRegex(AssertionError, 'Motion, actor binding, picking result'):
            self.exercise(changed=True)

    def test_capture_rejects_missing_grid_nonmutation_completion_marker(self):
        with self.assertRaisesRegex(AssertionError, 'incomplete before capture'):
            self.exercise(incomplete=True)
