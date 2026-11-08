import unittest
from tools import validate_source_app_activation as proof


class SourceAppActivationTests(unittest.TestCase):
    def test_original_deactivation_reset_order_with_machine_mutations(self):
        result = proof.validate()
        self.assertEqual(result['cases'], 96)
        self.assertEqual(len(result['negative_controls']), 4)
        self.assertTrue(result['actual_context_producer_and_recipient_executed'])
        self.assertFalse(result['physical_os_events_executed'])
        self.assertFalse(result['world_or_tick_executed'])


if __name__ == '__main__':
    unittest.main()
