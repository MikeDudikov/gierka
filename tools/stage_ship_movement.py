#!/usr/bin/env python3
"""Stage the proven source0b ship poses; no simulation or inferred artwork.

The bounded diagnostic covers SHIP_A1110 with the source mask0x83 and poses
0..87. Names, component geometry, ordering and RLE coverage come from source
records. Atlas coordinates use a bottom-left origin for Unity Texture2D.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

try:
    from .stage_mission_objects import SOURCE_HASHES, digest, write_payloads
    from .stage_unity_reference import bottom_up_rgba
    from .inspect_dkx import inspect_pair
    from .decode_sprite import resource_payload, dib_palette
    from .inspect_world_reference import base_palette_sprite
    from .decode_composite_sprite import decode_composite_frame
except ImportError:
    from stage_mission_objects import SOURCE_HASHES, digest, write_payloads
    from stage_unity_reference import bottom_up_rgba
    from inspect_dkx import inspect_pair
    from decode_sprite import resource_payload, dib_palette
    from inspect_world_reference import base_palette_sprite
    from decode_composite_sprite import decode_composite_frame

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_NAME = "ShipMovementManifest.json"
DESCRIPTOR = "SHIP_A1110"
DESCRIPTOR_SHA256 = "d15bb35d34c8daf7a0f6533853cbab22c97016178538c52d24b8a07306dfed98"
MASK = 0x83
POSE_COUNT, PLANE_COUNT = 88, 152
PLANE_SIZE, ATLAS_COLUMNS, ATLAS_ROWS = 56, 38, 4


def compose(source_root, *, heavy=False):
    #Two bounded actual local recipes;0b/0c share A,0d uses H with armor.
    descriptor_name = 'SHIP_H1110' if heavy else DESCRIPTOR
    descriptor_hash = '2f93ba1641471759b67fefa0163d0ab0a3c7cc5963c197a0f72873a76baece5c' if heavy else DESCRIPTOR_SHA256
    mask, size = (0xa3,72) if heavy else (MASK,PLANE_SIZE)
    plane_count, columns, rows = (224,32,7) if heavy else (PLANE_COUNT,ATLAS_COLUMNS,ATLAS_ROWS)
    parts = [(0,0,0,-21000),(1,0,0,10),(5,0,0,5),(7,0,0,4)] if heavy else [(0,0,0,-21000),(1,0,0,10),(7,0,0,4)]
    sources = {}
    for name, expected in SOURCE_HASHES.items():
        raw = (Path(source_root) / name).read_bytes()
        if digest(raw) != expected:
            raise ValueError("Original source hash differs: " + name)
        sources[name] = raw
    data = sources["files/DATA/OBJECTS.DKD"]
    entries = inspect_pair(sources["files/DATA/OBJECTS.DKX"], data)
    descriptor = next(entry for entry in entries if (entry["type"], entry["name"]) == (8, descriptor_name))
    descriptor_raw = resource_payload(descriptor, data)
    if digest(descriptor_raw) != descriptor_hash:
        raise ValueError("Ship descriptor differs from the proven source recipe")
    map_data = sources["installed/missions/maplib.dkd"]
    map_entries = inspect_pair(sources["installed/missions/maplib.dkx"], map_data)
    palette_entry = next(entry for entry in map_entries if (entry["type"], entry["name"]) == (1, "PALETTE"))
    palette = dib_palette(resource_payload(palette_entry, map_data))

    poses, images, plane_metadata = [], {}, {}
    for frame_index in range(POSE_COUNT):
        frame = decode_composite_frame(descriptor, data, entries, frame_index, mask)
        if (frame["width"], frame["height"], frame["frame_count"], frame["source_part_count"]) != (size, size, 152, 9):
            raise ValueError("Ship descriptor exceeds the bounded source pose layout")
        if [(part["source_index"], part["offset_x"], part["offset_y"], part["depth"])
                for part in frame["components"]] != parts:
            raise ValueError("Ship pose differs from the proven component recipe")
        components = []
        for part in frame["components"]:
            sprite = part["sprite"]
            image = base_palette_sprite(sprite, palette)
            if image.size != (size, size):
                raise ValueError("Ship component is outside the verified full component plane")
            name = part["name"]
            info = {key: sprite[key] for key in ("width", "height", "left", "top", "box_width", "box_height", "flags")}
            info.update(name=name, payload_sha256=part["payload_sha256"], rgba_sha256=digest(image.tobytes()))
            if name not in images:
                images[name], plane_metadata[name] = image, info
            elif info != plane_metadata[name] or image.tobytes() != images[name].tobytes():
                raise ValueError("A source component name produced conflicting planes")
            components.append({key: part[key] for key in
                               ("source_index", "name", "offset_x", "offset_y", "depth", "payload_sha256")})
        poses.append({"frame_index": frame_index, "logical_width": frame["width"],
                      "logical_height": frame["height"], "components": components,
                      "inline_draw_order": [part["source_index"] for part in frame["inline_components"]]})
    if len(images) != plane_count:
        raise ValueError("Unexpected unique source ship plane count")
    atlas = Image.new("RGBA", (columns * size, rows * size))
    planes = []
    # Dict insertion preserves first appearance in frame/source-part order.
    for index, (name, image) in enumerate(images.items()):
        x, top = index % columns * size, index // columns * size
        atlas.paste(image, (x, top))
        planes.append(dict(plane_metadata[name], atlas_x=x, atlas_y=atlas.height - top - image.height))
    metadata = {"schema_version": 1, "mission": "miss000", "instance_id": 13 if heavy else 11,
                "native_canvas_width": 1920, "native_canvas_height": 1080,
                "descriptor_resource": descriptor_name, "descriptor_payload_sha256": digest(descriptor_raw),
                "component_mask": mask, "pose_count": len(poses),
                "component_instance_count": sum(len(pose["components"]) for pose in poses),
                "plane_count": len(planes), "poses": poses, "planes": planes,
                "atlas_width": atlas.width, "atlas_height": atlas.height,
                "atlas_columns": columns, "atlas_rows": rows,
                "atlas_coordinate_origin": "bottom-left", "format": "RGBA32", "row_order": "bottom-to-top",
                "base_palette_sha256": digest(palette),
                "sources": {name: {"bytes": len(raw), "sha256": digest(raw)} for name, raw in sources.items()},
                "scope": ("Source0d full-health mask0xa3 poses0..87 for controlled fleet motion; no full mission simulation or final2026art" if heavy else "Source0b full-health mask0x83 poses0..87 for a controlled movement diagnostic; no full mission simulation or final2026art"),
                "excluded": ["other models and masks", "poses88..151", "damage and equipment changes",
                             "idle RNG initialization", "world scheduling", "wall-clock conversion"]}
    return {"ShipHeavyMovementRgba.bytes" if heavy else "ShipMovementRgba.bytes": bottom_up_rgba(atlas)}, metadata, atlas


def stage(source_root, project, *, replace_generated=False, preview=None):
    payloads, metadata, atlas = compose(source_root)
    report = write_payloads(Path(project) / "Assets/Resources/ShipMovementGenerated", payloads, metadata,
                            replace_generated, manifest_name=MANIFEST_NAME)
    if preview is not None:
        preview = Path(preview)
        preview.mkdir(parents=True, exist_ok=True)
        atlas.save(preview / "ship-movement-atlas.png")
        (preview / MANIFEST_NAME).write_text(json.dumps(report, indent=2) + "\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=ROOT / "reference/raw/ancient-conquest")
    parser.add_argument("--project", type=Path, default=ROOT / "Unity/AncientConquest")
    parser.add_argument("--replace-generated", action="store_true")
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args(argv)
    report = stage(args.source_root, args.project, replace_generated=args.replace_generated, preview=args.preview)
    print(json.dumps({key: report[key] for key in
                      ("pose_count", "component_instance_count", "plane_count", "payloads")}, indent=2))


if __name__ == "__main__":
    main()
