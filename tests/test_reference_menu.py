import struct
import unittest

from PIL import Image

from tools.render_reference_menu import (composite_indices, draw_text, indexed_dib,
                                         measure_text)


class ReferenceMenuTests(unittest.TestCase):
    def test_indexed_dib_preserves_indices_palette_padding_and_orientation(self):
        header = bytearray(40)
        struct.pack_into("<IiiHHI", header, 0, 40, 3, 2, 1, 8, 0)
        struct.pack_into("<I", header, 32, 2)
        palette = b"\0\0\xff\0\0\xff\0\0"
        # Stored bottom row then top row, with padding outside the pixel plane.
        payload = bytes(header) + palette + b"\0\1\0\xff\1\0\1\xff"
        size, indices, colors = indexed_dib(payload)
        self.assertEqual(size, (3, 2))
        self.assertEqual(indices, b"\1\0\1\0\1\0")
        self.assertEqual(colors, [(255, 0, 0), (0, 255, 0)])

    def test_missing_character_uses_first_glyph_and_spacing_is_between_glyphs(self):
        font = {"glyphs": [dict(code=127, width=3, height=7),
                           dict(code=65, width=5, height=9)]}
        self.assertEqual(measure_text("A?A", font), (15, 9))
        self.assertEqual(measure_text("", font), (0, 0))
        self.assertEqual(measure_text("?", font), (3, 7))

    def test_transparency_uses_palette_index_even_when_rgb_entries_match(self):
        target = Image.new("RGB", (2, 1), (0, 255, 0))
        composite_indices(target, (2, 1), b"\0\1", [(255, 0, 0)] * 2,
                          (0, 0), color_key=0)
        self.assertEqual(list(target.get_flattened_data()), [(0, 255, 0), (255, 0, 0)])
        with self.assertRaises(ValueError):
            composite_indices(target, (2, 1), b"\0", [(255, 0, 0)], (0, 0))

    def test_glyph_blit_preserves_opaque_zero_and_uses_fallback_atlas_rectangle(self):
        font = {"glyphs": [dict(code=127, x=0, y=0, width=1, height=1),
                           dict(code=65, x=1, y=0, width=2, height=1)]}
        palette = [(0, 0, 0), (255, 0, 0)] + [(0, 0, 0)] * 4 + [(0, 255, 0)]
        atlas = ((3, 1), b"\1\6\0", palette)
        image = Image.new("RGB", (4, 1), (0, 0, 255))
        draw_text(image, "A?", font, atlas, (0, 0), color_key=6)
        self.assertEqual(list(image.get_flattened_data()),
                         [(0, 0, 255), (0, 0, 0), (0, 0, 255), (255, 0, 0)])


if __name__ == "__main__":
    unittest.main()
