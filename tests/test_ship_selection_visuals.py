import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from tools import validate_ship_selection_visuals as validation
class ShipSelectionVisualTests(unittest.TestCase):
 def test_actual_original_selection_and_setter_match_checked_csharp(self):
  try:r=validation.validate()
  except validation.MissingPrerequisite as e:self.skipTest(str(e))
  self.assertEqual((r['cases'],r['snapshots'],r['publications'],r['selector_deletions'],r['health_removals'],r['guards']),(7,407,226,7,7,5))
 def test_reselect_during_reverse_keeps_removed_health_absent(self):
  c=next(c for c in validation.load_fixture()['cases']if c['label']=='reselect-during-reverse')
  i=next(i for i,op in enumerate(c['operations'])if i>10 and op[0]=='S')
  self.assertEqual(c['rows'][i]['selection'],1);self.assertFalse(c['rows'][i]['health_exists'])
  self.assertTrue(any(r['frame']>=10 for r in c['rows'][i:]));self.assertFalse(any(r['health_visible']for r in c['rows'][i:]))
 def test_changed_selector_fixture_is_rejected_before_execution(self):
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)/'altered.json';p.write_bytes(validation.FIXTURE.read_bytes()+b' ')
   with patch.object(validation,'FIXTURE',p):
    with self.assertRaisesRegex(AssertionError,'fixture SHA'):validation.load_fixture()
