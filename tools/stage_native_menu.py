#!/usr/bin/env python3
"""Stage an unchanged HD background and an independently authored native UI.

The background stays at its original resolution. No old whole-frame image is
resized or projected. Original button/font layers are temporary reconstruction
inputs; their final 2026-quality reconstruction remains a separate art task.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct

from PIL import Image
import pefile

try:
    from .render_reference_menu import (EXE_SHA256, RESOURCE_IDS, indexed_dib,
        pe_strings, composite_indices, draw_text, measure_text)
    from .inspect_dkx import inspect_pair, decode_font, allocation_blocks
    from .decode_sprite import decode_sprite, resource_payload
    from .stage_unity_reference import bottom_up_rgba
except ImportError:
    from render_reference_menu import (EXE_SHA256, RESOURCE_IDS, indexed_dib,
        pe_strings, composite_indices, draw_text, measure_text)
    from inspect_dkx import inspect_pair, decode_font, allocation_blocks
    from decode_sprite import decode_sprite, resource_payload
    from stage_unity_reference import bottom_up_rgba

WIDTH, HEIGHT = 1920, 1080
BUTTON_WIDTH, BUTTON_HEIGHT = 313, 72
BUTTON_COUNT, BUTTON_STATES = 6, 4
REPOSITORY = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def native_button_rect(number):
    """Preserve button proportions, but adapt each center to native 16:9 anchors."""
    if not 1 <= number <= 6:
        raise ValueError("Main menu button number must be 1..6")
    uniform_scale = min(WIDTH / 800, HEIGHT / 600)
    width, height = round(174 * uniform_scale), round(40 * uniform_scale)
    center_x = (30 + 40 * number + 174 / 2) * WIDTH / 800
    center_y = (180 + 52 * number + 40 / 2) * HEIGHT / 600
    return round(center_x - width / 2), round(center_y - height / 2), width, height


def read_hd_background(path, expected_sha256, *, allow_draft_upscale=False):
    path = Path(path)
    raw = path.read_bytes()
    if digest(raw) != expected_sha256:
        raise ValueError("HD background hash differs from the selected draft")
    with Image.open(path) as source:
        if source.format != "PNG":
            raise ValueError("HD background must be a PNG")
        image = source.convert("RGBA")
    width, height = image.size
    minimum = (1280, 720) if allow_draft_upscale else (WIDTH, HEIGHT)
    if width < minimum[0] or height < minimum[1] or width > 8192 or height > 8192:
        raise ValueError("Background must contain at least native 1920x1080 detail; smaller art requires explicit draft staging")
    if abs(width / height - WIDTH / HEIGHT) > 0.01:
        raise ValueError("Background must be authored at 16:9; old 4:3 or 5:4 frames are refused")
    if image.getextrema()[3] != (255, 255):
        raise ValueError("The full background must be opaque")
    return image, {"path": str(path), "png_sha256": expected_sha256,
                   "width": width, "height": height,
                   "upscale_draft": width < WIDTH or height < HEIGHT,
                   "rgba_sha256": digest(image.tobytes()),
                   "staging_transform": "RGBA channel conversion and bottom-up rows only; no image resize/crop"}


def compose_native_ui(source_root, *, include_buttons=False):
    root = Path(source_root)
    paths = (root / "installed/ancient.exe", root / "installed/missions/controlm.dkx",
             root / "installed/missions/controlm.dkd")
    executable, index, data = [path.read_bytes() for path in paths]
    if digest(executable) != EXE_SHA256:
        raise ValueError("Menu source contract is not verified for this executable")
    strings = pe_strings(pefile.PE(data=executable), RESOURCE_IDS)
    lookup = {(entry["type"], entry["name"]): entry for entry in inspect_pair(index, data)}
    used = []

    def resource(kind, name):
        entry = lookup[kind, name]
        used.append({key: entry[key] for key in ("name", "type", "offset", "sha256")})
        return entry, resource_payload(entry, data)

    _, palette_source = resource(1, "0M_BKGND_00")
    _, _, palette = indexed_dib(palette_source)  # Palette only, never background pixels.
    font_entry, font_payload = resource(3, "0S_FNT_BS")
    font, _ = decode_font(font_entry, data, allocation_blocks(data))
    atlas_sources = font["atlas_sources"]
    if len(atlas_sources) != 4:
        raise ValueError("Verified menu font must have four variants")
    atlases = [indexed_dib(data[source["offset"]:source["offset"] + source["size"]])
               for source in atlas_sources]
    key = struct.unpack_from("<H", font_payload, 66)[0]
    if key != 6:
        raise ValueError("Verified font key changed")
    if any(atlas[2][index] != palette[index]
           for atlas in atlases for index in set(atlas[1]) - {key}):
        raise ValueError("Original font and UI palette disagree")
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    button_atlas = Image.new("RGBA", (BUTTON_COUNT * BUTTON_WIDTH,
                                     BUTTON_STATES * BUTTON_HEIGHT), (0, 0, 0, 0))
    controls = []
    for number, resource_id in enumerate(RESOURCE_IDS, 1):
        sprites = []
        for variant in range(2):
            _, payload = resource(6, f"0M_BUT{(number + 1) % 2}_{variant:02}")
            sprite = decode_sprite(payload)
            if (sprite["width"], sprite["height"]) != (174, 40):
                raise ValueError("Verified source button dimensions changed")
            sprites.append(sprite)
        label = strings[resource_id]
        text_width, text_height = measure_text(label, font)
        x, y, width, height = native_button_rect(number)
        for state in range(BUTTON_STATES):
            sprite = sprites[1 if state in (2, 3) else 0]
            button = Image.new("RGBA", (174, 40), (0, 0, 0, 0))
            composite_indices(button, (174, 40), sprite["indices"], palette, (0, 0),
                              coverage=sprite["coverage"])
            position = (int((174 - text_width) / 2), int((40 - text_height) / 2))
            # PaintMBut 0x4ea470: states0/1/2 use font1/2/3; hover3
            # draws font0 centrally and font3 in a rectangle smaller by4.
            if state == 3:
                draw_text(button, label, font, atlases[0], position, key)
                position = (int((170 - text_width) / 2), int((36 - text_height) / 2))
            draw_text(button, label, font, atlases[min(state + 1, 3)], position, key)
            button = button.resize((width, height), Image.Resampling.LANCZOS)
            button_atlas.alpha_composite(button, ((number - 1) * width, state * height))
            if state == 1:
                layer.alpha_composite(button, (x, y))
        controls.append({"resource_id": resource_id, "label": label,
                         "native_rect": [x, y, width, height]})
    ui_info = {"canvas": [WIDTH, HEIGHT], "controls": controls,
                   "geometry": "uniform shape scale 1.8; centers independently anchored to native 16:9 canvas",
                   "quality_status": "prototype original bitmap buttons/font; high-quality per-layer reconstruction pending",
                   "sources": [{"path": str(path), "sha256": digest(raw)}
                               for path, raw in zip(paths, (executable, index, data))],
                   "resources": used, "font_atlas_sources": atlas_sources,
                   "drawing_states": {"0": "disabled", "1": "normal", "2": "pressed", "3": "hover"}}
    if include_buttons:
        return layer, ui_info, button_atlas
    return layer, ui_info


def write_staged_payloads(output, background, ui, metadata, replace_generated=False,
                          *, button_atlas=None, allow_draft_upscale=False):
    output = Path(output)
    minimum = (1280, 720) if allow_draft_upscale else (WIDTH, HEIGHT)
    if (background.width < minimum[0] or background.height < minimum[1] or
            abs(background.width / background.height - WIDTH / HEIGHT) > 0.01):
        raise ValueError("Native background dimensions/aspect are required")
    if ui.size != (WIDTH, HEIGHT):
        raise ValueError("UI must be authored on the complete native canvas")
    if button_atlas is not None and button_atlas.size != (BUTTON_COUNT * BUTTON_WIDTH,
                                                         BUTTON_STATES * BUTTON_HEIGHT):
        raise ValueError("Button atlas must contain six columns and four drawing states")
    if output.resolve() != output.absolute():
        raise ValueError("Generated output path must not contain symlinks")
    background_bytes, ui_bytes = bottom_up_rgba(background), bottom_up_rgba(ui)
    metadata = dict(metadata, payload_sha256=digest(background_bytes),
                    ui_payload_sha256=digest(ui_bytes))
    files = {"MenuRgba.bytes": background_bytes, "MenuUiRgba.bytes": ui_bytes}
    if button_atlas is not None:
        buttons = bottom_up_rgba(button_atlas)
        files["MenuButtonsRgba.bytes"] = buttons
        metadata["buttons_payload_sha256"] = digest(buttons)
    files["MenuRgbaManifest.json"] = (json.dumps(metadata, indent=2) + "\n").encode()
    if any((output / name).is_symlink() for name in files):
        raise ValueError("Generated files must not be symlinks")
    differing = [name for name, raw in files.items()
                 if (output / name).exists() and (output / name).read_bytes() != raw]
    if differing and not replace_generated:
        raise FileExistsError("Different generated data exists; explicitly select --replace-generated")
    if differing:
        old = json.loads((output / "MenuRgbaManifest.json").read_text())
        for name, key in (("MenuRgba.bytes", "payload_sha256"), ("MenuUiRgba.bytes", "ui_payload_sha256"),
                          ("MenuButtonsRgba.bytes", "buttons_payload_sha256")):
            previous = output / name
            if previous.exists() and digest(previous.read_bytes()) != old.get(key):
                raise ValueError("Previous generated data hash mismatch; refusing replacement")
    output.mkdir(parents=True, exist_ok=True)
    for name, raw in files.items():
        target = output / name
        if target.exists() and target.read_bytes() == raw:
            continue
        temporary = output / (name + ".staging")
        with temporary.open("xb") as stream:
            stream.write(raw)
        os.replace(temporary, target)
    return metadata


def stage_native_menu(source_root, background_path, background_sha256, project,
                      replace_generated=False, *, allow_draft_upscale=False):
    background, art = read_hd_background(background_path, background_sha256,
                                        allow_draft_upscale=allow_draft_upscale)
    ui, ui_info, buttons = compose_native_ui(source_root, include_buttons=True)
    metadata = {"schema_version": 3, "kind": "native HD interactive menu draft",
                "width": background.width, "height": background.height,
                "background_upscale_draft": art["upscale_draft"],
                "native_canvas_width": WIDTH, "native_canvas_height": HEIGHT,
                "ui_width": WIDTH, "ui_height": HEIGHT, "format": "RGBA32",
                "button_atlas_width": buttons.width, "button_atlas_height": buttons.height,
                "button_count": BUTTON_COUNT, "button_states": BUTTON_STATES,
                "row_order": "bottom-to-top", "letterbox": False,
                "background": art, "ui": ui_info,
                "limitations": ["HD background is a cosmetic draft requiring acceptance.",
                                "Original bitmap UI is a temporary per-layer prototype.",
                                "Only pointer states and Quit are connected; other menu destinations and gameplay remain unimplemented."]}
    return write_staged_payloads(Path(project) / "Assets/Resources/ReferenceGenerated",
                                 background, ui, metadata, replace_generated, button_atlas=buttons,
                                 allow_draft_upscale=allow_draft_upscale)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--background", required=True, type=Path)
    parser.add_argument("--background-sha256", required=True)
    parser.add_argument("--source-root", type=Path,
                        default=REPOSITORY / "reference/raw/ancient-conquest")
    parser.add_argument("--project", type=Path, default=REPOSITORY / "Unity/AncientConquest")
    parser.add_argument("--replace-generated", action="store_true")
    parser.add_argument("--allow-draft-upscale", action="store_true",
                        help="Explicitly stage smaller 16:9 artwork as a temporary cosmetic draft, never as final native-detail art")
    args = parser.parse_args(argv)
    report = stage_native_menu(args.source_root, args.background, args.background_sha256,
                               args.project, args.replace_generated,
                               allow_draft_upscale=args.allow_draft_upscale)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
