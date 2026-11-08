from pathlib import Path
import tempfile,unittest
from tools import validate_ship_fleet_queued as proof


class ShipFleetQueuedEvidenceTests(unittest.TestCase):
    def test_shift_task_route_and_events_match_fresh_independent_source_entries(self):
        result=proof.validate();self.assertTrue(result['fresh_x86'])
        self.assertEqual((result['cases'],result['states'],result['paired_state_observations']),(55,1112,2224))
        self.assertFalse(result['csharp_port']);self.assertFalse(result['unity_runtime_queued'])
    def test_fixture_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory()as directory:
            path=Path(directory)/'changed.json';path.write_text('{}')
            with self.assertRaisesRegex(AssertionError,'Queued fixture SHA differs'):proof.load(path)
    def test_source_contract_distinguishes_deduplication_wrap_and_initial_dispatch(self):
        data=proof.load();case=next(c for c in data['cases']if c['label']=='normal-(11, 12, 13)')
        spec=next(c for c in proof.native.specifications()if c['label']==case['label'])
        #Isolated original instruction mutations;the uploaded EXE and production files are untouched.
        patches=[(0x4ce714,b'\x74',b'\x75'),(0x4ce843,b'\x02',b'\x01'),(0x4cf3c3,b'\x84',b'\x85')]
        for patch in patches:
            with self.subTest(address=hex(patch[0])):
                actual=proof.native.fixture([spec],[patch])
                with self.assertRaisesRegex(AssertionError,'Queued x86 mismatch'):proof.compare_cases(actual['cases'],[case])
    def test_observed_single_member_filter_lifo_and_periodic_extra_emissions_are_retained(self):
        cases={c['label']:c for c in proof.load()['cases']}
        state=lambda name:cases[name]['rows'][-1]['state']
        self.assertEqual(state('arrival-1-0-False')['packets'],[])
        self.assertEqual([p['actor']for p in state('arrival-3-0-False')['packets']],[11])
        self.assertEqual([p['actor']for p in state('arrival-lifo')['packets']],[12,11])
        result=state('arrival-3-101-True')
        self.assertEqual([p['actor']for p in result['packets']],[11,11,12,13])
        self.assertEqual([p['payload_hex']for p in result['packets'][:2]],['100000000400000000','120000000500000000'])
        self.assertEqual(result['route']['members'][0]['target'],[16,4])


if __name__=='__main__':unittest.main()
