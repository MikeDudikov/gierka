import unittest

from tools import validate_ship_adjacent_planner as planner


class ShipAdjacentPlannerTests(unittest.TestCase):
    def test_source_adjacent_planner_matches_actual_x86(self):
        try:
            report=planner.validate()
        except planner.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual((report['case_count'],report['passed'],report['accepted'],report['source_blocked']), (8,8,6,2))
        self.assertEqual(report['guard_count'],18)
        self.assertTrue(report['checked_compilation'])
        self.assertEqual(report['fixture_sha256'],planner.FIXTURE_SHA256)
        self.assertTrue(all(case['navigation']['return_low_byte']==0 for case in report['native_evidence']['cases']))


if __name__=='__main__':unittest.main()
