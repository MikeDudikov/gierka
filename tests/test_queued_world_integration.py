from pathlib import Path
import tempfile,unittest
from tools import validate_queued_world_integration as proof
from tools import validate_ship_world_step as world,validate_ship_busy_orders as busy
from tools import validate_ship_fleet_ui_replace as ui,validate_cohort_world_restore as restore


class QueuedWorldIntegrationTests(unittest.TestCase):
    def test_complete_world_matches_source_with_real_arrivals_and_explicit_memory(self):
        r=proof.validate()
        self.assertEqual((r['cases'],r['frames'],r['actor_states'],r['api_controls']),(50,5536,16608,10))
        self.assertTrue(r['fresh_x86_additional']);self.assertTrue(r['strict_event_records'])
        self.assertFalse(r['source_packets_injected_after_startup'])
        self.assertEqual(r['normal_world']['actor_states'],5388)

    def test_corpus_rejects_lost_arrivals_bad_word_order_and_same_tick_delivery(self):
        original=world.SOURCE.read_text()
        mutants=[('arrival','membership.NotifyMemberArrived(group,actors[entry].InstanceId,arrival.CellIndex,arrival.Counter);',';'),
            ('word-order','wavePrefixWords[membership.GetGroupMemberRegistryIndex(group,i)]','wavePrefixWords[i]'),
            ('eager-delivery','outgoing.Add(packet);emitted.Add(packet);',
                'actors[Find(packet.InstanceId)].ReceiveNormalCellMove(packet.InstanceId,packet.Read32(0),packet.Read32(4),packet.MoveArgument);outgoing.Add(packet);emitted.Add(packet);')]
        for label,before,after in mutants:
            with self.subTest(name=label),tempfile.TemporaryDirectory()as directory:
                self.assertEqual(original.count(before),1);path=Path(directory)/'ShipWorldStep.cs';path.write_text(original.replace(before,after))
                with self.assertRaisesRegex(AssertionError,'Integrated world (mismatch|execution failed)'):
                    proof.compare(source=path)

    def test_historical_ret_notification_projections_remain_unchanged(self):
        self.assertTrue(world.compare(world.load())['passed'])
        self.assertTrue(world.compare(busy.load_world())['passed'])
        self.assertTrue(ui.compare(ui.load())['passed'])
        self.assertTrue(restore.compare(restore.load())['passed'])

    def test_mixed_source_words_bind_actor_identity_not_registration_visit_order(self):
        for c in proof.load('queued_world_mixed')['cases']:
            with self.subTest(label=c['label']):
                self.assertEqual(c['prefixes'],[32767,117,-32768])
                emitted=[p['actor']for p in c['rows'][0]['emitted']]
                self.assertEqual(emitted,[13]if len(c['members'])==2 else[13,12])


if __name__=='__main__':unittest.main()
