from pathlib import Path
import tempfile
import unittest

from tools import validate_ship_frame_progression as progression


class ShipFrameProgressionTests(unittest.TestCase):
    def test_actual_csharp_matches_224_source_phase_cases_and_64_arithmetic_cases(self):
        try:
            report = progression.validate()
        except progression.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(report["source_phase_cases"], 224)
        self.assertEqual(report["arithmetic_stress_cases"], 64)
        self.assertEqual(report["passed"], 288)
        self.assertEqual(report["hooked_callees"], {})
        self.assertTrue(report["checked_compilation"])
        by_input = {(row["input"]["frame"], row["input"]["heading"], row["input"]["now"],
                     row["input"]["last_tick"], row["input"]["interval"]):
                    (row["x86_frame"], row["x86_last_tick"]) for row in report["cases"]}
        self.assertEqual(by_input[20, 5, 2, 0, 2], (20, 0))  # strict threshold
        self.assertEqual(by_input[23, 5, 100, 0, 2], (20, 100))  # one step, no catchup
        self.assertEqual(by_input[20, 5, 1, 0xfffffffe, 2], (21, 1))  # uint wrap
        self.assertEqual(by_input[0x7fffffff, 0, 3, 0, 2], (-0x80000000, 3))  # signed limit
        self.assertEqual(by_input[-1, -1, 3, 0, 2], (-4, 3))  # signed heading

    def test_changed_original_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            changed = Path(temporary) / "ancient.exe"
            changed.write_bytes(b"changed original")
            with self.assertRaisesRegex(ValueError, "SHA-256 differs"):
                progression.validate(changed)


if __name__ == "__main__":
    unittest.main()
