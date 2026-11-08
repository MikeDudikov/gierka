from pathlib import Path
import tempfile,unittest
from tools import validate_ship_busy_orders as busy


class ShipBusyOrdersTests(unittest.TestCase):
    def test_repeated_receipt_promotion_motion_and_world_match_fresh_x86(self):
        r=busy.validate();self.assertTrue(r['fresh_native'])
        self.assertEqual((r['actor']['cases'],r['actor']['states'],r['actor']['requests']),(18,9984,210))
        self.assertEqual((r['world']['cases'],r['world']['frames'],r['world']['registration_orders']),(8,1696,4))

    def test_unpinned_fixtures_are_rejected(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'tampered.json';p.write_text('{}')
            for loader in(busy.load,busy.load_world):
                with self.assertRaisesRegex(AssertionError,'fixture SHA differs'):loader(p)

    def test_original_detects_first_wins_physical_reset_and_immediate_delivery(self):
        data=busy.load();source=busy.live.SOURCE.read_text()
        before='ResetEffects();requestedX=x;requestedY=y;pendingFlags|=0x80u;'
        mutations=[(before,'if((pendingFlags&0x80u)!=0)return true;'+before),
            ('deferredFlags=0;activeFlags&=0xffffff0fu;','StopNavigation();deferredFlags=0;activeFlags&=0xffffff0fu;')]
        for before,after in mutations:
            with self.subTest(before=before),tempfile.TemporaryDirectory()as d:
                self.assertEqual(source.count(before),1);p=Path(d)/'ShipMoveOrder.cs';p.write_text(source.replace(before,after))
                with self.assertRaisesRegex(AssertionError,'Live fleet (mismatch|execution failed)'):busy.compare(data,source=p)
        source=busy.world.SOURCE.read_text();before='outgoing.Add(packet);emitted.Add(packet);'
        after=before+'actors[Find(packet.InstanceId)].ReceiveNormalCellMove(packet.InstanceId,packet.Read32(0),packet.Read32(4),packet.MoveArgument);'
        with tempfile.TemporaryDirectory()as d:
            self.assertEqual(source.count(before),1);p=Path(d)/'ShipWorldStep.cs';p.write_text(source.replace(before,after))
            with self.assertRaisesRegex(AssertionError,'World step (mismatch|execution failed)'):busy.world.compare(busy.load_world(),source=p)


if __name__=='__main__':unittest.main()
