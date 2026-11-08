import json
from pathlib import Path
import tempfile
import unittest
from tools import validate_ship_pointer_hover as hover

class ShipPointerHoverTests(unittest.TestCase):
    def test_whole_original_cursor_map_fleet_actor_hover_matches_checked_csharp(self):
        if not hover.gate.ORIGINAL.is_file():
            self.skipTest('Private original executable unavailable')
        try:
            result=hover.validate()
        except hover.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertTrue(result['passed'])
        self.assertEqual(result['state_count'],2327)
        self.assertEqual(result['source_query_count'],2319)
        self.assertEqual(result['visited_predicate_count'],288)
        self.assertEqual(result['guard_count'],15)
        self.assertTrue(result['checked_compilation'])
        self.assertTrue(result['warnings_as_errors'])

    def test_changed_native_stationary_refresh_is_rejected_before_analysis_dependencies(self):
        data=json.loads(hover.FIXTURE.read_text())
        row=next(o for o in data['operations']if o['label']=='stationary-stored-turn-mask')
        row['state']['last_query']=False
        with tempfile.TemporaryDirectory()as directory:
            path=Path(directory)/'changed.json';path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'fixture SHA256 differs'):
                hover.load_fixture(path)

    def test_native_fixture_retains_distinct_cache_occupancy_and_action_bit_rules(self):
        fixture=hover.load_fixture();rows={o['label']:o['state']for o in fixture['operations']if o['state']is not None}
        self.assertEqual([rows[label]['cursor_type']for label in('own-unselected','selection-refresh-without-move','sea-selected','occupied-transparent-cell')],[5,6,7,0])
        changed=rows['changed-screen-same-world']
        self.assertFalse(changed['has_map']);self.assertFalse(changed['last_query'])
        self.assertEqual(rows['invalidated-same-world-refresh']['cursor_type'],0)
        self.assertEqual([rows[label]['cursor_type']for label in('turn-mask-before','stationary-stored-turn-mask','stationary-restored-mask')],[6,0,6])
        self.assertEqual(rows['unchanged-mask-preserves-cycle']['cursor_type'],12)
        self.assertEqual(rows['friendly-no-cap31']['action_mask'],0)
        self.assertEqual(rows['friendly-no-cap31']['action_bit'],256)
        invalid=rows['source-map-invalidation'];self.assertFalse(invalid['has_map']);self.assertEqual(invalid['hovered_id'],12)
        self.assertEqual(rows['foreign-unselected-preserves-type']['cursor_type'],5)

if __name__=='__main__':unittest.main()
