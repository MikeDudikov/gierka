import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from tools import validate_pointer_cursor_visuals as validation
class PointerCursorVisualTests(unittest.TestCase):
 def test_actual_cursor_image_and_confirm_transactions_match_checked_csharp(self):
  try:r=validation.validate()
  except validation.MissingPrerequisite as e:self.skipTest(str(e))
  self.assertEqual((r['cases'],r['snapshots'],r['cursor_publication_operations'],r['confirm_publications'],r['confirm_deletions'],r['guards']),(8,94,44,17,5,7))
 def test_source_initial_interval_and_confirm_publish_delete_boundaries(self):
  cases=validation.load_fixture()['cases'];c=cases[0]
  create=next(i for i,op in enumerate(c['operations'])if op[0]=='C');self.assertFalse(c['rows'][create]['confirm_visible']);self.assertEqual(c['rows'][create]['confirm_frame'],0)
  first=next(r for r in c['rows'][create:]if r['confirm_publishes']);self.assertEqual(first['confirm_frame'],1)
  third=next(i for i,r in enumerate(c['rows'])if r['confirm_visible']and r['confirm_frame']==3);self.assertFalse(c['rows'][third+1]['confirm_exists'])
  self.assertEqual(next(c for c in cases if c['label']=='initial-sea-old500-0')['rows'][0]['frame'],0)
  self.assertEqual(next(c for c in cases if c['label']=='initial-sea-old500-500')['rows'][0]['frame'],1)
 def test_move_typechange_draw_then_global_draw_deletes_just_published_confirm(self):
  c=next(c for c in validation.load_fixture()['cases']if c['label']=='global-move-typechange-two-draw-boundary')
  self.assertTrue(c['rows'][-2]['confirm_visible']);self.assertEqual(c['rows'][-2]['confirm_frame'],3)
  self.assertEqual(c['rows'][-2]['draw_position'],[100,100]);self.assertEqual(c['rows'][-1]['draw_position'],[120,140])
  self.assertFalse(c['rows'][-1]['confirm_exists']);self.assertTrue(c['rows'][-1]['deletes_confirm'])
 def test_changed_cursor_fixture_is_rejected_before_execution(self):
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)/'altered.json';p.write_bytes(validation.FIXTURE.read_bytes()+b' ')
   with patch.object(validation,'FIXTURE',p):
    with self.assertRaisesRegex(AssertionError,'fixture SHA'):validation.load_fixture()
