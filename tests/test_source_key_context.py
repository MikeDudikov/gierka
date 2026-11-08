import unittest
from tools import validate_source_key_context as proof


class SourceKeyContextTests(unittest.TestCase):
    def test_original_context_gate_rectangle_and_message_order_with_machine_mutations(self):
        result = proof.validate()
        self.assertEqual((result['cases'], result['messages']), (12, 12))
        self.assertEqual(len(result['negative_controls']), 3)
        self.assertTrue(result['fresh_x86'])
        self.assertFalse(result['tick_or_world_executed'])
        self.assertFalse(result['csharp_integration'])


if __name__ == '__main__':
    unittest.main()
