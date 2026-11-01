import contextlib
import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

from tools import inventory_original as inventory


class ZipInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="original-media-fixture-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "fixture.zip"

    def make_zip(self, members, compression=zipfile.ZIP_DEFLATED):
        with zipfile.ZipFile(self.source, "w", compression=compression) as archive:
            for name, data in members:
                archive.writestr(name, data)

    def test_metadata_hash_totals_and_candidate_labels_without_integrity_claim(self):
        members = [("disc/ORIGINAL.ISO", b"disc fixture"), ("setup/game.exe", b"exe fixture"),
                   ("text/font.fon", b"font fixture"), ("src/game.cpp", b"source fixture"),
                   ("nested/assets.7z", b"archive fixture"), ("docs/readme.txt", b"documentation")]
        self.make_zip(members)
        report = inventory.inventory_zip(self.source)
        self.assertTrue(report["success"])
        self.assertEqual(report["content_integrity"], "not_checked")
        self.assertEqual(report["source"]["sha256"], hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.assertEqual(report["source"]["size_bytes"], self.source.stat().st_size)
        self.assertEqual(report["totals"]["uncompressed_bytes"], sum(len(data) for _, data in members))
        self.assertEqual(report["totals"]["members"], len(members))
        self.assertEqual(report["candidates"]["disc_image_candidate"][0]["path"], "disc/ORIGINAL.ISO")
        self.assertEqual(report["members"][3]["candidate_labels"], ["source_code_candidate"])
        self.assertEqual(report["members"][-1]["candidate_labels"], [])
        self.assertTrue(all(member["content_sha256"] is None for member in report["members"]))

    def test_verification_streams_crc_and_member_hashes_without_extracting(self):
        payload = bytes(range(256)) * 1000
        self.make_zip([("nested/", b""), ("nested/payload.bin", payload)])
        report = inventory.inventory_zip(self.source, verify_contents=True)
        self.assertTrue(report["success"])
        self.assertEqual(report["content_integrity"], "verified")
        self.assertEqual(report["verification"]["verified_members"], 2)
        self.assertEqual(report["verification"]["bytes_read"], len(payload))
        self.assertEqual(report["members"][1]["content_sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(list(self.root.iterdir()), [self.source])

    def test_unsafe_paths_are_reported_and_block_verification(self):
        paths = ["/absolute", "../parent", "folder/../../parent", "C:/drive", "C:relative",
                 "\\\\server\\share\\file", "//server/share/file", "folder\\..\\file"]
        self.make_zip([(name, b"fixture") for name in paths])
        metadata = inventory.inventory_zip(self.source)
        self.assertEqual(metadata["totals"]["unsafe_members"], len(paths))
        self.assertTrue(metadata["success"])
        verified = inventory.inventory_zip(self.source, verify_contents=True)
        self.assertFalse(verified["success"])
        self.assertEqual(verified["content_integrity"], "not_checked")
        self.assertEqual(verified["verification"]["status"], "blocked")
        self.assertEqual(verified["verification"]["bytes_read"], 0)

    def test_nul_member_name_is_not_hidden_by_zipinfo_truncation(self):
        self.make_zip([("badXname", b"fixture")], compression=zipfile.ZIP_STORED)
        self.source.write_bytes(self.source.read_bytes().replace(b"badXname", b"bad\0name"))
        report = inventory.inventory_zip(self.source, verify_contents=True)
        self.assertIn("nul_byte", report["members"][0]["unsafe_path_issues"])
        self.assertIn("\0", report["members"][0]["path"])
        self.assertFalse(report["success"])

    def test_encrypted_flag_is_reported_and_refused(self):
        for encryption_flag in [1, 1 << 6, 1 << 13]:
            with self.subTest(encryption_flag=encryption_flag):
                self.make_zip([("encrypted.bin", b"fixture")], compression=zipfile.ZIP_STORED)
                data = bytearray(self.source.read_bytes())
                local = data.index(b"PK\x03\x04")
                central = data.index(b"PK\x01\x02")
                struct.pack_into("<H", data, local + 6, struct.unpack_from("<H", data, local + 6)[0] | encryption_flag)
                struct.pack_into("<H", data, central + 8, struct.unpack_from("<H", data, central + 8)[0] | encryption_flag)
                self.source.write_bytes(data)
                report = inventory.inventory_zip(self.source, verify_contents=True)
                self.assertEqual(report["totals"]["encrypted_members"], 1)
                self.assertEqual(report["members"][0]["general_purpose_flags"], encryption_flag)
                self.assertFalse(report["success"])
                self.assertEqual(report["verification"]["bytes_read"], 0)

    def test_corrupt_member_crc_causes_failure_and_nonzero_exit(self):
        payload = b"distinct fixture contents"
        self.make_zip([("payload.dat", payload)], compression=zipfile.ZIP_STORED)
        data = self.source.read_bytes()
        self.source.write_bytes(data.replace(payload, b"X" + payload[1:], 1))
        metadata = inventory.inventory_zip(self.source)
        self.assertTrue(metadata["success"])
        self.assertEqual(metadata["content_integrity"], "not_checked")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = inventory.main([str(self.source), "--verify-contents"])
        report = json.loads(output.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(report["content_integrity"], "failed")
        self.assertEqual(report["members"][0]["content_integrity"], "failed")
        self.assertIsNone(report["members"][0]["content_sha256"])

    def test_declared_expanded_limit_prevents_any_payload_reads(self):
        self.make_zip([("compressed.bin", b"A" * 100_000)])
        report = inventory.inventory_zip(self.source, verify_contents=True, max_expanded_bytes=100)
        self.assertFalse(report["success"])
        self.assertEqual(report["verification"]["status"], "blocked")
        self.assertEqual(report["verification"]["bytes_read"], 0)
        self.assertEqual(report["errors"][0]["code"], "expanded_size_limit")
        self.assertTrue(inventory.inventory_zip(self.source, max_expanded_bytes=100)["success"])

    def test_verification_accepts_exact_size_limit(self):
        self.make_zip([("file.txt", b"12345")])
        self.assertTrue(inventory.inventory_zip(self.source, verify_contents=True, max_expanded_bytes=5)["success"])

    def test_invalid_zip_and_missing_file_do_not_claim_integrity(self):
        for contents in [b"not a zip", b""]:
            self.source.write_bytes(contents)
            report = inventory.inventory_zip(self.source, verify_contents=True)
            self.assertFalse(report["success"])
            self.assertEqual(report["content_integrity"], "not_checked")
            self.assertEqual(report["inventory_status"], "incomplete")
        self.source.unlink()
        self.assertFalse(inventory.inventory_zip(self.source)["success"])

    def test_existing_output_and_source_are_never_overwritten(self):
        self.make_zip([("file.txt", b"fixture")])
        original = self.source.read_bytes()
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(inventory.main([str(self.source), "--output", str(self.source)]), 1)
        self.assertEqual(self.source.read_bytes(), original)
        output = self.root / "report.json"
        output.write_text("user file")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(inventory.main([str(self.source), "--output", str(output)]), 1)
        self.assertEqual(output.read_text(), "user file")

    def test_cli_writes_json_to_new_explicit_output(self):
        self.make_zip([("file.txt", b"fixture")])
        output = self.root / "report.json"
        self.assertEqual(inventory.main([str(self.source), "--output", str(output)]), 0)
        self.assertEqual(json.loads(output.read_text())["content_integrity"], "not_checked")


if __name__ == "__main__":
    unittest.main()
