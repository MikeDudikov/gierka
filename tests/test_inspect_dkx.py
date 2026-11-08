import hashlib
import io
from pathlib import Path
import struct
import tempfile
import unittest
import wave

from tools.inspect_dkx import (FormatError, allocation_blocks, decode_dib,
                               decode_font, decode_pcm, export_known, inspect_pair)


def dib():
    header = bytearray(40)
    struct.pack_into("<IiiHHII", header, 0, 40, 2, 2, 1, 8, 0, 8)
    struct.pack_into("<I", header, 32, 2)
    # Bottom-up two rows, 4-byte padded stride. Palette: red, green.
    return bytes(header)+b"\0\0\xff\0\0\xff\0\0"+b"\0\1\0\0\1\0\0\0"


def pair(payload=b"data", kind=6, metadata=b"\0"*12, name=b"SPRITE"):
    index = bytearray(2112)
    index[:8] = b"DKBT\x01\x01\x00\x08"
    struct.pack_into("<I", index, 8, len(index))
    struct.pack_into("<I", index, 36, 64)
    data = bytearray(32)
    data[:8] = b"DKFM\x01\x01\0\0"
    block_size = ((len(payload)+7)//4)*4
    data += struct.pack("<I", block_size+1)+payload+b"\0"*(block_size-4-len(payload))+b"\0"*8
    struct.pack_into("<I", data, 8, len(data))
    record = struct.pack("<IIBIBI", 0xffffffff, 36, kind, len(payload), 0, len(payload))
    record += metadata+struct.pack("<H", len(name))+name
    struct.pack_into("<IIH", index, 64, 0xffffffff, 0xffffffff, len(record))
    index[80:80+len(record)] = record
    return index, data


class IndexTests(unittest.TestCase):
    def test_entry_bounds_hash_and_stale_header_bytes(self):
        index, data = pair()
        index[74:80] = b"stale!"
        entry, = inspect_pair(index, data)
        self.assertEqual(entry["name"], "SPRITE")
        self.assertEqual(entry["offset"], 36)
        self.assertEqual(entry["sha256"], hashlib.sha256(b"data").hexdigest())
        self.assertEqual(allocation_blocks(data), [(36, 4)])

    def test_cycle_and_unaligned_child_refused(self):
        for child in (64, 65, 4160):
            index, data = pair()
            struct.pack_into("<I", index, 80, child)
            with self.subTest(child=child), self.assertRaises(FormatError):
                inspect_pair(index, data)

    def test_truncated_names_size_and_allocation_markers_refused(self):
        for mutation in ("name", "node", "offset", "length", "marker", "flag"):
            index, data = pair()
            if mutation == "name": struct.pack_into("<H", index, 110, 500)
            elif mutation == "node": struct.pack_into("<H", index, 72, 2040)
            elif mutation == "offset": struct.pack_into("<I", index, 84, len(data))
            elif mutation == "length": struct.pack_into("<I", data, 8, 0)
            elif mutation == "marker": struct.pack_into("<I", data, 32, 5)
            elif mutation == "flag": index[93] = 2
            with self.subTest(mutation=mutation), self.assertRaises(FormatError):
                inspect_pair(index, data)


class PayloadTests(unittest.TestCase):
    def test_dib_palette_stride_and_bottom_up_orientation(self):
        image = decode_dib(dib())
        self.assertEqual(image.size, (2, 2))
        self.assertEqual(image.getpixel((0, 0)), (0, 255, 0))
        self.assertEqual(image.getpixel((0, 1)), (255, 0, 0))
        with self.assertRaises(FormatError): decode_dib(dib()[:-1])

    def test_pcm_preserves_samples_and_exports_standard_wave(self):
        samples = b"\x01\0\xff\x7f"
        payload = struct.pack("<HHIIHHHI", 1, 1, 22050, 44100, 2, 16, 0, 4)+b"\0"*4+samples
        fmt, result = decode_pcm(payload)
        self.assertEqual(result, samples)
        self.assertEqual(fmt["frames"], 2)
        index, data = pair(payload, 2)
        with tempfile.TemporaryDirectory() as root:
            dest = Path(root)/"exports"
            entries = inspect_pair(index, data)
            self.assertEqual(export_known(entries, data, dest), {"wav": 1})
            self.assertEqual(entries[0]["export_sha256"],
                hashlib.sha256((dest/"000000.wav").read_bytes()).hexdigest())
            self.assertEqual(entries[0]["pcm"]["samples_sha256"],
                             hashlib.sha256(samples).hexdigest())
            with wave.open(str(dest/"000000.wav"), "rb") as wav:
                self.assertEqual(wav.readframes(2), samples)
            with self.assertRaises(FileExistsError): export_known(entries, data, dest)
        with self.assertRaises(FormatError): decode_pcm(payload[:-1])

    def test_font_glyph_bounds_and_adjacent_atlas_provenance(self):
        bitmap = dib()
        font = bytearray(132)
        struct.pack_into("<H", font, 0, 1)
        struct.pack_into("<H", font, 100, 2)
        struct.pack_into("<5H", font, 102, 0, 0, 2, 2, 127)
        struct.pack_into("<5H", font, 112, 1, 0, 1, 1, 32)
        data = bytearray(32)
        offsets = []
        for p in (bitmap, font):
            size = ((len(p)+7)//4)*4
            offsets.append(len(data)+4)
            data += struct.pack("<I", size+1)+p+b"\0"*(size-4-len(p))
        data += b"\0"*8
        entry = {"offset": offsets[1], "stored_size": len(font), "compression": 0,
                 "metadata_hex": (struct.pack("<HHH", 2, 2, 2)+b"\0"*6).hex()}
        report, atlases = decode_font(entry, data, allocation_blocks(data))
        self.assertEqual(report["glyphs"], [dict(x=0, y=0, width=2, height=2, code=127),
                                           dict(x=1, y=0, width=1, height=1, code=32)])
        self.assertEqual(len(bytes.fromhex(report["header_hex"])), 102)
        self.assertEqual(report["trailer_hex"], "00" * 10)
        self.assertEqual(report["atlas_sources"][0]["sha256"], hashlib.sha256(bitmap).hexdigest())
        self.assertEqual(atlases[0].size, (2, 2))
        struct.pack_into("<H", data, offsets[1]+102, 2)
        with self.assertRaises(FormatError): decode_font(entry, data, allocation_blocks(data))


if __name__ == "__main__":
    unittest.main()
