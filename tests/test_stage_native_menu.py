import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from tools.stage_native_menu import (WIDTH, HEIGHT, digest, native_button_rect,
                                    read_hd_background, write_staged_payloads,
                                    BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_COUNT, BUTTON_STATES)


class NativeMenuTests(unittest.TestCase):
    def test_native_canvas_and_independent_control_anchors(self):
        self.assertEqual((WIDTH, HEIGHT), (1920, 1080))
        self.assertEqual(native_button_rect(1), (220, 418, 313, 72))
        self.assertEqual(native_button_rect(6), (700, 886, 313, 72))
        for number in range(1, 7):
            x, y, width, height = native_button_rect(number)
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(x + width, WIDTH)
            self.assertLessEqual(y + height, HEIGHT)
            self.assertAlmostEqual(width / height, 174 / 40, delta=0.01)
        with self.assertRaises(ValueError): native_button_rect(0)

    def test_hd_source_dimensions_and_pixels_are_not_resized(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "hd.png"
            source = Image.new("RGBA", (2560, 1440), (10, 20, 30, 255))
            source.putpixel((0, 1439), (1, 2, 3, 255))
            source.save(path)
            original = path.read_bytes()
            image, metadata = read_hd_background(path, digest(original))
            self.assertEqual(image.size, (2560, 1440))
            self.assertEqual(image.tobytes(), source.tobytes())
            self.assertEqual(metadata["rgba_sha256"], digest(source.tobytes()))
            self.assertEqual(path.read_bytes(), original)
            with self.assertRaisesRegex(ValueError, "hash"):
                read_hd_background(path, "0" * 64)

    def test_low_resolution_wrong_aspect_and_transparency_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "source.png"
            for size, alpha in (((800, 600), 255), ((1024, 819), 255),
                                ((1920, 1200), 255), ((1280, 1024), 0), ((1672, 941), 255)):
                with self.subTest(size=size, alpha=alpha):
                    Image.new("RGBA", size, (1, 2, 3, alpha)).save(path)
                    with self.assertRaises(ValueError):
                        read_hd_background(path, digest(path.read_bytes()))

    def test_separate_background_ui_planes_and_idempotent_staging(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "generated"
            background = Image.new("RGBA", (2560, 1440), (10, 20, 30, 255))
            background.putpixel((0, 1439), (1, 2, 3, 255))
            ui = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
            ui.putpixel((168, 406), (7, 8, 9, 255))
            metadata = {"width": 2560, "height": 1440,
                        "native_canvas_width": WIDTH, "native_canvas_height": HEIGHT}
            report = write_staged_payloads(output, background, ui, metadata)
            raw = (output / "MenuRgba.bytes").read_bytes()
            overlay = (output / "MenuUiRgba.bytes").read_bytes()
            self.assertEqual(len(raw), 2560 * 1440 * 4)
            self.assertEqual(raw[:4], bytes((1, 2, 3, 255)))
            self.assertEqual(len(overlay), WIDTH * HEIGHT * 4)
            pixel_offset = ((HEIGHT - 1 - 406) * WIDTH + 168) * 4
            self.assertEqual(overlay[pixel_offset:pixel_offset + 4], bytes((7, 8, 9, 255)))
            self.assertEqual(overlay[:4], bytes((0, 0, 0, 0)))
            self.assertEqual(report["payload_sha256"], digest(raw))
            before = (output / "MenuRgba.bytes").stat().st_mtime_ns
            self.assertEqual(write_staged_payloads(output, background, ui, metadata), report)
            self.assertEqual((output / "MenuRgba.bytes").stat().st_mtime_ns, before)

    def test_replacement_is_explicit_and_previous_hash_must_match(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            previous = b"old diagnostic data"
            (output / "MenuRgba.bytes").write_bytes(previous)
            (output / "MenuRgbaManifest.json").write_text(json.dumps({"payload_sha256": digest(previous)}))
            background = Image.new("RGBA", (WIDTH, HEIGHT), (1, 2, 3, 255))
            ui = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
            with self.assertRaises(FileExistsError):
                write_staged_payloads(output, background, ui, {})
            (output / "MenuRgba.bytes").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "Previous generated data hash"):
                write_staged_payloads(output, background, ui, {}, True)
            self.assertEqual((output / "MenuRgba.bytes").read_bytes(), b"tampered")

    def test_wrong_size_ui_is_refused_before_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "new"
            with self.assertRaisesRegex(ValueError, "complete native canvas"):
                write_staged_payloads(output, Image.new("RGBA", (WIDTH, HEIGHT)),
                                      Image.new("RGBA", (800, 600)), {})
            self.assertFalse(output.exists())

    def test_smaller_widescreen_art_requires_explicit_draft_and_reports_actual_detail(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "draft.png"
            Image.new("RGBA", (1672, 941), (1, 2, 3, 255)).save(path)
            with self.assertRaisesRegex(ValueError, "1920x1080"):
                read_hd_background(path, digest(path.read_bytes()))
            image, metadata = read_hd_background(path, digest(path.read_bytes()), allow_draft_upscale=True)
            self.assertEqual(image.size, (1672, 941))
            self.assertTrue(metadata["upscale_draft"])
            self.assertEqual((metadata["width"], metadata["height"]), image.size)

    def test_button_atlas_preserves_each_state_and_column_without_resizing(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "generated"
            background = Image.new("RGBA", (WIDTH, HEIGHT), (1, 2, 3, 255))
            ui = Image.new("RGBA", (WIDTH, HEIGHT))
            atlas = Image.new("RGBA", (BUTTON_COUNT * BUTTON_WIDTH, BUTTON_STATES * BUTTON_HEIGHT))
            for state in range(BUTTON_STATES):
                for button in range(BUTTON_COUNT):
                    atlas.putpixel((button * BUTTON_WIDTH + 3, state * BUTTON_HEIGHT + 5),
                                   (button, state, 7, 255))
            report = write_staged_payloads(output, background, ui, {}, button_atlas=atlas)
            raw = (output / "MenuButtonsRgba.bytes").read_bytes()
            for state in range(BUTTON_STATES):
                for button in range(BUTTON_COUNT):
                    offset = ((atlas.height - 1 - state * BUTTON_HEIGHT - 5) * atlas.width +
                              button * BUTTON_WIDTH + 3) * 4
                    self.assertEqual(raw[offset:offset + 4], bytes((button, state, 7, 255)))
            self.assertEqual(report["buttons_payload_sha256"], digest(raw))
            tampered = output / "MenuButtonsRgba.bytes"
            tampered.write_bytes(b"modified")
            with self.assertRaisesRegex(ValueError, "Previous generated data hash"):
                write_staged_payloads(output, background, ui, {}, True, button_atlas=atlas)
            self.assertEqual(tampered.read_bytes(), b"modified")

    def test_button_atlas_wrong_dimensions_are_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "generated"
            with self.assertRaisesRegex(ValueError, "four drawing states"):
                write_staged_payloads(output, Image.new("RGBA", (WIDTH, HEIGHT)),
                                      Image.new("RGBA", (WIDTH, HEIGHT)), {},
                                      button_atlas=Image.new("RGBA", (278, 64)))
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
