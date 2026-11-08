import tempfile
import unittest
from pathlib import Path

from tools import validate_mission_reef_seed as reef


class MissionReefSeedTests(unittest.TestCase):
    def test_actual_csharp_reference_matches_5_source_cases_and_99_x86_stress_cases(self):
        try:
            result = reef.validate()
        except reef.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(result['fixture_source_cases'], 5)
        self.assertEqual(result['stress_cases'], 99)
        self.assertEqual(result['case_count'], 104)
        self.assertEqual(result['passed'], 104)
        self.assertEqual(result['csharp_guard_count'], 11)
        self.assertTrue(result['checked_compilation'])
        self.assertEqual(result['range_intercepted_functions'], [])

    def test_tampered_native_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            fixture = Path(folder) / 'fixture.json'
            fixture.write_bytes(reef.FIXTURE.read_bytes() + b' ')
            with self.assertRaisesRegex(ValueError, 'fixture hash differs'):
                reef.load_fixture(fixture)


if __name__ == '__main__':
    unittest.main()
