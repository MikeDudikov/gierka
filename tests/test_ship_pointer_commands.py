import json
from pathlib import Path
import tempfile
import unittest
from tools import validate_ship_pointer_commands as commands


class ShipPointerCommandsTests(unittest.TestCase):
    def test_actual_original_release_group_and_membership_match_checked_csharp(self):
        if not commands.gate.ORIGINAL.is_file():
            self.skipTest('Private original executable unavailable')
        try:
            result = commands.validate()
        except commands.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertTrue(result['passed'])
        self.assertEqual((result['cases'], result['snapshots'], result['guard_count']), (9, 55, 19))

    def test_modified_native_membership_fixture_is_rejected(self):
        data = json.loads(commands.FIXTURE.read_text())
        data['cases'][0]['rows'][2]['commands'][0]['payload_hex'] = '010100000000'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'changed.json'
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'fixture SHA256 differs'):
                commands.load_fixture(path)


if __name__ == '__main__':
    unittest.main()
