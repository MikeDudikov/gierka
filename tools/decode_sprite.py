#!/usr/bin/env python3
"""Recover type-6 8-bit sprite indices and coverage from the observed CD format.

Indices and masks are lossless evidence. An optional DIB palette produces a
preview only; it does not establish the palette selected by the running game.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

try:
    from .inspect_dkx import inspect_pair
    from .extract_setup import decompress_block
except ImportError:
    from inspect_dkx import inspect_pair
    from extract_setup import decompress_block


class SpriteFormatError(ValueError):
    pass


def decode_sprite(payload: bytes, max_pixels=16 * 1024**2) -> dict:
    """Return top-down index/coverage planes without choosing any palette.

    Verified against the reader at ancient.exe 0x572d40 and blitter 0x574d50.
    Unknown format variants fail explicitly; retained flags can influence
    rendering beyond the decoded pixel coverage.
    """
    if len(payload) < 22:
        raise SpriteFormatError("Truncated sprite header")
    length, width, height, flags, left, top, box_width, box_height = struct.unpack_from("<Iii5H", payload)
    if length != len(payload):
        raise SpriteFormatError("Sprite byte count mismatch")
    if (width <= 0 or height <= 0 or width * height > max_pixels or
            left + box_width > width or top + box_height > height):
        raise SpriteFormatError("Sprite dimensions or bounds invalid")
    if flags & ~0x1D80 or flags & 0xFF != 0x80:
        raise SpriteFormatError("Unsupported sprite encoding flags")
    table_count = (flags >> 10) & 7
    if table_count != min(7, box_height // 16):
        raise SpriteFormatError("Row table count does not match observed layout")
    start = 22 + 2 * table_count
    if start > len(payload):
        raise SpriteFormatError("Truncated row table")
    table = list(struct.unpack_from("<" + "H" * table_count, payload, 22))
    indices = bytearray(width * height)
    coverage = bytearray(width * height)
    pos = start
    row_starts = []
    for row in range(box_height):
        row_starts.append(pos)
        x = 0
        while x < box_width:
            if pos >= len(payload):
                raise SpriteFormatError("Truncated sprite row")
            opcode = payload[pos]
            pos += 1
            if opcode == 0:
                # The original also handles a zero-row command. No such row was
                # needed by the validated sample set; refuse its unexplained
                # following byte rather than assigning speculative semantics.
                raise SpriteFormatError("Unsupported zero-row command")
            if opcode < 0x80:
                count = opcode
                x += count
                if x > box_width:
                    raise SpriteFormatError("Transparent run exceeds row")
                continue
            count = opcode & 0x3F
            if count == 0 or x + count > box_width:
                raise SpriteFormatError("Pixel run exceeds row or has zero length")
            end = pos + (1 if opcode >= 0xC0 else count)
            if end > len(payload):
                raise SpriteFormatError("Truncated pixel run")
            pixels = payload[pos:end]
            if opcode >= 0xC0:
                pixels *= count
            target = (top + row) * width + left + x
            indices[target:target + count] = pixels
            coverage[target:target + count] = b"\xff" * count
            pos = end
            x += count
    if pos != len(payload):
        raise SpriteFormatError("Trailing bytes after sprite rows")
    for number, offset in enumerate(table):
        row = (number + 1) * 16
        expected = row_starts[row] - 22 if row < box_height else 0
        if offset != expected:
            raise SpriteFormatError("Row seek table disagrees with decoded runs")
    return {"width": width, "height": height, "flags": flags,
            "left": left, "top": top, "box_width": box_width,
            "box_height": box_height, "row_offsets": table,
            "indices": bytes(indices), "coverage": bytes(coverage)}


def resource_payload(entry, data):
    payload = data[entry["offset"]:entry["offset"] + entry["stored_size"]]
    if entry["raw_size"] > 256 * 1024**2:
        raise SpriteFormatError("Resource exceeds supported decoded size")
    if entry["compression"]:
        payload = decompress_block(payload, max_output=entry["raw_size"])
    if len(payload) != entry["raw_size"]:
        raise SpriteFormatError("Decoded resource size mismatch")
    return payload


def dib_palette(payload):
    """Read the palette only from a checked 8-bit Windows DIB."""
    if len(payload) < 1064:
        raise SpriteFormatError("Truncated DIB palette")
    header, width, height, planes, bits, compression = struct.unpack_from("<IiiHHI", payload)
    colors = struct.unpack_from("<I", payload, 32)[0] or 256
    if (header, planes, bits, compression, colors) != (40, 1, 8, 0, 256):
        raise SpriteFormatError("Unsupported preview palette source")
    if width <= 0 or height == 0 or 1064 + ((width + 3) // 4) * 4 * abs(height) != len(payload):
        raise SpriteFormatError("Invalid palette source DIB dimensions")
    return bytes(value for offset in range(40, 1064, 4)
                 for value in (payload[offset + 2], payload[offset + 1], payload[offset]))


def export_selected(index_path, data_path, names, destination, palette_name=None):
    from PIL import Image
    index, data = Path(index_path).read_bytes(), Path(data_path).read_bytes()
    entries = inspect_pair(index, data)
    lookup = {entry["name"]: entry for entry in entries if entry["type"] == 6}
    selected = [lookup[name] for name in names]
    palette = None
    if palette_name:
        entry = next(e for e in entries if e["type"] == 1 and e["name"] == palette_name)
        palette = dib_palette(resource_payload(entry, data))
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    report = {"index_sha256": hashlib.sha256(index).hexdigest(),
              "data_sha256": hashlib.sha256(data).hexdigest(),
              "palette_preview_source": palette_name,
              "palette_binding_status": "Unverified; chosen DIB palette is a preview only",
              "sprites": []}
    for number, entry in enumerate(selected):
        payload = resource_payload(entry, data)
        sprite = decode_sprite(payload)
        stem = f"{number:04d}"
        size = sprite["width"], sprite["height"]
        Image.frombytes("L", size, sprite["indices"]).save(destination / (stem + "-indices.png"))
        mask = Image.frombytes("L", size, sprite["coverage"])
        mask.save(destination / (stem + "-coverage.png"))
        if palette:
            preview = Image.frombytes("P", size, sprite["indices"])
            preview.putpalette(palette)
            preview = preview.convert("RGBA")
            preview.putalpha(mask)
            preview.save(destination / (stem + "-preview.png"))
        metadata = {k: v for k, v in sprite.items() if k not in ("indices", "coverage")}
        metadata.update(name=entry["name"], offset=entry["offset"],
                        stored_payload_sha256=entry["sha256"],
                        decoded_payload_sha256=hashlib.sha256(payload).hexdigest(),
                        indices_sha256=hashlib.sha256(sprite["indices"]).hexdigest(),
                        coverage_sha256=hashlib.sha256(sprite["coverage"]).hexdigest(),
                        stem=stem)
        report["sprites"].append(metadata)
    (destination / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index", type=Path)
    parser.add_argument("data", type=Path)
    parser.add_argument("--name", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preview-palette", help="Name of a type-1 DIB in this same container")
    args = parser.parse_args(argv)
    report = export_selected(args.index, args.data, args.name, args.output, args.preview_palette)
    print(f"Recovered {len(report['sprites'])} sprite index/coverage pairs")


if __name__ == "__main__":
    main()
