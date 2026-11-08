from pathlib import Path
import tempfile
import unittest
from tools import validate_source_nearest_pathfinder as nearest


class SourceNearestPathfinderTests(unittest.TestCase):
    def test_actual_csharp_matches_nearest_source_paths_fields_and_reached_flag(self):
        try:
            report=nearest.validate()
        except nearest.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(report['passed'],1380)
        self.assertEqual(report['direct_cases'],850)
        self.assertEqual(report['wave_cases'],530)
        self.assertEqual(report['guard_count'],9)
        self.assertTrue(report['checked_compilation'])
        self.assertTrue(report['warnings_as_errors'])
        self.assertEqual(report['native_evidence']['algorithm_hooks'],[])
        cases={row['label']:row for row in report['native_evidence']['cases']}
        direct=cases['mission_(18, 2)_1'];wave=cases['mission_(18, 2)_0']
        self.assertEqual(direct['path_hex'],wave['path_hex'])
        self.assertEqual((direct['reached'],wave['reached']),(1,0))
        self.assertFalse(direct['used_wave']);self.assertTrue(wave['used_wave'])
        self.assertEqual(wave['wave_iterations'],2)
        self.assertEqual(cases['metric_2_2_open_2']['path_hex'],'00000000070000000007')
        self.assertEqual(cases['metric_2_2_open_2']['reached'],1)
        self.assertEqual(cases['metric_2_2_wave_2']['path_hex'],'00000000000000000004')
        self.assertEqual(cases['metric_2_2_wave_2']['reached'],0)

    def test_changed_fixture_is_rejected_without_execution_dependencies(self):
        with tempfile.TemporaryDirectory() as temporary:
            p=Path(temporary)/'changed.json';p.write_text('{}')
            with self.assertRaisesRegex(ValueError,'fixture SHA-256 differs'):
                nearest.load_fixture(p)


if __name__=='__main__':unittest.main()
