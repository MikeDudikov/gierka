from pathlib import Path
import hashlib
import unittest
from tools import smoke_ship_box as box


class ShipBoxProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=box.ROOT/'tests/fixtures/ship_box_input.log'
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!='24d58431afcad0ff26eab4b10025be382ea420312ba4b6081c8919f7b639d1c6':
            raise AssertionError('Box runtime fixture SHA differs')
        cls.good=raw.decode().replace('\r\n','\n')
        if not box.native.pick.gate.ORIGINAL.is_file():
            raise unittest.SkipTest('Private original executable unavailable')

    def model(self, text):
        model=box.Model()
        for line in text.splitlines():model.consume(line)
        return model

    def changed(self, anchor, old, new):
        line=next(line for line in self.good.splitlines()if anchor in line)
        self.assertIn(old,line)
        return self.good.replace(line,line.replace(old,new,1),1)

    def test_completed_runtime_log_matches_original_query_policy_selector_and_queue(self):
        model=self.model(self.good)
        self.assertTrue(model.complete)
        self.assertEqual(model.checkpoints,box.STAGES)
        self.assertEqual((len(model.events),len(model.releases)),(33,5))
        self.assertEqual(model.releases[3]['members'],'0000000b,0000000d,0000000c')
        self.assertEqual(model.releases[3]['outcome'],'unsupported-fleet-set')
        self.assertTrue(all(not row['synthesized_up']for row in model.cancels))

    def test_protocol_corruption_cannot_hide_behind_unchanged_framebuffer(self):
        initial_queue=next(line for line in self.good.splitlines()if line.startswith(box.pointer.PREFIX+'queue: stage=initial;'))
        bad={
            'phase':self.changed('[ShipBoxReference] checkpoint: stage=visible-forward;','phase=1','phase=2'),
            'extent':self.changed('[ShipBoxReference] checkpoint: stage=extent-unpublished;','extent=111,111','extent=110,111'),
            'owner':self.changed('[ShipBoxReference] release: bounds=15,1,3,3;','members=0000000b','members=0000000c'),
            'selected':self.changed('[ShipPointerReference] checkpoint: stage=selected-box;','selected=True','selected=False'),
            'rng':self.changed('[ShipPointerReference] event: index=0;','rng=0','rng=1'),
            'base-queue':self.good.replace(initial_queue+'\n','',1),
            'fabricated-command':self.good.replace('[ShipBoxReference] release: ',box.pointer.PREFIX+'packet: event=0; index=0; action=20; payload=120000000500000000\n[ShipBoxReference] release: ',1),
        }
        for name,text in bad.items():
            with self.subTest(name=name), self.assertRaises(AssertionError):self.model(text)


if __name__=='__main__':unittest.main()
