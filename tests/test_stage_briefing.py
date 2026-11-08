import json
from pathlib import Path
import struct
import tempfile
import unittest

from PIL import Image

from tools.stage_briefing import (ROOT, WIDTH, HEIGHT, BUTTON_RECTS, RADIO_RECTS,
    SOURCE_HASHES, digest, parse_description, tokens, form_lines, format_description,
    checked_sources, compose_briefing, write_payloads)


def make_description(slots):
    count = len(slots)
    bitmap = bytearray((count + 7) // 8)
    raw = bytearray(struct.pack("<IIIIII", 0, 0, count, max(count, 1), 20, 0))
    strings = bytearray()
    for index, value in enumerate(slots):
        if value is not None:
            bitmap[index // 8] |= 0x80 >> (index % 8)
            strings.extend(value.encode("ascii") + b"\0")
    return bytes(raw + bitmap + strings)


class DescriptionTests(unittest.TestCase):
    def test_presence_bitmap_is_msb_first_and_null_slots_are_preserved(self):
        slots = ["A", None, "", "@B", None, None, None, "H", "I"]
        raw = make_description(slots)
        self.assertEqual(raw[24:26], bytes((0xb1, 0x80)))
        self.assertEqual(parse_description(raw), slots)

    def test_truncated_or_ambiguous_serialization_refused(self):
        valid = make_description(["A"])
        for raw in (b"", valid[:24], valid[:-1], valid + b"\0"):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    parse_description(raw)
        malformed = bytearray(valid)
        struct.pack_into("<I", malformed, 12, 0)
        with self.assertRaisesRegex(ValueError, "count/capacity"):
            parse_description(malformed)

    def test_tokenizer_retains_delimiters_and_repeated_spaces(self):
        self.assertEqual(list(tokens("A, B.  C")), ["A,", " ", "B.", " ", " ", "C"])

    def test_physical_nul_is_not_a_line_break_and_indent_preserves_spaces(self):
        font = {"glyphs": [{"code": code, "x": 0, "y": 0, "width": 1, "height": 2}
                           for code in range(32, 128)]}
        self.assertEqual(form_lines(["One", "Two"], font, 100), ["One Two "])
        self.assertEqual(form_lines([""], font, 100), [])
        self.assertEqual(form_lines(["", "One", ""], font, 100), ["One  "])
        self.assertEqual(format_description(["@A", "B"], font, 100), ["    ", "   A B "])
        self.assertEqual(format_description(["@A", None, "Ignored"], font, 100), ["    ", "   A "])
        with self.assertRaisesRegex(ValueError, "Inline font"):
            format_description(["@A&B"], font)


class BriefingStagingTests(unittest.TestCase):
    def test_native_geometry_keeps_shapes_and_has_icon_only_hit_regions(self):
        self.assertEqual((WIDTH, HEIGHT), (1920, 1080))
        for x, y, width, height in BUTTON_RECTS:
            self.assertAlmostEqual(width / height, 116 / 40, delta=.01)
            self.assertLessEqual(x + width, WIDTH)
            self.assertLessEqual(y + height, HEIGHT)
        self.assertEqual(RADIO_RECTS, ((1591, 792, 41, 41), (1591, 846, 41, 41),
                                      (1591, 900, 41, 41)))
        self.assertTrue(all(rect[0] + rect[2] < 1656 for rect in RADIO_RECTS))

    def test_payload_hashes_orientation_idempotence_and_tamper_guard(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "Generated"
            image = Image.new("RGBA", (1, 2))
            image.putpixel((0, 0), (1, 2, 3, 4))
            image.putpixel((0, 1), (5, 6, 7, 8))
            images = {"BackgroundRgba.bytes": image}
            report = write_payloads(output, images, {"schema_version": 1})
            path = output / "BackgroundRgba.bytes"
            self.assertEqual(path.read_bytes(), bytes((5, 6, 7, 8, 1, 2, 3, 4)))
            self.assertEqual(report["payloads"][path.name]["sha256"], digest(path.read_bytes()))
            before = path.stat().st_mtime_ns
            self.assertEqual(write_payloads(output, images, {"schema_version": 1}), report)
            self.assertEqual(path.stat().st_mtime_ns, before)
            image.putpixel((0, 0), (9, 10, 11, 12))
            with self.assertRaises(FileExistsError):
                write_payloads(output, images, {"schema_version": 1})
            path.write_bytes(b"modified")
            with self.assertRaisesRegex(ValueError, "Previous generated briefing hash"):
                write_payloads(output, images, {"schema_version": 1}, True)
            self.assertEqual(path.read_bytes(), b"modified")

    def test_source_hash_guard_refuses_changed_original(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "installed/ancient.exe"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"different executable")
            with self.assertRaisesRegex(ValueError, "source hash differs"):
                checked_sources(root)

    def test_actual_miss000_lines_match_original_x86_output_digest(self):
        source_root = ROOT / "reference/raw/ancient-conquest"
        if not all((source_root / name).is_file() for name in SOURCE_HASHES):
            self.skipTest("Private original game inputs are not installed")
        images, metadata = compose_briefing(source_root)
        evidence = json.loads((ROOT / "tests/fixtures/briefing_miss000_format.json").read_text())
        rows = metadata["text_source_lines"]
        self.assertEqual(metadata["description_sha256"], evidence["description_sha256"])
        self.assertEqual(digest("\0".join(row["text"] for row in rows).encode("ascii")),
                         evidence["lines_sha256"])
        self.assertEqual([row["width"] for row in rows], evidence["widths"])
        self.assertEqual([row["height"] for row in rows], evidence["heights"])
        self.assertEqual([row["y"] for row in rows], list(range(0, 285, 19)))
        self.assertEqual(images["StaticUiRgba.bytes"].size, (1920, 1080))
        self.assertEqual(images["ButtonsRgba.bytes"].size, (418, 288))
        self.assertEqual(images["DifficultyRgba.bytes"].size, (504, 149))
        self.assertEqual([control["resource_id"] for control in metadata["controls"]], [1010, 1002])
        self.assertEqual(metadata["default_difficulty"], 0)
        self.assertIn("Start intentionally disabled while faithful gameplay is unimplemented",
                      metadata["limitations"])


if __name__ == "__main__":
    unittest.main()
