from pathlib import Path
import tempfile
import unittest

from tools import validate_ship_fleet_membership as membership


class ShipFleetMembershipTests(unittest.TestCase):
    def test_ordered_commit_reassignment_and_fifo_reception_match_fresh_original(self):
        result = membership.validate()
        self.assertTrue(result['passed'])
        self.assertTrue(result['fresh_native'])
        self.assertEqual(result['cases'], 258)
        self.assertEqual(result['states'], 2175)
        self.assertEqual(result['api_controls'], 23)

    def test_changed_fixture_is_rejected_before_native_or_csharp_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'changed.json'
            path.write_text('{}')
            with self.assertRaisesRegex(AssertionError, 'Membership fixture SHA differs'):
                membership.load(path)

    def test_oracle_detects_missing_removal_packet_and_early_simulation_membership(self):
        fixture = membership.load()
        original = membership.SOURCE.read_text()
        mutations = [
            ('missing-removal', 'commands.Add(new ShipFleetMembershipCommand(actor.Id, -1));', ''),
            ('early-simulation', 'actor.UiGroup = checked((short)next);',
             'actor.UiGroup = checked((short)next); actor.SimulationGroup = actor.UiGroup;'),
        ]
        for label, before, after in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                self.assertEqual(original.count(before), 1)
                source = Path(directory) / 'ShipFleetMembership.cs'
                source.write_text(original.replace(before, after))
                with self.assertRaisesRegex(AssertionError, 'Membership (mismatch|execution failed)'):
                    membership.compare_fixture(fixture, source)


if __name__ == '__main__':
    unittest.main()
