from pathlib import Path
import hashlib,unittest
from tools import smoke_ship_fleet_control as qa
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/ship_fleet_control_player.log'
SHA='96e0aabb53515c8f3a79dc946a431200972218a3f1177ee6720a90ebc3b9c587'
class FleetControlQATests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest()==SHA
  cls.log=FIXTURE.read_text();cls.reference=qa.reference()
 def test_actual_first_order_replay_matches_all23_checkpoints(self):
  rows,done=qa.validate_log(self.log,self.reference);self.assertTrue(done);self.assertEqual(len(rows),23)
  self.assertEqual(sum(len(r['actors'])for r in rows.values()),69)
  self.assertEqual(sum(len(r['parts'])for r in rows.values()),230)
  self.assertEqual(sum(len(r['queue'])for r in rows.values()),782)
 def test_checker_rejects_wrong_recipient_payload_selection_pose_and_missing_fence(self):
  lines=self.log.splitlines(keepends=True);variants={}
  packet=next(i for i,s in enumerate(lines)if s.startswith('[ShipFleetControl] packet: id=11; action=41;'))
  changed=list(lines);changed[packet]=changed[packet].replace('id=11','id=12');variants['recipient']=''.join(changed)
  changed=list(lines);changed[packet]=changed[packet].replace('010000000000','010100000000');variants['payload']=''.join(changed)
  selected=next(i for i,s in enumerate(lines)if s.startswith('[ShipFleetSelection] checkpoint: stage=dispatch-up;'))
  changed=list(lines);changed[selected]=changed[selected].replace('0000000b,0000000c,0000000d','0000000b,0000000c');variants['selection']=''.join(changed)
  actor=next(i for i,s in enumerate(lines)if s.startswith('[ShipFleetMotion] actor: tick-25\t11\t'))
  changed=list(lines);fields=changed[actor].split('\t');fields[4]=str(int(fields[4])+1);changed[actor]='\t'.join(fields);variants['live-position']=''.join(changed)
  variants['fence']=self.log.replace('[ShipFleetMotion] end: recall-c-up\n','')
  for label,log in variants.items():
   with self.subTest(label=label),self.assertRaises(AssertionError):qa.validate_log(log,self.reference)
if __name__=='__main__':unittest.main()
