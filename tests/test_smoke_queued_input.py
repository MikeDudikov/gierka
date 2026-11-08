from pathlib import Path
import hashlib,unittest
from tools import smoke_queued_input as qa
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/queued_input_player.log'
SHA='476d2e8cd35c9ab2cd3e7103a93800f18ad7ec532eb66cc76a49e412b36be628'


class QueuedInputRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest()==SHA
        cls.log=FIXTURE.read_text();cls.reference=qa.reference()

    def test_real_inputsystem_world_route_and_renderer_readouts_match_original(self):
        rows,done=qa.validate_log(self.log,self.reference)
        self.assertTrue(done)
        self.assertEqual((len(rows),sum(len(r['actors'])for r in rows.values())),(33,99))
        self.assertEqual(sum(len(r['parts'])for r in rows.values()),330)
        self.assertEqual(sum(len(r['queue'])for r in rows.values()),1122)

    def test_checker_rejects_lost_packet_wrong_marker_mask_position_order_route_and_mail_delay(self):
        self.assertEqual(len(qa.negative_controls(self.log,self.reference)),6)


if __name__=='__main__':unittest.main()
