from pathlib import Path
import json,shutil,tempfile,unittest
from tools import validate_crt_context as proof


class CrtContextTests(unittest.TestCase):
    def test_original_native_crt_samples_and_fresh_wave_replays_are_valid(self):
        r=proof.validate();self.assertTrue(r['fresh_x86_replay'])
        self.assertEqual((r['native_crt_samples'],r['native_crt_words'],r['replay_cases']),(512,[117],4))
        self.assertFalse(r['native_windows_verified']);self.assertFalse(r['original_game_entry_called'])
    def test_zero_cannot_replace_measured_neighbor_for_disconnected_water(self):
        cases={(c['terrain'],c['adjacent_input']):c for c in proof.load()['cases']}
        self.assertEqual([p['actor']for p in cases['mission',117]['state']['packets']],[11,12,13])
        self.assertEqual([r['candidate']for r in cases['disconnected',117]['comparisons']],[0,0,0])
        self.assertEqual(cases['disconnected',117]['state']['packets'],[])
        self.assertEqual([p['actor']for p in cases['disconnected',0]['state']['packets']],[11,12,13])
    def test_qemu_shutdown_and_pe32_control_are_not_crt_success(self):
        out=proof.ROOT/'artifacts/queued-crt-context'
        first=proof.inspect_vm(out/'vm-run');self.assertEqual(first['qemu_exit'],0);self.assertFalse(first['passed'])
        second=proof.inspect_vm(out/'vm-desktop');self.assertTrue(second['pe32_control_passed']);self.assertFalse(second['passed'])
    def test_changed_fixture_and_incomplete_native_log_are_rejected(self):
        with tempfile.TemporaryDirectory()as directory:
            path=Path(directory)/'bad.json';path.write_text('{}')
            with self.assertRaisesRegex(AssertionError,'Measured CRT fixture SHA differs'):proof.load(path)
            raw=proof.ROOT/'artifacts/queued-crt-context/vm-owned-pages/crt.jsonl'
            path.write_text('\n'.join(raw.read_text().splitlines()[:-1])+'\n')
            with self.assertRaises(AssertionError):proof.native.sample(path)


if __name__=='__main__':unittest.main()
