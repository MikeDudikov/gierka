import json
from pathlib import Path
import tempfile
import unittest

from tools import validate_ship_adjacent_movement as adjacent


class ShipAdjacentMovementTests(unittest.TestCase):
    def test_native_plans_turns_positions_publications_and_ownership_match_checked_csharp(self):
        try:
            report = adjacent.validate()
        except adjacent.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(report["case_count"], 38)
        self.assertEqual(report["snapshot_count"], 1271)
        self.assertEqual(report["passed_snapshots"], 1271)
        self.assertEqual(report["native_move_ship_calls"], 1233)
        self.assertEqual(report["native_planner_calls"], 38)
        self.assertEqual(report["native_publications"], 587)
        self.assertEqual(report["arrived_routes"], 24)
        self.assertEqual(report["rejected_routes"], 8)
        self.assertEqual(report["deferred_timeout_routes"], 6)
        self.assertEqual(report["guard_count"], 42)
        self.assertTrue(report["checked_compilation"])
        source = {row["label"]: row for row in report["cases"]}
        self.assertFalse(source["h2_pending1"]["accepted"])
        self.assertFalse(source["h3_pending1"]["accepted"])
        for heading, calls in ((0,61),(1,79),(4,43),(5,44),(6,43),(7,62)):
            row = source[f"h{heading}_pending1"]
            self.assertTrue(row["accepted"])
            self.assertEqual(row["snapshots"], calls + 1)
            self.assertEqual(row["final_snapshot"]["occupied_cell_count"], 8)
        deferred = source["postplan_occupied_h1"]["final_snapshot"]
        self.assertEqual(deferred["stamp"] - deferred["last_state_counter"], 50)
        self.assertEqual(deferred["world"], [1028,132])
        self.assertEqual(deferred["owned_cells"], [64])

    def test_native_turn_or_publication_evidence_cannot_be_changed_without_pin_failure(self):
        fixture = adjacent.load_fixture()
        fixture["cases"][0]["trace"][1]["drawn_frame"] = 47
        with tempfile.TemporaryDirectory(prefix="changed-adjacent-source-") as temporary:
            path = Path(temporary) / "changed.json"
            path.write_text(json.dumps(fixture))
            with self.assertRaisesRegex(ValueError, "fixture SHA-256"):
                adjacent.load_fixture(path)


if __name__ == "__main__":
    unittest.main()
