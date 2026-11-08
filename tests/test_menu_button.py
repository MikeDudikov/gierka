import unittest

from tools import validate_menu_button as button


class MenuButtonDifferentialTests(unittest.TestCase):
    def test_original_type_one_pointer_traces_match_actual_csharp(self):
        try:
            result = button.validate()
        except button.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(result["trace_count"], 44)
        self.assertEqual(result["passed"], result["case_count"])
        self.assertGreater(result["case_count"], 140)
        self.assertEqual(result["original_sha256"], button.gate.EXPECTED)


if __name__ == "__main__":
    unittest.main()
