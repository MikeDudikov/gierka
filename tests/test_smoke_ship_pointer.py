"""Integration-checker controls; the fixture is recorded Unity output, not a native oracle."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from tools import smoke_ship_pointer as pointer


class PointerInputLogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = pointer.ROOT / 'tests/fixtures/ship_pointer_input.log'
        manifest = json.loads(fixture.with_name('ship_pointer_input_manifest.json').read_text())
        raw = fixture.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == manifest['fixture_sha256']
        assert manifest['field_adaptations'] == []
        cls.good = raw.decode()
        cls.reference = pointer.load_reference()
        cls.parsed, cls.model = pointer.parse_log(cls.good, cls.reference, two=True, complete=True)

    def line(self, prefix):
        return next(line for line in self.good.splitlines() if line.startswith(pointer.PREFIX + prefix))

    def changed(self, prefix, old, new):
        line = self.line(prefix)
        assert old in line and old != new
        return self.good.replace(line, line.replace(old, new), 1)

    def reject(self, log, message=None):
        with self.assertRaises((AssertionError, ValueError)) as caught:
            pointer.parse_log(log, self.reference, two=True, complete=True)
        if message:
            self.assertIn(message, str(caught.exception))

    def test_actual_metadata_checks_all_counters_and_ordered_source_packets(self):
        self.assertEqual(len(self.parsed['checkpoints']), 35)
        self.assertEqual(len(self.parsed['events']), 21)
        self.assertEqual(len(self.parsed['motions']), 232)
        self.assertEqual({row['counter'] for row in self.parsed['motions']}, set(range(198)))
        self.assertEqual([(row['event'], row['index'], row['action'], row['payload']) for row in self.parsed['packets']],
                         [(16, 0, 41, '010000000000'), (16, 1, 20, '120000000500000000'),
                          (20, 0, 20, '100000000400000000')])
        self.assertFalse(self.model.samples['motion-1-101']['pending'])
        self.assertTrue(self.model.rows['subpixel-same-logical']['pointer_header']['confirm'])
        self.assertFalse(self.model.rows['subpixel-same-logical']['pointer_header']['confirm_visible'])

    def test_missing_noncheckpoint_tick_cannot_hide_behind_valid_checkpoints(self):
        removed = self.line('motion: counter=2;')
        self.reject(self.good.replace(removed + '\n', ''), 'Missing mouse-driven simulation counter')

    def test_all_counter_values_cannot_hide_backwards_chronology(self):
        lines = self.good.splitlines()
        indices = [next(i for i, row in enumerate(lines) if row.startswith(pointer.PREFIX + f'motion: counter={n};'))
                   for n in (2, 3)]
        lines[indices[0]], lines[indices[1]] = lines[indices[1]], lines[indices[0]]
        self.reject('\n'.join(lines) + '\n', 'Simulation counter moved backwards')

    def test_left_release_same_packet_move_and_right_release_rules_are_checked(self):
        mutations = {
            'left-down-does-not-select': self.changed('event: index=2;', 'message=97', 'message=98'),
            'right-up-is-not-move': self.changed('event: index=6;', 'message=100', 'message=98'),
            'same-frame-up-required': self.good.replace(self.line('event: index=9;') + '\n', ''),
            'move-before-up-required': self.changed('event: index=15;', 'message=96', 'message=98'),
            'release-must-use-new-cell': self.changed('event: index=16;', 'cell=18,5', 'cell=18,4'),
            'no-fabricated-right-packet': self.good.replace(self.line('event: index=6;'),
                pointer.PREFIX + 'packet: event=6; index=0; action=20; payload=120000000500000000\n' + self.line('event: index=6;')),
        }
        for name, bad in mutations.items():
            with self.subTest(name=name):
                self.reject(bad)

    def test_native_packet_membership_byte_zero_and_motion_values_are_checked(self):
        mutations = {
            'membership-group': self.changed('packet: event=16; index=0;', 'payload=010000000000', 'payload=010100000000'),
            'move-priority-byte': self.changed('packet: event=16; index=1;', 'payload=120000000500000000', 'payload=120000000500000001'),
            'lost-membership': self.good.replace(self.line('packet: event=16; index=0;') + '\n', ''),
            'packet-order': self.changed('packet: event=16; index=0;', 'index=0', 'index=1'),
            'simulation-membership': self.changed('event: index=16;', 'simulation_group=0', 'simulation_group=-1'),
            'rng': self.changed('motion: counter=2;', 'rng=0', 'rng=1'),
            'stored-frame': self.changed('motion: counter=2;', 'frame=47', 'frame=20'),
            'published-world': self.changed('motion: counter=2;', 'published=1028,132', 'published=1029,132'),
        }
        for name, bad in mutations.items():
            with self.subTest(name=name):
                self.reject(bad)

    def test_native_selector_health_cursor_hotspot_and_subpixel_noop_are_checked(self):
        mutations = {
            'selector-drawn': self.changed('visual: stage=motion-1-47; kind=selector;', 'RAM_056X05609', 'RAM_056X05608'),
            'selector-health-order': self.changed('visual: stage=motion-1-47; kind=health;', 'order=44', 'order=45'),
            'health-position': self.changed('visual: stage=motion-1-47; kind=health;', 'position=1074,164', 'position=1075,164'),
            'cursor-hotspot': self.changed('visual: stage=motion-1-47; kind=cursor;', 'position=590,335', 'position=608,352'),
            'cursor-render-pipeline': self.changed('visual: stage=motion-1-47; kind=cursor;', 'order=32767', 'order=32766'),
            'cursor-family': self.changed('visual: stage=motion-1-47; kind=cursor;', 'CUR_SEA_N00', 'CUR_OWN_N00'),
            'held-selector-counter': self.changed('checkpoint: stage=subpixel-same-logical;', 'selector_last_counter=0', 'selector_last_counter=1'),
            'subpixel-cursor-draw': self.changed('checkpoint: stage=subpixel-same-logical;', 'cursor_last_tick=0', 'cursor_last_tick=750'),
            'subpixel-confirm-draw': self.changed('checkpoint: stage=subpixel-same-logical;', 'confirm_stored=0', 'confirm_stored=3'),
            'missing-clock-advance': self.changed('event: index=17;', 'visual_ms=750', 'visual_ms=0'),
            'confirm-click-offset-while-hidden': self.changed('visual: stage=request-1; kind=confirm;', 'position=1173,328', 'position=1174,328'),
            'cursor-native-interval': self.changed('checkpoint: stage=subpixel-same-logical;', 'cursor_interval=150', 'cursor_interval=10000'),
        }
        for name, bad in mutations.items():
            with self.subTest(name=name):
                self.reject(bad)

    def test_cancellation_never_synthesizes_up_and_final_checkpoint_requires_full_block(self):
        self.reject(self.good.replace('synthesized_up=False', 'synthesized_up=True', 1), 'Cancellation manufactured source Up')
        last_queue = [line for line in self.good.splitlines() if line.startswith(pointer.PREFIX + 'queue: stage=motion-2-197;')][-1]
        self.reject(self.good.replace(last_queue + '\n', ''), 'Final pointer checkpoint block incomplete')

    def test_cancellation_requires_source_context_schema_and_held_phase(self):
        cancel = self.line('cancel: counter=0;')
        mutations = {
            'missing-device-cancel': self.good.replace(cancel + '\n', ''),
            'wrong-counter': self.good.replace(cancel, cancel.replace('counter=0', 'counter=1'), 1),
            'wrong-selection': self.good.replace(cancel, cancel.replace('selected=True', 'selected=False'), 1),
            'unknown-field': self.good.replace(cancel, cancel + '; extra=1', 1),
            'wrong-phase': self.good.replace(cancel + '\n', '').replace(self.line('event: index=11;'),
                self.line('event: index=11;') + '\n' + cancel, 1),
        }
        for name, bad in mutations.items():
            with self.subTest(name=name):
                self.reject(bad)
        # Focus and device hooks may deliver identical cancellation callbacks.
        # They must stay in the held phase and may never manufacture Up.
        duplicate = self.good.replace(cancel, cancel + '\n' + cancel, 1)
        parsed, _ = pointer.parse_log(duplicate, self.reference, two=True, complete=True)
        self.assertEqual(len(parsed['cancels']), len(self.parsed['cancels']) + 1)

    def test_live_reader_trims_only_unterminated_tail_and_checks_complete_malformed_row(self):
        parsed, _ = pointer.parse_log(self.good + pointer.PREFIX + 'motion: coun', self.reference, two=True)
        self.assertEqual(parsed, self.parsed)
        self.reject(self.good + pointer.PREFIX + 'motion: coun', 'unterminated tail')
        self.reject(self.good + pointer.PREFIX + 'motion: coun\n', 'Malformed pointer token')
        self.reject(self.good.replace(pointer.READY + '\n', ''), 'scope/readiness')
        self.reject(pointer.READY + '\n' + self.good, 'scope/readiness')


class PointerCaptureFenceTests(unittest.TestCase):
    def exercise(self, changed=False, incomplete=False):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory); image = Image.new('RGB', (8, 8)); png = output / 'frame.png'; image.save(png)
            before = {'checkpoints': [{'stage': 'held'}], 'visuals': {'held': [{'sprite': 'CUR_SEA_N00'}]}}
            after = copy.deepcopy(before)
            if changed:
                after['visuals']['held'][0]['sprite'] = 'CUR_SEA_N01'
            model = type('Model', (), {'rows': {} if incomplete else {'held': {'expected_image': image, 'regions': []}}})()
            player = type('Player', (), {'poll': lambda self: None})()
            with patch.object(pointer, 'parse_log', side_effect=[(before, model), (after, model)]), \
                    patch.object(pointer.terrain, 'read_log', return_value='log'), \
                    patch.object(pointer.menu, 'capture', return_value=png), \
                    patch.object(pointer.order, 'frame_metrics', return_value=(True, {'matched': True})):
                return pointer.capture_checkpoint(player, {}, output, output / 'player.log', {}, False, 'held')

    def test_complete_static_capture_passes(self):
        self.assertEqual(self.exercise()['presentation_attempt_count'], 1)

    def test_ui_only_mutation_fails_even_when_pixels_and_motion_pass(self):
        with self.assertRaisesRegex(AssertionError, 'state changed during capture'):
            self.exercise(changed=True)

    def test_incomplete_checkpoint_cannot_be_captured(self):
        with self.assertRaisesRegex(AssertionError, 'Incomplete/wrong pointer fence'):
            self.exercise(incomplete=True)


class NativeForegroundProtocolTests(unittest.TestCase):
    def result(self):
        phase = {'foreground': 100, 'pid': 10, 'matched': True, 'set_foreground_result': 1,
                 'bring_to_top_result': 1, 'title': 'AncientConquest'}
        return {'player_hwnd': 100, 'sink_hwnd': 200, 'before': copy.deepcopy(phase),
                'sink': dict(phase, foreground=200, pid=20, title='Untitled - Notepad'),
                'restored': copy.deepcopy(phase), 'passed': True}

    def test_win32_foreground_requires_distinct_processes_and_actual_hwnds(self):
        result = self.result()
        # API return values are observations. Actual GetForegroundWindow matches
        # establish the transition, even if SetForegroundWindow returned zero.
        result['before']['set_foreground_result'] = 0
        self.assertEqual(pointer.validate_focus_foreground(json.dumps(result) + '\n'), result)

    def test_win32_foreground_protocol_corruptions_are_rejected(self):
        mutations = []
        for phase, key, value in [('sink', 'foreground', 100), ('restored', 'foreground', 200),
                                  ('sink', 'pid', 10), ('before', 'pid', 0), ('before', 'pid', True),
                                  ('sink', 'matched', False), ('restored', 'title', 'Notepad'),
                                  ('before', 'set_foreground_result', True)]:
            row = self.result(); row[phase][key] = value; mutations.append(json.dumps(row) + '\n')
        row = self.result(); row['passed'] = False; mutations.append(json.dumps(row) + '\n')
        row = self.result(); del row['sink']; mutations.append(json.dumps(row) + '\n')
        good = json.dumps(self.result()) + '\n'
        mutations.extend((good.rstrip('\n'), good + good))
        for index, bad in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises((AssertionError, ValueError)):
                pointer.validate_focus_foreground(bad)
