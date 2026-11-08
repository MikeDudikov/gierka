from pathlib import Path
import tempfile,unittest
from tools import validate_cohort_world_restore as cohort


class CohortWorldRestoreTests(unittest.TestCase):
    def test_world_records_context_and_future_steps_match_fresh_x86(self):
        r=cohort.validate();self.assertTrue(r['fresh_x86'])
        self.assertEqual((r['cases'],r['frames'],r['restores'],r['actor_states'],r['api_controls']),(12,2544,24,7704,29))
    def test_fixture_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'changed.json';p.write_text('{}')
            with self.assertRaisesRegex(AssertionError,'fixture SHA differs'):cohort.load(p)
    def test_source_and_api_detect_wrong_clock_mail_and_partial_batch(self):
        source=cohort.SOURCE.read_text();data=cohort.load()
        before='for(int i=0;i<actors.Length;i++)actors[i].ValidateInPlaceSourceMovementState(owned[i],sourceCounter);\n            for(int i=0;i<actors.Length;i++)actors[i].RestoreSourceMovementState(owned[i],sourceCounter);'
        interleaved='for(int i=0;i<actors.Length;i++){actors[i].ValidateInPlaceSourceMovementState(owned[i],sourceCounter);actors[i].RestoreSourceMovementState(owned[i],sourceCounter);}'
        mutations=[(before,interleaved),
            ('actors[i].RestoreSourceMovementState(owned[i],sourceCounter);','actors[i].RestoreSourceMovementState(owned[i],unchecked(sourceCounter+1));'),
            ('var owned=new byte[records.Length][];','PreparationCounter=0;var owned=new byte[records.Length][];')]
        for before,after in mutations:
            with self.subTest(before=before),tempfile.TemporaryDirectory()as d:
                self.assertEqual(source.count(before),1);p=Path(d)/'ShipWorldStep.cs';p.write_text(source.replace(before,after))
                with self.assertRaisesRegex(AssertionError,'Cohort (mismatch|execution failed|API execution failed)'):cohort.compare(data,source=p)


if __name__=='__main__':unittest.main()
