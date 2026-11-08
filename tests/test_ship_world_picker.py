import json
from pathlib import Path
import tempfile
import unittest
from tools import validate_ship_world_picker as picker

class ShipWorldPickerTests(unittest.TestCase):
    def test_whole_original_query_hit_and_visitation_match_checked_csharp(self):
        if not picker.gate.ORIGINAL.is_file():
            self.skipTest('Private original executable unavailable')
        try:
            result=picker.validate()
        except picker.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertTrue(result['passed'])
        self.assertEqual(result['query_count'],1206)
        self.assertEqual(result['visited_predicate_count'],5665)
        self.assertEqual(result['guard_count'],21)
        self.assertEqual(result['native_intercepted_callees'],[])

    def test_changed_native_order_is_rejected_before_optional_analysis_imports(self):
        data=json.loads(picker.FIXTURE.read_text())
        duplicate=next(row for row in data['cases']if row['label']=='duplicate-owner')
        self.assertEqual(duplicate['visits'][:2],[300,300])
        duplicate['visits']=list(dict.fromkeys(duplicate['visits']))
        with tempfile.TemporaryDirectory()as directory:
            path=Path(directory)/'changed.json';path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'fixture SHA256 differs'):
                picker.load_fixture(path)

if __name__=='__main__':unittest.main()
