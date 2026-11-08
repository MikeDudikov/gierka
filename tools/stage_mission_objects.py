#!/usr/bin/env python3
"""Stage original mission seeds and frozen reef reference art, not gameplay."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct

from PIL import Image

try:
    from .inspect_dkx import inspect_pair
    from .decode_sprite import resource_payload, decode_sprite, dib_palette
    from .inspect_world_reference import base_palette_sprite
    from .stage_unity_reference import bottom_up_rgba
    from .stage_terrain import SOURCE_HASHES as TERRAIN_HASHES
except ImportError:
    from inspect_dkx import inspect_pair
    from decode_sprite import resource_payload, decode_sprite, dib_palette
    from inspect_world_reference import base_palette_sprite
    from stage_unity_reference import bottom_up_rgba
    from stage_terrain import SOURCE_HASHES as TERRAIN_HASHES

ROOT = Path(__file__).resolve().parents[1]
SOURCE_HASHES = dict(TERRAIN_HASHES, **{
    "files/DATA/OBJECTS.DKX": "67aa31b7e7728a1c4f215c63932b55ea66f3ac1ecdb732bfd368bae2a8375f60",
    "files/DATA/OBJECTS.DKD": "01474065782a7170d54f564df2205572f8a0675411bef0f350dab55c3fd20e50",
})
MANIFEST_NAME = "MissionObjectsManifest.json"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pack_seeds(records):
    """Canonical name order; exact per-record payloads remain unchanged."""
    names, blob, packed = set(), bytearray(), []
    for name, raw, source in sorted(records, key=lambda item: item[0]):
        if not re.fullmatch(r"OBJ_[0-9a-fA-F]{8}", name) or len(raw) < 16:
            raise ValueError("Invalid canonical object seed name/header")
        identifier = int(name[4:], 16)
        if identifier in names:
            raise ValueError("Duplicate object instance ID")
        names.add(identifier)
        tag, kind, side, player = struct.unpack_from("<4I", raw)
        packed.append({"resource_name": name, "instance_id": identifier,
                       "class_tag": tag, "kind": kind, "side_index": side, "player_index": player,
                       "payload_offset": len(blob), "payload_length": len(raw),
                       "payload_sha256": digest(raw), "source": source})
        blob.extend(raw)
    return bytes(blob), packed


def decode_reef_frames(entries, data, palette):
    resources = {(entry["type"], entry["name"]): entry for entry in entries}
    atlas = Image.new("RGBA", (128, 64))
    frames = []
    for column, variant in enumerate((2, 3)):
        name = f"BREEF{variant}SPR_1"
        descriptor = resources[7, name]
        raw = resource_payload(descriptor, data)
        if len(raw) != 49 or b"\0" not in raw[:32]:
            raise ValueError("Unexpected reef animation descriptor")
        prefix = raw[:32].split(b"\0", 1)[0].decode("ascii")
        digits, start, count = raw[32], *struct.unpack_from("<hh", raw, 33)
        if (prefix, digits, start, count) != (f"BREEF{variant}L_", 2, 0, 30):
            raise ValueError("Reef animation no longer matches its verified loader path")
        names = [prefix + f"{start + index:0{digits}d}" for index in range(count)]
        if any((6, frame_name) not in resources for frame_name in names):
            raise ValueError("Reef animation has a missing source frame")
        entry = resources[6, names[0]]
        sprite_raw = resource_payload(entry, data)
        sprite = decode_sprite(sprite_raw)
        if (sprite["width"], sprite["height"]) != (64, 64) or sprite["flags"] & 0x100:
            raise ValueError("Reef frame is outside the verified full-plane path")
        image = base_palette_sprite(sprite, palette)
        # Source bbox offsets are already embedded in the full 64x64 plane.
        atlas.paste(image, (column * 64, 0))
        frames.append({"variant": variant, "reference_state": 1, "reference_frame_index": 0,
                       "animation_resource": name, "animation_payload_sha256": digest(raw),
                       "animation_frame_count": count, "frame_resource": names[0],
                       "frame_payload_sha256": digest(sprite_raw),
                       "atlas_x": column * 64, "atlas_y": 0, "width": 64, "height": 64,
                       "rgba_sha256": digest(image.tobytes()),
                       "full_plane_anchor": "world cell *64; bbox left/top already decoded into alpha"})
    return atlas, frames


def compose(source_root):
    loaded = {}
    for name, expected in SOURCE_HASHES.items():
        raw = (Path(source_root) / name).read_bytes()
        if digest(raw) != expected:
            raise ValueError("Original source hash differs: " + name)
        loaded[name] = raw
    mission_data = loaded["installed/missions/miss000.dkd"]
    mission_entries = inspect_pair(loaded["installed/missions/miss000.dkx"], mission_data)
    objects_data = loaded["files/DATA/OBJECTS.DKD"]
    object_entries = inspect_pair(loaded["files/DATA/OBJECTS.DKX"], objects_data)
    map_data = loaded["installed/missions/maplib.dkd"]
    map_entries = inspect_pair(loaded["installed/missions/maplib.dkx"], map_data)
    palette_entry = next(e for e in map_entries if (e["type"], e["name"]) == (1, "PALETTE"))
    palette = dib_palette(resource_payload(palette_entry, map_data))
    blob, records = pack_seeds([(entry["name"], resource_payload(entry, mission_data), entry)
        for entry in mission_entries if entry["type"] == 12 and entry["name"].startswith("OBJ_")])
    if len(records) != 45:
        raise ValueError("Unexpected original miss000 seed count")
    atlas, frames = decode_reef_frames(object_entries, objects_data, palette)
    source_named = {(e["type"], e["name"]): e for e in mission_entries}
    descriptor = resource_payload(source_named[0, "DESCRIPTOR"], mission_data)
    views = resource_payload(source_named[12, "WIN_VIEW"], mission_data)
    if len(descriptor) != 1788 or len(views) != 80:
        raise ValueError("Unexpected original descriptor/view payload lengths")
    payloads = {"ObjectSeeds.bytes": blob, "ReefFramesRgba.bytes": bottom_up_rgba(atlas),
                "MissionDescriptor.bytes": descriptor, "SavedViews.bytes": views}
    metadata = {"schema_version": 1, "mission": "miss000", "native_canvas_width": 1920,
                "native_canvas_height": 1080, "record_count": len(records),
                "record_order": "source BTree prefix enumeration: equal type12/length12 keys in ordinal ASCII order",
                "record_layout": "exact source payloads concatenated; header four uint32LE words",
                "records": records, "reef_frames": frames, "reef_atlas_width": atlas.width,
                "reef_atlas_height": atlas.height, "format": "RGBA32", "row_order": "bottom-to-top",
                "reef_scope": "frozen state1/frame0 reference on an empty collision grid; not initial gameplay state",
                "sources": {name: {"bytes": len(raw), "sha256": digest(raw)} for name, raw in loaded.items()},
                "base_palette_sha256": digest(palette),
                "excluded": ["constructors for all classes", "simulation", "AI", "collision state",
                             "dynamic animation", "final2026art", "LIST_OBJ is not a seed list"]}
    return payloads, metadata, atlas


def write_payloads(output, payloads, metadata, replace_generated=False, *, manifest_name=MANIFEST_NAME):
    output = Path(output).absolute()
    if output.resolve() != output:
        raise ValueError("Generated path must not contain symlinks")
    if Path(manifest_name).name != manifest_name or not manifest_name.endswith(".json"):
        raise ValueError("Invalid generated manifest name")
    if any(Path(name).name != name or not name.endswith(".bytes") for name in payloads):
        raise ValueError("Invalid generated payload name")
    metadata = dict(metadata, payloads={name: {"bytes": len(raw), "sha256": digest(raw)}
                                        for name, raw in payloads.items()})
    files = dict(payloads, **{manifest_name: (json.dumps(metadata, indent=2) + "\n").encode()})
    if any((output / name).is_symlink() for name in files):
        raise ValueError("Generated files must not be symlinks")
    changed = [name for name, raw in files.items()
               if (output / name).exists() and (output / name).read_bytes() != raw]
    if changed and not replace_generated:
        raise FileExistsError("Changed object data requires --replace-generated")
    if changed:
        old = json.loads((output / manifest_name).read_text())
        for name, entry in old["payloads"].items():
            if Path(name).name != name or not name.endswith(".bytes"):
                raise ValueError("Invalid previous generated payload name")
            path = output / name
            if path.is_symlink() or not path.is_file() or digest(path.read_bytes()) != entry["sha256"]:
                raise ValueError("Previous generated object hash mismatch")
    output.mkdir(parents=True, exist_ok=True)
    for name, raw in files.items():
        path = output / name
        if path.exists() and path.read_bytes() == raw:
            continue
        temporary = output / (name + ".staging")
        with temporary.open("xb") as stream:
            stream.write(raw)
        os.replace(temporary, path)
    return metadata


def stage(source_root, project, *, replace_generated=False, preview=None):
    payloads, metadata, atlas = compose(source_root)
    report = write_payloads(Path(project) / "Assets/Resources/MissionObjectsGenerated",
                            payloads, metadata, replace_generated)
    if preview is not None:
        preview = Path(preview)
        preview.mkdir(parents=True, exist_ok=True)
        atlas.save(preview / "reef-reference-atlas.png")
        (preview / MANIFEST_NAME).write_text(json.dumps(report, indent=2) + "\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=ROOT / "reference/raw/ancient-conquest")
    parser.add_argument("--project", type=Path, default=ROOT / "Unity/AncientConquest")
    parser.add_argument("--replace-generated", action="store_true")
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args(argv)
    report = stage(args.source_root, args.project, replace_generated=args.replace_generated,
                   preview=args.preview)
    print(json.dumps({key: report[key] for key in ("record_count", "payloads")}, indent=2))


if __name__ == "__main__":
    main()
