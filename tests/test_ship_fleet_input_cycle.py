from pathlib import Path
import tempfile,unittest
from tools import validate_ship_fleet_input_cycle as v
class FleetInputCycleTests(unittest.TestCase):
 def test_actual_ui_packets_handed_to_actual_three_body_core_match_csharp(self):
  r=v.validate();self.assertTrue(r['fresh_native']);self.assertEqual((r['cases'],r['states'],r['tick_calls']),(1,606,600));self.assertEqual(r['api_controls'],33)
  d=v.load();self.assertEqual([p['action']for p in d['packets']],[41]*3+[20]*3)
  self.assertEqual([list(bytes.fromhex(p['payload_hex'])[::4][:2])for p in d['packets'][3:]],[[18,5],[20,6],[19,4]])
 def test_tampered_fixture_is_rejected(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'bad.json';p.write_text('{}')
   with self.assertRaisesRegex(AssertionError,'Fleet input cycle fixture SHA differs'):v.load(p)
if __name__=='__main__':unittest.main()
