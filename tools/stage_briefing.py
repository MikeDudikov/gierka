#!/usr/bin/env python3
"""Stage the source-verified static miss000 briefing on a native 1920x1080 canvas.

The original game is never executed. The background is kept at its supplied
resolution; independent font/button layers retain their source proportions.
This is a static briefing prototype, not the complete timed/audio presentation.
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
    from .inspect_dkx import inspect_pair, decode_font, allocation_blocks
    from .decode_sprite import resource_payload, decode_sprite
    from .render_reference_menu import (EXE_SHA256, indexed_dib, pe_strings,
                                        draw_text, measure_text, composite_indices)
    from .stage_native_menu import read_hd_background
    from .stage_unity_reference import bottom_up_rgba
except ImportError:
    from inspect_dkx import inspect_pair, decode_font, allocation_blocks
    from decode_sprite import resource_payload, decode_sprite
    from render_reference_menu import (EXE_SHA256, indexed_dib, pe_strings,
                                      draw_text, measure_text, composite_indices)
    from stage_native_menu import read_hd_background
    from stage_unity_reference import bottom_up_rgba

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 1920, 1080
SCALE = 1.8
DELIMITERS = " ,.;:!?/\\()[]{}"
TEXT_RECT = (237, 144, 1134, 792)
BUTTON_RECTS = ((620, 977, 209, 72), (1091, 977, 209, 72))
RADIO_RECTS = tuple((1591, 792 + i * 54, 41, 41) for i in range(3))
DIFFICULTY_RECT = (1591, 792, 168, 149)
SOURCE_HASHES = {
    "installed/ancient.exe": EXE_SHA256,
    "installed/missions/controlm.dkx": "b32a80c703650d8873938544ee4b0718c70a2fd5a577d1b2814bf21b97224974",
    "installed/missions/controlm.dkd": "6f4b90903c880baf938d94577f8058904fafab5008b1963104cc8253cd842cbe",
    "installed/missions/miss000.dkx": "b4b2fda60bb38e837b6d0548caa86229e1fbebf8cb9fd806c4f39c9bd75835ce",
    "installed/missions/miss000.dkd": "a77e801a93baafd6942db9087d7541f8c85ed2f3c88d440b9f9e81b45ba9a0d1",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def parse_description(payload):
    """Deserialize ccSarrTy: 24-byte header, MSB-first presence bitmap, NUL slots."""
    if len(payload) < 24:
        raise ValueError("Truncated description header")
    count, capacity, grow = struct.unpack_from("<III", payload, 8)
    if count > 100000 or capacity < count or capacity > 100000 or not grow:
        raise ValueError("Invalid description count/capacity/grow")
    bitmap_length = (count + 7) // 8
    cursor = 24 + bitmap_length
    if cursor > len(payload):
        raise ValueError("Truncated description presence bitmap")
    slots = []
    for index in range(count):
        if payload[24 + index // 8] & (0x80 >> (index % 8)):
            end = payload.find(b"\0", cursor)
            if end < 0:
                raise ValueError("Unterminated description string")
            # The selected source is ASCII. Never silently invent a Unicode mapping.
            slots.append(payload[cursor:end].decode("ascii", errors="strict"))
            cursor = end + 1
        else:
            slots.append(None)
    if cursor != len(payload):
        raise ValueError("Unexpected description trailing bytes")
    return slots


def tokens(text, delimiters=DELIMITERS):
    """Original GetWord keeps the delimiter terminating each token."""
    start = 0
    for index, character in enumerate(text):
        if character in delimiters:
            yield text[start:index + 1]
            start = index + 1
    if start < len(text):
        yield text[start:]


def form_lines(records, font, width=630):
    """Port the verified FormSarr path; preserve all trailing and internal spaces."""
    if width <= 0:
        raise ValueError("Text width must be positive")
    line, line_width = "", 0
    output = []

    def emit(value):
        output.append(value if not output else value.lstrip(" \t"))

    for record in records:
        for token in tokens(record):
            if line_width + measure_text(token, font)[0] + 1 > width:
                if line:
                    emit(line)
                line = ""
            line += token
            if len(line) >= 512:
                raise ValueError("Text exceeds verified original formatter buffer")
            line_width = measure_text(line, font)[0]
        saved = line
        if line:  # Original5469c0 returns early for an empty destination.
            line += DELIMITERS[0]
        line_width = measure_text(line, font)[0]
        if line_width > width:
            if saved:
                emit(saved)
            line, line_width = "", 0
    if line:
        emit(line)
    return output


def format_description(slots, font, width=630):
    """Port FormIndentSarr's verified no-inline-escape miss000 path."""
    output, group = [], []
    for text in slots:
        if text is None:
            break
        if "&" in text:
            raise ValueError("Inline font controls are outside the verified miss000 path")
        beginning = 0
        for index, character in enumerate(text):
            if character == "@":
                group.append(text[beginning:index])
                output.extend(form_lines(["  ", *group], font, width))
                group = []
                beginning = index + 1
        if beginning != len(text):
            group.append(text[beginning:])
    if group:
        output.extend(form_lines(["  ", *group], font, width))
    return output


def checked_sources(source_root):
    root = Path(source_root)
    result = {}
    for name, expected in SOURCE_HASHES.items():
        raw = (root / name).read_bytes()
        if digest(raw) != expected:
            raise ValueError("Original source hash differs: " + name)
        result[name] = raw
    return result


def scaled_layer(image):
    return image.resize((round(image.width * SCALE), round(image.height * SCALE)),
                        Image.Resampling.LANCZOS)


def compose_briefing(source_root):
    sources = checked_sources(source_root)
    executable = sources["installed/ancient.exe"]
    data = sources["installed/missions/controlm.dkd"]
    index = sources["installed/missions/controlm.dkx"]
    lookup = {(entry["type"], entry["name"]): entry for entry in inspect_pair(index, data)}
    used = []

    def resource(kind, name):
        entry = lookup[kind, name]
        used.append({key: entry[key] for key in ("type", "name", "offset", "sha256")})
        return entry, resource_payload(entry, data)

    _, original_background = resource(1, "0M_BKGND_05")
    size, indices, palette = indexed_dib(original_background)
    if size != (800, 600):
        raise ValueError("Original briefing background changed")
    fonts = {}
    for name in ("0S_FNT_MH", "0S_FNT_BH", "0S_FNT_BS"):
        entry, payload = resource(3, name)
        font, _ = decode_font(entry, data, allocation_blocks(data))
        key = struct.unpack_from("<H", payload, 66)[0]
        atlases = []
        for source in font["atlas_sources"]:
            atlas = indexed_dib(data[source["offset"]:source["offset"] + source["size"]])
            if any(atlas[2][number] != palette[number] for number in set(atlas[1]) - {key}):
                raise ValueError("Original briefing font/background palette mismatch")
            atlases.append(atlas)
        fonts[name] = font, atlases, key
    strings = pe_strings(pefile.PE(data=executable), (1010, 1002, 105, 106, 107, 108))
    mission_data = sources["installed/missions/miss000.dkd"]
    mission_entries = inspect_pair(sources["installed/missions/miss000.dkx"], mission_data)
    description_entry = next(entry for entry in mission_entries
                             if (entry["type"], entry["name"]) == (23, "DISCRIPTION"))
    description = resource_payload(description_entry, mission_data)
    slots = parse_description(description)
    if not slots or not isinstance(slots[0], str) or not slots[0].startswith('@"') or not slots[0].endswith('"'):
        raise ValueError("Verified miss000 title format changed")
    mission_title = slots[0][2:-1]
    body_font, body_atlases, body_key = fonts["0S_FNT_MH"]
    lines = format_description(slots, body_font)
    body = Image.new("RGBA", (630, 440), (0, 0, 0, 0))
    line_metadata, y = [], 0
    for text in lines:
        width, height = measure_text(text, body_font)
        draw_text(body, text, body_font, body_atlases[2], (0, y), body_key)
        line_metadata.append({"text": text, "x": 0, "y": y, "width": width, "height": height})
        y += height + 1
    if y - 1 > 440:
        raise ValueError("Description exceeds verified static briefing viewport")
    static = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    static.alpha_composite(scaled_layer(body), TEXT_RECT[:2])
    heading_font, heading_atlases, heading_key = fonts["0S_FNT_BH"]
    heading = Image.new("RGBA", measure_text(strings[105], heading_font))
    draw_text(heading, strings[105], heading_font, heading_atlases[2], (0, 0), heading_key)
    static.alpha_composite(scaled_layer(heading), (1584, 729))

    button_atlas = Image.new("RGBA", (418, 288))
    button_font, button_atlases, button_key = fonts["0S_FNT_BS"]
    controls = []
    for column, resource_id in enumerate((1010, 1002)):
        name = f"0M_BUT{column + 2}_"
        sprite_list = []
        for number in range(2):
            _, payload = resource(6, name + f"{number:02}")
            sprite = decode_sprite(payload)
            if (sprite["width"], sprite["height"]) != (116, 40):
                raise ValueError("Briefing buttons must retain source116x40 dimensions")
            sprite_list.append(sprite)
        text = strings[resource_id]
        text_width, text_height = measure_text(text, button_font)
        for state in range(4):
            sprite = sprite_list[int(state in (2, 3))]
            button = Image.new("RGBA", (116, 40))
            composite_indices(button, (116, 40), sprite["indices"], palette, (0, 0),
                              coverage=sprite["coverage"])
            position = (int((116 - text_width) / 2), int((40 - text_height) / 2))
            if state == 3:
                draw_text(button, text, button_font, button_atlases[0], position, button_key)
                position = (int((112 - text_width) / 2), int((36 - text_height) / 2))
            draw_text(button, text, button_font, button_atlases[min(state + 1, 3)], position, button_key)
            button_atlas.alpha_composite(scaled_layer(button), (column * 209, state * 72))
        controls.append({"resource_id": resource_id, "label": text,
                         "native_rect": list(BUTTON_RECTS[column])})

    radio_sprites = []
    for number in range(2):
        _, payload = resource(6, "0M_CHECK" + str(number))
        sprite = decode_sprite(payload)
        if (sprite["width"], sprite["height"]) != (23, 23):
            raise ValueError("Briefing radio icons must retain source23x23 dimensions")
        icon = Image.new("RGBA", (23, 23))
        composite_indices(icon, (23, 23), sprite["indices"], palette, (0, 0),
                          coverage=sprite["coverage"])
        radio_sprites.append(scaled_layer(icon))
    difficulty = Image.new("RGBA", (504, 149))
    difficulty_controls = []
    for value in range(3):
        difficulty_controls.append({"value": value, "label": strings[106 + value],
                                    "native_rect": list(RADIO_RECTS[value])})
    for selection in range(3):
        panel = Image.new("RGBA", (168, 149))
        for value in range(3):
            selected = value == selection
            panel.alpha_composite(radio_sprites[int(selected)], (0, value * 54))
            label = strings[106 + value]
            label_layer = Image.new("RGBA", measure_text(label, heading_font))
            # TabClass records: selected1 -> font2; unselected0 -> font1.
            draw_text(label_layer, label, heading_font, heading_atlases[2 if selected else 1],
                      (0, 0), heading_key)
            panel.alpha_composite(scaled_layer(label_layer), (65, value * 54))
        difficulty.alpha_composite(panel, (selection * 168, 0))
    metadata = {
        "schema_version": 1, "width": WIDTH, "height": HEIGHT,
        "native_canvas_width": WIDTH, "native_canvas_height": HEIGHT,
        "mission": "miss000", "mission_title": mission_title,
        "static_width": WIDTH, "static_height": HEIGHT,
        "button_atlas_width": 418, "button_atlas_height": 288,
        "button_count": 2, "button_states": 4, "controls": controls,
        "difficulty_atlas_width": 504, "difficulty_atlas_height": 149,
        "difficulty_rect": list(DIFFICULTY_RECT), "difficulty_controls": difficulty_controls,
        "default_difficulty": 0, "text_rect": list(TEXT_RECT),
        "description_sha256": digest(description), "description_slots": slots,
        "text_source_font": "0S_FNT_MH", "text_source_width": 630,
        "text_source_spacing": [1, 1], "text_source_lines": line_metadata,
        "text_presentation": "All static lines shown from local0,0; timed reveal/audio not implemented",
        "sources": [{"path": name, "sha256": digest(raw)} for name, raw in sources.items()],
        "resources": used,
        "limitations": ["Static prototype, not full timed/audio briefing",
                        "Start intentionally disabled while faithful gameplay is unimplemented",
                        "Original bitmap UI/fonts are temporary per-layer reconstruction, not final2026art",
                        "Original runtime palette/resource-prefix selection remains unverified"],
    }
    return {"StaticUiRgba.bytes": static, "ButtonsRgba.bytes": button_atlas,
            "DifficultyRgba.bytes": difficulty}, metadata


def write_payloads(output, images, metadata, replace_generated=False):
    output = Path(output).absolute()
    if output.resolve() != output:
        raise ValueError("Generated output must not contain symlinks")
    if any(not name.endswith(".bytes") or Path(name).name != name for name in images):
        raise ValueError("Invalid generated payload name")
    payloads = {name: bottom_up_rgba(image) for name, image in images.items()}
    metadata = dict(metadata, payloads={name: {"bytes": len(raw), "sha256": digest(raw)}
                                       for name, raw in payloads.items()})
    files = dict(payloads, **{"BriefingManifest.json": (json.dumps(metadata, indent=2) + "\n").encode()})
    if any((output / name).is_symlink() for name in files):
        raise ValueError("Generated files must not be symlinks")
    changes = [name for name, raw in files.items()
               if (output / name).exists() and (output / name).read_bytes() != raw]
    if changes and not replace_generated:
        raise FileExistsError("Changed briefing data requires explicit --replace-generated")
    if changes:
        old = json.loads((output / "BriefingManifest.json").read_text())
        for name, entry in old["payloads"].items():
            if not name.endswith(".bytes") or Path(name).name != name:
                raise ValueError("Invalid previous generated payload name")
            path = output / name
            if path.is_symlink() or not path.is_file() or digest(path.read_bytes()) != entry["sha256"]:
                raise ValueError("Previous generated briefing hash mismatch")
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


def stage_briefing(source_root, background_path, background_sha256, project,
                   *, allow_draft_upscale=False, replace_generated=False, preview=None):
    images, metadata = compose_briefing(source_root)
    background, background_info = read_hd_background(
        background_path, background_sha256, allow_draft_upscale=allow_draft_upscale)
    images["BackgroundRgba.bytes"] = background
    metadata.update(background_width=background.width, background_height=background.height,
                    background_upscale_draft=background_info["upscale_draft"], background=background_info,
                    format="RGBA32", row_order="bottom-to-top")
    report = write_payloads(Path(project) / "Assets/Resources/BriefingGenerated", images,
                            metadata, replace_generated)
    if preview is not None:
        preview = Path(preview)
        preview.mkdir(parents=True, exist_ok=True)
        images["StaticUiRgba.bytes"].save(preview / "static-ui.png")
        images["ButtonsRgba.bytes"].save(preview / "button-atlas.png")
        images["DifficultyRgba.bytes"].save(preview / "difficulty-atlas.png")
        (preview / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=ROOT / "reference/raw/ancient-conquest")
    parser.add_argument("--project", type=Path, default=ROOT / "Unity/AncientConquest")
    parser.add_argument("--background", type=Path, required=True)
    parser.add_argument("--background-sha256", required=True)
    parser.add_argument("--allow-draft-upscale", action="store_true")
    parser.add_argument("--replace-generated", action="store_true")
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args(argv)
    report = stage_briefing(args.source_root, args.background, args.background_sha256, args.project,
                           allow_draft_upscale=args.allow_draft_upscale,
                           replace_generated=args.replace_generated, preview=args.preview)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
