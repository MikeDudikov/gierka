from pathlib import Path
import hashlib,unittest
from tools import smoke_queued_input as committed,smoke_pending_queued_input as pending
ROOT=Path(__file__).resolve().parents[1]
PINS={'committed': '095271bca65006775c024cddf0edb6165e0ff86b558eb9d79e55a79d1d40744b', 'pending': '32c3f3d7b5ee2581712087d337ae9a4773bf3e3594ed97b4b1e65d3cb471f837'}


class SourceRouteKeysRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles={}
        for mode,qa in (('committed',committed),('pending',pending)):
            file=ROOT/'tests/fixtures'/('source_route_keys_'+mode+'_player.log')
            assert hashlib.sha256(file.read_bytes()).hexdigest()==PINS[mode]
            cls.profiles[mode]=(qa,file.read_text(),qa.reference(source_keys=True))

    def test_source_key_envelopes_and_marker_lifecycle_match_actual_inputsystem_players(self):
        for mode,(qa,log,reference)in self.profiles.items():
            with self.subTest(mode=mode):
                rows,done=committed.validate_log(log,reference)
                self.assertTrue(done)
                self.assertEqual(len(rows),33 if mode=='committed'else 35)
                self.assertEqual(len(reference['key_events']),4)
                if mode=='pending':
                    self.assertEqual(reference['markers']['route-clear-point'],[])
                    self.assertEqual(len(reference['markers']['hidden-duplicate-down']),2)
                else:self.assertEqual(reference['markers']['queue-normal-down'],[])

    def test_checkers_reject_lost_key_messages_and_lost_restoration_alongside_world_faults(self):
        for mode,(qa,log,reference)in self.profiles.items():
            with self.subTest(mode=mode):
                detected=qa.negative_controls(log,reference)
                self.assertIn('lost_key_envelope',detected)
                self.assertEqual(len(detected),7 if mode=='committed'else 8)


if __name__=='__main__':unittest.main()
