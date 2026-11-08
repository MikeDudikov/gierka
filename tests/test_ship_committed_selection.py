from pathlib import Path
import tempfile,unittest
from tools import validate_ship_committed_selection as v

class CommittedSelectionTests(unittest.TestCase):
 def test_ctrl_recall_plain_selection_and_right_blank_match_original(self):
  r=v.validate();self.assertTrue(r['fresh_native']);self.assertEqual((r['cases'],r['states']),(135,360))
 def test_tampered_fixture_is_rejected(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'bad.json';p.write_text('{}')
   with self.assertRaisesRegex(AssertionError,'Committed selection fixture SHA differs'):v.load(p)
 def test_wrong_group_recall_is_detected(self):
  text=v.SOURCE.read_text();before='short group=(flags&8u)!=0&&uiGroup!=null?uiGroup(input.HoveredOwner):(short)-1;';after='short group=(flags&16u)!=0&&uiGroup!=null?uiGroup(input.HoveredOwner):(short)-1;';self.assertEqual(text.count(before),1)
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'ShipPendingSelection.cs';p.write_text(text.replace(before,after))
   with self.assertRaisesRegex(AssertionError,'Committed selection mismatch'):v.compare(v.load(),source=p)

if __name__=='__main__':unittest.main()
