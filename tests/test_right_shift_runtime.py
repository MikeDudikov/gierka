from pathlib import Path
import hashlib
import unittest
from tools import smoke_queued_input as committed
from tools import smoke_pending_queued_input as pending

ROOT = Path(__file__).resolve().parents[1]
PINS = {'right_committed': ('3e20ee559650b49088a606c233e38da4d3c4da941cba2a1a92f502bbdae97e94', 0, True), 'right_pending': ('d031143d2a56e6f306f350b9cfc89d3bcd22cea862ff09fb31f9b7f9311ab40f', 3, True), 'left_pending': ('06343aa0ae64bb28d3377b0512737d263e6b1b5e32c2e46a4c861918ebb43b59', 0, False)}


class RightShiftRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = {}
        for name, (sha, position, right) in PINS.items():
            path = ROOT / 'tests/fixtures' / ('right_shift_' + name + '_player.log')
            assert hashlib.sha256(path.read_bytes()).hexdigest() == sha
            qa = committed if name == 'right_committed' else pending
            reference = qa.reference(position, source_keys=True)
            key_name = 'RightShift' if right else 'LeftShift'
            reference['key_controls'] = [(key_name, row[1]) for row in reference['key_events']]
            cls.profiles[name] = (qa, path.read_text(), reference)

    def test_actual_right_and_default_left_key_controls_preserve_source_world_and_marker_outputs(self):
        for name, (qa, log, reference) in self.profiles.items():
            with self.subTest(profile=name):
                rows, done = committed.validate_log(log, reference)
                self.assertTrue(done)
                self.assertEqual(len(rows), 33 if name == 'right_committed' else 35)
                self.assertEqual(len(reference['key_controls']), 4)

    def test_checker_rejects_wrong_physical_control_even_when_boolean_envelopes_are_unchanged(self):
        for name, (qa, log, reference) in self.profiles.items():
            with self.subTest(profile=name):
                detected = qa.negative_controls(log, reference)
                self.assertIn('wrong_shift_control', detected)
                self.assertEqual(len(detected), 8 if name == 'right_committed' else 9)


if __name__ == '__main__':
    unittest.main()
