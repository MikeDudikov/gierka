from pathlib import Path
import tempfile
import unittest

from tools import validate_source_wave_field as wave


class SourceWaveFieldTests(unittest.TestCase):
    def test_actual_csharp_matches_source_fields_and_iteration_counts(self):
        try:
            report=wave.validate()
        except wave.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(report['passed'],749)
        self.assertEqual(report['compared_field_cells'],390267)
        self.assertEqual(report['csharp_contract_checks'],9)
        self.assertEqual(report['original']['algorithm_intercepts'],[])
        self.assertTrue(report['checked_compilation'])
        self.assertTrue(report['warnings_as_errors'])
        groups={row['group'] for row in report['original']['cases']}
        self.assertIn('exhaustive3x3',groups)
        self.assertIn('original-source-map',groups)
        cases=report['original']['cases']
        self.assertTrue(any(row['result']==0 for row in cases))
        self.assertTrue(any(row['result']>1 for row in cases))
        self.assertTrue(all(row['wave_entries']==1 for row in cases))
        self.assertTrue(any(row['frontier_insertions']>256 for row in cases))

    def test_changed_original_is_rejected_before_wave_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            source=Path(temporary)
            (source/'installed').mkdir()
            (source/'installed/ancient.exe').write_bytes(b'changed original')
            with self.assertRaisesRegex(ValueError,'SHA-256 differs'):
                wave.validate(source)


if __name__=='__main__':unittest.main()
