import unittest
from tools import smoke_source_context_input as proof


class SourceContextMarkerTests(unittest.TestCase):
    def test_actual_producer_dispatch_and_fleet_receiver_preserve_logical_route(self):
        rows = proof.source_lifecycle()['rows']
        self.assertEqual(len(rows), 4)
        self.assertEqual([r['state']['marker_destroyed'] for r in rows], [[], [], [1, 2], [1, 2]])
        self.assertEqual([r['state']['route']['registered'] for r in rows], [3, 3, 3, 3])


if __name__ == '__main__':
    unittest.main()
