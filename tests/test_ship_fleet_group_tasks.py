from pathlib import Path
import tempfile
import unittest
from tools import validate_ship_fleet_group_tasks as groups


class ShipFleetGroupTasksTests(unittest.TestCase):
    #Compare actual49ca60/49bd60/49bef0 plus taskWork/41 receipt in the same x86 engine.
    def test_owned_groups_tasks_events_slots_and_receipt_match_fresh_original(self):
        result=groups.validate()
        self.assertTrue(result['fresh_native'])
        self.assertEqual(result['cases'],262)
        self.assertEqual(result['api_controls'],26)
        self.assertGreater(result['watch35'],0)

    def test_changed_fixture_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory()as directory:
            path=Path(directory)/'changed.json';path.write_text('{}')
            with self.assertRaisesRegex(AssertionError,'Group ownership fixture SHA differs'):groups.load(path)

    #Mutation controls target observed x86 semantics,not a duplicate implementation.
    def test_source_comparison_detects_slot_event_owner_index_age_and_return_regressions(self):
        data=groups.load();source=groups.SOURCE.read_text()
        mutations=[
            ('Count--;','Count--; Slots.RemoveAt(Count);'),
            ('old.Task.MemberRemoved(sourceCounter, removedIndex, actor.Id,','old.Task.MemberRemoved(sourceCounter, 0, actor.Id,'),
            ('actor.MemberIndex = group.Count; group.Append(registryIndex);',
             'actor.MemberIndex = group.Count; group.Append(registryIndex); group.Task.MemberAdded(sourceCounter, actor.MemberIndex, actor.Id);'),
            ('old.Task.MemberRemoved(sourceCounter, removedIndex, actor.Id,','groups[0].Task.MemberRemoved(sourceCounter, removedIndex, actor.Id,'),
            ('public void ClearNormalTask(int groupIndex) => GetGroup(groupIndex).Task.Clear();',
             'public void ClearNormalTask(int groupIndex) { GetGroup(groupIndex).Task.Clear(); GetGroup(groupIndex).Age = 0; }'),
            ('group.Age = group.Task.Work','groups[0].Age = group.Task.Work'),
            ('RemoveUnchecked(index, sourceCounter, registry); return 0;',
             'RemoveUnchecked(index, sourceCounter, registry); return 1;')]
        for before,after in mutations:
            with self.subTest(before=before),tempfile.TemporaryDirectory()as directory:
                self.assertEqual(source.count(before),1)
                path=Path(directory)/'ShipFleetMembership.cs';path.write_text(source.replace(before,after))
                with self.assertRaisesRegex(AssertionError,'Group ownership (mismatch|execution failed)'):
                    groups.compare(data,source=path)


if __name__=='__main__':unittest.main()
