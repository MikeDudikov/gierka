import unittest

from tools import validate_ship_adjacent_query as query


class ShipAdjacentQueryDifferentialTests(unittest.TestCase):
    def test_actual_unhooked_cell_predicate_matches_checked_csharp(self):
        try:
            report = query.validate()
        except query.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(report["case_count"], 7120)
        self.assertEqual(report["passed"], 7120)
        self.assertEqual(report["case_groups"], {"source_neighbors": 48, "flag_owner_cases": 2304,
            "corner_owner_cases": 64, "corner_flag_cases": 28, "linked_state_cases": 68, "boundary_cases": 4608})
        self.assertEqual([row["result"] for row in report["source_neighbors"]],
                         [True, True, False, False, True, True, True, True])
        self.assertEqual(report["native_function_intercepts"], [])
        self.assertTrue(report["checked_compilation"])
        self.assertEqual(set(report["csharp_guards"]), query.GUARDS)
        self.assertEqual(report["csharp_contract_checks"], len(query.GUARDS))
        self.assertEqual(report["fixture_sha256"], query.FIXTURE_SHA256)


if __name__ == "__main__":
    unittest.main()
