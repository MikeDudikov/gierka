import contextlib
import hashlib
import io
from pathlib import Path
import struct
import tempfile
import unittest

from tools.extract_setup import (SetupFormatError, decompress_block, inspect_setup,
                                 main, parse_setup)


def literal_block(payload):
    """Small fixture with <= 13 literal bytes and an explicit long terminator."""
    assert len(payload) <= 13
    flags = (1 << len(payload)) - 1 | (1 << (len(payload) + 1))
    return struct.pack("<H", flags) + payload + b"\0\0\0"


def setup_fixture(payload=b"fixture", name="game.dat", folder="", compressed=True):
    block = literal_block(payload) if compressed else payload
    header = bytearray(83)
    header[:20] = b"PQSetup data for AC\0"
    record = bytearray(563)
    struct.pack_into("<I", record, 0, 559)
    record[8] = int(compressed)
    record[9] = 128
    record[10:10 + len(name)] = name.encode()
    record[271:271 + len(folder)] = folder.encode()
    struct.pack_into("<I", record, 551, 1)
    struct.pack_into("<I", record, 559, len(block))
    return bytes(header) + block + record + struct.pack("<II", 83 + len(block), 1)


class CompressionTests(unittest.TestCase):
    def test_literals_and_empty_stream(self):
        self.assertEqual(decompress_block(literal_block(b"test")), b"test")
        self.assertEqual(decompress_block(literal_block(b"")), b"")

    def test_short_back_reference(self):
        # Literal ABC, short length3 displacement-3, end marker.
        self.assertEqual(decompress_block(b"\x47\x01ABC\xfd\0\0\0"), b"ABCABC")

    def test_long_back_reference_and_overlap(self):
        # Literal A, long length5 displacement-1, end marker.
        self.assertEqual(decompress_block(b"\x15\0A\xff\xfb\0\0\0"), b"AAAAAA")

    def test_long_extension_continue_and_extended_length(self):
        # One literal A; long extension1 is a no-op; long extension3 repeats4.
        encoded = b"\x55\0A\0\0\1\xff\xf8\3\0\0\0"
        self.assertEqual(decompress_block(encoded), b"AAAAA")

    def test_flag_word_refill_precedes_sixteenth_literal(self):
        encoded = b"\xff\xff" + b"123456789abcdef" + b"\2\0" + b"g\0\0\0"
        self.assertEqual(decompress_block(encoded), b"123456789abcdefg")

    def test_malformed_and_limits(self):
        for source in (b"", b"\1", literal_block(b"test")[:-1],
                       literal_block(b"test") + b"extra", b"\x00\0\xff"):
            with self.subTest(source=source), self.assertRaises(SetupFormatError):
                decompress_block(source)
        with self.assertRaises(SetupFormatError):
            decompress_block(literal_block(b"test"), max_output=3)
        with self.assertRaises(SetupFormatError):
            decompress_block(b"\x02\0\xff\xf9\0\0\0")


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "SETUP.DAT"
        self.source.write_bytes(setup_fixture())

    def test_report_and_extract_match_hashed_payload(self):
        destination = self.root / "files"
        report = inspect_setup(self.source, destination)
        self.assertEqual(report["totals"], {"files": 1, "directories": 0,
                                            "decoded_bytes": 7})
        self.assertEqual((destination / "game.dat").read_bytes(), b"fixture")
        self.assertEqual(report["entries"][0]["sha256"],
                         hashlib.sha256(b"fixture").hexdigest())
        self.assertEqual(self.source.read_bytes(), setup_fixture())

    def test_uncompressed_supported_and_quota_enforced(self):
        self.source.write_bytes(setup_fixture(compressed=False))
        self.assertEqual(inspect_setup(self.source)["totals"]["decoded_bytes"], 7)
        with self.assertRaises(SetupFormatError):
            inspect_setup(self.source, max_bytes=6)

    def test_traversal_and_absolute_paths_refused(self):
        for name, folder in (("../bad", ""), ("bad", "..\\"),
                             ("bad", "C:\\"), ("bad", "\\server\\"),
                             ("bad", "missing-separator")):
            with self.subTest(name=name, folder=folder), self.assertRaises(SetupFormatError):
                parse_setup(setup_fixture(name=name, folder=folder))

    def test_table_lengths_bounds_and_coverage_validated(self):
        original = setup_fixture()
        toc = struct.unpack_from("<I", original, len(original) - 8)[0]
        for offset, value in ((toc, 558), (toc + 551, 2), (toc + 559, 999999),
                              (len(original) - 8, 1)):
            source = bytearray(original)
            struct.pack_into("<I", source, offset, value)
            with self.subTest(offset=offset), self.assertRaises(SetupFormatError):
                parse_setup(source)
        with self.assertRaises(SetupFormatError):
            parse_setup(original[:-1])

    def test_existing_output_and_directory_never_overwritten(self):
        destination = self.root / "existing"
        destination.mkdir()
        marker = destination / "user.txt"
        marker.write_text("keep")
        with self.assertRaises(SetupFormatError):
            inspect_setup(self.source, destination)
        report = self.root / "report.json"
        report.write_text("keep")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main([str(self.source), "--output", str(report)]), 1)
        self.assertEqual(marker.read_text(), "keep")
        self.assertEqual(report.read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
