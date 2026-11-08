import json
from pathlib import Path
import tempfile
import unittest

from tools import validate_prepared_ship_movement as movement


class PreparedShipMovementTests(unittest.TestCase):
    def test_actual_native_adjacent_route_and_all_motion_snapshots_match_checked_csharp(self):
        try:
            report = movement.validate()
        except movement.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(report["case_count"], 6)
        self.assertEqual(report["snapshot_count"], 186)
        self.assertEqual(report["passed_snapshots"], 186)
        self.assertEqual(report["move_ship_calls"], 180)
        self.assertEqual(report["native_planner_cases"], 1)
        self.assertEqual(report["publication_snapshots_compared"], 186)
        self.assertEqual(report["source_publication_count"], 115)
        self.assertEqual(report["guard_count"], 40)
        self.assertTrue(report["checked_compilation"])
        one = report["cases"][0]
        self.assertEqual(one["final_snapshot"]["world"], [964, 196])
        self.assertEqual(one["final_snapshot"]["tick"], 44)
        self.assertEqual([(row["tick"], row["cell_index"], row["after"]) for row in one["grid_writes"]],
                         [(1, 87, "0x70000000"), (30, 64, "0x0")])

    def test_pinned_native_evidence_rejects_a_changed_path_without_running_original(self):
        fixture = movement.load_fixture()
        fixture["cases"][-1]["native_navigation"]["points"][1][0] = 14
        with tempfile.TemporaryDirectory(prefix="changed-original-movement-") as temporary:
            path = Path(temporary) / "changed.json"
            path.write_text(json.dumps(fixture))
            with self.assertRaisesRegex(ValueError, "fixture SHA-256"):
                movement.load_fixture(path)


if __name__ == "__main__":
    unittest.main()
