from pathlib import Path
import hashlib,unittest
from tools import smoke_ship_fleet_ui_world as qa
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/ship_fleet_ui_world_player.log'
SHA='eb577ab1b3202b4c8dcd1d4c102c30708a2f9b685f2a27f409f3e817a2891415'


class FleetUiWorldQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest()==SHA
        cls.log=FIXTURE.read_text();cls.reference=qa.reference()
    def test_actual_input_world_mail_and_group_context_match(self):
        rows,done=qa.validate_log(self.log,self.reference)
        self.assertTrue(done);self.assertEqual(len(rows),23)
        self.assertEqual(sum(len(row['actors'])for row in rows.values()),69)
        self.assertEqual(sum(len(row['queue'])for row in rows.values()),782)
    def test_checker_rejects_immediate_membership_early_mail_wrong_age_and_missing_lifecycle(self):
        replacements=[
            ('stage=dispatch-up; age=0; consumed=0; queued=6; prep=0; ui=0,0,0; sim=-1,-1,-1',
             'stage=dispatch-up; age=0; consumed=0; queued=6; prep=0; ui=0,0,0; sim=0,0,0'),
            ('stage=tick-1; age=1; consumed=0; queued=6; prep=1;',
             'stage=tick-1; age=1; consumed=3; queued=0; prep=1;'),
            ('[ShipWorldStep] received: at=3; packet=11:41:0:',
             '[ShipWorldStep] received: at=2; packet=11:41:0:'),
            ('stage=tick-10; age=10;','stage=tick-10; age=11;'),
            ('group_task_scheduler=True;','group_task_scheduler=False;'),
            ('[ShipFleetControl] world: stage=recall-c-up; age=99; consumed=3; queued=0; prep=2; ui=0,0,0; sim=0,0,0\n','')]
        for before,after in replacements:
            with self.subTest(before=before):
                self.assertEqual(self.log.count(before),1)
                with self.assertRaises(AssertionError):qa.validate_log(self.log.replace(before,after),self.reference)
    def test_checker_waits_for_a_complete_line_from_concurrent_player(self):
        marker='[ShipFleetControl] world: stage=dispatch-up;'
        prefix=self.log[:self.log.index(marker)]
        full=self.log[self.log.index(marker):].splitlines()[0]
        for count in(1,len(marker),len(full)-1):
            rows,done=qa.validate_log(prefix+full[:count],self.reference)
            self.assertFalse(done);self.assertEqual(len(rows),9)


if __name__=='__main__':unittest.main()
