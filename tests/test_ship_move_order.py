import unittest
from tools import validate_ship_move_order as validation

class ShipMoveOrderTests(unittest.TestCase):
    def test_pinned_whole_native_order_cases_keep_requested_and_path_goals_distinct(self):
        fixture=validation.load_fixture()
        cases={case['label']:case for case in fixture['cases']}
        self.assertEqual(len(cases),7)
        self.assertEqual(sum(case['ticks']for case in cases.values()),941)
        self.assertEqual(sum(len(case['samples'])for case in cases.values()),956)
        nearest=cases['nearest18_2']
        self.assertFalse(nearest['finished'])
        self.assertEqual(nearest['samples'][-1]['cell'],[17,2])
        self.assertEqual(nearest['samples'][-1]['active_target'],[18,2])
        self.assertEqual(nearest['samples'][-1]['active']&0x80,0x80)
        blocked=cases['blocked16_1']['samples'][-1]
        self.assertEqual((blocked['request_new'],blocked['path_count'],blocked['cell']),(1,0,[16,2]))
        clear=next(row for row in cases['reach20_4']['samples']if row['operation']=='tick' and row['counter']==103)
        self.assertEqual((clear['active'],clear['state'],clear['world'],clear['cache_cells']),
                         (1024,4,[1270,246],[]))
        second=[row for row in cases['two18_5_then16_4']['samples']if row['operation']=='request'][1]
        self.assertEqual((second['sample_index'],second['counter'],second['epoch']),(103,101,2))
        self.assertFalse(second['publications'])
        self.assertFalse(second['animation_tail_reached'])

    def test_whole_original_request_work_move_idle_chain_matches_checked_csharp(self):
        try:
            result=validation.validate()
        except validation.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertTrue(result['passed'])
        self.assertTrue(result['checked_compilation'])
        self.assertEqual(result['snapshot_count'],956)
        self.assertEqual(result['native_tick_calls'],941)
        self.assertEqual(result['publication_count'],446)
        self.assertEqual(result['grid_mutation_count'],62)
        self.assertEqual(result['guard_count'],35)
        self.assertEqual(result['maximum_publications_per_operation'],2)

if __name__=='__main__':unittest.main()
