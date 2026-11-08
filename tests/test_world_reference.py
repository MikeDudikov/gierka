import unittest

from tools.inspect_world_reference import base_palette_sprite, used_palette_differences


class WorldReferenceTests(unittest.TestCase):
    def test_palette_comparison_ignores_unused_cells_but_retains_index_identity(self):
        palette = bytes((1, 2, 3, 1, 2, 3, 4, 5, 6)) + bytes(768 - 9)
        stored = [(1, 2, 3), (1, 2, 3), (7, 8, 9)]
        self.assertEqual(used_palette_differences(bytes((0, 1, 1)), stored, palette), [])
        self.assertEqual(used_palette_differences(bytes((2, 1, 2)), stored, palette), [2])
        with self.assertRaisesRegex(ValueError, "own stored palette"):
            used_palette_differences(bytes((3,)), stored, palette)

    def test_coverage_keeps_written_index_zero_and_repeated_rgb(self):
        palette = bytes((10, 20, 30, 10, 20, 30)) + bytes(762)
        sprite = {"width": 3, "height": 1, "indices": bytes((0, 1, 0)),
                  "coverage": bytes((255, 255, 0))}
        image = base_palette_sprite(sprite, palette)
        self.assertEqual(list(image.get_flattened_data()), [(10, 20, 30, 255),
                                                (10, 20, 30, 255),
                                                (10, 20, 30, 0)])

    def test_missing_palette_or_truncated_coverage_refused(self):
        sprite = {"width": 2, "height": 2, "indices": bytes(4), "coverage": bytes(3)}
        with self.assertRaisesRegex(ValueError, "256-entry"):
            base_palette_sprite(sprite, bytes(765))
        with self.assertRaisesRegex(ValueError, "size mismatch"):
            base_palette_sprite(sprite, bytes(768))


if __name__ == "__main__":
    unittest.main()
