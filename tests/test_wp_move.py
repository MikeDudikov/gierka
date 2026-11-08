import unittest
from tools import validate_wp_move as proof


class OriginalWaypointTests(unittest.TestCase):
    def test_original_constructor_and_position_writes_match_staged_source_resources(self):
        result=proof.validate()
        self.assertTrue(result['fresh_x86'])
        self.assertEqual((result['constructor_cases'],result['unique_frames']),(256,100))
        self.assertEqual(len(result['position_cases']),6)
        self.assertFalse(result['original_renderer_executed'])


if __name__=='__main__':unittest.main()
