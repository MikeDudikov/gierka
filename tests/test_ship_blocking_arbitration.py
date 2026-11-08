import tempfile,unittest
from pathlib import Path
from tools import validate_ship_blocking_arbitration as arb


class BlockingArbitrationTests(unittest.TestCase):
    def test_complete_source_cancellation_and_promotion_are_reproducible(self):
        r=arb.validate();self.assertTrue(r['fresh_x86']);self.assertEqual(r['cases'],144);self.assertEqual(r['constructor_writes'],3)
    def test_fixture_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'changed.json';p.write_text('{}')
            with self.assertRaisesRegex(AssertionError,'fixture SHA differs'):arb.load(p)
    def test_retaining_discarded_move_is_detected(self):
        d=arb.load();c=next(c for c in d['cases']if c['gate']==1 and c['pending_input']==128 and c['before']['active']&128)
        c['after']['deferred']=128
        with self.assertRaises(AssertionError):arb.check(d)


if __name__=='__main__':unittest.main()
