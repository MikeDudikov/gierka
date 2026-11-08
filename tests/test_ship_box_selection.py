import json
from pathlib import Path
import tempfile
import unittest
from tools import validate_ship_box_selection as box


class ShipBoxSelectionTests(unittest.TestCase):
    def test_original_queries_policies_and_pixels_match_checked_csharp(self):
        if not box.gate.ORIGINAL.is_file():
            self.skipTest('Private original executable unavailable')
        try:
            result = box.validate()
        except box.gate.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertTrue(result['passed'])
        self.assertEqual((result['queries'], result['policies'], result['raster_cases'], result['guard_count']),
                         (1745, 144, 1920, 25))

    def test_modified_source_query_or_raster_fixture_is_rejected(self):
        for field in ('queries', 'raster'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                data = json.loads(box.FIXTURE.read_text())
                if field == 'queries':
                    data[field][0]['result']['members'] = [11]
                else:
                    data[field]['cases'][0]['bitmap_hex'] = '00' * 512
                path = Path(directory) / 'changed.json'
                path.write_text(json.dumps(data))
                with self.assertRaisesRegex(AssertionError, 'fixture SHA differs'):
                    box.load_fixture(path)


if __name__ == '__main__':
    unittest.main()
