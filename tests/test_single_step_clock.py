import unittest

from tools import validate_single_step_clock as clock


class SingleStepClockDifferentialTests(unittest.TestCase):
    def test_original_branch_matches_actual_csharp_at_boundaries_and_after_callbacks(self):
        try:
            result = clock.validate()
        except clock.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(result["case_count"], 1287)
        self.assertEqual(result["passed"], result["case_count"])
        self.assertEqual(result["callback_mutation_cases"], 63)
        self.assertEqual(result["invalid_quantum_csharp_checks"], 4)
        self.assertEqual(result["original_sha256"], clock.EXPECTED)


if __name__ == "__main__":
    unittest.main()
