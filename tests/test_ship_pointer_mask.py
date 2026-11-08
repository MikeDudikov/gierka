import json
from pathlib import Path
import tempfile
import unittest

from tools import validate_ship_pointer_mask as mask


class ShipPointerMaskTests(unittest.TestCase):
    def test_actual_original_full_planes_and_queries_match_checked_csharp(self):
        root = mask.ROOT / 'reference/raw/ancient-conquest'
        if not all((root / name).is_file() for name in mask.native.staging.SOURCE_HASHES):
            self.skipTest('Private original ship assets unavailable')
        try:
            result = mask.validate()
        except mask.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertTrue(result['passed'])
        self.assertEqual(result['native_calls'], 432428)
        self.assertEqual(result['full_plane_pixels'], 423960)
        self.assertEqual(result['point_cases'], 8468)
        self.assertEqual(result['guard_count'], 13)
        self.assertEqual(result['native_hooks'], [])

    def test_changed_native_fixture_is_rejected_before_analysis_dependencies(self):
        data = json.loads(mask.FIXTURE.read_text())
        data['families'][0]['planes'][0]['covered'] += 1
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'changed.json'
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'fixture SHA256 differs'):
                mask.load_fixture(path)


if __name__ == '__main__':
    unittest.main()
