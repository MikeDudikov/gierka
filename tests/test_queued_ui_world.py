import unittest
from tools import validate_queued_ui_world as proof


class QueuedUiWorldTests(unittest.TestCase):
    def test_source_ui_and_complete_csharp_world_match_with_shift_during_movement(self):
        r=proof.validate();self.assertTrue(r['fresh_x86'])
        self.assertEqual((r['cases'],r['frames'],r['requests'],r['actor_states']),(12,2400,48,7344))
        self.assertFalse(r['unity_input_adapter'])

    def test_original_requests_distinguish_creation_append_duplicate_and_normal_return(self):
        for c in proof.load()['cases']:
            with self.subTest(label=c['label']):
                self.assertEqual([r['kind']for r in c['requests']],['shift','shift','shift','click'])
                self.assertEqual([len(r['packets'])for r in c['requests']],[3,0,0,3])
                self.assertEqual([r['snapshot']['group']['task'][1]for r in c['requests']],[2,2,2,1])
                self.assertEqual(c['requests'][2]['snapshot']['group']['route']['points'],[[18,6],[16,4]])


if __name__=='__main__':unittest.main()
