import unittest

from tools import validate_mission_object_selection as selection


class MissionObjectSelectionDifferentialTests(unittest.TestCase):
    def test_original_object_filter_dispatch_ids_and_order_match_actual_csharp(self):
        try:
            report = selection.validate()
        except selection.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(report["passed"], 1450)
        self.assertEqual(report["case_count"], 1450)
        self.assertEqual(report["case_groups"], {"source": 315, "tag-stress": 1003,
                                                "slot-stress": 120, "kind-bypass": 4,
                                                "id-boundary": 8})
        self.assertEqual(report["configuration_csharp_checks"], 36)
        self.assertTrue(report["checked_compilation"])
        self.assertEqual(report["original_enumeration"]["all_record_count"], 63)
        self.assertEqual(report["original_enumeration"]["object_count"], 45)
        self.assertEqual(report["original_enumeration"]["hooks"], {})
        self.assertEqual(len(report["source_start_scenario"]), 45)
        self.assertTrue(all(row["selected"] for row in report["source_start_scenario"]))
        self.assertEqual(report["fixture_sha256"], selection.FIXTURE_SHA256)


if __name__ == "__main__":
    unittest.main()
