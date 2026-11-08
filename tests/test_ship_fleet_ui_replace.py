from pathlib import Path
import tempfile,unittest
from tools import validate_ship_fleet_ui_replace as proof


class FleetUiReplaceTests(unittest.TestCase):
    def test_reused_task_requests_and_world_fifo_match_fresh_x86(self):
        result=proof.validate();self.assertTrue(result['fresh_x86'])
        self.assertEqual((result['cases'],result['frames'],result['requests'],result['actor_states']),(12,2400,16,7248))
        self.assertEqual((result['registration_orders'],result['api_controls']),(4,28))
    def test_fixture_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory()as directory:
            path=Path(directory)/'changed.json';path.write_text('{}')
            with self.assertRaisesRegex(AssertionError,'UI replace fixture SHA differs'):proof.load(path)
    def test_boundary_checker_detects_wrong_request_tick_lost_fifo_and_immediate_receipt(self):
        source=proof.PROBE.read_text();data=proof.load()
        request='Membership.RequestNormalMove(0,registry,Terrain,24,24,x,y,Counter);'
        enqueue='for(int i=0;i<Membership.GetNormalTaskCommandCount(0);i++)Outgoing.Add(ShipWorldStep.Command.Task(Counter,Membership.GetNormalTaskCommand(0,i)));'
        immediate='for(int i=0;i<3;i++){var p=Membership.GetNormalTaskCommand(0,i);Motion[i].ReceiveNormalCellMove((uint)Ids[i],p.X,p.Y,p.ByteArgument);}'
        for before,after in((request,request.replace('Counter);','unchecked(Counter+1));')),
                             (request,'Outgoing.Clear();'+request),(request,request+immediate)):
            with self.subTest(before=before),tempfile.TemporaryDirectory()as directory:
                self.assertEqual(source.count(before),1);path=Path(directory)/'Probe.cs';path.write_text(source.replace(before,after))
                with self.assertRaisesRegex(AssertionError,'UI replace (mismatch|execution failed|API execution failed)'):
                    proof.compare(data,probe=path)


if __name__=='__main__':unittest.main()
