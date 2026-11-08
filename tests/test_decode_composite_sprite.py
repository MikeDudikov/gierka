import hashlib
import json
from pathlib import Path
import struct
import unittest

from tools.decode_composite_sprite import decode_composite_frame, inline_draw_order
from tools.inspect_dkx import inspect_pair

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "reference/raw/ancient-conquest"
FIXTURE = ROOT / "tests/fixtures/composite_original_selection.json"


def make_entry(kind, name, raw, offset=0, metadata=b"\0" * 12):
    return {"type": kind, "name": name, "offset": offset, "metadata_hex": metadata.hex(),
            "stored_size": len(raw), "raw_size": len(raw), "compression": 0,
            "sha256": hashlib.sha256(raw).hexdigest()}


def make_composite(rows, parts, frames, dimensions=(72, 60)):
    descriptor = bytearray()
    for x, y, depth, name in rows:
        encoded = name.encode("ascii")
        descriptor.extend(struct.pack("<3i", x, y, depth) + encoded + b"\0" * (32 - len(encoded)))
    payload = bytes(descriptor)
    entry = make_entry(8, "COMPOSITE", payload, metadata=struct.pack("<4hI", parts, frames, *dimensions, 0))
    data = bytearray(payload)
    entries = [entry]
    for name in dict.fromkeys(row[3] for row in rows):
        # Full plane3x3, cropped pixel at1,1, literal index0. No color key.
        raw = struct.pack("<Iii5H", 24, 3, 3, 0x80, 1, 1, 1, 1) + b"\x81\0"
        entries.append(make_entry(6, name, raw, len(data)))
        data.extend(raw)
    return entry, bytes(data), entries


class CompositeSpriteTests(unittest.TestCase):
    def test_frame_major_mask_selection_narrows_coordinates_and_keeps_negative_children(self):
        rows = [(0, 0, 10, "FIRST"), (0, 0, -21000, "SHADOW"),
                (65535, -65537, 65540, "NEXT"), (0, 0, -21000, "SHADOW2")]
        entry, data, entries = make_composite(rows, 2, 2)
        result = decode_composite_frame(entry, data, entries, 1, 3)
        self.assertEqual((result["width"], result["height"], result["frame_count"],
                          result["source_part_count"]), (72, 60, 2, 2))
        self.assertEqual([(part["name"], part["offset_x"], part["offset_y"], part["depth"])
                          for part in result["components"]],
                         [("NEXT", -1, -1, 4), ("SHADOW2", 0, 0, -21000)])
        self.assertEqual([part["name"] for part in result["inline_components"]], ["NEXT"])
        self.assertEqual([part["name"] for part in result["detached_components"]], ["SHADOW2"])
        # Logical dimensions do not replace each component's full-plane dimensions.
        sprite = result["components"][0]["sprite"]
        self.assertEqual((sprite["width"], sprite["height"]), (3, 3))
        self.assertEqual(sprite["coverage"][4], 255)
        self.assertEqual(sprite["indices"][4], 0)
        self.assertEqual(sum(bool(value) for value in sprite["coverage"]), 1)
        one = decode_composite_frame(entry, data, entries, 0, 2)
        self.assertEqual([part["source_index"] for part in one["components"]], [1])
        self.assertEqual(one["inline_components"], [])
        self.assertEqual(len(one["detached_components"]), 1)

    def test_inline_sort_uses_original_nonstable_pairwise_order(self):
        rows = [(0, 0, value, f"PART{index}") for index, value in enumerate((4, 3, 4, 5))]
        entry, data, entries = make_composite(rows, 4, 1)
        result = decode_composite_frame(entry, data, entries, 0, 15)
        self.assertEqual([part["name"] for part in result["components"]],
                         ["PART0", "PART1", "PART2", "PART3"])
        self.assertEqual([part["name"] for part in result["inline_components"]],
                         ["PART3", "PART2", "PART0", "PART1"])

    def test_uint32_high_mask_bit_and_frame_bounds_are_explicit(self):
        rows = [(0, 0, 1, f"PART{index}") for index in range(32)]
        entry, data, entries = make_composite(rows, 32, 1)
        selected = decode_composite_frame(entry, data, entries, 0, 0x80000000)
        self.assertEqual([part["source_index"] for part in selected["components"]], [31])
        for frame in (-1, 1, True, 1.0):
            with self.subTest(frame=frame), self.assertRaisesRegex(ValueError, "frame index"):
                decode_composite_frame(entry, data, entries, frame, 1)
        for mask in (0, -1, 0x100000000, True, 1.0):
            with self.subTest(mask=mask), self.assertRaisesRegex(ValueError, "mask"):
                decode_composite_frame(entry, data, entries, 0, mask)
        two, two_data, two_entries = make_composite(rows[:2], 2, 1)
        with self.assertRaisesRegex(ValueError, "no source part"):
            decode_composite_frame(two, two_data, two_entries, 0, 4)
        with self.assertRaisesRegex(ValueError, "sparse runtime stride"):
            decode_composite_frame(two, two_data, two_entries, 0, 0x80000001)
        all_parts = decode_composite_frame(two, two_data, two_entries, 0, 0xffffffff)
        self.assertEqual(len(all_parts["components"]), 2)

    def test_bad_metadata_truncated_records_and_ambiguous_resources_fail(self):
        entry, data, entries = make_composite([(0, 0, 1, "PART")], 1, 1)
        for patch in ({"type": 7}, {"metadata_hex": "bad"}, {"metadata_hex": "00" * 8},
                      {"metadata_hex": struct.pack("<4hI", 0, 1, 72, 60, 0).hex()},
                      {"metadata_hex": struct.pack("<4hI", 33, 1, 72, 60, 0).hex()},
                      {"metadata_hex": struct.pack("<4hI", 1, 0, 72, 60, 0).hex()},
                      {"metadata_hex": struct.pack("<4hI", 1, 1, -1, 60, 0).hex()},
                      {"stored_size": 43, "raw_size": 43}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                decode_composite_frame(dict(entry, **patch), data, entries, 0, 1)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            decode_composite_frame(entry, data, entries + [entries[1]], 0, 1)
        with self.assertRaisesRegex(ValueError, "type6"):
            decode_composite_frame(entry, data, [entry, dict(entries[1], type=18)], 0, 1)

    def test_part_names_and_unverified_sprite_flag_are_rejected(self):
        entry, data, entries = make_composite([(0, 0, 1, "PART")], 1, 1)
        for encoded, message in ((b"X" * 32, "NUL"), (b"\xff" + b"\0" * 31, "ASCII"),
                                 (b"\0" * 32, "type6")):
            changed = bytearray(data)
            changed[12:44] = encoded
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                decode_composite_frame(entry, bytes(changed), entries, 0, 1)
        changed = bytearray(data)
        struct.pack_into("<H", changed, entries[1]["offset"] + 12, 0x180)
        with self.assertRaisesRegex(ValueError, "flag0x100"):
            decode_composite_frame(entry, bytes(changed), entries, 0, 1)

    def test_original_no_hook_sort_fixture_covers_negative_depth_and_equal_depth_order(self):
        proof = json.loads(FIXTURE.read_text())
        self.assertEqual(proof["sort_hooks"], {})
        self.assertEqual(proof["sort_cases"], 340)
        for row in proof["synthetic_sort_cases"]:
            parts = [{"source_index": index, "depth": depth, "detached": depth < 0}
                     for index, depth in enumerate(row["depths"])]
            self.assertEqual([part["source_index"] for part in inline_draw_order(parts)],
                             row["inline_source_indices"])

    def test_actual_type8_selection_and_order_match_original_loader_fixture(self):
        proof = json.loads(FIXTURE.read_text())
        # Fixed fixture was captured from actual554d50 and the bounded original
        # sort. Input hashes bind it to the private reference, not our decoder.
        self.assertEqual(hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
                         "25e59c7365666e669edb6705b9c85fd5947cae5ba9c016a3563411a6d0818e50")
        if not all((SOURCE_ROOT / name).is_file() for name in proof["sources"]):
            self.skipTest("Private original game inputs are not installed")
        for name, expected in proof["sources"].items():
            self.assertEqual(hashlib.sha256((SOURCE_ROOT / name).read_bytes()).hexdigest(), expected)
        data = (SOURCE_ROOT / "files/DATA/OBJECTS.DKD").read_bytes()
        entries = inspect_pair((SOURCE_ROOT / "files/DATA/OBJECTS.DKX").read_bytes(), data)
        descriptors = {(entry["type"], entry["name"]): entry for entry in entries}
        self.assertEqual(proof["loader_cases"], 12)
        for case in proof["cases"]:
            for row in case["frames"]:
                result = decode_composite_frame(descriptors[8, case["descriptor"]], data, entries,
                                                 row["frame_index"], case["mask"])
                self.assertEqual((result["width"], result["height"], result["frame_count"]),
                                 (case["width"], case["height"], case["frame_count"]))
                self.assertEqual([{key: part[key] for key in ("name", "offset_x", "offset_y", "depth")}
                                  for part in result["components"]], row["components"])
                self.assertEqual([part["name"] for part in result["inline_components"]], row["inline_names"])


if __name__ == "__main__":
    unittest.main()
