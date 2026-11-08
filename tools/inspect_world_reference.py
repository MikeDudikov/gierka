#!/usr/bin/env python3
"""Export bounded world-art reference samples from verified original bytes.

Terrain DIBs retain their own stored palette. Object sprites are separately
labelled as a reconstruction using the game's PALETTE base state; animation,
player remapping, lighting, shadow mixing and palette cycling are not applied.
No game code is executed and no original file is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

try:
    from .decode_sprite import decode_sprite, dib_palette, resource_payload
    from .inspect_dkx import decode_dib, inspect_pair
    from .render_reference_menu import indexed_dib
except ImportError:
    from decode_sprite import decode_sprite, dib_palette, resource_payload
    from inspect_dkx import decode_dib, inspect_pair
    from render_reference_menu import indexed_dib


REPOSITORY = Path(__file__).resolve().parents[1]
SOURCE_HASHES = {
    "installed/ancient.exe": "cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021",
    "installed/missions/maplib.dkx": "05484166ca374630f7c29c26e561656a11941ef331fb014e52f72aed81c23650",
    "installed/missions/maplib.dkd": "7fe0623d957e196e5279c6bced55db292648b5c9ebc6f1420fcd293c0685b685",
    "files/DATA/OBJECTS.DKX": "67aa31b7e7728a1c4f215c63932b55ea66f3ac1ecdb732bfd368bae2a8375f60",
    "files/DATA/OBJECTS.DKD": "01474065782a7170d54f564df2205572f8a0675411bef0f350dab55c3fd20e50",
}
TERRAIN_NAMES = ("b_isl_bkg00_001", "b_isl_bkg00_015", "b_isl_bkg01_001",
                 "b_isl_bkg01_015", "b_sea00_001", "b_shelf_001")
SPRITE_NAMES = ("CORP_1A0000", "VOLCANO0_00", "FISH_3236")


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def used_palette_differences(indices, stored_palette, base_palette):
    """Compare RGB only at used indices, retaining repeated RGB/index identity."""
    if len(base_palette) != 768:
        raise ValueError("A complete 256-entry RGB palette is required")
    used = sorted(set(indices))
    if used and used[-1] >= len(stored_palette):
        raise ValueError("Terrain index is outside its own stored palette")
    return [index for index in used
            if tuple(base_palette[index * 3:index * 3 + 3]) != stored_palette[index]]


def base_palette_sprite(sprite, palette):
    """Map indices literally, and derive alpha from RLE coverage only."""
    if len(palette) != 768:
        raise ValueError("A complete 256-entry RGB palette is required")
    size = sprite["width"], sprite["height"]
    if len(sprite["indices"]) != size[0] * size[1] or len(sprite["coverage"]) != size[0] * size[1]:
        raise ValueError("Sprite index/coverage size mismatch")
    image = Image.frombytes("P", size, sprite["indices"])
    image.putpalette(palette)
    image = image.convert("RGBA")
    image.putalpha(Image.frombytes("L", size, sprite["coverage"]))
    return image


def export_reference(source_root, destination):
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("Reference destination must be a fresh directory")
    loaded, sources = {}, []
    for relative, expected in SOURCE_HASHES.items():
        raw = (Path(source_root) / relative).read_bytes()
        actual = sha256(raw)
        if actual != expected:
            raise ValueError("Unexpected original source hash: " + relative)
        loaded[relative] = raw
        sources.append({"path": relative, "bytes": len(raw), "sha256": actual})
    map_data = loaded["installed/missions/maplib.dkd"]
    object_data = loaded["files/DATA/OBJECTS.DKD"]
    map_entries = inspect_pair(loaded["installed/missions/maplib.dkx"], map_data)
    object_entries = inspect_pair(loaded["files/DATA/OBJECTS.DKX"], object_data)
    maps = {(entry["type"], entry["name"]): entry for entry in map_entries}
    objects = {(entry["type"], entry["name"]): entry for entry in object_entries}
    palette_entry = maps[1, "PALETTE"]
    base_palette = dib_palette(resource_payload(palette_entry, map_data))

    # Check every stored DIB palette, including mismatches. A separate record
    # prevents small-map water colours from being silently called equivalent.
    audit = []
    for entry in map_entries:
        if entry["type"] == 1:
            _, indices, palette = indexed_dib(resource_payload(entry, map_data))
            audit.append({"name": entry["name"], "used_palette_mismatches":
                          used_palette_differences(indices, palette, base_palette)})

    prepared = []
    for name in TERRAIN_NAMES:
        entry = maps[1, name]
        raw = resource_payload(entry, map_data)
        size, indices, palette = indexed_dib(raw)
        differences = used_palette_differences(indices, palette, base_palette)
        if differences:
            raise ValueError("Selected terrain differs from the base palette: " + name)
        prepared.append((decode_dib(raw).convert("RGBA"), {
            "kind": "terrain DIB with its own stored palette", "name": name,
            "entry": entry, "decoded_payload_sha256": sha256(raw),
            "size": list(size), "used_indices": sorted(set(indices)),
            "base_palette_used_index_mismatches": differences,
            "colour_evidence": "own DIB palette; all used entries also equal PALETTE"}))
    for name in SPRITE_NAMES:
        entry = objects[6, name]
        raw = resource_payload(entry, object_data)
        sprite = decode_sprite(raw)
        prepared.append((base_palette_sprite(sprite, base_palette), {
            "kind": "object sprite reconstructed in base PALETTE state", "name": name,
            "entry": entry, "decoded_payload_sha256": sha256(raw),
            "size": [sprite["width"], sprite["height"]], "flags": sprite["flags"],
            "indices_sha256": sha256(sprite["indices"]),
            "coverage_sha256": sha256(sprite["coverage"]),
            "used_indices": sorted({index for index, covered in
                                    zip(sprite["indices"], sprite["coverage"]) if covered}),
            "colour_evidence": "named gameplay base PALETTE; runtime effects not applied"}))

    destination.mkdir(parents=True)
    assets = []
    # The sheet is diagnostic only. Exported individual PNGs remain at the
    # exact source dimensions; the sheet's labelled 2x nearest view is explicit.
    sheet = Image.new("RGB", (600, 680), (36, 42, 49))
    draw = ImageDraw.Draw(sheet)
    for number, (image, metadata) in enumerate(prepared):
        path = destination / f"{number:02d}.png"
        image.save(path)
        metadata.update({"png": path.name, "png_sha256": sha256(path.read_bytes()),
                         "rgba_sha256": sha256(image.tobytes())})
        assets.append(metadata)
        x, y = (number % 3) * 200, (number // 3) * 210
        if number < 6:
            view = image.resize((128, 128), Image.Resampling.NEAREST)
        else:
            view = image  # Volcano fits the labelled source-size row.
        sheet.paste(view, (x + 10, y + 10), view)
        draw.text((x + 8, y + 174), metadata["name"], fill="white")
        draw.text((x + 8, y + 190), f"{image.width}x{image.height}", fill="white")
    sheet.save(destination / "world-reference-sheet.png")
    report = {
        "kind": "static original asset reconstruction; not gameplay screenshot or modernized art",
        "sources": sources, "palette_entry": palette_entry,
        "base_rgb_palette_sha256": sha256(base_palette), "assets": assets,
        "static_code_evidence": [
            {"va": "0x004eda40", "meaning": "InitAppDB opens missions/maplib into application+0xd50"},
            {"va": "0x004edc50", "meaning": "InitGameDB opens objects into application+0xd54"},
            {"va": "0x005101a7", "meaning": "GameSystemTy::GetMessage loads type1 PALETTE; copied to game+0x139e and application+0x11ad"},
            {"va": "0x0051bcb0", "meaning": "InitMapaBig chooses 0x40 tile side, copies type1 PALETTE, loads ANIM_PALETTE from application+0xd50"},
            {"va": "0x0056c4b0", "meaning": "Converts DIB palette BGR bytes at+40 to RGB entries; no gamma or colour-space transform"}],
        "dib_palette_audit": audit,
        "dib_matching_used_indices": sum(not row["used_palette_mismatches"] for row in audit),
        "sheet": "world-reference-sheet.png",
        "sheet_sha256": sha256((destination / "world-reference-sheet.png").read_bytes()),
        "limitations": ["No original runtime comparison on this host.",
                        "Object sprites use base PALETTE; colour cycling, lighting, player remapping and shadows are unresolved.",
                        "Names and lexicographic frame suffixes do not establish animation order, directions or playback rate.",
                        "No map layout, mission, model, simulation or Unity rendering is implemented here."]}
    (destination / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path,
                        default=REPOSITORY / "reference/raw/ancient-conquest")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    report = export_reference(args.source_root, args.output)
    print(json.dumps({"assets": len(report["assets"]),
                      "DIBs_audited": len(report["dib_palette_audit"]),
                      "DIBs_equal_on_used_indices": report["dib_matching_used_indices"]}))


if __name__ == "__main__":
    main()
