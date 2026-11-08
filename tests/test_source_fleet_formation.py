from pathlib import Path
import tempfile
import unittest

from tools import validate_source_fleet_formation as formation


class SourceFleetFormationTests(unittest.TestCase):
    def test_formations_full_fields_and_complete_waves_match_fresh_original(self):
        result = formation.validate()
        self.assertTrue(result['fresh_native'])
        self.assertEqual((result['formation_cases'], result['formation_exact'], result['heading_guards']), (3028, 2988, 40))
        self.assertEqual((result['mission_passable_cases'], result['full_wave_cases']), (1452, 5250))
        self.assertEqual(result['api_controls'], 19)

    def test_changed_fixtures_are_rejected_before_execution(self):
        for name in formation.HASHES:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / name
                path.write_text('{}')
                with self.assertRaisesRegex(AssertionError, 'Formation fixture SHA differs'):
                    formation.load(name, path)

    def test_source_direction_tie_and_fixed_terrain_index_regressions_are_detected(self):
        data = formation.load('source_fleet_formation.json')
        source = formation.SOURCE.read_text()
        mutations = [
            ('reverse-direction', 'originY, false) - 4)', 'originY, false) - 1)'),
            ('candidate-tie', 'a.OriginCost < b.OriginCost', 'a.OriginCost > b.OriginCost'),
            ('native-edge-index', 'if (map[firstIndex] != 0)', 'if (map[cy * width + cx] != 0)'),
        ]
        for label, before, after in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                self.assertEqual(source.count(before), 1)
                path = Path(directory) / 'SourceFleetFormation.cs'
                path.write_text(source.replace(before, after))
                with self.assertRaisesRegex(AssertionError, 'Formation (mismatch|source-heading guard differs|execution failed)'):
                    formation.compare(data, source=path)


if __name__ == '__main__':
    unittest.main()
