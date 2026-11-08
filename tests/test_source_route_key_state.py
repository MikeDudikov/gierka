import unittest
from tools import validate_source_route_key_state as proof


class SourceRouteKeyStateTests(unittest.TestCase):
    def test_actual_csharp_matches_x86_state_and_rejects_behavior_mutations(self):
        result = proof.validate()
        self.assertEqual(result['states'], 150)
        self.assertEqual(len(result['negative_controls']), 5)
        self.assertTrue(result['raw_uint_preserved'])
        self.assertFalse(result['world_or_tick_executed'])


if __name__ == '__main__':
    unittest.main()
