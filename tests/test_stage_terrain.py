import json
from pathlib import Path
import struct
import tempfile
import unittest

from PIL import Image

from tools.stage_terrain import (ROOT, SOURCE_HASHES, digest, checked_sources,
    parse_map, map_word, rebuild_libraries, resolve_word, decode_frame,
    compose_terrain, original_lookup_oracle, write_payloads)


def library_record(identifier, prefix, kind=6, flags=0):
    record = bytearray(211)
    record[0], record[1], record[40] = identifier, flags, kind
    record[8:8 + len(prefix)] = prefix.encode("ascii")
    return bytes(record)


def entry(kind, name, raw=b""):
    return {"type": kind, "name": name, "offset": 0, "stored_size": len(raw),
            "raw_size": len(raw), "compression": 0, "sha256": digest(raw)}


class TerrainParserTests(unittest.TestCase):
    def test_planar_addressing_is_not_interleaved_and_preserves_empty_high_byte(self):
        words = list(range(48))
        words[0], words[1], words[6] = 0x3400, 0x07ff, 0x0201
        raw = struct.pack("<48H", *words)
        geometry = parse_map(struct.pack("<4h", 3, 2, 64, 64).hex(), raw)
        self.assertEqual(map_word(raw, geometry, 0, 0, 0), 0x3400)
        self.assertEqual(map_word(raw, geometry, 1, 0, 0), 0x07ff)
        self.assertEqual(map_word(raw, geometry, 0, 0, 1), 0x0201)
        self.assertEqual(map_word(raw, geometry, 2, 1, 7), 47)
        self.assertIsNone(resolve_word(0x3400, []))
        for x, y, layer in ((-1, 0, 0), (3, 0, 0), (0, 2, 0), (0, 0, 8)):
            with self.assertRaises(IndexError):
                map_word(raw, geometry, x, y, layer)
        for metadata, data in ((b"", raw), (struct.pack("<4h", -1, 2, 64, 64), raw),
                               (struct.pack("<4h", 3, 2, 64, 64), raw[:-2])):
            with self.assertRaises(ValueError):
                parse_map(metadata.hex(), data)

    def test_loader_uses_exact_kind_prefix_numeric_suffix_and_first_gap(self):
        records = b"".join((library_record(47, "b_AMBER"),
                            library_record(2, "b_AMBER"),
                            library_record(3, "b_AMBER", kind=1),
                            library_record(4, "b_AMBER", flags=128)))
        entries = [entry(6, "b_AMBER001"), entry(6, "b_AMBER003"),
                   entry(6, "b_AMBER000"), entry(6, "b_AMBER_001"),
                   entry(1, "b_AMBER001"), entry(1, "b_AMBER002")]
        libraries = rebuild_libraries(records, "0400", entries)
        self.assertEqual([len(item["frames"]) for item in libraries], [1, 1, 2, 0])
        self.assertEqual(libraries[1]["alias_of_ordinal"], 0)
        self.assertIs(libraries[1]["frames"], libraries[0]["frames"])
        self.assertIsNone(libraries[2]["alias_of_ordinal"])
        library, index, selected = resolve_word(0x2f01, libraries)
        self.assertEqual((library["ordinal"], index, selected["name"]), (0, 0, "b_AMBER001"))
        self.assertEqual(resolve_word(0x0302, libraries)[2]["type"], 1)
        for word in (0x2f02, 0x0401, 0x0501):
            with self.assertRaisesRegex(ValueError, "no loaded"):
                resolve_word(word, libraries)
        with self.assertRaisesRegex(ValueError, "Ambiguous duplicate"):
            rebuild_libraries(records, "0400", entries + [entries[0]])

    def test_dib_is_opaque_in_world_palette_including_indices_zero_and_six(self):
        # Embedded DIB palette deliberately differs: indexed game surface uses
        # the installed world palette, so embedded RGB must not override it.
        raw = (struct.pack("<IiiHH6I", 40, 2, 1, 1, 8, 0, 4, 0, 0, 256, 0)
               + b"\0\0\0\0" * 256 + bytes((0, 6, 0, 0)))
        palette = bytes(value for index in range(256) for value in (index, 40, 90))
        image, info = decode_frame(entry(1, "opaque", raw), raw, palette)
        self.assertEqual(image.tobytes(), bytes((0, 40, 90, 255, 6, 40, 90, 255)))
        self.assertEqual(info["embedded_palette_used_index_mismatches"], [0, 6])

    def test_sprite_bounds_are_content_crop_not_external_pivot_and_zero_is_opaque(self):
        raw = struct.pack("<Iii5H", 24, 3, 3, 0x80, 1, 1, 1, 1) + b"\x81\0"
        palette = bytes((17, 31, 49)) * 256
        image, info = decode_frame(entry(6, "masked", raw), raw, palette)
        background = Image.new("RGBA", (3, 3), (200, 100, 50, 255))
        background.alpha_composite(image)
        self.assertEqual(background.getpixel((1, 1)), (17, 31, 49, 255))
        self.assertEqual(background.getpixel((2, 2)), (200, 100, 50, 255))
        self.assertEqual(image.getpixel((0, 0))[3], 0)
        self.assertEqual(info["content_bounds"], [1, 1, 1, 1])


class TerrainStagingTests(unittest.TestCase):
    def test_orientation_hash_idempotence_explicit_replacement_and_tamper_guard(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "TerrainGenerated"
            terrain = Image.new("RGBA", (1, 2))
            terrain.putpixel((0, 0), (1, 2, 3, 4))
            terrain.putpixel((0, 1), (5, 6, 7, 8))
            metadata = {"schema_version": 1}
            report = write_payloads(output, terrain, b"\x34\x12", metadata)
            path = output / "TerrainRgba.bytes"
            self.assertEqual(path.read_bytes(), bytes((5, 6, 7, 8, 1, 2, 3, 4)))
            self.assertEqual((output / "MapPlanar.bytes").read_bytes(), b"\x34\x12")
            self.assertEqual(report["payloads"][path.name]["sha256"], digest(path.read_bytes()))
            before = {name: (output / name).stat().st_mtime_ns for name in
                      ("TerrainRgba.bytes", "MapPlanar.bytes", "TerrainManifest.json")}
            self.assertEqual(write_payloads(output, terrain, b"\x34\x12", metadata), report)
            self.assertEqual(before, {name: (output / name).stat().st_mtime_ns for name in before})
            with self.assertRaises(FileExistsError):
                write_payloads(output, terrain, b"new", metadata)
            write_payloads(output, terrain, b"new", metadata, True)
            path.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "Previous generated terrain hash"):
                write_payloads(output, terrain, b"other", metadata, True)
            self.assertEqual(path.read_bytes(), b"tampered")

    def test_changed_original_and_symlink_output_are_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "installed/ancient.exe"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"altered")
            with self.assertRaisesRegex(ValueError, "source hash differs"):
                checked_sources(root)
            (root / "real").mkdir()
            (root / "link").symlink_to(root / "real", target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlinks"):
                write_payloads(root / "link", Image.new("RGBA", (1, 1)), b"", {})

    def test_actual_composite_keeps_all_source_placements_and_palette_masks(self):
        source_root = ROOT / "reference/raw/ancient-conquest"
        if not all((source_root / name).is_file() for name in SOURCE_HASHES):
            self.skipTest("Private original game inputs are not installed")
        terrain, layers, raw, report = compose_terrain(source_root)
        self.assertEqual(terrain.size, (1536, 1536))
        self.assertEqual(terrain.getextrema()[3], (255, 255))
        self.assertEqual(digest(terrain.tobytes()),
                         "fc3d2a19db9dabc77e9883dfdf5e86a96edc55233fe02c3d9501831e4ec71ee1")
        self.assertEqual(len(layers), 8)
        self.assertEqual((report["native_canvas_width"], report["native_canvas_height"]), (1920, 1080))
        self.assertEqual(report["active_counts_by_layer"], [576, 9, 132, 70, 85, 12, 41, 82])
        self.assertEqual((report["draw_count"], report["unique_frame_count"]), (1007, 264))
        self.assertEqual(len(report["active_libraries"]), 17)
        self.assertTrue(all(not info.get("embedded_palette_used_index_mismatches") for info in report["frames"]))
        self.assertTrue(all((info["width"], info["height"]) == (64, 64) for info in report["frames"]))
        self.assertEqual(digest(raw), "931138965e7ff49641ff28e389a48104f113d66666badf6de027c8d6e716cfe3")
        # Independent original x86 lookup fixture selects every frame/cell. It
        # also includes 3601 inactive cells, not only visible draw traces.
        fixture = ROOT / "tests/fixtures/terrain_miss000_lookup.bin"
        evidence = json.loads(fixture.with_suffix(".json").read_text())
        self.assertEqual(digest(fixture.read_bytes()), evidence["rows_sha256"])
        active = []
        for offset, (word, index, kind) in enumerate(struct.iter_unpack("<HhB", fixture.read_bytes())):
            if index >= 0:
                x, remainder = divmod(offset, 24 * 8)
                y, layer = divmod(remainder, 8)
                active.append((x, y, layer, word, index, kind))
        self.assertEqual([(row["x"], row["y"], row["layer"], row["word"], row["frame_index"], row["drawing_type"])
                          for row in report["draw_trace"]], active)

    def test_original_x86_accessor_matches_all4608_source_cells_without_hooks(self):
        source_root = ROOT / "reference/raw/ancient-conquest"
        if not all((source_root / name).is_file() for name in SOURCE_HASHES):
            self.skipTest("Private original game inputs are not installed")
        rows, report = original_lookup_oracle(source_root)
        fixture = ROOT / "tests/fixtures/terrain_miss000_lookup.bin"
        self.assertEqual(rows, fixture.read_bytes())
        self.assertEqual(report, json.loads(fixture.with_suffix(".json").read_text()))
        self.assertEqual((report["cases"], report["active_cases"], report["bounds_cases"]), (4608, 1007, 6))
        self.assertEqual(report["intercepted_functions"], [])


if __name__ == "__main__":
    unittest.main()
