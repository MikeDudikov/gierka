from pathlib import Path
import tempfile,unittest
from tools import validate_ship_state_port as port


class ShipStatePortTests(unittest.TestCase):
    def test_original_state_import_and_blocking_work_match_csharp(self):
        r=port.validate();self.assertTrue(r['fresh_x86']);self.assertEqual((r['cases'],r['states'],r['api_controls']),(222,15096,10))
    def test_fixture_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'changed.json';p.write_text('{}')
            with self.assertRaisesRegex(AssertionError,'fixture SHA differs'):port.load(p)
    def test_source_detects_wrong_gate_deferred_and_counter_policies(self):
        data=port.load();s=port.SOURCE.read_text()
        mutations=[('moveBlockingGate==0','moveBlockingGate!=0'),
            ('if(pendingFlags!=0)deferredFlags=0;','if(pendingFlags==0)deferredFlags=0;'),
            ('if(lastPlan==counter) return;','if(lastPlan!=counter) return;'),
            ('if(actor>=0x54c&&actor<=0x5d0)return actor-0x49;','if(actor>=0x54c&&actor<=0x5d0)return actor-0x48;')]
        for before,after in mutations:
            with self.subTest(before=before),tempfile.TemporaryDirectory()as d:
                self.assertEqual(s.count(before),1);p=Path(d)/'ShipMoveOrder.cs';p.write_text(s.replace(before,after))
                with self.assertRaisesRegex(AssertionError,'State port (mismatch|execution failed)'):port.compare(data,source=p)


if __name__=='__main__':unittest.main()
