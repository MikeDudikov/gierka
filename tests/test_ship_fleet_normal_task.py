from pathlib import Path
import tempfile
import unittest
from tools import validate_ship_fleet_normal_task as task


class ShipFleetNormalTaskTests(unittest.TestCase):
    def test_task_clock_events_assignments_and_packets_match_fresh_original(self):
        result = task.validate()
        self.assertTrue(result['fresh_native'])
        self.assertEqual(result['cases'], 124)
        self.assertEqual(result['api_controls'], 20)
        self.assertGreater(result['watch35_packets'], 0)

    def test_changed_fixture_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'changed.json'; path.write_text('{}')
            with self.assertRaisesRegex(AssertionError, 'Normal task fixture SHA differs'):
                task.load(path)

    def test_oracle_detects_clock_queue_slot_assignment_and_payload_regressions(self):
        data = task.load(); source = task.SOURCE.read_text()
        mutations = [
            ('elapsedSteps > 100', 'elapsedSteps >= 100'),
            ('int index = events.Count - 1; index >= 0; index--', 'int index = 0; index < events.Count; index++'),
            ('if (slots[item.MemberIndex] == item.InstanceId) return true;', ''),
            ('new List<Assignment>(assignments)', 'new List<Assignment>()'),
            ('SourceDistance(member.X, x) > 1', 'SourceDistance(member.X, x) > 0'),
            ('watch[21] = 255', 'watch[21] = 0')]
        for before, after in mutations:
            with self.subTest(before=before), tempfile.TemporaryDirectory() as directory:
                self.assertIn(before, source)
                changed = Path(directory) / 'ShipFleetNormalTask.cs'
                changed.write_text(source.replace(before, after, 1))
                with self.assertRaisesRegex(AssertionError, 'Normal task (mismatch|execution failed)'):
                    task.compare(data, source=changed)


if __name__ == '__main__':
    unittest.main()
