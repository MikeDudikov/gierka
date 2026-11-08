import json
from pathlib import Path
import tempfile
import unittest

from tools import validate_ship_route_planner as planner


class ShipRoutePlannerTests(unittest.TestCase):
    def test_all_original_map_goals_and_planning_maps_match_checked_csharp(self):
        try:
            report=planner.validate()
        except planner.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual((report['passed'],report['planned'],report['no_route']), (576,362,214))
        self.assertEqual(report['guard_count'],9)
        self.assertTrue(report['checked_compilation'])
        by_goal={tuple(case['goal']):case for case in report['cases']}
        self.assertEqual(by_goal[14,4]['points'],[[16,2,5],[15,3,5],[14,4,5]])
        self.assertEqual(by_goal[18,5]['points'],[[16,2,7],[17,3,7],[18,4,7],[18,5,6]])
        self.assertTrue(by_goal[19,4]['planned'])  # destination restores base terrain after local occupancy overlay
        self.assertFalse(by_goal[16,1]['planned'])
        self.assertFalse(by_goal[16,2]['planned'])
        self.assertEqual(by_goal[20,4]['return_low_byte'],0)

    def test_changed_native_planner_evidence_is_rejected_before_execution(self):
        fixture=planner.load_fixture();fixture['cases'][0]['planned']=not fixture['cases'][0]['planned']
        with tempfile.TemporaryDirectory()as temporary:
            p=Path(temporary)/'changed.json';p.write_text(json.dumps(fixture))
            with self.assertRaisesRegex(ValueError,'fixture SHA-256'):
                planner.load_fixture(p)


if __name__=='__main__':unittest.main()
