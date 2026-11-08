import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools import validate_ship_turn_progression as progression


FIXTURE = Path(__file__).parent / 'fixtures/ship_turn_traces.json'
FIXTURE_SHA = '298be52cb4d4cd867b6060bf84cb6a2eb7ee65d9e91b1edfd98830a387a488dd'
REPORT_SHA = '7f7038851cf1d5b37aa416fffd92b014b0c46b71ddc325fd1eb324acb5a4f80b'
SCRIPT_SHA = '490b1b30bd2931d898779b41ff808c2d8188b540218b0ea91db08232118fa0a5'


class ShipTurnProgressionTests(unittest.TestCase):
    def test_pinned_native_traces_preserve_threshold_publication_and_turn_direction(self):
        raw = FIXTURE.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), FIXTURE_SHA)
        native = json.loads(raw)
        self.assertEqual(native['source_report_sha256'], REPORT_SHA)
        self.assertEqual(native['source_script_sha256'], SCRIPT_SHA)
        self.assertEqual(native['original_sha256'], progression.EXPECTED)
        self.assertEqual((native['entry_point'], native['helper']), ('0x4a3320', '0x4b5390'))
        self.assertEqual(native['hooked_callees'], {
            '0x587318': 'setjmp returns0',
            '0x4df6e0': 'capture source draw request, no renderer'})
        self.assertEqual((native['source_trace_count'], native['source_step_count']), (128, 2480))
        self.assertEqual(sum(len(trace['trace']) for trace in native['turn_traces']), 2480)
        by_input = {(trace['initial_heading'], trace['target_heading'], trace['path_present']): trace
                    for trace in native['turn_traces']}
        self.assertEqual(set(by_input), {(heading, target, has_path)
            for heading in range(8) for target in range(8) for has_path in (False, True)})
        for (heading, target, has_path), trace in by_input.items():
            self.assertEqual(trace['initial_input'], {
                'frame': heading * 4, 'heading': heading, 'target_heading': target,
                'turn_step': 0, 'now': 0, 'last_tick': 0, 'interval': 2,
                'has_path': has_path, 'state': 2, 'changed_marker': 0})
            # Frame initialization mutates stored pose before strict elapsed>2
            # permits a DrawSprite publication. These are separate observations.
            for step in trace['trace'][:3]:
                self.assertEqual(step['draw_calls'], [])
                self.assertEqual((step['frame'], step['last_stamp'], step['move_state']),
                                 (32 + 3 * heading, 0, 2))
            self.assertEqual(trace['trace'][3]['tick'], 3)
            self.assertEqual(len(trace['trace'][3]['draw_calls']), 1)
            final = trace['trace'][-1]
            self.assertEqual((final['heading'], final['frame'], final['move_state'], final['changed_marker']),
                             (target, target * 4, 3 if has_path else 0, 1))
            self.assertEqual(final['draw_calls'], [{key: final[key] for key in
                ('heading', 'frame', 'frame_step', 'last_stamp', 'move_state', 'changed_marker')}])
        # At exactly half a revolution the source keeps the raw sign, and the
        # 32..55 ring wraps without inventing an additional pose56.
        self.assertEqual(by_input[0, 4, False]['trace'][0]['frame_step'], 1)
        self.assertEqual(by_input[4, 0, False]['trace'][0]['frame_step'], -1)
        self.assertEqual((by_input[0, 7, False]['trace'][3]['frame'],
                          by_input[0, 7, False]['trace'][3]['heading']), (55, 7))
        self.assertEqual(by_input[7, 1, False]['trace'][9]['frame'], 32)
        self.assertEqual(len(by_input[0, 0, False]['trace']), 4)
        self.assertEqual(len(by_input[0, 0, True]['trace']), 4)

    def test_actual_csharp_matches_native_turn_traces_and_arithmetic_stress(self):
        try:
            report = progression.validate()
        except progression.MissingPrerequisite as error:
            self.skipTest(str(error))
        self.assertEqual(report['source_trace_count'], 128)
        self.assertEqual(report['source_step_count'], 2480)
        self.assertEqual(report['stress_case_count'], 1296)
        self.assertEqual((report['case_count'], report['passed'], report['normal_zero_return_count']),
                         (3776, 3776, 3776))
        self.assertEqual((report['whole_move_caller_cases'], report['whole_move_normal_return']), (256, 1))
        self.assertEqual(report['whole_move_source_calls_per_case'],
                         {'0x4a3320': 1, '0x4a3560': 0, '0x4a4d49': 0})
        self.assertTrue(report['checked_compilation'])
        self.assertEqual(report['fixture_sha256'], FIXTURE_SHA)
        fields = ('frame', 'heading', 'target_heading', 'turn_step', 'now', 'last_tick', 'interval')
        by_input = {(case['scope'], *(case['input'][key] for key in fields)): case['x86']
                    for case in report['cases'] if case['scope'] != 'source_turn_trace'}
        # A former idle pose is corrected before the ordinary turn step, and
        # large elapsed values advance one pose rather than catching up.
        result = by_input['initial_and_idle_pose', 56, 0, 4, 0, 100, 0, 2]
        self.assertEqual((result['frame'], result['turn_step'], result['last_tick'], result['publishes_pose']),
                         (33, 1, 100, True))
        # Wrapped uint elapsed 1 - 0xfffffffe is3, exceeding interval2.
        result = by_input['initial_and_idle_pose', 0, 0, 4, 0, 1, 0xfffffffe, 2]
        self.assertEqual((result['frame'], result['last_tick'], result['publishes_pose']), (33, 1, True))
        # INT_MIN + signed step -128 wraps before the source ring clamps it.
        # The source then completes target0; checked C# must preserve that.
        result = by_input['raw_arithmetic_stress', -0x80000000, -1, 0, -128, 3, 0, 2]
        self.assertEqual(result, {'frame': 0, 'heading': 0, 'turn_step': -128, 'last_tick': 3,
                                 'state': 3, 'changed_marker': 1, 'publishes_pose': True})

    def test_changed_original_is_rejected_before_original_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            original = Path(temporary) / 'ancient.exe'
            original.write_bytes(b'changed original')
            with self.assertRaisesRegex(ValueError, 'SHA-256 differs'):
                progression.validate(original)


if __name__ == '__main__':
    unittest.main()
