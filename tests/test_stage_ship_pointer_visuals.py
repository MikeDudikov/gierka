import tempfile,unittest,json
from pathlib import Path
from tools import stage_ship_pointer_visuals as stage
class StageShipPointerVisualTests(unittest.TestCase):
 def test_atlas_geometry_health_and_idempotent_generation(self):
  with tempfile.TemporaryDirectory()as tmp:
   project=Path(tmp);stage.stage(stage.SOURCE_ROOT,project);out=project/'Assets/Resources/ShipPointerVisualsGenerated';before={p.name:p.read_bytes()for p in out.iterdir()if p.is_file()};stage.stage(stage.SOURCE_ROOT,project);self.assertEqual(before,{p.name:p.read_bytes()for p in out.iterdir()if p.is_file()})
   m=json.loads((out/stage.MANIFEST_NAME).read_text());self.assertEqual((m['atlas_width'],m['atlas_height'],m['frame_count']),(1024,128,29));self.assertEqual(len((out/'ShipPointerVisualsRgba.bytes').read_bytes()),1024*128*4)
   self.assertEqual([(f['width'],f['height'])for f in m['frames'][:10]],[(60,60)]*10);self.assertEqual(m['healthbar']['frame'],28);self.assertEqual((m['frames'][28]['width'],m['frames'][28]['height']),(34,4))
 def test_all_original_inputs_have_individual_hash_guards(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)
   for name in stage.SOURCE_HASHES:
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.symlink_to(stage.SOURCE_ROOT/name)
   for name in stage.SOURCE_HASHES:
    p=root/name;p.unlink();p.write_bytes(b'changed')
    with self.assertRaisesRegex(ValueError,'Original pointer visual source differs: '+name.replace('.','\\.')):stage.checked_sources(root)
    p.unlink();p.symlink_to(stage.SOURCE_ROOT/name)
 def test_existing_modified_payload_cannot_be_silently_replaced(self):
  with tempfile.TemporaryDirectory()as tmp:
   project=Path(tmp);stage.stage(stage.SOURCE_ROOT,project);p=project/'Assets/Resources/ShipPointerVisualsGenerated/ShipPointerVisualsRgba.bytes';p.write_bytes(b'changed')
   with self.assertRaises(ValueError):stage.stage(stage.SOURCE_ROOT,project,replace_generated=True)
