from pathlib import Path
import hashlib,unittest
from tools import smoke_pending_queued_input as qa
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/pending_queued_input_player.log'
SHA='274ab839bdcbcffc23ceccf41449a248dfbf01290c2c86953b17315763b60201'


class PendingQueuedInputRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest()==SHA
        cls.log=FIXTURE.read_text();cls.reference=qa.reference()

    def test_first_shift_mail_route_and_hidden_marker_readouts_match_source(self):
        rows,done=qa.shared.validate_log(self.log,self.reference)
        self.assertTrue(done)
        self.assertEqual((len(rows),sum(len(r['actors'])for r in rows.values())),(35,105))
        self.assertEqual(sum(len(r['parts'])for r in rows.values()),350)
        self.assertEqual(sum(len(r['queue'])for r in rows.values()),1190)

    def test_checker_rejects_recreated_graphics_erased_route_task_replacement_mail_and_recall_faults(self):
        self.assertEqual(len(qa.negative_controls(self.log,self.reference)),6)


if __name__=='__main__':unittest.main()
