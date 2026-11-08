import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from PIL import Image

from tools import stage_mission_units as units
from tools.decode_sprite import decode_sprite, dib_palette, resource_payload
from tools.inspect_dkx import inspect_pair
from tools.inspect_world_reference import base_palette_sprite
from tools.stage_mission_objects import write_payloads, MANIFEST_NAME as OBJECT_MANIFEST_NAME
from tools.stage_terrain import load_terrain

ROOT = units.ROOT
SOURCE_ROOT = ROOT / 'reference/raw/ancient-conquest'
SHIP_FIXTURE = ROOT / 'tests/fixtures/mission_ship_seed.json'
COMPOSITE_FIXTURE = ROOT / 'tests/fixtures/composite_original_selection.json'
CELL_FIXTURE = ROOT / 'tests/fixtures/mission_cell_flags.bin'
SHIP_FIXTURE_SHA = '1ae221249bf8812b5a033c769134b22d6266e85d232d18a53e8473fa0cfcdab9'
# Final loader proof retains every captured native result; decoder hash changed
# after the supported mixed-mask stride guard was added.
COMPOSITE_FIXTURE_SHA = '25e59c7365666e669edb6705b9c85fd5947cae5ba9c016a3563411a6d0818e50'
CELL_FLAGS_SHA = 'eb8c22b2dc3a3d6de5be5c5a28560701333cbc8610e8dd687052f4f93b260283'
ATLAS_BOTTOM_UP_SHA = 'b5fe5fd59554f82ca710a9fdce4999ca7044b7c5dddb52e724dafbfb79de284c'
ATLAS_TOP_DOWN_SHA = 'cd0bf113192d2b10f831faff6afca05e7d77f0764c8f9493d5b86460b761fa0d'


def synthetic_library(*rows):
    raw = bytearray()
    for identifier, category in rows:
        record = bytearray(211)
        record[0] = identifier
        struct.pack_into('<I', record, 4, category)
        raw.extend(record)
    return bytes(raw)


class MissionUnitsFlagAndWriteTests(unittest.TestCase):
    def test_source_flag_layout_first_id_and_unmasked_category_bits(self):
        geometry = {'map_width_cells': 2, 'map_height_cells': 1}
        raw = bytearray(32)  #8planar layers ×2cells ×2bytes.
        struct.pack_into('<H', raw, 0, 0x0101)  #Category0x21 must retain its bit above low nibble.
        struct.pack_into('<H', raw, 2, 0x6300)  #Missing ID99 is irrelevant with selector0.
        struct.pack_into('<H', raw, 10, 0xfe01)
        struct.pack_into('<H', raw, 30, 0x0201)
        library = synthetic_library((1, 0x21), (254, 0x87654321), (2, 3), (254, 0xdeadbeef))
        # Constants exercise exact source545650 behavior, including spill and
        # final32-bit wrapping; masking every category to0xf would fail.
        self.assertEqual(units.cell_flags(bytes(raw), geometry, library),
                         struct.pack('<II', 0x21, 0x35432100))
        with self.assertRaisesRegex(ValueError, 'Truncated source library'):
            units.cell_flags(bytes(raw), geometry, library[:-1])
        changed = bytearray(raw)
        struct.pack_into('<H', changed, 2, 0x6301)
        with self.assertRaisesRegex(ValueError, 'no source category'):
            units.cell_flags(bytes(changed), geometry, library)

    def test_units_manifest_writer_preserves_default_and_replacement_guards(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payloads = {'CellFlags.bytes': b'flags', 'ShipComponentsRgba.bytes': b'rgba'}
            output = root / 'Units'
            report = write_payloads(output, payloads, {'schema_version': 1}, manifest_name=units.MANIFEST_NAME)
            names = [*payloads, units.MANIFEST_NAME]
            self.assertEqual(json.loads((output / units.MANIFEST_NAME).read_text()), report)
            self.assertFalse((output / OBJECT_MANIFEST_NAME).exists())
            before = {name: (output / name).stat().st_mtime_ns for name in names}
            self.assertEqual(write_payloads(output, payloads, {'schema_version': 1},
                                            manifest_name=units.MANIFEST_NAME), report)
            self.assertEqual(before, {name: (output / name).stat().st_mtime_ns for name in names})
            changed = dict(payloads, **{'CellFlags.bytes': b'new-flags'})
            with self.assertRaises(FileExistsError):
                write_payloads(output, changed, {'schema_version': 1}, manifest_name=units.MANIFEST_NAME)
            write_payloads(output, changed, {'schema_version': 1}, True, manifest_name=units.MANIFEST_NAME)
            (output / 'ShipComponentsRgba.bytes').write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError, 'Previous generated object hash mismatch'):
                write_payloads(output, payloads, {'schema_version': 1}, True, manifest_name=units.MANIFEST_NAME)
            self.assertEqual((output / 'ShipComponentsRgba.bytes').read_bytes(), b'tampered')
            # New optional manifest parameter must preserve the previous callers.
            write_payloads(root / 'Objects', {'A.bytes': b'a'}, {})
            self.assertTrue((root / 'Objects' / OBJECT_MANIFEST_NAME).is_file())

    def test_units_manifest_and_payload_symlinks_do_not_escape_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); real = root / 'real'; real.mkdir()
            link = root / 'link'; link.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'symlinks'):
                write_payloads(link, {'CellFlags.bytes': b'x'}, {}, manifest_name=units.MANIFEST_NAME)
            retained = root / 'retained'; retained.write_bytes(b'original')
            for name in ('CellFlags.bytes', units.MANIFEST_NAME):
                path = real / name; path.symlink_to(retained)
                with self.assertRaisesRegex(ValueError, 'symlinks'):
                    write_payloads(real, {'CellFlags.bytes': b'x'}, {}, True, manifest_name=units.MANIFEST_NAME)
                self.assertEqual(retained.read_bytes(), b'original'); path.unlink()
            for name in ('../outside.json', '/tmp/outside.json', 'Unit.bytes'):
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'manifest name'):
                    write_payloads(root / 'invalid', {'CellFlags.bytes': b'x'}, {}, manifest_name=name)
            self.assertFalse((root / 'invalid').exists())


class ActualMissionUnitStagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not all((SOURCE_ROOT / name).is_file() for name in units.SOURCE_HASHES):
            raise unittest.SkipTest('Private original game inputs are not installed')
        cls.payloads, cls.metadata, cls.atlas = units.compose(SOURCE_ROOT)
        if units.digest(SHIP_FIXTURE.read_bytes()) != SHIP_FIXTURE_SHA:
            raise AssertionError('Original ship initialization fixture changed')
        if units.digest(COMPOSITE_FIXTURE.read_bytes()) != COMPOSITE_FIXTURE_SHA:
            raise AssertionError('Original type8 loader fixture changed')
        cls.ship_native = json.loads(SHIP_FIXTURE.read_text())['records']
        cls.composite_native = json.loads(COMPOSITE_FIXTURE.read_text())['cases']

    def test_original_sources_are_hash_guarded_before_parsing(self):
        self.assertEqual(len(units.SOURCE_HASHES), 7)
        self.assertEqual(set(self.metadata['sources']), set(units.SOURCE_HASHES))
        for changed_name in sorted(units.SOURCE_HASHES):
            with self.subTest(source=changed_name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                for name in units.SOURCE_HASHES:
                    path = root / name; path.parent.mkdir(parents=True, exist_ok=True)
                    if name == changed_name: path.write_bytes(b'altered original')
                    else: path.symlink_to(SOURCE_ROOT / name)
                with self.assertRaisesRegex(ValueError, 'source hash differs: ' + changed_name):
                    units.compose(root)

    def test_all576_flags_match_original_grid_creation_fixture(self):
        expected = CELL_FIXTURE.read_bytes()
        self.assertEqual(units.digest(expected), CELL_FLAGS_SHA)
        self.assertEqual(self.payloads['CellFlags.bytes'], expected)
        self.assertEqual(len(expected), 576 * 4)
        self.assertEqual((self.metadata['map_width_cells'], self.metadata['map_height_cells']), (24, 24))
        _sources, raw_map, geometry, _libraries, _palette, data, entries = load_terrain(SOURCE_ROOT)
        self.assertEqual(units.cell_flags(raw_map, geometry, resource_payload(entries[1], data)), expected)

    def test_eight_ship_recipes_match_executed_original_seed_fields(self):
        ships = self.metadata['ships']
        self.assertEqual([ship['instance_id'] for ship in ships], [11, 12, 13, 16, 39, 40, 41, 42])
        self.assertEqual((self.metadata['ship_count'], self.metadata['component_instance_count']), (8, 29))
        self.assertEqual((self.metadata['schema_version'], self.metadata['mission'],
                          self.metadata['native_canvas_width'], self.metadata['native_canvas_height']),
                         (1, 'miss000', 1920, 1080))
        keys = ('resource_name', 'instance_id', 'owner_side', 'owner_player', 'model_value',
                'model_variant', 'runtime_class_tag', 'cell_x', 'cell_y', 'heading',
                'requested_health_percent', 'source_order_count')
        for actual, native in zip(ships, self.ship_native):
            for key in keys: self.assertEqual(actual[key], native[key], (actual['resource_name'], key))
            self.assertEqual(actual['seed_payload_sha256'], native['payload_sha256'])
            self.assertEqual(actual['reference_state'], native['observed_damage_state'])
        # Header owner bytes are selection metadata. Ship ownership is copied
        # from the duplicated source fields+20/+24 by the actual LoadDateBase.
        native = self.ship_native[0]; raw = bytearray.fromhex(native['payload_hex'])
        struct.pack_into('<II', raw, 8, 4, 0)
        record = {'class_tag': 200, 'resource_name': native['resource_name'], 'instance_id': native['instance_id']}
        reread = units.ship_recipe(record, bytes(raw))
        self.assertEqual((reread['owner_side'], reread['owner_player'], reread['descriptor_resource']),
                         (native['owner_side'], native['owner_player'], 'SHIP_A1110'))

    def test_components_and_source_order_match_original_type8_loader_fixture(self):
        proof = {(case['descriptor'], case['mask'], frame['frame_index']): (case, frame)
                 for case in self.composite_native for frame in case['frames']}
        self.assertEqual({ship['descriptor_resource'] for ship in self.metadata['ships']},
                         {'SHIP_A1110', 'SHIP_H1110', 'SHIP_B4400', 'SHIP_G4400'})
        for ship in self.metadata['ships']:
            key = (ship['descriptor_resource'], ship['component_mask'], ship['reference_frame_index'])
            self.assertIn(key, proof)
            case, frame = proof[key]
            self.assertEqual((ship['logical_width'], ship['logical_height']), (case['width'], case['height']))
            self.assertEqual([{field: part[field] for field in ('name', 'offset_x', 'offset_y', 'depth')}
                              for part in ship['components']], frame['components'])
            # Negative-depth parts remain selected source components, rather
            # than being silently omitted as transparent/invalid entries.
            self.assertTrue(any(part['depth'] < 0 for part in ship['components']))
        self.assertEqual(sum(len(ship['components']) for ship in self.metadata['ships']), 29)

    def test_atlas_exact_rgba_palette_orientation_and_first_occurrence_order(self):
        self.assertEqual(self.atlas.size, (1104, 72))
        self.assertEqual(units.digest(self.atlas.tobytes()), ATLAS_TOP_DOWN_SHA)
        raw = self.payloads['ShipComponentsRgba.bytes']
        self.assertEqual((len(raw), units.digest(raw)), (317952, ATLAS_BOTTOM_UP_SHA))
        restored = Image.frombytes('RGBA', self.atlas.size, raw).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        self.assertEqual(restored.tobytes(), self.atlas.tobytes())
        names = list(dict.fromkeys(component['name'] for ship in self.metadata['ships'] for component in ship['components']))
        self.assertEqual([frame['name'] for frame in self.metadata['frames']], names)
        self.assertEqual(len(names), 17)
        data = (SOURCE_ROOT / 'files/DATA/OBJECTS.DKD').read_bytes()
        entries = inspect_pair((SOURCE_ROOT / 'files/DATA/OBJECTS.DKX').read_bytes(), data)
        lookup = {(entry['type'], entry['name']): entry for entry in entries}
        map_data = (SOURCE_ROOT / 'installed/missions/maplib.dkd').read_bytes()
        maps = inspect_pair((SOURCE_ROOT / 'installed/missions/maplib.dkx').read_bytes(), map_data)
        palette = dib_palette(resource_payload(next(e for e in maps if (e['type'], e['name']) == (1, 'PALETTE')), map_data))
        self.assertEqual(units.digest(palette), '41a0675766dab4d042bd802796139ed06259699033e0a5f8fdcc394971cd5270')
        cursor = 0
        for frame in self.metadata['frames']:
            self.assertEqual((frame['atlas_x'], frame['atlas_y']), (cursor, 0))
            sprite = decode_sprite(resource_payload(lookup[6, frame['name']], data))
            wanted = base_palette_sprite(sprite, palette)
            self.assertEqual((frame['width'], frame['height']), wanted.size)
            pixels = self.atlas.crop((cursor, 0, cursor + wanted.width, wanted.height))
            self.assertEqual(pixels.tobytes(), wanted.tobytes())
            self.assertEqual(frame['rgba_sha256'], units.digest(wanted.tobytes()))
            self.assertTrue(set(pixels.getchannel('A').tobytes()) <= {0, 255})
            cursor += wanted.width
        self.assertEqual(cursor, self.atlas.width)

    def test_unsupported_seed_layout_health_orders_and_graphics_roles_fail(self):
        base = self.ship_native[0]
        raw = bytes.fromhex(base['payload_hex'])
        record = {'class_tag': 200, 'resource_name': base['resource_name'], 'instance_id': base['instance_id']}
        with self.assertRaisesRegex(ValueError, 'Expected a source ShipClassTy'):
            units.ship_recipe(dict(record, class_tag=601), raw)
        for malformed in (b'', raw[:16], raw[:-1], raw + b'\0'):
            with self.assertRaisesRegex(ValueError, 'mode0 layout'):
                units.ship_recipe(record, malformed)
        for offset, value, message in ((16, 1, 'mode0 layout'), (16, 2, 'mode0 layout'),
                                       (48, 99, 'full-health/no-order'), (48, 101, 'full-health/no-order'),
                                       (512, 1, 'full-health/no-order'), (512, 0xffffffff, 'full-health/no-order'),
                                       (28, 2, 'verified graphics recipe'), (28, 256, 'verified graphics recipe'),
                                       (20, 0, 'verified graphics recipe'), (24, 2, 'verified graphics recipe')):
            altered = bytearray(raw); struct.pack_into('<I', altered, offset, value)
            with self.subTest(offset=offset, value=value), self.assertRaisesRegex(ValueError, message):
                units.ship_recipe(record, bytes(altered))

    def test_stage_writes_native_units_resources_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / 'Project'
            preview = Path(temporary) / 'Preview'
            report = units.stage(SOURCE_ROOT, project, preview=preview)
            output = project / 'Assets/Resources/MissionUnitsGenerated'
            self.assertEqual(report['ship_count'], 8)
            self.assertEqual(report['component_instance_count'], 29)
            self.assertEqual(json.loads((output / units.MANIFEST_NAME).read_text()), report)
            self.assertFalse((output / OBJECT_MANIFEST_NAME).exists())
            for name, raw in self.payloads.items():
                self.assertEqual((output / name).read_bytes(), raw)
                self.assertEqual(report['payloads'][name], {'bytes': len(raw), 'sha256': units.digest(raw)})
            self.assertEqual(json.loads((preview / units.MANIFEST_NAME).read_text()), report)
            with Image.open(preview / 'ship-components.png') as image:
                self.assertEqual(image.tobytes(), self.atlas.tobytes())
            names = [*self.payloads, units.MANIFEST_NAME]
            before = {name: (output / name).stat().st_mtime_ns for name in names}
            self.assertEqual(units.stage(SOURCE_ROOT, project, replace_generated=True), report)
            self.assertEqual(before, {name: (output / name).stat().st_mtime_ns for name in names})


if __name__ == '__main__':
    unittest.main()
