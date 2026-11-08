from pathlib import Path
import tempfile
import unittest

from tools import validate_ship_idle_progression as idle


class ShipIdleProgressionTests(unittest.TestCase):
    def test_actual_checked_csharp_matches_whole_original_idle_and_init_seed_block(self):
        try:
            report = idle.validate()
        except idle.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(report['passed'], 4232)
        self.assertEqual(report['trace_count'], 32)
        self.assertEqual(report['normal_trace_calls'], 3840)
        self.assertEqual(report['seed_case_count'], 77)
        self.assertEqual(report['whole_move_ship_case_count'], 96)
        self.assertEqual(report['publication_count'], 456)
        self.assertEqual(report['release_call_count'], 56)
        self.assertEqual(report['grid_write_count'], 56)
        self.assertTrue(report['checked_compilation'])
        self.assertEqual(report['native_query_and_grid_hooks'], [])
        self.assertEqual(report['seed_hooks'], [])

    def test_source_trace_preserves_rng_without_draw_and_draws_before_stored_advance(self):
        fixture = idle.load_fixture()
        trace = next(case for case in fixture['cases'] if case['label'] == 'trace_h5_seed0')['entries']
        drawn = [(row['input']['now'], row['native']['draws'][0]['frame'])
                 for row in trace if row['native']['draws']]
        self.assertEqual(drawn, [(16, 76), (34, 77), (52, 78), (70, 79), (87, 79), (105, 78)])
        self.assertEqual(trace[0]['native']['result'][4], 12345)
        self.assertEqual(trace[0]['native']['result'][8], 0)
        first = trace[16]['native']
        self.assertEqual(first['draws'][0]['last_tick_at_draw'], 0)
        self.assertEqual(first['draws'][0]['frame'], 76)
        self.assertEqual(first['result'][0], 77)
        self.assertEqual(first['result'][2], 16)
        self.assertEqual(first['result'][3], 2)
        self.assertEqual(first['result'][5], 10953)
        self.assertEqual(first['result'][6], -1)
        self.assertEqual(first['grid_writes'][0]['cell'], 87)

    def test_native_idle_release_preserves_foreign_owner_and_current_cell(self):
        try:
            image, size = idle.image_checked()
        except idle.MissingPrerequisite as error:
            self.skipTest(str(error))
        oracle = idle.IdleOracle(image, size)
        case = dict(frame=20, heading=5, frame_step=1, now=100, last_tick=0,
                    interval=2, random_state=0, speed=7, reserved=87, cell=64)
        oracle.setup(case, foreign=True)
        result = oracle.invoke()
        self.assertEqual(result['release_calls'], [87])
        self.assertEqual(result['grid_writes'], [])
        self.assertEqual(oracle.r(idle.GRID + 8 + 87 * 24 + 4), idle.OBJ + 0x2000)
        self.assertEqual(oracle.r(idle.GRID + 8 + 64 * 24 + 4), idle.OBJ)
        self.assertEqual(result['result'][6], -1)
        case['reserved'] = 64
        oracle.setup(case)
        result = oracle.invoke()
        self.assertEqual(result['release_calls'], [])
        self.assertEqual(result['grid_writes'], [])
        self.assertEqual(result['result'][6], -1)
        self.assertEqual(oracle.r(idle.GRID + 8 + 64 * 24 + 4), idle.OBJ)

    def test_changed_fixture_or_original_is_rejected_before_optional_analysis_imports(self):
        with tempfile.TemporaryDirectory(prefix='idle-provenance-') as temporary:
            p = Path(temporary) / 'changed.exe'
            p.write_bytes(b'not-the-verified-original')
            with self.assertRaisesRegex(ValueError, 'executable SHA-256'):
                idle.image_checked(p)
            p = Path(temporary) / 'changed.json'
            p.write_bytes(idle.FIXTURE.read_bytes() + b' ')
            with self.assertRaisesRegex(AssertionError, 'fixture SHA-256'):
                idle.load_fixture(p)


if __name__ == '__main__':
    unittest.main()
