from pathlib import Path
import hashlib,json,tempfile,unittest
from PIL import Image
from tools import stage_ship_heavy_movement as heavy,probe_ship_heavy_poses as native
from tools.decode_sprite import decode_sprite

FIXTURE=heavy.ROOT/'tests/fixtures/ship_heavy_poses.json'
FIXTURE_SHA='abc5d63688c335ad456dbeea4adfb1f9d9be254ddec53aa8d93af42308f7bbe2'


class ShipHeavyMovementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest()==FIXTURE_SHA
        cls.reference=json.loads(FIXTURE.read_text())
        cls.payloads,cls.meta,cls.atlas=heavy.compose()

    def test_fresh_original_loader_sort_and_1342_pixel_buffers_match_pinned_evidence(self):
        self.assertEqual(native.fixture(),self.reference)
        self.assertEqual((self.reference['selected_frames'],self.reference['component_rows'],len(self.reference['planes']),self.reference['pixel_buffer_comparisons']),(88,352,224,1342))
        self.assertEqual((self.reference['sort_hooks'],self.reference['pixel_hooks']),([],[]))

    def test_88_staged_poses_keep_original_four_parts_armor_and_inline_order(self):
        self.assertEqual((self.meta['instance_id'],self.meta['descriptor_resource'],self.meta['component_mask']),(13,'SHIP_H1110',0xa3))
        for staged,source in zip(self.meta['poses'],self.reference['row']['frames']):
            self.assertEqual((staged['logical_width'],staged['logical_height'],staged['inline_draw_order']),(72,72,[1,5,7]))
            self.assertEqual([p['source_index']for p in staged['components']],[0,1,5,7])
            self.assertEqual([{k:p[k]for k in('name','offset_x','offset_y','depth')}for p in staged['components']],source['components'])
            self.assertEqual([p['name']for p in staged['components']if p['depth']>=0],source['inline_names'])
        self.assertEqual(self.meta['component_instance_count'],352)

    def test_every_plane_atlas_crop_and_bottom_up_bytes_keep_source_rle_coverage(self):
        m=native.bootstrap();maps_raw=(heavy.ROOT/'reference/raw/ancient-conquest/installed/missions/maplib.dkd').read_bytes()
        maps=heavy.movement.inspect_pair((heavy.ROOT/'reference/raw/ancient-conquest/installed/missions/maplib.dkx').read_bytes(),maps_raw)
        palette=heavy.movement.dib_palette(heavy.movement.resource_payload(next(e for e in maps if(e['type'],e['name'])==(1,'PALETTE')),maps_raw))
        proof={p['name']:p for p in self.reference['planes']}
        self.assertEqual(len(self.meta['planes']),224)
        for p in self.meta['planes']:
            raw=m['resource_payload'](m['resources'][6,p['name']],m['data']);s=decode_sprite(raw);image=heavy.movement.base_palette_sprite(s,palette)
            top=504-p['atlas_y']-72;crop=self.atlas.crop((p['atlas_x'],top,p['atlas_x']+72,top+72))
            self.assertEqual(crop.tobytes(),image.tobytes(),p['name'])
            self.assertEqual(crop.tobytes()[3::4],s['coverage'])
            self.assertEqual(p['payload_sha256'],proof[p['name']]['payload_sha256'])
        raw=self.payloads['ShipHeavyMovementRgba.bytes']
        self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(4644864,'f057829bdbd9c53090bc2b680ef419e299bd5e56c4a33c275f6a0177cb194138'))
        self.assertEqual(Image.frombytes('RGBA',(2304,504),raw).transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes(),self.atlas.tobytes())

    def test_tenth_stage_is_idempotent_and_keeps_existing_A_resources_unchanged(self):
        old=heavy.ROOT/'Unity/AncientConquest/Assets/Resources/ShipMovementGenerated'
        before={p.name:p.read_bytes()for p in old.iterdir()if p.is_file()}
        with tempfile.TemporaryDirectory()as directory:
            project=Path(directory);a=heavy.stage(heavy.ROOT/'reference/raw/ancient-conquest',project)
            paths=list((project/'Assets/Resources/ShipHeavyMovementGenerated').iterdir());times={p.name:p.stat().st_mtime_ns for p in paths}
            self.assertEqual(a,heavy.stage(heavy.ROOT/'reference/raw/ancient-conquest',project))
            self.assertEqual(times,{p.name:p.stat().st_mtime_ns for p in paths})
        self.assertEqual(before,{p.name:p.read_bytes()for p in old.iterdir()if p.is_file()})


if __name__=='__main__':unittest.main()
