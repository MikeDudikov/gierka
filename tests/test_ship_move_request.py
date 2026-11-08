import unittest

from tools import validate_ship_move_request as request


class ShipMoveRequestDifferentialTests(unittest.TestCase):
    def test_actual_action20_and_idle_promotion_match_checked_csharp(self):
        try:
            report = request.validate()
        except request.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(report["native_request_cases"], 47)
        self.assertEqual(report["native_source_cases"], 8)
        self.assertEqual(report["native_stress_cases"], 39)
        self.assertEqual(report["native_priority_prefix_cases"], 31)
        self.assertEqual(report["case_count"], 45)
        self.assertEqual(report["passed"], 45)
        self.assertEqual(report["source_case_count"], 8)
        self.assertEqual(report["step_comparisons"], 169)
        self.assertEqual(report["csharp_contract_checks"], 10)
        self.assertTrue(report["checked_compilation"])
        self.assertEqual(report["fixture_sha256"], request.FIXTURE_SHA256)
        self.assertEqual(report["hooks"]["priority_prefix"], {})
        self.assertEqual(report["hooks"]["request_and_idle_consumer"],
                         {"0x587318": "normal setjmp return"})


if __name__ == "__main__":
    unittest.main()
