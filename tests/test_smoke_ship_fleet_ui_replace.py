from pathlib import Path
import hashlib,unittest
from tools import smoke_ship_fleet_ui_replace as qa
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/ship_fleet_ui_replace_player.log'
SHA='da8e6ac96ff8d62ccd0bb017aabb66bd63263ed5d30a2b149b65834a28daa264'


class FleetUiReplaceQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest()==SHA
        cls.log=FIXTURE.read_text();cls.reference=qa.reference()
    def test_actual_replacement_fifo_task_and_render_states_match(self):
        rows,done=qa.validate_log(self.log,self.reference)
        self.assertTrue(done);self.assertEqual(len(rows),30)
        self.assertEqual(sum(len(row['actors'])for row in rows.values()),90)
        self.assertEqual(sum(len(row['parts'])for row in rows.values()),300)
        self.assertEqual(sum(len(row['queue'])for row in rows.values()),1020)
    def test_checker_rejects_age_reset_wrong_task_tick_early_delivery_and_lost_packets(self):
        lines=self.log.splitlines(keepends=True);variants={}
        changes=[
          ('replacement: counter=25; group=0; goal=18,6; requested=25; age=25; queued=3',
           'replacement: counter=25; group=0; goal=18,6; requested=25; age=0; queued=3'),
          ('task: stage=replace-last-up; requested=25; goal=16,4','task: stage=replace-last-up; requested=26; goal=16,4'),
          ('[ShipWorldStep] received: at=26; packet=11:20:25:120000000600000000',
           '[ShipWorldStep] received: at=25; packet=11:20:25:120000000600000000'),
          ('[ShipFleetControl] packet: id=12; action=20; payload=140000000700000000\n',''),
          ('world: stage=replace-first-up; age=25; consumed=3; queued=3;',
           'world: stage=replace-first-up; age=25; consumed=6; queued=3;'),
          ('[ShipFleetControl] task: stage=recall-c-up; requested=25; goal=16,4\n',''),
          ('[ShipFleetControl] guard: reason=normal-committed-replacement-only\n','')]
        for before,after in changes:
            self.assertEqual(self.log.count(before),1);variants[before]=self.log.replace(before,after)
        index=next(i for i,line in enumerate(lines)if line.startswith('[ShipFleetMotion] actor: replace-first-up\t11\t'))
        changed=list(lines);fields=changed[index].split('\t');fields[32]=str(int(fields[32])|128);changed[index]='\t'.join(fields)
        variants['immediate-inbox']=''.join(changed)
        for label,log in variants.items():
            with self.subTest(label=label),self.assertRaises(AssertionError):qa.validate_log(log,self.reference)


if __name__=='__main__':unittest.main()
