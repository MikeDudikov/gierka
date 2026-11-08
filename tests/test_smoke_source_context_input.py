from pathlib import Path
import hashlib
import unittest
from tools import smoke_source_context_input as proof

ROOT = Path(__file__).resolve().parents[1]
PINS = {
    'left': '49a84bdf197756caad7abdfa91d325fb5989cc4d86fb81e8124978fe54db2836',
    'right': '2be52cd0768629799050a0ebeefec4b2f8d10cf6c1cbcd03c88bbe29eba0f2b4',
}


class SourceContextRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = {}
        for name, position in (('left', 0), ('right', 3)):
            path = ROOT / 'tests/fixtures' / ('source_context_' + name + '_player.log')
            assert hashlib.sha256(path.read_bytes()).hexdigest() == PINS[name]
            cls.profiles[name] = (path.read_text(), proof.reference(position, name == 'right'))

    def test_actual_players_preserve_world_and_route_through_context_reset(self):
        for name, (log, reference) in self.profiles.items():
            with self.subTest(name=name):
                rows, done = proof.validate_log(log, reference)
                self.assertTrue(done)
                self.assertEqual(len(rows), 39)
                self.assertEqual(len(reference['markers']['context-blocked']), 2)
                self.assertEqual(reference['markers']['context-reset'], [])
                self.assertEqual(len(reference['key_events']), 5)
                self.assertEqual(len(reference['key_controls']), 4)

    def test_checker_rejects_context_order_state_and_existing_world_faults(self):
        for name, (log, reference) in self.profiles.items():
            with self.subTest(name=name):
                controls = proof.negative_controls(log, reference)
                self.assertEqual(len(controls), 13)
                self.assertIn('context_advanced_tick', controls)
                self.assertIn('reset_kept_key_state', controls)


if __name__ == '__main__':
    unittest.main()
