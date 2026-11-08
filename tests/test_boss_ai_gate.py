import unittest

from tools import validate_boss_ai_gate as gate


class BossAiGateDifferentialTests(unittest.TestCase):
    def test_original_x86_dispatch_matches_actual_csharp_for_35_cases(self):
        try:
            result = gate.validate()
        except gate.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(result["case_count"], 35)
        self.assertEqual(result["passed"], 35)
        self.assertEqual(result["original_sha256"], gate.EXPECTED)


if __name__ == "__main__":
    unittest.main()
