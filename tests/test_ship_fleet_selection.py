from pathlib import Path
import json,tempfile,unittest
from tools import validate_ship_pending_selection as pending,validate_ship_fleet_hover as hover,validate_ship_fleet_visuals as visuals,stage_ship_fleet_visuals as stage

class ShipFleetSelectionTests(unittest.TestCase):
 def test_original_pending_selection_and_recycled_sprite_slots_match_checked_csharp(self):
  r=pending.validate();self.assertTrue(r['passed']);self.assertEqual((r['pending_cases'],r['slot_states']),(1710,2376))
 def test_all_local_hover_subsets_match_original_cursor_and_fleet(self):
  r=hover.validate();self.assertEqual((r['states'],r['selected_subsets']),(9280,8))
 def test_three_selector_sizes_progression_rle_and_health_match_original(self):
  r=visuals.validate();self.assertEqual((r['states'],r['rle_frames'],r['rle_buffers'],r['health_buffers']),(1221,30,180,6))
 def test_changed_native_fixtures_fail_before_execution(self):
  loaders=[(pending.load,'ship_pending_selection.json'),(pending.load,'source_sprite_slots.json'),(hover.load,None),(visuals.load,None)]
  for loader,name in loaders:
   with self.subTest(name=name),tempfile.TemporaryDirectory()as tmp:
    path=Path(tmp)/'changed.json';path.write_text('{}')
    with self.assertRaisesRegex(AssertionError,'fixture SHA differs'):
     loader(name,path)if name else loader(path)
 def test_ninth_stage_is_idempotent_and_rejects_modified_existing_data(self):
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp);stage.stage(stage.pointer.SOURCE_ROOT,p);out=p/'Assets/Resources/ShipFleetVisualsGenerated';before={f.name:f.read_bytes()for f in out.iterdir()if f.is_file()}
   stage.stage(stage.pointer.SOURCE_ROOT,p);self.assertEqual(before,{f.name:f.read_bytes()for f in out.iterdir()if f.is_file()})
   m=json.loads((out/stage.MANIFEST_NAME).read_text());self.assertEqual([(f['selector_size'],f['health_width'])for f in m['families']],[(60,34),(68,42),(76,50)])
   self.assertEqual(len((out/'ShipFleetVisualsRgba.bytes').read_bytes()),1024000)
   (out/'ShipFleetVisualsRgba.bytes').write_bytes(b'changed')
   with self.assertRaises(ValueError):stage.stage(stage.pointer.SOURCE_ROOT,p,True)
if __name__=='__main__':unittest.main()
