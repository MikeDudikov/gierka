from pathlib import Path
import tempfile,unittest
from tools import validate_fleet_queued_world as proof
from tools import validate_ship_world_step as world
from tools import validate_ship_busy_orders as busy
from tools import validate_ship_live_fleet as live
from tools import validate_fleet_queued_port as task


class FleetQueuedWorldTests(unittest.TestCase):
    def test_fresh_source_world_and_actor_arrivals_match_all_pinned_states(self):
        result=proof.validate()
        self.assertEqual((result['cases'],result['frames'],result['actor_states']),(46,5416,16386))
        self.assertEqual((result['arrival_calls'],result['near_arrival_calls'],result['exact_arrival_calls']),(258,196,62))
        self.assertEqual((result['registration_orders'],result['wave_reads']),(24,48))
        self.assertTrue(result['fresh_x86']);self.assertEqual(result['actor_port']['api_controls'],2)
        self.assertFalse(result['csharp_queued_world_integrated']);self.assertFalse(result['ui_shift_enabled'])

    def test_actual_csharp_observation_rejects_wrong_cell_near_gate_and_repeat_suppression(self):
        source=proof.SIM/'ShipMoveOrder.cs';original=source.read_text()
        mutations=[('goal-cell','arrival=new Arrival(counter,lastCell);','arrival=new Arrival(counter,cellY*24+cellX);'),
            ('near-distance','if(distance==1) RecordArrival();','if(distance==0) RecordArrival();'),
            ('repeat-suppression','arrival=new Arrival(counter,lastCell);',
                'if(arrival.CellIndex==lastCell && unchecked(arrival.Counter+1u)==counter) return; arrival=new Arrival(counter,lastCell);')]
        d=proof.load();d=dict(d,cases=d['cases'][:1])
        for name,before,after in mutations:
            with self.subTest(name=name),tempfile.TemporaryDirectory()as directory:
                self.assertIn(before,original);changed=Path(directory)/'ShipMoveOrder.cs';changed.write_text(original.replace(before,after))
                with self.assertRaisesRegex(AssertionError,'Queued arrival C# mismatch'):
                    proof.compare_actor(d,source=changed)

    def test_source_instruction_controls_distinguish_both_calls_and_signed_memory(self):
        d=proof.load();cases={c['label']:c for c in d['cases']};specs={s['label']:s for s in proof.native.specifications()}
        patches=[('registry--1,11,12,13',(0x4a49af,bytes.fromhex('e84ccdffff'),bytes.fromhex('83c4109090'))),
            ('registry--1,11,12,13',(0x4a4a67,bytes.fromhex('e894ccffff'),bytes.fromhex('83c4109090'))),
            ('periodic-0--32768',(0x4cebcb,bytes.fromhex('0f9c'),bytes.fromhex('0f92')))]
        for label,patch in patches:
            with self.subTest(address=hex(patch[0])):
                actual=proof.native.fixture([specs[label]],[patch])['cases'][0]
                with self.assertRaisesRegex(AssertionError,'Queued world x86 mismatch'):
                    proof.compare_cases([actual],[cases[label]])
                # Difference must affect actual task/mail state,not just the debug call recorder.
                self.assertNotEqual([(r['group'],r['emitted'])for r in actual['rows']],
                    [(r['group'],r['emitted'])for r in cases[label]['rows']])

    def test_registry_order_mail_delay_and_explicit_prefix_contract_are_observed(self):
        cases={c['label']:c for c in proof.load()['cases']}
        first=cases['registry--1,11,12,13'];last=cases['registry-11,12,13,-1']
        row=lambda c,t:next(r for r in c['rows']if r['counter']==t)
        self.assertEqual(row(first,58)['emitted'],[])
        self.assertEqual([p['actor']for p in row(last,58)['emitted']],[12])
        self.assertEqual([(p['actor'],p['queued_at'])for p in row(first,60)['received']],[(12,59)])
        self.assertEqual([(p['actor'],p['queued_at'])for p in row(last,59)['received']],[(12,58)])
        self.assertEqual(row(first,58)['arrivals'][0]['cell'],162)
        self.assertEqual(row(first,58)['arrivals'][0]['actual_cell'],163)
        self.assertEqual([p['actor']for p in cases['islands-0-0']['rows'][0]['emitted']],[11,12,13])
        self.assertEqual(cases['islands-0-117']['rows'][0]['emitted'],[])
        self.assertEqual(cases['periodic-0-32767']['rows'][0]['emitted'],[])
        self.assertEqual([p['actor']for p in cases['periodic-0--32768']['rows'][0]['emitted']],[11,12,13])

    def test_legacy_world_busy_body_and_existing_task_port_remain_unchanged(self):
        self.assertTrue(world.compare(world.load())['passed'])
        self.assertTrue(world.compare(busy.load_world())['passed'])
        self.assertTrue(live.compare(live.load())['passed'])
        self.assertTrue(task.compare()['passed'])


if __name__=='__main__':unittest.main()
