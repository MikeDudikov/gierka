import unittest
from tools import validate_source_key_visibility as proof


class SourceKeyVisibilityTests(unittest.TestCase):
    def test_original_accelerator_bytes_and_forwarded_messages_match_including_reset_gate(self):
        r=proof.validate()
        self.assertTrue(r['fresh_x86'])
        self.assertEqual(r['operations'],10)
        self.assertEqual([row['key']for row in r['accelerators']],[29,42,54])
        self.assertTrue(r['original_set_accelerator_executed'])
        self.assertFalse(r['os_keyboard_polling'])


if __name__=='__main__':unittest.main()
