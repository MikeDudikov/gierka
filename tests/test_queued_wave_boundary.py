from pathlib import Path
import tempfile,unittest
from tools import validate_queued_wave_boundary as proof


class QueuedWaveBoundaryTests(unittest.TestCase):
    def test_comparison_and_emissions_match_fresh_original_with_explicit_neighbor(self):
        result=proof.validate();self.assertTrue(result['fresh_x86'])
        self.assertEqual((result['cases'],result['comparisons'],result['offset_bytes']),(5,15,-2))
        self.assertTrue(result['behavior_depends_on_adjacent_memory']);self.assertFalse(result['native_crt_layout_verified'])
    def test_fixture_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory()as directory:
            p=Path(directory)/'changed.json';p.write_text('{}')
            with self.assertRaisesRegex(AssertionError,'Queued wave fixture SHA differs'):proof.load(p)
    def test_native_signed_comparison_can_suppress_all_three_periodic_packets(self):
        cases=proof.load()['cases']
        for case in cases:
            suppressed=case['adjacent_input']==32767
            self.assertEqual([r['result']for r in case['comparisons']],[int(suppressed)]*3)
            self.assertEqual([p['actor']for p in case['state']['packets']],[]if suppressed else[11,12,13])
            for record in case['comparisons']:
                self.assertEqual((record['index'],record['offset_bytes'],record['allocation_bytes']),(-1,-2,1152))


if __name__=='__main__':unittest.main()
