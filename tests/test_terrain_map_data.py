import hashlib
from pathlib import Path
import struct
import tempfile
import unittest

from tools import validate_terrain_map_data as terrain


RAW_MAP_SHA256 = "931138965e7ff49641ff28e389a48104f113d66666badf6de027c8d6e716cfe3"
FIXTURE_SHA256 = "2c26432812ce2c1a4862c0b36f4d5716da972bb5d78e64298469b057ab0d018d"
PROVENANCE_SHA256 = "a7f6558d7ff68f01dad5e096fab5ae53999f298432fa2c1ee2be8f37d3774f44"


class TerrainMapDataDifferentialTests(unittest.TestCase):
    def load_reference(self):
        try:
            return terrain.load_reference()
        except terrain.MissingPrerequisite as error:
            self.skipTest(str(error))

    def test_frozen_native_rows_match_the_guarded_planar_source(self):
        raw_map, rows, evidence = self.load_reference()
        self.assertEqual(hashlib.sha256(raw_map).hexdigest(), RAW_MAP_SHA256)
        self.assertEqual(hashlib.sha256(terrain.FIXTURE.read_bytes()).hexdigest(), FIXTURE_SHA256)
        self.assertEqual(hashlib.sha256(terrain.PROVENANCE.read_bytes()).hexdigest(), PROVENANCE_SHA256)
        self.assertEqual(len(raw_map), 24 * 24 * 8 * 2)
        self.assertEqual(len(rows), 4608)
        self.assertEqual(evidence["entry_va"], "0x00545190")
        self.assertEqual(evidence["intercepted_functions"], [])
        self.assertEqual(evidence["rows_sha256"], FIXTURE_SHA256)
        self.assertEqual(evidence["map_sha256"], RAW_MAP_SHA256)

        active = 0
        for row_number, (word, frame_index, drawing_type) in enumerate(rows):
            x, remainder = divmod(row_number, 24 * 8)
            y, layer = divmod(remainder, 8)
            offset = 2 * ((layer * 24 + y) * 24 + x)
            self.assertEqual(word, struct.unpack_from("<H", raw_map, offset)[0])
            if word & 255:
                active += 1
                self.assertEqual(frame_index, (word & 255) - 1)
                self.assertIn(drawing_type, (1, 6))
            else:
                self.assertEqual((frame_index, drawing_type), (-1, 255))
        self.assertEqual(active, 1007)
        self.assertEqual(len(rows) - active, 3601)

    def test_tampered_native_fixture_is_rejected(self):
        self.load_reference()
        altered = bytearray(terrain.FIXTURE.read_bytes())
        altered[0] ^= 1
        with tempfile.TemporaryDirectory(prefix="terrain-map-fixture-") as temporary:
            path = Path(temporary) / "lookup.bin"
            path.write_bytes(altered)
            with self.assertRaises(ValueError):
                terrain.load_reference(fixture=path)

    def test_changed_provenance_bytes_are_rejected_even_when_json_is_unchanged(self):
        self.load_reference()
        with tempfile.TemporaryDirectory(prefix="terrain-map-provenance-") as temporary:
            path = Path(temporary) / "lookup.json"
            path.write_bytes(terrain.PROVENANCE.read_bytes() + b" ")
            with self.assertRaises(ValueError):
                terrain.load_reference(provenance=path)

    def test_changed_high_byte_of_empty_source_selector_is_rejected(self):
        raw_map, _, _ = self.load_reference()
        altered = bytearray(raw_map)
        offset = next(offset for offset in range(0, len(altered), 2) if altered[offset] == 0)
        altered[offset + 1] ^= 0x80
        with tempfile.TemporaryDirectory(prefix="terrain-map-source-") as temporary:
            path = Path(temporary) / "MapPlanar.bytes"
            path.write_bytes(altered)
            with self.assertRaises(ValueError):
                terrain.load_reference(raw_map=path)

    def test_actual_csharp_matches_all_4608_native_rows_and_checks_map_guards(self):
        try:
            report = terrain.validate()
        except terrain.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(report["case_count"], 4608)
        self.assertEqual(report["passed"], 4608)
        self.assertEqual(report["active_cases"], 1007)
        self.assertEqual(report["inactive_cases"], 3601)
        self.assertTrue(report["checked_compilation"])
        checks = report["csharp_guard_checks"]
        self.assertIsInstance(checks, list)
        self.assertTrue(all(isinstance(check, str) for check in checks))
        required = {
            "input_immutability", "geometry_properties", "layer_count",
            "ctor_length_null", "ctor_length_short", "ctor_length_long", "ctor_large_length",
            "bounds_x_negative", "bounds_layer_end",
        } | {f"selector_bytes_{layer}" for layer in range(8)}
        self.assertTrue(required.issubset(checks), f"Missing C# guard checks: {sorted(required - set(checks))}")


if __name__ == "__main__":
    unittest.main()
