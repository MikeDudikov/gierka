import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools import validate_source_sprite_depth_queue as depth


class SourceSpriteDepthQueueTests(unittest.TestCase):
    def test_actual_checked_csharp_matches_fresh_original_registration_and_updates(self):
        try:
            result = depth.validate()
        except depth.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(result['passed'], 3849)
        self.assertEqual(result['case_count'], 14)
        self.assertEqual(result['guard_count'], 14)
        self.assertEqual(set(result['guards']), depth.GUARDS)
        self.assertEqual(result['register_operations'] + result['update_operations'], 3849)
        self.assertTrue(result['checked_compilation'])
        self.assertEqual(result['native_hooks'], [])

    def test_native_cohort_ties_retain_the_side_reached_by_publication_history(self):
        try:
            trace = depth.original_cohort_trace([267, 268, 268, 269, 268, 267, 323, 324, 325, 324])
        except depth.MissingPrerequisite as error:
            self.skipTest(str(error))
        ids = {(row['resource_name'], row['kind']): row['node_id'] for row in trace['registration']}
        b, d, c = [ids[('OBJ_000000' + instance, 'inline_parent')] for instance in ('0b', '0d', '0c')]
        earlier = lambda state, first, second: state['draw_order'].index(first) < state['draw_order'].index(second)
        rows = trace['states']
        self.assertTrue(earlier(rows[1], b, d))
        self.assertEqual(rows[1], rows[2])
        self.assertTrue(earlier(rows[4], d, b))
        self.assertTrue(earlier(rows[7], b, c))
        self.assertTrue(earlier(rows[9], c, b))
        self.assertEqual(len(trace['registration']), 21)
        self.assertTrue(all(sorted(row['draw_order']) == list(range(21)) for row in rows))

    def test_changed_fixture_or_executable_is_rejected_before_native_execution(self):
        with tempfile.TemporaryDirectory(prefix='source-depth-tamper-') as temporary:
            changed = Path(temporary) / 'changed.json'
            changed.write_bytes(depth.FIXTURE.read_bytes() + b' ')
            with self.assertRaisesRegex(AssertionError, 'fixture SHA-256'):
                depth.load_fixture(changed)
            changed_exe = Path(temporary) / 'changed.exe'
            changed_exe.write_bytes(b'not-the-verified-original')
            with self.assertRaisesRegex(ValueError, 'executable SHA-256'):
                depth.original_cohort_trace([268], original=changed_exe)


if __name__ == '__main__':
    unittest.main()
