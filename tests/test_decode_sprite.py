import struct
import unittest

from tools.decode_sprite import SpriteFormatError, decode_sprite


def sprite(stream, width=5, height=1, left=0, top=0, box_width=None,
           box_height=None, flags=0x80, table=()):
    if box_width is None:
        box_width = width
    if box_height is None:
        box_height = height
    prefix = struct.pack("<" + "H" * len(table), *table)
    return struct.pack("<Iii5H", 22 + len(prefix) + len(stream), width, height,
                       flags, left, top, box_width, box_height) + prefix + stream


class SpriteTests(unittest.TestCase):
    def test_skip_literal_repeat_and_opaque_zero(self):
        result = decode_sprite(sprite(b"\1\x82\0\x12\xc2\x34"))
        self.assertEqual(result["indices"], b"\0\0\x12\x34\x34")
        self.assertEqual(result["coverage"], b"\0\xff\xff\xff\xff")

    def test_top_down_canvas_and_bounding_box(self):
        result = decode_sprite(sprite(b"\x82\x05\x06\x82\x07\x08",
                                       width=4, height=4, left=1, top=1,
                                       box_width=2, box_height=2))
        self.assertEqual(result["indices"], bytes([0,0,0,0,0,5,6,0,0,7,8,0,0,0,0,0]))
        self.assertEqual(result["coverage"].count(255), 4)

    def test_row_table_offsets_verified(self):
        # Each row is two bytes, header has one2-byte table entry.
        result = decode_sprite(sprite(b"\x81\x22" * 17, width=1, height=17,
                                       flags=0x480, table=(34,)))
        self.assertEqual(result["indices"], b"\x22" * 17)
        with self.assertRaises(SpriteFormatError):
            decode_sprite(sprite(b"\x81\x22" * 17, width=1, height=17,
                                 flags=0x480, table=(33,)))

    def test_final_table_entry_zero_at_exact_sixteen_rows(self):
        result = decode_sprite(sprite(b"\x81\x22" * 16, width=1, height=16,
                                       flags=0x480, table=(0,)))
        self.assertEqual(result["coverage"], b"\xff" * 16)

    def test_empty_sprite_preserves_canvas(self):
        result = decode_sprite(sprite(b"", width=8, height=8, left=8,
                                       box_width=0, box_height=0))
        self.assertEqual(result["indices"], bytes(64))
        self.assertEqual(result["coverage"], bytes(64))

    def test_invalid_headers_runs_truncation_and_limits(self):
        bad = [b"", sprite(b"\x82\x01"), sprite(b"\x86abcdef"),
               sprite(b"\x80abcde"), sprite(b"\xc0x"), sprite(b"\0\0"),
               sprite(b"\xc5xextra"), sprite(b"\xc5x", flags=0x81),
               sprite(b"\xc5x", left=1)]
        for payload in bad:
            with self.subTest(payload=payload), self.assertRaises(SpriteFormatError):
                decode_sprite(payload)
        with self.assertRaises(SpriteFormatError):
            decode_sprite(sprite(b"\xc5x"), max_pixels=4)


if __name__ == "__main__":
    unittest.main()
