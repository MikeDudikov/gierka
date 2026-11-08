from pathlib import Path
import tempfile
import unittest

from tools import stage_ship_picking as picking


class StageShipPickingTests(unittest.TestCase):
    def source(self):
        root = picking.ROOT / 'reference/raw/ancient-conquest'
        if not all((root / name).is_file() for name in picking.SOURCE_HASHES):
            self.skipTest('Private original ship assets unavailable')
        return root

    def test_original_four_families_keep_exact_planes_and_logical_geometry(self):
        payloads, manifest = picking.compose(self.source())
        self.assertEqual(manifest['mask_count'], 96)
        self.assertEqual([(f['family'], f['width'], f['height']) for f in manifest['families']],
                         [('A1', 56, 56), ('H1', 72, 72), ('B4', 64, 64), ('G4', 72, 72)])
        blob = payloads['ShipHitMasks.bytes']
        self.assertEqual(len(blob), 52800)
        self.assertEqual(picking.digest(blob), '60f3696904880fa4c4a51da2094f96145b30859013463369d1b953aebf3ba240')
        offset = 0
        for family in manifest['families']:
            for plane in family['masks']:
                self.assertEqual(plane['offset'], offset)
                raw = blob[offset:offset + plane['length']]
                self.assertEqual(picking.digest(raw), plane['sha256'])
                offset += plane['length']
        self.assertEqual(offset, len(blob))

    def test_staging_is_idempotent_and_rejects_modified_previous_payload(self):
        source = self.source()
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            first = picking.stage(source, project)
            output = project / 'Assets/Resources/ShipPickingGenerated'
            before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir()}
            self.assertEqual(picking.stage(source, project), first)
            self.assertEqual(before, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir()})
            data = output / 'ShipHitMasks.bytes'
            raw = bytearray(data.read_bytes()); raw[0] ^= 1; data.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, 'Previous generated object hash mismatch'):
                picking.stage(source, project, replace_generated=True)

    def test_changed_original_is_rejected_without_writing_project(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            exe = root / 'installed/ancient.exe'; exe.parent.mkdir(); exe.write_bytes(b'changed source')
            with self.assertRaisesRegex(ValueError, 'Original source hash differs: installed/ancient.exe'):
                picking.compose(root)


if __name__ == '__main__':
    unittest.main()
