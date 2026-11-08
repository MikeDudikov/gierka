from pathlib import Path
import tempfile
import unittest

from tools import validate_mission_initial_setup as setup


class MissionInitialSetupDifferentialTests(unittest.TestCase):
    def reference(self):
        try:
            return setup.load_reference()
        except setup.MissingPrerequisite as error:
            self.skipTest(str(error))

    def test_actual_csharp_matches_original_selection_and_view_lookup(self):
        try:
            result = setup.validate()
        except setup.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(result["passed"], 177)
        self.assertEqual(result["case_count"], 177)
        self.assertEqual(result["source_case_count"], 1)
        self.assertEqual(result["synthetic_case_count"], 176)
        self.assertEqual(result["intercepted_functions"], [])
        self.assertTrue(result["checked_compilation"])
        self.assertEqual(set(result["csharp_guard_checks"]), setup.EXPECTED_GUARDS)
        self.assertEqual(result["csharp_guard_count"], 25)
        source = result["cases"][0]
        self.assertTrue(source["source_miss000"])
        self.assertEqual((source["selected_side"], source["selected_player"]), (1, 1))
        self.assertEqual(source["saved_origin"], [15, 0])
        self.assertEqual([(index, value) for index, value in
                          enumerate(bytes.fromhex(source["players_descriptor_hex"])) if value],
                         [(5, 1), (16, 3)])
        self.assertEqual({case["campaign_index"] for case in result["cases"]}, {0, 1, 2, 3})

    def test_changed_mission_inputs_are_rejected_before_resource_decoding(self):
        self.reference()
        with tempfile.TemporaryDirectory(prefix="mission-setup-source-") as temporary:
            prefix = Path(temporary) / "miss000"
            for suffix in (".dkx", ".dkd"):
                original = setup.MISSION.with_suffix(suffix).read_bytes()
                changed = bytearray(original)
                changed[len(changed) // 2] ^= 0x80
                for candidate in (".dkx", ".dkd"):
                    prefix.with_suffix(candidate).write_bytes(changed if candidate == suffix
                        else setup.MISSION.with_suffix(candidate).read_bytes())
                with self.subTest(changed=suffix), self.assertRaises(ValueError):
                    setup.load_reference(prefix)

    def test_changed_original_executable_is_rejected(self):
        self.reference()
        if not setup.ORIGINAL.is_file():
            self.skipTest("Original executable missing")
        original = bytearray(setup.ORIGINAL.read_bytes())
        original[-1] ^= 1
        with tempfile.TemporaryDirectory(prefix="mission-setup-executable-") as temporary:
            executable = Path(temporary) / "ancient.exe"
            executable.write_bytes(original)
            try:
                with self.assertRaises(ValueError):
                    setup.validate(original=executable)
            except setup.MissingPrerequisite as error:
                self.skipTest(str(error))


if __name__ == "__main__":
    unittest.main()
