import unittest

from tools import validate_briefing_difficulty as difficulty


class BriefingDifficultyDifferentialTests(unittest.TestCase):
    def test_original_type_five_pointer_paths_match_actual_csharp(self):
        try:
            report = difficulty.validate()
        except difficulty.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(report["passed"], report["case_count"])
        self.assertGreater(report["case_count"], 500)
        self.assertEqual(report["initial_choices"], [0, 1, 2])
        self.assertEqual(len(report["layouts"]), 2)
        self.assertEqual(report["configuration_csharp_checks"], 10)


if __name__ == "__main__":
    unittest.main()
