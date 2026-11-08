#!/usr/bin/env python3
"""Compose an 800x600 static main-menu reference from verified original bytes.

This is an analysis artifact, not a screenshot of a running game or a Unity
implementation. Button state 0 is selected explicitly; input behavior and
runtime palette installation still require comparison with the original.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile
from PIL import Image

try:
    from .inspect_dkx import allocation_blocks, decode_dib, decode_font, inspect_pair
    from .decode_sprite import decode_sprite, resource_payload
except ImportError:
    from inspect_dkx import allocation_blocks, decode_dib, decode_font, inspect_pair
    from decode_sprite import decode_sprite, resource_payload


EXE_SHA256 = "cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021"
RESOURCE_IDS = (1042, 101, 1027, 1026, 1000, 103)
EVIDENCE_RANGES = (
    (0x530C40, 0x530FA4, "button creation and positions"),
    (0x531030, 0x53149F, "button command to label resource binding"),
    (0x53D633, 0x53D7A0, "background and font resource binding"),
    (0x4EA470, 0x4EA622, "button draw state and label centering"),
    (0x547100, 0x547330, "glyph lookup and text measurement"),
    (0x547734, 0x54775A, "font transparent palette index"),
    (0x579260, 0x5792C0, "8-bit transparent copy"),
)


def indexed_dib(payload):
    """Read checked top-down palette indices without collapsing color keys."""
    decode_dib(payload)  # Validate the supported DIB dimensions and exact length.
    width, height = struct.unpack_from("<ii", payload, 4)
    colors = struct.unpack_from("<I", payload, 32)[0] or 256
    palette = [tuple(payload[40 + i * 4:43 + i * 4][::-1]) for i in range(colors)]
    start, stride = 40 + colors * 4, ((width + 3) // 4) * 4
    rows = range(height - 1, -1, -1) if height > 0 else range(-height)
    indices = b"".join(payload[start + y * stride:start + y * stride + width] for y in rows)
    if any(value >= colors for value in indices):
        raise ValueError("DIB pixel has no palette entry")
    return (width, abs(height)), indices, palette


def glyph_lookup(font):
    if not font["glyphs"]:
        raise ValueError("Font has no fallback glyph")
    lookup = {g["code"]: g for g in font["glyphs"]}
    return lookup, font["glyphs"][0]


def measure_text(text, font, spacing=1):
    lookup, fallback = glyph_lookup(font)
    glyphs = [lookup.get(ord(character), fallback) for character in text]
    return (sum(g["width"] for g in glyphs) + max(0, len(glyphs) - 1) * spacing,
            max((g["height"] for g in glyphs), default=0))


def composite_indices(destination, size, indices, palette, position, *, coverage=None, color_key=None):
    if len(indices) != size[0] * size[1]:
        raise ValueError("Pixel plane length mismatch")
    if coverage is not None and len(coverage) != len(indices):
        raise ValueError("Coverage plane length mismatch")
    if coverage is not None and color_key is not None:
        raise ValueError("Choose explicit coverage or a palette color key")
    pixels = b"".join(bytes(palette[index]) for index in indices)
    image = Image.frombytes("RGB", size, pixels)
    if coverage is None and color_key is not None:
        coverage = bytes(0 if index == color_key else 255 for index in indices)
    mask = Image.frombytes("L", size, coverage) if coverage is not None else None
    destination.paste(image, position, mask)


def draw_text(destination, text, font, atlas, position, color_key, spacing=1):
    lookup, fallback = glyph_lookup(font)
    size, indices, palette = atlas
    x, y = position
    for character in text:
        glyph = lookup.get(ord(character), fallback)
        rows = [indices[(glyph["y"] + row) * size[0] + glyph["x"]:
                        (glyph["y"] + row) * size[0] + glyph["x"] + glyph["width"]]
                for row in range(glyph["height"])]
        composite_indices(destination, (glyph["width"], glyph["height"]), b"".join(rows),
                          palette, (x, y), color_key=color_key)
        x += glyph["width"] + spacing


def pe_strings(pe, resource_ids, language=1049):
    result = {}
    tables = next(e for e in pe.DIRECTORY_ENTRY_RESOURCE.entries if e.id == 6)
    for block in tables.directory.entries:
        wanted = [r for r in resource_ids if r // 16 + 1 == block.id]
        if not wanted:
            continue
        candidates = [entry for entry in block.directory.entries if entry.id == language]
        if len(candidates) != 1:
            raise ValueError("Verified PE string language is missing or ambiguous")
        entry = candidates[0].data.struct
        raw = pe.get_data(entry.OffsetToData, entry.Size)
        cursor = 0
        for index in range(16):
            if cursor + 2 > len(raw):
                raise ValueError("Truncated PE string table")
            count = struct.unpack_from("<H", raw, cursor)[0]
            cursor += 2
            if cursor + count * 2 > len(raw):
                raise ValueError("Truncated PE string")
            text = raw[cursor:cursor + count * 2].decode("utf-16le")
            if (block.id - 1) * 16 + index in wanted:
                result[(block.id - 1) * 16 + index] = text
            cursor += count * 2
    if set(result) != set(resource_ids) or any(not value for value in result.values()):
        raise ValueError("Required PE strings are missing")
    return result


def render_reference(source_root, destination):
    root, destination = Path(source_root), Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("Reference output must be a fresh directory")
    paths = (root / "installed/ancient.exe", root / "installed/missions/controlm.dkx",
             root / "installed/missions/controlm.dkd")
    executable, index, data = [path.read_bytes() for path in paths]
    if hashlib.sha256(executable).hexdigest() != EXE_SHA256:
        raise ValueError("Menu code contract is only verified for the recorded executable")
    pe = pefile.PE(data=executable)
    strings = pe_strings(pe, RESOURCE_IDS)
    entries = inspect_pair(index, data)
    lookup = {(entry["type"], entry["name"]): entry for entry in entries}
    used = []

    def resource(kind, name):
        entry = lookup[kind, name]
        used.append({key: entry[key] for key in ("name", "type", "offset", "stored_size", "sha256")})
        return entry, resource_payload(entry, data)

    _, background = resource(1, "0M_BKGND_00")
    size, bg_indices, bg_palette = indexed_dib(background)
    if size != (800, 600):
        raise ValueError("Verified menu background dimensions changed")
    image = Image.new("RGB", size)
    composite_indices(image, size, bg_indices, bg_palette, (0, 0))
    font_entry, font_payload = resource(3, "0S_FNT_BS")
    font, _ = decode_font(font_entry, data, allocation_blocks(data))
    atlas_source = font["atlas_sources"][1]  # Explicit original drawing state 0.
    atlas = indexed_dib(data[atlas_source["offset"]:atlas_source["offset"] + atlas_source["size"]])
    color_key = struct.unpack_from("<H", font_payload, 66)[0]
    if color_key != 6:
        raise ValueError("Verified font color key changed")
    # Palette differences in unused atlas cells must not silently alter glyphs.
    used_indices = set(atlas[1]) - {color_key}
    if any(atlas[2][number] != bg_palette[number] for number in used_indices):
        raise ValueError("Font and background disagree on used palette colors")
    buttons = []
    for number, resource_id in enumerate(RESOURCE_IDS, 1):
        descriptor = f"0M_BUT{(number + 1) % 2}_"
        _, descriptor_payload = resource(11, descriptor)
        if descriptor_payload.split(b"\0", 1)[0].decode("ascii") != descriptor:
            raise ValueError("Button descriptor name mismatch")
        sprite_entry, payload = resource(6, descriptor + "00")
        sprite = decode_sprite(payload)
        if (sprite["width"], sprite["height"]) != (174, 40):
            raise ValueError("Verified button dimensions changed")
        position = (30 + 40 * number, 180 + 52 * number)
        composite_indices(image, (174, 40), sprite["indices"], bg_palette, position,
                          coverage=sprite["coverage"])
        text = strings[resource_id]
        width, height = measure_text(text, font)
        local_text = (int((174 - width) / 2), int((40 - height) / 2))
        draw_text(image, text, font, atlas,
                  (position[0] + local_text[0], position[1] + local_text[1]), color_key)
        buttons.append({"resource_id": resource_id, "label": text, "rect": [*position, 174, 40],
                        "sprite": sprite_entry["name"], "text_size": [width, height],
                        "text_local_position": list(local_text)})
    destination.mkdir(parents=True)
    image.save(destination / "main-menu-state0.png")
    report = {"kind": "static reconstruction from original resources and executable",
              "runtime_screenshot": False, "unity_implementation": False,
              "size": list(size), "button_drawing_state": 0, "font_atlas_variant": 1,
              "horizontal_character_spacing": 1, "transparent_font_index": color_key,
              "buttons": buttons, "font_atlas_source": atlas_source,
              "sources": [{"path": str(path), "sha256": hashlib.sha256(content).hexdigest()}
                          for path, content in zip(paths, (executable, index, data))],
              "resources": used,
              "code_evidence": [{"va_start": hex(start), "va_end_exclusive": hex(end),
                                 "purpose": purpose,
                                 "sha256": hashlib.sha256(pe.get_data(start - pe.OPTIONAL_HEADER.ImageBase,
                                                                     end - start)).hexdigest()}
                                for start, end, purpose in EVIDENCE_RANGES],
              "pixels_sha256": hashlib.sha256(image.tobytes()).hexdigest(),
              "png_sha256": hashlib.sha256((destination / "main-menu-state0.png").read_bytes()).hexdigest(),
              "limitations": ["Not compared with the running original yet.",
                              "Drawing state 0 is selected; hover/click/disabled meanings are unverified.",
                              "Prefix 0 is selected explicitly; resolution-mode selection is unverified.",
                              "Sprites use the background DIB palette; runtime palette installation is unverified.",
                              "No behavior, sound, animation, or native widescreen adaptation is implemented."]}
    (destination / "manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    report = render_reference(args.source_root, args.output)
    print(f"Composed static reference, {len(report['buttons'])} buttons; runtime comparison pending")


if __name__ == "__main__":
    main()
