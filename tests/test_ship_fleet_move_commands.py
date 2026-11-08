from pathlib import Path
import tempfile
import unittest

from tools import validate_ship_fleet_move_commands as commands


class ShipFleetMoveCommandsTests(unittest.TestCase):
    def test_membership_then_individual_move_packets_and_receivers_match_original(self):
        result = commands.validate()
        self.assertTrue(result['fresh_native'])
        self.assertEqual(result['fallback_cases'], 12)
        self.assertEqual(result['api_controls'], 13)

    def test_changed_fixture_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'changed.json'
            path.write_text('{}')
            with self.assertRaisesRegex(AssertionError, 'Fleet move fixture SHA differs'):
                commands.load(path)

    def test_oracle_detects_wrong_fallback_byte_and_actor_address(self):
        data = commands.load()
        source = commands.SOURCE.read_text()
        for before, after in [('formation.Succeeded ? (byte)0 : (byte)255', 'formation.Succeeded ? (byte)0 : (byte)0'),
                              ('InstanceId = instanceId;', 'InstanceId = 11;')]:
            with self.subTest(before=before), tempfile.TemporaryDirectory() as directory:
                self.assertEqual(source.count(before), 1)
                path = Path(directory) / 'ShipFleetMoveCommands.cs'
                path.write_text(source.replace(before, after))
                with self.assertRaisesRegex(AssertionError, 'Fleet move (mismatch|execution failed)'):
                    commands.compare(data, source=path)


if __name__ == '__main__':
    unittest.main()
