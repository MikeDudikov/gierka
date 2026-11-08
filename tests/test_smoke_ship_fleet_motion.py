from pathlib import Path
import hashlib,unittest
from tools import smoke_ship_fleet_motion as qa

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/ship_fleet_motion_render.log'
SHA='5cc271ad646e41061fb0b123123dfbd8c1c07dc1dc27114732f55ffeb47c3880'


class FleetMotionQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest()==SHA
        cls.log=FIXTURE.read_text();cls.reference=qa.load_reference()

    def test_actual_player_log_matches_all_native_actor_parts_and_queue_checkpoints(self):
        stages,complete=qa.parse(self.log,self.reference)
        self.assertTrue(complete);self.assertEqual(len(stages),17)
        self.assertEqual(sum(len(s['actors'])for s in stages.values()),51)
        self.assertEqual(sum(len(s['parts'])for s in stages.values()),170)
        self.assertEqual(sum(len(s['queue'])for s in stages.values()),578)
        self.assertEqual(len(self.reference['publications']),188)

    def test_checker_rejects_missing_armor_wrong_anchor_group_queue_and_publication_order(self):
        lines=self.log.splitlines(keepends=True)
        armor=next(i for i,s in enumerate(lines)if s.startswith(qa.PREFIX+'part: initial; id=13; index=5;'))
        anchor=next(i for i,s in enumerate(lines)if s.startswith(qa.PREFIX+'part: initial; id=13; index=0;'))
        actor=next(i for i,s in enumerate(lines)if s.startswith(qa.PREFIX+'actor: initial\t13\t'))
        queue=next(i for i,s in enumerate(lines)if s.startswith(qa.PREFIX+'queue: stage=initial;'))
        pubs=[i for i,s in enumerate(lines)if s.startswith(qa.PREFIX+'publication: ')]
        variants={}
        changed=list(lines);changed.pop(armor);variants['missing-armor']=''.join(changed)
        changed=list(lines);changed[anchor]=changed[anchor].replace('world=1212,252','world=1216,252');variants['wrong-anchor']=''.join(changed)
        changed=list(lines);changed[actor]=changed[actor].rsplit('\t',1)[0]+'\t0\n';variants['early-group']=''.join(changed)
        changed=list(lines);changed.pop(queue);variants['missing-queue']=''.join(changed)
        changed=list(lines);changed[pubs[0]],changed[pubs[1]]=changed[pubs[1]],changed[pubs[0]];variants['publication-order']=''.join(changed)
        variants['missing-final-fence']=self.log.replace(qa.PREFIX+'end: tick-250\n','')
        for label,log in variants.items():
            with self.subTest(label=label),self.assertRaises(AssertionError):qa.parse(log,self.reference)


if __name__=='__main__':unittest.main()
