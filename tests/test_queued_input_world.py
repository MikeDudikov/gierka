import json,unittest
from tools import smoke_queued_input as runtime,probe_queued_ui_world as native,validate_queued_ui_world as proof


class AccessibleQueuedInputTests(unittest.TestCase):
    def test_accessible_normal_return_matches_original_and_pure_world_without_packet_injection(self):
        data=runtime.load()
        fresh=json.loads(json.dumps(native.fixture(normal_goal=(20,5),positions=(0,3),afters=(25,))))
        self.assertEqual(data,fresh)
        result=proof.compare(data=data)
        self.assertEqual((result['cases'],result['frames'],result['actor_states']),(2,400,1224))
        for case in data['cases']:
            self.assertEqual([len(r['packets'])for r in case['requests']],[3,0,0,3])
            occupied=dict(case['rows'][84]['actors'][0]['claims'])
            self.assertIn(5*24+18,occupied)
            self.assertNotIn(5*24+20,occupied)
            self.assertEqual(data['terrain'][5*24+20],0)


if __name__=='__main__':unittest.main()
