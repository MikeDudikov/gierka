import hashlib,unittest
from pathlib import Path
from tools import smoke_ship_fleet as fleet

class ShipFleetProtocolTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  raw=(fleet.ROOT/'tests/fixtures/ship_fleet_input.log').read_bytes()
  if hashlib.sha256(raw).hexdigest()!='e91217d9e784523142b08124680c5017fda895b9b6b5db5bf5ec6242ea429ef1':raise AssertionError('Fleet input fixture SHA differs')
  cls.good=raw.decode().replace('\r\n','\n')
 def model(self,text):
  model=fleet.Model()
  for line in text.splitlines():model.consume(line)
  return model
 def changed(self,anchor,old,new):
  line=next(line for line in self.good.splitlines()if anchor in line);self.assertIn(old,line)
  return self.good.replace(line,line.replace(old,new,1),1)
 def test_complete_fleet_runtime_protocol_matches_original_policy_and_visual_lifecycle(self):
  m=self.model(self.good);self.assertTrue(m.complete);self.assertEqual(m.checkpoints,fleet.STAGES)
  self.assertEqual((len(m.events),len(m.releases),m.guard_count),(47,11,1));self.assertEqual(m.state['members'],[11])
  self.assertEqual((m.counter,m.sel[13]['selection']),(43,2));self.assertTrue(all(not c['synthesized_up']for c in m.cancels))
 def test_source_protocol_corruptions_fail_even_when_the_framebuffer_is_unchanged(self):
  bad={
   'member-order':self.changed('[ShipFleetSelection] checkpoint: stage=all-up;','members=0000000b,0000000d,0000000c','members=0000000b,0000000c,0000000d'),
   'modifier':self.changed('[ShipFleetSelection] release: message=98; flags=4;','flags=4','flags=0'),
   'hidden-slot':self.changed('[ShipFleetSelection] visual: stage=all-up; id=0000000b;','node=21','node=22'),
   'health-family':self.changed('[ShipFleetSelection] visual: stage=cd-healthy; id=0000000d;','health_sprite=HEALTH_100_76','health_sprite=HEALTH_100_60'),
   'callback-target':self.changed('[ShipFleetSelection] selection: id=0000000b; selected=True','id=0000000b','id=0000000c'),
   'fabricated-order':self.good.replace('[ShipFleetSelection] release: ',fleet.pointer.PREFIX+'packet: event=0; index=0; action=20; payload=120000000500000000\n[ShipFleetSelection] release: ',1),
  }
  for name,text in bad.items():
   with self.subTest(name=name),self.assertRaises(AssertionError):self.model(text)
if __name__=='__main__':unittest.main()
