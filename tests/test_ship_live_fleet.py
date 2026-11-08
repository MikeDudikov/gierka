from pathlib import Path
import tempfile
import unittest

from tools import validate_ship_live_fleet as fleet


class ShipLiveFleetTests(unittest.TestCase):
    def test_actual_receipt_promotion_live_planning_and_three_body_motion_match_original(self):
        result = fleet.validate()
        self.assertTrue(result['fresh_native'])
        self.assertEqual((result['cases'], result['states'], result['tick_calls']), (14, 10827, 10740))
        self.assertEqual((result['requests'], result['group_word_inputs']), (45, 36))
        self.assertEqual(result['api_controls'], 33)
        self.assertEqual((result['planning_cases'], result['planning_field_cells']), (130, 149760))
        self.assertEqual((result['publications'], result['grid_mutations']), (1997, 196))

    def test_changed_fixture_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'changed.json'
            path.write_text('{}')
            with self.assertRaisesRegex(AssertionError, 'Live fleet fixture SHA differs'):
                fleet.load(path)

    def test_oracle_detects_wrong_group_cache_and_rng_policies(self):
        data = fleet.load()
        source = fleet.PLANNER.read_text()
        mutations = [
            ('if(actor.SimulationGroup!=-1 && actor.SimulationGroup==simulationGroup && !force)continue;',
             'if(actor.SimulationGroup!=-1 && actor.SimulationGroup==simulationGroup && force)continue;'),
            ('if(actor.IsShip && (actor.MovementState==4 || actor.MovementState==5))',
             'if(actor.IsShip && actor.MovementState==255)'),
            ('randomState=unchecked(randomState*0x41c64e6du+0x3039u);\n                force=',
             'randomState=unchecked(randomState*0x41c64e6du+0x3038u);\n                force='),
        ]
        for before, after in mutations:
            with self.subTest(before=before), tempfile.TemporaryDirectory() as directory:
                self.assertEqual(source.count(before), 1)
                path = Path(directory) / 'ShipReplanPlanner.cs'
                path.write_text(source.replace(before, after))
                with self.assertRaisesRegex(AssertionError, 'Live fleet (mismatch|execution failed)'):
                    fleet.compare(data, planner=path)


if __name__ == '__main__':
    unittest.main()
