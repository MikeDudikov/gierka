import json
from pathlib import Path
import tempfile
import unittest

from tools import validate_source_pathfinder as pathfinder


class SourcePathfinderTests(unittest.TestCase):
    def test_original_routes_and_all_working_field_cells_match_checked_csharp(self):
        try:
            report=pathfinder.validate()
        except pathfinder.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual((report['passed'],report['direct_cases'],report['wave_cases']), (374,234,140))
        self.assertEqual(report['guard_count'],6)
        self.assertTrue(report['checked_compilation'])
        cases={case['label']:case for case in report['native_evidence']['cases']}
        detour=cases['mission_20_4']
        self.assertTrue(detour['used_wave'])
        self.assertEqual(detour['path_hex'],'10000200001100020000120003000713000300001400040007')
        corner=cases['mission_18_5']
        self.assertFalse(corner['used_wave'])
        self.assertEqual(corner['point_count'],4)
        self.assertEqual(report['native_evidence']['algorithm_hooks'],[])

    def test_changed_original_route_evidence_is_rejected_before_execution(self):
        fixture=pathfinder.load_fixture();fixture['cases'][0]['path_hex']='0000'
        with tempfile.TemporaryDirectory()as temporary:
            p=Path(temporary)/'changed.json';p.write_text(json.dumps(fixture))
            with self.assertRaisesRegex(ValueError,'fixture SHA-256'):
                pathfinder.load_fixture(p)


if __name__=='__main__':unittest.main()
