from pathlib import Path
import tempfile,unittest
from tools import validate_ship_fleet_ui_world as proof


class FleetUiWorldTests(unittest.TestCase):
    def test_ui_packets_mail_group_and_ship_work_match_fresh_x86(self):
        result=proof.validate()
        self.assertTrue(result['fresh_native'])
        self.assertEqual((result['cases'],result['frames'],result['actor_states'],result['registration_orders']),(12,2400,7200,4))
        self.assertEqual((result['received'],result['emitted'],result['api_controls']),(72,0,20))
    def test_fixture_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory()as directory:
            path=Path(directory)/'changed.json';path.write_text('{}')
            with self.assertRaisesRegex(AssertionError,'UI world fixture SHA differs'):proof.load(path)


if __name__=='__main__':unittest.main()
