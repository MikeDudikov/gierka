import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import pycdlib

from tools import inventory_disc as disc


def sector(payload):
    assert len(payload) == 2048
    return disc.SYNC + b'\x00\x00\x00\x01' + payload + bytes(288)


class DiscInventoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='disc-fixture-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.bin = self.root / 'fixture.bin'
        self.cue = self.root / 'fixture.cue'

    def cue_text(self, tail=''):
        self.cue.write_text('FILE "fixture.BIN" BINARY\n TRACK 01 MODE1/2352\n INDEX 01 00:00:00\n' + tail)

    def make_iso(self):
        iso = pycdlib.PyCdlib()
        iso.new(interchange_level=3)
        payload = b'test payload' * 300
        iso.add_fp(io.BytesIO(payload), len(payload), iso_path='/TEST.BIN;1')
        iso.add_fp(io.BytesIO(b''), 0, iso_path='/EMPTY.TXT;1')
        content = io.BytesIO()
        iso.write_fp(content)
        iso.close()
        data = content.getvalue()
        self.bin.write_bytes(b''.join(sector(data[i:i+2048]) for i in range(0, len(data), 2048)))
        self.cue_text()
        return payload

    def test_case_insensitive_resolution_and_audio_boundaries(self):
        self.bin.write_bytes(sector(bytes(2048)) * 20)
        self.cue_text(' TRACK 02 AUDIO\n PREGAP 00:02:00\n INDEX 00 00:00:09\n INDEX 01 00:00:10\n')
        path, tracks = disc.parse_cue(self.cue)
        self.assertEqual(path, self.bin)
        self.assertEqual(tracks[0].end_sector, 9)
        self.assertEqual(tracks[1].pregap, 150)
        self.assertEqual(tracks[1].end_sector, 20)

    def test_rejects_case_ambiguity_even_when_exact_match_exists(self):
        self.bin.write_bytes(sector(bytes(2048)))
        (self.root / 'fixture.BIN').write_bytes(self.bin.read_bytes())
        self.cue_text()
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            disc.parse_cue(self.cue)

    def test_cue_refuses_traversal_symlink_and_unsupported_directives(self):
        self.bin.write_bytes(sector(bytes(2048)))
        for name in ('../fixture.bin', '/fixture.bin', 'C:fixture.bin', 'folder\\fixture.bin'):
            with self.subTest(name=name):
                self.cue.write_text(f'FILE "{name}" BINARY\n TRACK 01 MODE1/2352\n INDEX 01 00:00:00\n')
                with self.assertRaises(ValueError):
                    disc.parse_cue(self.cue)
        self.bin.unlink()
        target = self.root / 'target.bin'
        target.write_bytes(sector(bytes(2048)))
        self.bin.symlink_to(target)
        self.cue_text()
        with self.assertRaisesRegex(ValueError, 'symlink'):
            disc.parse_cue(self.cue)
        self.bin.unlink()
        self.bin.write_bytes(target.read_bytes())
        self.cue_text(' FLAGS PRE\n')
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            disc.parse_cue(self.cue)

    def test_cue_invalid_indexes_and_truncation(self):
        self.bin.write_bytes(sector(bytes(2048)) * 3)
        bad = [
            'FILE "fixture.bin" BINARY\n TRACK 01 MODE1/2352\n',
            'FILE "fixture.bin" BINARY\n TRACK 01 AUDIO\n INDEX 01 00:00:00\n',
            'FILE "fixture.bin" BINARY\n TRACK 01 MODE1/2352\n INDEX 01 00:00:03\n',
            'FILE "fixture.bin" BINARY\n TRACK 01 MODE1/2352\n INDEX 01 00:00:00\n TRACK 02 AUDIO\n INDEX 01 00:00:00\n',
            'FILE "fixture.bin" BINARY\n TRACK 01 MODE1/2352\n INDEX 00 00:00:02\n INDEX 01 00:00:01\n',
            'FILE "fixture.bin" BINARY\n TRACK 02 MODE1/2352\n INDEX 01 00:00:00\n',
            'FILE "fixture.bin" BINARY\n TRACK 01 MODE1/2352\n INDEX 01 00:60:00\n',
            'FILE "fixture.bin" BINARY\n TRACK 01 MODE1/2352\n INDEX 01 00:00:75\n',
        ]
        for text in bad:
            with self.subTest(text=text):
                self.cue.write_text(text)
                with self.assertRaises(ValueError):
                    disc.parse_cue(self.cue)
        self.cue_text()
        self.bin.write_bytes(b'truncated')
        with self.assertRaisesRegex(ValueError, 'multiple'):
            disc.parse_cue(self.cue)

    def test_mode1_reads_seek_boundaries_and_excludes_audio(self):
        first = bytes(range(256)) * 8
        second = bytes(reversed(range(256))) * 8
        self.bin.write_bytes(sector(bytes(2048)) + sector(first) + sector(second) + bytes(2352))
        with disc.Mode1View(self.bin, 1, 3) as view:
            self.assertEqual(view.read(3), first[:3])
            self.assertEqual(view.seek(2046), 2046)
            self.assertEqual(view.read(5), first[-2:] + second[:3])
            view.seek(-2, io.SEEK_END)
            self.assertEqual(view.read(), second[-2:])
            self.assertEqual(view.read(), b'')
            view.seek(9999)
            self.assertEqual(view.read(), b'')
            with self.assertRaises(ValueError):
                view.seek(-1)
            with self.assertRaises(ValueError):
                view.seek(0, 99)
            with self.assertRaises(TypeError):
                view.seek(1.5)
            with self.assertRaises(TypeError):
                view.read(1.5)
            view.seek(4096)
            self.assertEqual(view.read(-2), b'')
            view.seek(0)
            buffer = bytearray(10)
            self.assertEqual(view.readinto(buffer), 10)
            self.assertEqual(bytes(buffer), first[:10])
        with self.assertRaises(ValueError):
            view.read(1)

    def test_bad_mode_sync_short_sector_and_invalid_bounds_are_refused(self):
        good = sector(bytes(2048))
        for data in (b'X' + good[1:], good[:15] + b'\x02' + good[16:]):
            self.bin.write_bytes(data)
            with disc.Mode1View(self.bin, 0, 1) as view:
                with self.assertRaisesRegex(ValueError, 'Invalid MODE1'):
                    view.read()
        self.bin.write_bytes(good)
        for start, end in ((-1, 1), (0, 0), (0, 2)):
            with self.assertRaises(ValueError):
                disc.Mode1View(self.bin, start, end)
        self.bin.write_bytes(good[:-1])
        with self.assertRaises(ValueError):
            disc.Mode1View(self.bin, 0, 1)

    def test_real_iso_inventory_and_extraction_hashes_match(self):
        payload = self.make_iso()
        output = self.root / 'extracted'
        report = disc.inventory_disc(self.cue, extract_to=output)
        self.assertTrue(report['success'])
        self.assertEqual(report['total_file_bytes'], len(payload))
        self.assertEqual((output / 'TEST.BIN').read_bytes(), payload)
        files = {f['relative_path']: f for f in report['files']}
        self.assertEqual(files['TEST.BIN']['sha256'], hashlib.sha256(payload).hexdigest())
        self.assertEqual(files['EMPTY.TXT']['size_bytes'], 0)
        self.assertEqual(report['source']['bin_sha256'], hashlib.sha256(self.bin.read_bytes()).hexdigest())
        raw = self.bin.read_bytes()
        logical = b''.join(raw[i+16:i+16+2048] for i in range(0, len(raw), 2352))
        self.assertEqual(report['data_track']['payload_sha256'], hashlib.sha256(logical).hexdigest())
        self.assertEqual(list(self.root.glob('*.iso')), [])

    def test_byte_quota_prevents_output_and_existing_outputs_preserved(self):
        self.make_iso()
        output = self.root / 'extracted'
        with self.assertRaisesRegex(ValueError, 'quota'):
            disc.inventory_disc(self.cue, extract_to=output, max_bytes=1)
        self.assertFalse(output.exists())
        output.mkdir()
        sentinel = output / 'keep.txt'
        sentinel.write_text('user file')
        with self.assertRaises(FileExistsError):
            disc.inventory_disc(self.cue, extract_to=output)
        self.assertEqual(sentinel.read_text(), 'user file')
        report = self.root / 'report.json'
        report.write_text('user report')
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(disc.main([str(self.cue), '--output', str(report)]), 1)
        self.assertEqual(report.read_text(), 'user report')

    def test_report_cli_valid_json_and_invalid_iso_nonzero(self):
        self.make_iso()
        report = self.root / 'report.json'
        self.assertEqual(disc.main([str(self.cue), '--output', str(report)]), 0)
        self.assertTrue(json.loads(report.read_text())['success'])
        self.bin.write_bytes(sector(bytes(2048)) * 20)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(disc.main([str(self.cue)]), 1)


    def make_audio(self):
        self.bin.write_bytes(b''.join(bytes([i]) * 2352 for i in range(10)))
        self.cue_text(' TRACK 02 AUDIO\n PREGAP 00:02:00\n INDEX 00 00:00:01\n INDEX 01 00:00:02\n'
                      ' TRACK 03 AUDIO\n INDEX 00 00:00:06\n INDEX 01 00:00:07\n')
        return disc.parse_cue(self.cue)[1]

    def test_raw_audio_exact_ranges_final_track_and_manifest(self):
        tracks = self.make_audio()
        output = self.root / 'audio'
        report = disc.export_audio(self.bin, tracks, output)
        self.assertTrue(report['success'])
        self.assertEqual(report['total_bytes'], 7 * 2352)
        self.assertEqual(report['pcm_sample_byte_order'], 'unverified; no WAV conversion performed')
        first, final = report['tracks']
        self.assertEqual(first['source_byte_offset'], 2 * 2352)
        self.assertEqual(first['size_bytes'], 4 * 2352)
        self.assertEqual(first['stereo_sample_frames'], 4 * 588)
        self.assertEqual(first['synthetic_pregap_sectors_excluded'], 150)
        self.assertEqual(first['stored_pregap_sectors_excluded'], 1)
        self.assertEqual(final['end_sector_exclusive'], 10)
        self.assertEqual(final['stereo_sample_frames'], 3 * 588)
        raw = self.bin.read_bytes()
        for entry in report['tracks']:
            data = (output / entry['file']).read_bytes()
            start = entry['source_byte_offset']
            self.assertEqual(data, raw[start:start + entry['size_bytes']])
            self.assertEqual(entry['sha256'], hashlib.sha256(data).hexdigest())
        self.assertEqual(json.loads((output / 'audio-manifest.json').read_text()), report)
        self.assertEqual(list(output.glob('*.wav')), [])

    def test_audio_output_collisions_symlinks_and_quota_refused_before_writes(self):
        tracks = self.make_audio()
        output = self.root / 'audio'
        with self.assertRaisesRegex(ValueError, 'quota'):
            disc.export_audio(self.bin, tracks, output, max_bytes=1)
        self.assertFalse(output.exists())
        output.mkdir()
        sentinel = output / 'keep.txt'
        sentinel.write_text('user content')
        with self.assertRaises(FileExistsError):
            disc.export_audio(self.bin, tracks, output)
        self.assertEqual(sentinel.read_text(), 'user content')
        link = self.root / 'link'
        link.symlink_to(output, target_is_directory=True)
        with self.assertRaises(FileExistsError):
            disc.export_audio(self.bin, tracks, link)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            disc.export_audio(self.bin, tracks, link / 'nested')
        self.assertFalse((output / 'nested').exists())
        broken = self.root / 'broken'
        broken.symlink_to(self.root / 'missing', target_is_directory=True)
        with self.assertRaises(FileExistsError):
            disc.export_audio(self.bin, tracks, broken)

    def test_audio_refuses_data_overlap_out_of_bounds_and_no_audio(self):
        tracks = self.make_audio()
        tracks[1].index01 = 0
        with self.assertRaisesRegex(ValueError, 'overlap'):
            disc.export_audio(self.bin, tracks, self.root / 'output')
        tracks = self.make_audio()
        tracks[-1].end_sector = 11
        with self.assertRaisesRegex(ValueError, 'outside'):
            disc.export_audio(self.bin, tracks, self.root / 'output')
        with self.assertRaisesRegex(ValueError, 'no audio'):
            disc.export_audio(self.bin, tracks[:1], self.root / 'output')
        self.assertFalse((self.root / 'output').exists())

    def test_audio_option_with_actual_iso_and_output_overlap_refused(self):
        self.make_iso()
        sectors = self.bin.stat().st_size // 2352
        with self.bin.open('ab') as target:
            target.write(bytes([73]) * 2352 * 2)
        minutes, remainder = divmod(sectors, 75 * 60)
        seconds, frame = divmod(remainder, 75)
        self.cue_text(f' TRACK 02 AUDIO\n PREGAP 00:02:00\n INDEX 01 {minutes:02d}:{seconds:02d}:{frame:02d}\n')
        output = self.root / 'audio'
        extracted = self.root / 'data'
        report = disc.inventory_disc(self.cue, audio_to=output, extract_to=extracted)
        self.assertEqual(report['audio_export']['tracks'][0]['sectors'], 2)
        self.assertEqual((output / 'track02.cdda').read_bytes(), bytes([73]) * 2352 * 2)
        self.assertTrue((extracted / 'TEST.BIN').is_file())
        overlap = self.root / 'overlap'
        with self.assertRaisesRegex(ValueError, 'overlap'):
            disc.inventory_disc(self.cue, extract_to=overlap, audio_to=overlap / 'child' / '..')
        self.assertFalse(overlap.exists())


if __name__ == '__main__':
    unittest.main()
