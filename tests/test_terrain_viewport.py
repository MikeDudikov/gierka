import unittest

from tools import validate_terrain_viewport as viewport


class TerrainViewportDifferentialTests(unittest.TestCase):
    def test_original_x86_geometry_matches_actual_csharp_for_1080_cases(self):
        try:
            result = viewport.validate()
        except viewport.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(result["case_count"], 1080)
        self.assertEqual(result["passed"], 1080)
        self.assertEqual(result["clamp_cases"], 702)
        self.assertEqual(result["position_cases"], 378)
        self.assertEqual(result["axis_comparisons"], 2160)
        self.assertEqual(result["original_sha256"], viewport.EXPECTED)
        self.assertTrue(result["checked_compilation"])


if __name__ == "__main__":
    unittest.main()
