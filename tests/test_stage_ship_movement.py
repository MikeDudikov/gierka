import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from tools import stage_ship_movement as movement
from tools.decode_sprite import decode_sprite, dib_palette, resource_payload
from tools.inspect_dkx import inspect_pair
from tools.inspect_world_reference import base_palette_sprite
from tools.stage_mission_objects import MANIFEST_NAME as OBJECT_MANIFEST_NAME, write_payloads


ROOT = movement.ROOT
SOURCE_ROOT = ROOT / 'reference/raw/ancient-conquest'
FIXTURE = ROOT / 'tests/fixtures/ship_a_pose_selection.json'
FIXTURE_SHA = 'b1bc3be7a6db713b4055eddf949c07340436cb644fcccb1aa97c834a93b362a0'
NATIVE_REPORT_SHA = '31d8e0c923f310737bb9530f0f58ebb0f18b529dbc26cd5bf6bb4b0e9cf71386'
PIXEL_REPORT_SHA = 'eee2d0bdadac10be06eca42b8da2e8e41e4f9e021cab0afc1edd0e300ada7065'
DESCRIPTOR_SHA = 'd15bb35d34c8daf7a0f6533853cbab22c97016178538c52d24b8a07306dfed98'
ATLAS_TOP_DOWN_SHA = '8ef55b3bbf82d1c2af70c233769a1bb0606ded943a7dfd16045c6cd7027d7114'
ATLAS_BOTTOM_UP_SHA = '9b204db564030e808e6ef067aa64caef8f3f462ae555d186b55b04916193fb82'
PALETTE_SHA = '41a0675766dab4d042bd802796139ed06259699033e0a5f8fdcc394971cd5270'


class ShipMovementWriteGuardTests(unittest.TestCase):
    def test_explicit_replacement_checks_previous_hashes_before_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'Movement'
            payloads = {'ShipMovementRgba.bytes': b'original-rgba'}
            metadata = {'schema_version': 1, 'pose_count': 88}
            report = write_payloads(output, payloads, metadata, manifest_name=movement.MANIFEST_NAME)
            self.assertEqual(json.loads((output / movement.MANIFEST_NAME).read_text()), report)
            self.assertFalse((output / OBJECT_MANIFEST_NAME).exists())
            names = [*payloads, movement.MANIFEST_NAME]
            before = {name: (output / name).stat().st_mtime_ns for name in names}
            self.assertEqual(write_payloads(output, payloads, metadata,
                                            manifest_name=movement.MANIFEST_NAME), report)
            self.assertEqual(before, {name: (output / name).stat().st_mtime_ns for name in names})
            changed = {'ShipMovementRgba.bytes': b'replacement-rgba'}
            with self.assertRaises(FileExistsError):
                write_payloads(output, changed, metadata, manifest_name=movement.MANIFEST_NAME)
            self.assertEqual((output / 'ShipMovementRgba.bytes').read_bytes(), b'original-rgba')
            replaced = write_payloads(output, changed, metadata, True, manifest_name=movement.MANIFEST_NAME)
            self.assertEqual(replaced['payloads']['ShipMovementRgba.bytes']['sha256'],
                             movement.digest(b'replacement-rgba'))
            (output / 'ShipMovementRgba.bytes').write_bytes(b'tampered-rgba')
            manifest_before = (output / movement.MANIFEST_NAME).read_bytes()
            with self.assertRaisesRegex(ValueError, 'Previous generated object hash mismatch'):
                write_payloads(output, payloads, metadata, True, manifest_name=movement.MANIFEST_NAME)
            self.assertEqual((output / 'ShipMovementRgba.bytes').read_bytes(), b'tampered-rgba')
            self.assertEqual((output / movement.MANIFEST_NAME).read_bytes(), manifest_before)

    def test_symlinks_fail_without_touching_targets_and_default_manifest_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real = root / 'real'; real.mkdir()
            linked = root / 'linked'; linked.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'symlinks'):
                write_payloads(linked, {'ShipMovementRgba.bytes': b'x'}, {},
                               manifest_name=movement.MANIFEST_NAME)
            retained = root / 'retained'; retained.write_bytes(b'retained')
            for name in ('ShipMovementRgba.bytes', movement.MANIFEST_NAME):
                path = real / name; path.symlink_to(retained)
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'symlinks'):
                    write_payloads(real, {'ShipMovementRgba.bytes': b'x'}, {}, True,
                                   manifest_name=movement.MANIFEST_NAME)
                self.assertEqual(retained.read_bytes(), b'retained')
                path.unlink()
            write_payloads(root / 'Objects', {'Original.bytes': b'object'}, {})
            self.assertTrue((root / 'Objects' / OBJECT_MANIFEST_NAME).is_file())
            self.assertFalse((root / 'Objects' / movement.MANIFEST_NAME).exists())


class ActualShipMovementStagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not all((SOURCE_ROOT / name).is_file() for name in movement.SOURCE_HASHES):
            raise unittest.SkipTest('Private original game inputs are not installed')
        fixture_raw = FIXTURE.read_bytes()
        if movement.digest(fixture_raw) != FIXTURE_SHA:
            raise AssertionError('Original ship pose/pixel evidence fixture changed')
        cls.native = json.loads(fixture_raw)
        cls.payloads, cls.metadata, cls.atlas = movement.compose(SOURCE_ROOT)
        cls.data = (SOURCE_ROOT / 'files/DATA/OBJECTS.DKD').read_bytes()
        entries = inspect_pair((SOURCE_ROOT / 'files/DATA/OBJECTS.DKX').read_bytes(), cls.data)
        cls.objects = {(entry['type'], entry['name']): entry for entry in entries}
        data = (SOURCE_ROOT / 'installed/missions/maplib.dkd').read_bytes()
        maps = inspect_pair((SOURCE_ROOT / 'installed/missions/maplib.dkx').read_bytes(), data)
        cls.palette = dib_palette(resource_payload(next(entry for entry in maps
            if (entry['type'], entry['name']) == (1, 'PALETTE')), data))

    def test_all_seven_original_files_are_guarded_before_resource_decoding(self):
        self.assertEqual(len(movement.SOURCE_HASHES), 7)
        self.assertEqual(set(self.metadata['sources']), set(movement.SOURCE_HASHES))
        for name, expected in movement.SOURCE_HASHES.items():
            self.assertEqual(self.metadata['sources'][name],
                             {'bytes': (SOURCE_ROOT / name).stat().st_size, 'sha256': expected})
        for changed_name in movement.SOURCE_HASHES:
            with self.subTest(source=changed_name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                for name in movement.SOURCE_HASHES:
                    path = root / name; path.parent.mkdir(parents=True, exist_ok=True)
                    if name == changed_name:
                        path.write_bytes(b'altered original')
                    else:
                        path.symlink_to(SOURCE_ROOT / name)
                with self.assertRaisesRegex(ValueError, 'source hash differs: ' + changed_name):
                    movement.compose(root)

    def test_all_88_poses_match_actual_native_loader_and_sort_results(self):
        self.assertEqual(self.native['native_report_sha256'], NATIVE_REPORT_SHA)
        self.assertEqual(self.native['pixel_report_sha256'], PIXEL_REPORT_SHA)
        self.assertEqual(self.native['native_loader_va'], '0x554d50')
        self.assertEqual(self.native['native_sort_hooks'], [])
        self.assertEqual(self.native['pixel_entry_point'], '0x574290')
        self.assertEqual(self.native['pixel_hooked_callees'], [])
        self.assertEqual(self.native['pixel_buffer_comparisons'], 868)
        self.assertEqual((self.metadata['pose_count'], self.metadata['component_instance_count'],
                          self.metadata['plane_count']), (88, 264, 152))
        self.assertEqual((self.metadata['descriptor_resource'], self.metadata['component_mask']),
                         ('SHIP_A1110', 0x83))
        self.assertEqual(self.metadata['descriptor_payload_sha256'], DESCRIPTOR_SHA)
        self.assertEqual(movement.digest(resource_payload(self.objects[8, 'SHIP_A1110'], self.data)),
                         DESCRIPTOR_SHA)
        self.assertEqual((self.metadata['schema_version'], self.metadata['mission'],
                          self.metadata['native_canvas_width'], self.metadata['native_canvas_height']),
                         (1, 'miss000', 1920, 1080))
        poses = self.metadata['poses']
        self.assertEqual([pose['frame_index'] for pose in poses], list(range(88)))
        native_planes = {plane['name']: plane for plane in self.native['planes']}
        for pose, native in zip(poses, self.native['frames']):
            self.assertEqual((pose['logical_width'], pose['logical_height']), (56, 56))
            self.assertEqual(pose['frame_index'], native['frame_index'])
            self.assertEqual([part['source_index'] for part in pose['components']], [0, 1, 7])
            self.assertEqual([{key: part[key] for key in ('name', 'offset_x', 'offset_y', 'depth')}
                              for part in pose['components']], native['components'])
            self.assertEqual(pose['inline_draw_order'], [1, 7])
            self.assertEqual([part['name'] for part in pose['components'] if part['depth'] >= 0],
                             native['inline_names'])
            for part in pose['components']:
                self.assertEqual(part['payload_sha256'], native_planes[part['name']]['payload_sha256'])
        # Both turning and idle pose ranges are retained; forward-only 32 poses
        # cannot satisfy this native 88-pose descriptor selection contract.
        self.assertEqual(len(poses[32:56]), 24)
        self.assertEqual(len(poses[56:88]), 32)

    def test_152_planes_retain_original_bounds_flags_payloads_and_first_use_order(self):
        names = list(dict.fromkeys(part['name'] for frame in self.native['frames']
                                  for part in frame['components']))
        self.assertEqual(len(names), 152)
        self.assertEqual([plane['name'] for plane in self.metadata['planes']], names)
        native_planes = {plane['name']: plane for plane in self.native['planes']}
        for index, plane in enumerate(self.metadata['planes']):
            native = native_planes[plane['name']]
            self.assertEqual(plane['payload_sha256'], native['payload_sha256'])
            self.assertEqual(plane['flags'], native['flags'])
            self.assertEqual([plane['width'], plane['height']], native['dimensions'])
            self.assertEqual([plane[key] for key in ('left', 'top', 'box_width', 'box_height')],
                             native['bounds'])
            self.assertEqual((plane['atlas_x'], plane['atlas_y']),
                             ((index % 38) * 56, (3 - index // 38) * 56))
            self.assertEqual(movement.digest(resource_payload(self.objects[6, plane['name']], self.data)),
                             native['payload_sha256'])

    def test_every_atlas_crop_uses_exact_base_palette_and_explicit_rle_coverage(self):
        self.assertEqual(movement.digest(self.palette), PALETTE_SHA)
        self.assertEqual(self.metadata['base_palette_sha256'], PALETTE_SHA)
        covered_six = 0
        for plane in self.metadata['planes']:
            sprite = decode_sprite(resource_payload(self.objects[6, plane['name']], self.data))
            image = base_palette_sprite(sprite, self.palette)
            top = self.atlas.height - plane['atlas_y'] - plane['height']
            crop = self.atlas.crop((plane['atlas_x'], top,
                                   plane['atlas_x'] + plane['width'], top + plane['height']))
            self.assertEqual(crop.tobytes(), image.tobytes(), plane['name'])
            self.assertEqual(plane['rgba_sha256'], movement.digest(image.tobytes()))
            pixels = crop.tobytes()
            self.assertEqual(pixels[3::4], sprite['coverage'])
            self.assertTrue(set(sprite['coverage']) <= {0, 255})
            # Actual selected source planes contain covered index6 pixels.
            # Those are opaque palette colors, not a transparency convention.
            for index, (value, coverage) in enumerate(zip(sprite['indices'], sprite['coverage'])):
                if value == 6 and coverage:
                    covered_six += 1
                    self.assertEqual(pixels[index * 4:index * 4 + 4], self.palette[18:21] + b'\xff')
        self.assertEqual(covered_six, 22)

    def test_rgba_golden_hashes_bottom_up_rows_and_bounded_grid_dimensions(self):
        self.assertEqual(self.atlas.size, (2128, 224))
        self.assertEqual((self.metadata['atlas_width'], self.metadata['atlas_height'],
                          self.metadata['atlas_columns'], self.metadata['atlas_rows']), (2128, 224, 38, 4))
        self.assertEqual((self.metadata['format'], self.metadata['row_order']), ('RGBA32', 'bottom-to-top'))
        self.assertEqual(movement.digest(self.atlas.tobytes()), ATLAS_TOP_DOWN_SHA)
        raw = self.payloads['ShipMovementRgba.bytes']
        self.assertEqual(set(self.payloads), {'ShipMovementRgba.bytes'})
        self.assertEqual((len(raw), movement.digest(raw)), (1906688, ATLAS_BOTTOM_UP_SHA))
        restored = Image.frombytes('RGBA', self.atlas.size, raw).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        self.assertEqual(restored.tobytes(), self.atlas.tobytes())
        stride = self.atlas.width * 4
        self.assertEqual(raw[:stride], self.atlas.tobytes()[-stride:])
        self.assertEqual(raw[-stride:], self.atlas.tobytes()[:stride])
        self.assertLess(self.atlas.width, 8192)

    def test_stage_writes_new_resources_preview_and_reuses_unchanged_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / 'Project'
            preview = Path(temporary) / 'Preview'
            report = movement.stage(SOURCE_ROOT, project, preview=preview)
            output = project / 'Assets/Resources/ShipMovementGenerated'
            self.assertEqual(report['pose_count'], 88)
            self.assertEqual(report['component_instance_count'], 264)
            self.assertEqual(report['plane_count'], 152)
            self.assertEqual(json.loads((output / movement.MANIFEST_NAME).read_text()), report)
            self.assertFalse((output / OBJECT_MANIFEST_NAME).exists())
            self.assertEqual(json.loads((preview / movement.MANIFEST_NAME).read_text()), report)
            for name, raw in self.payloads.items():
                self.assertEqual((output / name).read_bytes(), raw)
                self.assertEqual(report['payloads'][name], {'bytes': len(raw), 'sha256': movement.digest(raw)})
            with Image.open(preview / 'ship-movement-atlas.png') as image:
                self.assertEqual(image.tobytes(), self.atlas.tobytes())
            names = [*self.payloads, movement.MANIFEST_NAME]
            before = {name: (output / name).stat().st_mtime_ns for name in names}
            self.assertEqual(movement.stage(SOURCE_ROOT, project, replace_generated=True), report)
            self.assertEqual(before, {name: (output / name).stat().st_mtime_ns for name in names})


if __name__ == '__main__':
    unittest.main()
