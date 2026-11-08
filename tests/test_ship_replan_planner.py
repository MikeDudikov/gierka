import json
from pathlib import Path
import tempfile
import unittest

from tools import validate_ship_replan_planner as planner


class ShipReplanPlannerTests(unittest.TestCase):
    def test_actual_current_origin_plans_fields_rng_and_cache_match_checked_csharp(self):
        try:
            report=planner.validate()
        except planner.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(report['passed'],228)
        self.assertEqual(report['guard_count'],13)
        self.assertTrue(report['checked_compilation'])
        self.assertTrue(report['warnings_as_errors'])
        cases={row['label']:row for row in report['original']['cases']}
        partial=cases['matrix_4']  # source0b16,2, requested18,2, range1
        self.assertEqual((partial['point_count'],partial['reached_within_range']), (2,True))
        self.assertEqual(partial['path_hex'],'10000200001100020000')
        old=cases['cached_outside_window']
        self.assertEqual(old['cell'],[14,4])
        self.assertEqual(old['cached_obstacles_after'],[115])
        self.assertEqual(int.from_bytes(bytes.fromhex(old['input_map_hex'])[230:232],'little',signed=True),-1)
        high=cases['priority_51_1']
        self.assertEqual(high['random_state_after'],(0xffffffff*0x41c64e6d+0x3039)&0xffffffff)
        self.assertEqual(cases['priority_50_1']['random_state_after'],0xffffffff)
        self.assertEqual(cases['two_cached']['cached_obstacles_after'],[115,141])

    def test_changed_native_planning_evidence_is_rejected_before_execution(self):
        changed=planner.load_fixture();changed['cases'][0]['cached_obstacles_after']=[]
        with tempfile.TemporaryDirectory()as temporary:
            path=Path(temporary)/'changed.json';path.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError,'fixture SHA-256'):
                planner.load_fixture(path)


if __name__=='__main__':unittest.main()
