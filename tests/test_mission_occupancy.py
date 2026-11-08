import tempfile
import unittest
from pathlib import Path
from tools import validate_mission_occupancy as occupancy

class MissionOccupancyTests(unittest.TestCase):
    def test_actual_csharp_matches_original_flags_queries_and_ownership(self):
        try:
            result=occupancy.validate()
        except occupancy.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(result['cell_flags_compared'],576)
        self.assertEqual(result['query_cases'],1536)
        self.assertEqual(result['query_result_comparisons'],3072)
        self.assertEqual(result['owner_sequences'],36)
        self.assertEqual(result['passed'],1572)
        self.assertEqual(result['csharp_guard_count'],len(occupancy.GUARDS))
        self.assertTrue(result['checked_compilation'])
        self.assertEqual(result['intercepted_functions'],[])

    def test_changed_native_flags_or_provenance_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            flags=Path(folder)/'flags.bin';metadata=Path(folder)/'flags.json'
            flags.write_bytes(occupancy.FIXTURE.read_bytes()+b'\0');metadata.write_bytes(occupancy.PROVENANCE.read_bytes())
            with self.assertRaisesRegex(ValueError,'cell flags hash differs'):occupancy.load_fixture(flags,metadata)
            flags.write_bytes(occupancy.FIXTURE.read_bytes());metadata.write_bytes(metadata.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'provenance hash differs'):occupancy.load_fixture(flags,metadata)

if __name__=='__main__':unittest.main()
