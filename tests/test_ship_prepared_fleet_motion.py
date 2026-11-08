from pathlib import Path
import tempfile
import unittest

from tools import validate_ship_prepared_fleet_motion as fleet


class ShipPreparedFleetMotionTests(unittest.TestCase):
    def test_three_actual_profiles_shared_claims_and_crossing_routes_match_original(self):
        result=fleet.validate()
        self.assertTrue(result['fresh_native'])
        self.assertEqual((result['cases'],result['states'],result['tick_calls']),(15,6795,6750))
        self.assertEqual((result['publications'],result['grid_mutations']),(1440,300))
        self.assertEqual(result['api_controls'],22)

    def test_changed_fixture_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory()as directory:
            path=Path(directory)/'changed.json';path.write_text('{}')
            with self.assertRaisesRegex(AssertionError,'Prepared fleet fixture SHA differs'):fleet.load(path)

    def test_oracle_detects_wrong_size_acceleration_and_stale_retry(self):
        data=fleet.load();source=fleet.SOURCE.read_text()
        for before,after in [('anchorOffset=(64-logicalSize)/2;','anchorOffset=4;'),
                             ('baseAcceleration=reservationAcceleration;','baseAcceleration=1200;'),
                             ('if(preparedLocal) retry=0;','')]:
            with self.subTest(before=before),tempfile.TemporaryDirectory()as directory:
                self.assertEqual(source.count(before),1)
                path=Path(directory)/'ShipMoveOrder.cs';path.write_text(source.replace(before,after))
                with self.assertRaisesRegex(AssertionError,'Prepared fleet (mismatch|execution failed)'):fleet.compare(data,source=path)


if __name__=='__main__':unittest.main()
