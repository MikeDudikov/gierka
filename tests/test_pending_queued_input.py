import unittest
from tools import validate_pending_queued_input as proof


class FirstPendingShiftTests(unittest.TestCase):
    def test_original_pending_commit_world_and_selection_marker_lifecycle_match(self):
        r=proof.validate()
        self.assertEqual((r['cases'],r['frames'],r['actor_states']),(2,400,1200))
        self.assertEqual(r['initial_ui_packet_counts'],[6,0,0])
        self.assertEqual(r['marker_counts'],[2,0,0,0,0,1,0,0,3,0])
        self.assertTrue(r['fresh_x86'])
        self.assertFalse(r['source_packets_injected_after_startup'])


if __name__=='__main__':unittest.main()
