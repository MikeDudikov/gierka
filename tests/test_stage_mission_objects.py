import json
from pathlib import Path
import struct
import tempfile
import unittest

from PIL import Image

from tools.decode_sprite import decode_sprite, resource_payload
from tools.inspect_dkx import inspect_pair
from tools.stage_mission_objects import (ROOT, SOURCE_HASHES, MANIFEST_NAME, digest,
    pack_seeds, decode_reef_frames, compose, write_payloads)


SOURCE_ROOT = ROOT / "reference/raw/ancient-conquest"
SOURCE_NAMES = {
    "installed/ancient.exe", "installed/missions/miss000.dkx", "installed/missions/miss000.dkd",
    "installed/missions/maplib.dkx", "installed/missions/maplib.dkd",
    "files/DATA/OBJECTS.DKX", "files/DATA/OBJECTS.DKD",
}


def entry(kind, name, raw):
    return {"type": kind, "name": name, "offset": 0, "stored_size": len(raw),
            "raw_size": len(raw), "compression": 0, "sha256": digest(raw)}


def synthetic_reefs():
    data = bytearray()
    entries = []
    for variant in (2, 3):
        descriptor = bytearray(49)
        prefix = f"BREEF{variant}L_"
        descriptor[:len(prefix)] = prefix.encode("ascii")
        descriptor[32] = 2
        struct.pack_into("<hh", descriptor, 33, 0, 30)
        # Serialized dimension/pointer slots are stale, not graphic dimensions.
        descriptor[37:49] = b"\xff" * 12
        record = entry(7, f"BREEF{variant}SPR_1", descriptor)
        record["offset"] = len(data)
        data.extend(descriptor)
        entries.append(record)
        for number in range(30):
            # One written index0 at (3,5); other full-plane pixels are RLE gaps.
            raw = struct.pack("<Iii5H", 24, 64, 64, 0x80, 3, 5, 1, 1) + b"\x81\0"
            record = entry(6, prefix + f"{number:02d}", raw)
            record["offset"] = len(data)
            data.extend(raw)
            entries.append(record)
    return entries, bytes(data)


class MissionObjectPackingTests(unittest.TestCase):
    def test_seed_packing_preserves_little_endian_words_exact_payloads_and_source(self):
        first = struct.pack("<4I", 0x12345678, 2, 0x7fffffff, 0x80000000) + b"\x00\xfftail"
        second = struct.pack("<4I", 601, 1, 0xffffffff, 3)
        source1, source2 = {"offset": 200}, {"offset": 100}
        blob, records = pack_seeds([("OBJ_00000010", second, source2),
                                    ("OBJ_00000002", first, source1)])
        self.assertEqual(blob, first + second)
        self.assertEqual([record["instance_id"] for record in records], [2, 16])
        self.assertEqual([record["payload_offset"] for record in records], [0, len(first)])
        self.assertEqual([record["payload_length"] for record in records], [len(first), 16])
        self.assertEqual([record["payload_sha256"] for record in records],
                         [digest(first), digest(second)])
        self.assertEqual((records[0]["class_tag"], records[0]["kind"],
                          records[0]["side_index"], records[0]["player_index"]),
                         (0x12345678, 2, 0x7fffffff, 0x80000000))
        self.assertIs(records[0]["source"], source1)
        self.assertIs(records[1]["source"], source2)

    def test_noncanonical_names_short_headers_and_duplicate_numeric_ids_are_refused(self):
        raw = b"\0" * 16
        for name in ("OBJ_1", "OBJ_000000000", "obj_00000001", "OBJ_0000000g",
                     "OBJ_00000001\n", "OBJ_+0000001", "../OBJ_00000001"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "name/header"):
                pack_seeds([(name, raw, {})])
        for size in (0, 4, 12, 15):
            with self.subTest(size=size), self.assertRaisesRegex(ValueError, "name/header"):
                pack_seeds([("OBJ_00000001", b"\0" * size, {})])
        # Names differ, but the source IDs are hexadecimal and identical.
        with self.assertRaisesRegex(ValueError, "Duplicate object instance ID"):
            pack_seeds([("OBJ_0000000a", raw, {}), ("OBJ_0000000A", raw, {})])

    def test_reef_descriptor_naming_kind_and_full_plane_mask_are_enforced(self):
        entries, data = synthetic_reefs()
        palette = bytes((17, 31, 49)) * 256
        atlas, records = decode_reef_frames(entries, data, palette)
        self.assertEqual(atlas.size, (128, 64))
        self.assertEqual([record["frame_resource"] for record in records],
                         ["BREEF2L_00", "BREEF3L_00"])
        self.assertEqual([record["animation_frame_count"] for record in records], [30, 30])
        self.assertEqual(atlas.getpixel((3, 5)), (17, 31, 49, 255))
        self.assertEqual(atlas.getpixel((67, 5)), (17, 31, 49, 255))
        self.assertEqual(atlas.getpixel((0, 0))[3], 0)
        self.assertEqual(atlas.getpixel((6, 10))[3], 0)  # no second bbox offset
        # A later missing frame must fail even though the diagnostic draws frame0.
        missing = [record for record in entries if record["name"] != "BREEF2L_29"]
        wrong_kind = [dict(record, type=18) if record["name"] == "BREEF2L_00" else record
                      for record in entries]
        for malformed in (missing, wrong_kind):
            with self.assertRaisesRegex(ValueError, "missing source frame"):
                decode_reef_frames(malformed, data, palette)
        for offset, replacement in ((32, b"\x03"), (33, b"\x01\0"), (35, b"\xff\xff")):
            changed = bytearray(data)
            changed[offset:offset + len(replacement)] = replacement
            with self.subTest(offset=offset), self.assertRaisesRegex(ValueError, "verified loader path"):
                decode_reef_frames(entries, bytes(changed), palette)
        frame = next(record for record in entries if record["name"] == "BREEF2L_00")
        changed = bytearray(data)
        struct.pack_into("<H", changed, frame["offset"] + 12, 0x180)
        with self.assertRaisesRegex(ValueError, "full-plane path"):
            decode_reef_frames(entries, bytes(changed), palette)


class MissionObjectWriteTests(unittest.TestCase):
    def test_write_idempotence_explicit_replacement_and_previous_hash_guard(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "Generated"
            payloads = {"ObjectSeeds.bytes": b"seed", "ReefFramesRgba.bytes": b"pixels"}
            report = write_payloads(output, payloads, {"schema_version": 1})
            self.assertEqual(report["payloads"]["ObjectSeeds.bytes"],
                             {"bytes": 4, "sha256": digest(b"seed")})
            self.assertEqual(json.loads((output / MANIFEST_NAME).read_text()), report)
            names = [*payloads, MANIFEST_NAME]
            before = {name: (output / name).stat().st_mtime_ns for name in names}
            self.assertEqual(write_payloads(output, payloads, {"schema_version": 1}), report)
            self.assertEqual(before, {name: (output / name).stat().st_mtime_ns for name in names})
            with self.assertRaises(FileExistsError):
                write_payloads(output, dict(payloads, **{"ObjectSeeds.bytes": b"new"}),
                               {"schema_version": 1})
            write_payloads(output, dict(payloads, **{"ObjectSeeds.bytes": b"new"}),
                           {"schema_version": 1}, True)
            (output / "ObjectSeeds.bytes").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "Previous generated object hash mismatch"):
                write_payloads(output, payloads, {"schema_version": 1}, True)
            self.assertEqual((output / "ObjectSeeds.bytes").read_bytes(), b"tampered")

    def test_symlink_destinations_and_nonlocal_payload_names_are_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real = root / "real"
            real.mkdir()
            link = root / "link"
            link.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlinks"):
                write_payloads(link, {"A.bytes": b"x"}, {})
            outside = root / "external"
            outside.write_bytes(b"retained")
            (real / "A.bytes").symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "symlinks"):
                write_payloads(real, {"A.bytes": b"x"}, {}, True)
            self.assertEqual(outside.read_bytes(), b"retained")
            for name in ("../A.bytes", "A.png", "/tmp/A.bytes"):
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, "payload name"):
                    write_payloads(root / "new", {name: b"x"}, {})
            self.assertFalse((root / "new").exists())


class ActualMissionObjectStagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not all((SOURCE_ROOT / name).is_file() for name in SOURCE_NAMES):
            raise unittest.SkipTest("Private original game inputs are not installed")
        cls.payloads, cls.metadata, cls.atlas = compose(SOURCE_ROOT)

    def test_all_seven_original_sources_are_guarded_before_parsing(self):
        self.assertEqual(set(SOURCE_HASHES), SOURCE_NAMES)
        for changed_name in sorted(SOURCE_NAMES):
            with self.subTest(source=changed_name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                for name in SOURCE_NAMES:
                    path = root / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if name == changed_name:
                        path.write_bytes(b"altered original")
                    else:
                        path.symlink_to(SOURCE_ROOT / name)
                with self.assertRaisesRegex(ValueError, "source hash differs: " + changed_name):
                    compose(root)

    def test_exact45_source_payloads_and_original_btree_prefix_order(self):
        blob = self.payloads["ObjectSeeds.bytes"]
        self.assertEqual((len(blob), digest(blob)),
                         (8356, "448ef43d4a625439bf4d853a4d1d37cc6845ada22d6274a57be0a4ebf4383539"))
        records = self.metadata["records"]
        self.assertEqual((len(records), self.metadata["record_count"]), (45, 45))
        fixture = ROOT / "tests/fixtures/mission_miss000_object_order.json"
        self.assertEqual(digest(fixture.read_bytes()),
                         "e63f1c1b9161ef69de6d69d66bb4e0b3b1089d0eb1096b7129848863d1706348")
        proof = json.loads(fixture.read_text())
        self.assertEqual(proof["hooks"], {})
        self.assertEqual(proof["index_sha256"], SOURCE_HASHES["installed/missions/miss000.dkx"])
        self.assertEqual([(row["source"]["type"], row["resource_name"], row["source"]["offset"])
                          for row in records],
                         [(row["type"], row["name"], row["data_offset"]) for row in proof["records"]])
        mission = (SOURCE_ROOT / "installed/missions/miss000.dkd").read_bytes()
        cursor = 0
        for row in records:
            length = row["payload_length"]
            self.assertEqual(row["payload_offset"], cursor)
            actual = blob[cursor:cursor + length]
            self.assertEqual(actual, resource_payload(row["source"], mission))
            self.assertEqual(digest(actual), row["payload_sha256"])
            self.assertEqual(struct.unpack_from("<4I", actual),
                             tuple(row[name] for name in ("class_tag", "kind", "side_index", "player_index")))
            cursor += length
        self.assertEqual(cursor, len(blob))

    def test_frozen_initial_reef_atlas_palette_coverage_and_bottom_up_rows(self):
        atlas = self.atlas
        self.assertEqual(atlas.size, (128, 64))
        self.assertEqual(digest(atlas.tobytes()),
                         "2f30602d1dd9c2a5c22101c7ff661b47e13445fdbce4c0b960cd9df67690fcd3")
        raw = self.payloads["ReefFramesRgba.bytes"]
        self.assertEqual((len(raw), digest(raw)),
                         (32768, "6b033ca9c2068fa50823823066661bedff8a5a7226404c070f911142ff98707d"))
        restored = Image.frombytes("RGBA", (128, 64), raw).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        self.assertEqual(restored.tobytes(), atlas.tobytes())
        self.assertEqual(self.metadata["base_palette_sha256"],
                         "41a0675766dab4d042bd802796139ed06259699033e0a5f8fdcc394971cd5270")
        self.assertEqual((self.metadata["format"], self.metadata["row_order"]),
                         ("RGBA32", "bottom-to-top"))
        data = (SOURCE_ROOT / "files/DATA/OBJECTS.DKD").read_bytes()
        index = (SOURCE_ROOT / "files/DATA/OBJECTS.DKX").read_bytes()
        entries = {(row["type"], row["name"]): row for row in inspect_pair(index, data)}
        for frame, expected_index6, expected_gaps in zip(self.metadata["reef_frames"], (21, 9), (2585, 3009)):
            self.assertEqual((frame["reference_state"], frame["reference_frame_index"],
                              frame["animation_frame_count"]), (1, 0, 30))
            source = decode_sprite(resource_payload(entries[6, frame["frame_resource"]], data))
            pixels = atlas.crop((frame["atlas_x"], 0, frame["atlas_x"] + 64, 64)).tobytes()
            self.assertEqual(digest(pixels), frame["rgba_sha256"])
            self.assertEqual(sum(not covered for covered in source["coverage"]), expected_gaps)
            self.assertEqual(sum(value == 6 and bool(covered) for value, covered
                                 in zip(source["indices"], source["coverage"])), expected_index6)
            for position, covered in enumerate(source["coverage"]):
                self.assertEqual(pixels[4 * position + 3], 255 if covered else 0)
            # Source index6 is opaque when written; gaps alone are transparent.
            for position, (value, covered) in enumerate(zip(source["indices"], source["coverage"])):
                if value == 6 and covered:
                    self.assertEqual(pixels[4 * position + 3], 255)

    def test_descriptor_and_saved_views_remain_exact_source_not_list_obj(self):
        expected = {
            "MissionDescriptor.bytes": (1788, "458dac3b5942c5dff55d0640cb354a3761be9c824074cb99c29a939856a03ded"),
            "SavedViews.bytes": (80, "b8a17a6b40efc364c44dc2a1470a1ace8188de20e6cf057edd6865eff04800f8"),
        }
        self.assertEqual((self.metadata["schema_version"], self.metadata["mission"],
                          self.metadata["native_canvas_width"], self.metadata["native_canvas_height"]),
                         (1, "miss000", 1920, 1080))
        self.assertEqual(set(self.metadata["sources"]), SOURCE_NAMES)
        for name, expected_hash in SOURCE_HASHES.items():
            self.assertEqual(self.metadata["sources"][name]["sha256"], expected_hash)
        for name, (length, sha) in expected.items():
            self.assertEqual((len(self.payloads[name]), digest(self.payloads[name])), (length, sha))
        words = struct.unpack("<20I", self.payloads["SavedViews.bytes"])
        self.assertEqual([index for index, word in enumerate(words) if word == 15], [0, 1, 4, 5])
        self.assertTrue(all(word in (0, 15) for word in words))
        self.assertIn("LIST_OBJ is not a seed list", self.metadata["excluded"])
        self.assertIn("empty collision grid", self.metadata["reef_scope"])


if __name__ == "__main__":
    unittest.main()
