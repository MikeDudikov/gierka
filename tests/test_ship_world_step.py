from pathlib import Path
import tempfile,unittest
from tools import validate_ship_world_step as world

class ShipWorldStepTests(unittest.TestCase):
    def test_clock_mail_registry_task_and_full_bodies_match_fresh_original(self):
        r=world.validate();self.assertTrue(r['fresh_native']);self.assertEqual(r['cases'],31);self.assertEqual(r['actor_states'],5388);self.assertEqual(r['api_controls'],20)
    def test_fixture_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'changed.json';p.write_text('{}')
            with self.assertRaisesRegex(AssertionError,'World step fixture SHA differs'):world.load(p)
    def test_source_checks_detect_delivery_order_latency_registry_and_clock_mutations(self):
        data=world.load();source=world.SOURCE.read_text()
        mutations=[
            ('if(PreparationCounter<2)','if(PreparationCounter<1)'),
            ('ready.AddRange(outgoing);outgoing.Clear();','ready.AddRange(outgoing);'),
            ('foreach(int entry in registration)','foreach(int entry in new int[]{-1,0,1,2})'),
            ('Command.Task(counter,membership.GetTaskCommand(group,i))','Command.Task(unchecked(counter+1),membership.GetTaskCommand(group,i))'),
            ('if(packet.Action==41)membership.ConsumeNext();','if(packet.Action==41){}')]
        for before,after in mutations:
            with self.subTest(before=before),tempfile.TemporaryDirectory()as d:
                self.assertEqual(source.count(before),1);p=Path(d)/'ShipWorldStep.cs';p.write_text(source.replace(before,after))
                with self.assertRaisesRegex(AssertionError,'World step (mismatch|execution failed)'):world.compare(data,source=p)

if __name__=='__main__':unittest.main()
