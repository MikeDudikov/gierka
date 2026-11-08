import unittest

from tools import validate_mission_ship_seed as ship


class MissionShipSeedDifferentialTests(unittest.TestCase):
    def test_actual_source_ship_projection_and_anchor_match_checked_csharp(self):
        try:
            report = ship.validate()
        except ship.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(report["case_count"], 184)
        self.assertEqual(report["passed"], 184)
        self.assertEqual(report["source_count"], 8)
        self.assertEqual(report["case_groups"], {"source": 8, "variant-heading": 96,
                                                "byte-fields": 10, "full-model": 10,
                                                "health-input": 12, "order-metadata": 6,
                                                "anchor-arithmetic": 42})
        self.assertEqual(report["csharp_contract_checks"], 9)
        self.assertTrue(report["checked_compilation"])
        self.assertEqual(report["anchor_instruction_range"]["hooks"], {})
        self.assertEqual(report["fixture_sha256"], ship.FIXTURE_SHA256)
        self.assertTrue(all(row["observed_damage_state"] == 1 for row in report["original_source_records"]))


if __name__ == "__main__":
    unittest.main()
