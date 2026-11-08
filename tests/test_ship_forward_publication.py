import unittest

from tools import validate_ship_forward_publication as publication


class ShipForwardPublicationTests(unittest.TestCase):
    def test_original_setter_and_renderer_keep_last_publication_for_45_calls(self):
        try:
            report = publication.validate()
        except publication.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual((report["case_count"], report["passed"]), (45, 45))
        self.assertEqual(report["hooked_callees"], {})
        self.assertEqual(len(report["source_hashes"]), 7)
        rows = report["rows"]
        for call in (3, 4, 6):
            self.assertFalse(rows[call]["published"])
            self.assertNotEqual(rows[call]["stored_frame"], rows[call]["drawn_frame"])
        self.assertEqual([(rows[call]["stored_frame"], rows[call]["drawn_frame"])
                          for call in (0, 1, 5, 29, 30, 44)],
                         [(20, 20), (20, 20), (21, 21), (21, 21), (22, 22), (22, 22)])
        self.assertEqual([(rows[call]["render_world_x"], rows[call]["render_world_y"])
                          for call in (0, 1, 3, 4, 5, 44)],
                         [(1028, 132), (1028, 132), (1028, 132), (1028, 132), (1027, 133), (964, 196)])


if __name__ == "__main__":
    unittest.main()
