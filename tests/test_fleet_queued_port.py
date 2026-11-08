from pathlib import Path
import tempfile,unittest
from tools import validate_fleet_queued_port as port
from tools import validate_ship_fleet_normal_task as normal
from tools import validate_ship_fleet_group_tasks as groups
from tools import validate_ship_world_step as world


class FleetQueuedPortTests(unittest.TestCase):
    def test_single_owner_matches_fresh_x86_and_explicit_heap_contexts(self):
        result=port.validate()
        self.assertEqual((result['cases'],result['canonical_states'],result['api_controls']),(64,1121,19))
        self.assertTrue(result['fresh_x86']);self.assertEqual(result['wave']['signed_words'],11520)
        self.assertTrue(result['world_guard']['counter_phase_mail_actors_grid_unchanged'])
        self.assertFalse(result['world_queued_integration']);self.assertFalse(result['ui_shift_enabled'])

    def test_corpus_rejects_behavioral_mutations_in_the_actual_csharp_task(self):
        original=(port.SIM/'ShipFleetNormalTask.cs').read_text()
        mutations=[('global-dedup','if (!duplicate) queuedPoints.Add','if (!duplicate || queuedPoints.Count >= 0) queuedPoints.Add'),
            ('lifo','for (int i = events.Count - 1; i >= 0; i--)','for (int i = 0; i < events.Count; i++)'),
            ('age-boundary','if (elapsedSteps > 100)','if (elapsedSteps >= 100)'),
            ('signed-prefix','best < prefix','unchecked((ushort)best) < unchecked((ushort)prefix)'),
            ('stale-target','if (member.X == cell % width && member.Y == cell / width)','if (true)')]
        for name,before,after in mutations:
            with self.subTest(name=name),tempfile.TemporaryDirectory()as directory:
                self.assertIn(before,original);path=Path(directory)/'ShipFleetNormalTask.cs';path.write_text(original.replace(before,after))
                with self.assertRaisesRegex(AssertionError,'Queued port mismatch|Queued port execution failed'):
                    port.compare(overrides={'ShipFleetNormalTask.cs':path})

    def test_normal_tasks_membership_and_existing_world_registration_are_unchanged(self):
        self.assertTrue(normal.compare(normal.load())['passed'])
        self.assertTrue(groups.compare(groups.load())['passed'])
        self.assertTrue(world.compare(world.load())['passed'])


if __name__=='__main__':unittest.main()
