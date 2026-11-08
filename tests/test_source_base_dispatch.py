import unittest
from tools import validate_source_base_dispatch as proof


class SourceBaseDispatchTests(unittest.TestCase):
    def test_original_recursive_reset_routing_and_machine_mutations(self):
        result = proof.validate()
        self.assertEqual((result['direct_operations'], result['context_cases']), (42, 108))
        self.assertEqual(len(result['negative_controls']), 5)
        self.assertTrue(result['actual_recursive_recipient_executed'])
        self.assertFalse(result['native_full_application'])
        self.assertFalse(result['world_or_tick_executed'])


if __name__ == '__main__':
    unittest.main()
