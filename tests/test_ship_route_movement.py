import json
from pathlib import Path
import tempfile
import unittest

from tools import validate_ship_route_movement as route


class ShipRouteMovementTests(unittest.TestCase):
    def test_actual_planner_and_multi_waypoint_motion_match_all_native_states_and_effects(self):
        try:
            report = route.validate()
        except route.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(report["case_count"],32)
        self.assertEqual(report["snapshot_count"],1593)
        self.assertEqual(report["passed_snapshots"],1593)
        self.assertEqual(report["native_move_ship_calls"],1561)
        self.assertEqual(report["native_planner_calls"],32)
        self.assertEqual(report["native_publications"],1046)
        self.assertEqual(report["native_grid_mutations"],248)
        self.assertEqual(report["arrived_routes"],24)
        self.assertEqual(report["rejected_routes"],4)
        self.assertEqual(report["guard_count"],57)
        self.assertTrue(report["checked_compilation"])
        cases={row["label"]:row for row in report["cases"]}
        for x,y,count in ((14,4,59),(16,4,56),(17,4,70),(18,5,86),(20,4,107),(20,6,108)):
            case=cases[f"goal_{x}_{y}_pending1"]
            self.assertEqual(case["snapshots"],count+1)
            self.assertEqual(case["final_snapshot"]["cell"],[x,y])
        stopped=cases["goal_19_4_pending1"]["final_snapshot"]
        self.assertEqual(stopped["cell"],[18,3])
        self.assertEqual(stopped["speed"],21906)
        self.assertEqual(stopped["stamp"]-stopped["last_state_counter"],50)

    def test_native_intermediate_publication_is_protected_by_fixture_pin(self):
        fixture=route.load_fixture()
        case=next(c for c in fixture["cases"] if c["label"]=="goal_17_4_pending1")
        row=next(t for t in case["trace"] if len(t["publications"])==2)
        row["publications"][0]["depth"]+=1
        with tempfile.TemporaryDirectory(prefix="changed-route-publication-") as temporary:
            path=Path(temporary)/"changed.json";path.write_text(json.dumps(fixture))
            with self.assertRaisesRegex(ValueError,"fixture SHA-256"):
                route.load_fixture(path)


if __name__=="__main__":unittest.main()
