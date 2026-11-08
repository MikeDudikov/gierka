from pathlib import Path
import tempfile,unittest
from tools import validate_ship_state_restore as restore


class ShipStateRestoreTests(unittest.TestCase):
    def test_original_export_restore_and_future_work_match_native_controls(self):
        r=restore.validate();self.assertTrue(r['fresh_x86']);self.assertEqual((r['cases'],r['future_states']),(36,1152))
    def test_changed_fixture_is_rejected(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'changed.json';p.write_text('{}')
            with self.assertRaisesRegex(AssertionError,'fixture SHA differs'):restore.load(p)
    def test_lost_imported_gate_is_detected(self):
        d=restore.load();c=next(c for c in d['cases']if c['gate']==1);c['imported_gate']=0
        with self.assertRaises(AssertionError):restore.check(d)


if __name__=='__main__':unittest.main()
