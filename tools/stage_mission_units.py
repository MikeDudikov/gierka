#!/usr/bin/env python3
"""Stage eight source ship references and occupancy flags, without simulation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

from PIL import Image

try:
    from .stage_mission_objects import SOURCE_HASHES, digest, pack_seeds, write_payloads
    from .stage_terrain import parse_map, map_word, LIBRARY_RECORD_SIZE
    from .stage_unity_reference import bottom_up_rgba
    from .inspect_dkx import inspect_pair
    from .decode_sprite import resource_payload, dib_palette
    from .inspect_world_reference import base_palette_sprite
    from .decode_composite_sprite import decode_composite_frame
except ImportError:
    from stage_mission_objects import SOURCE_HASHES, digest, pack_seeds, write_payloads
    from stage_terrain import parse_map, map_word, LIBRARY_RECORD_SIZE
    from stage_unity_reference import bottom_up_rgba
    from inspect_dkx import inspect_pair
    from decode_sprite import resource_payload, dib_palette
    from inspect_world_reference import base_palette_sprite
    from decode_composite_sprite import decode_composite_frame

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_NAME = "MissionUnitsManifest.json"
# The renderer accepts these proven source combinations, not guessed filenames
# for other models, owners, damaged states or customization.
SHIP_DESCRIPTORS = {(0, 1, 1): "SHIP_A1110", (7, 1, 1): "SHIP_H1110",
                    (1, 4, 0): "SHIP_B4400", (6, 4, 0): "SHIP_G4400"}


def cell_flags(raw_map, geometry, library_payload):
    if len(library_payload) % LIBRARY_RECORD_SIZE:
        raise ValueError("Truncated source library descriptors")
    categories = {}
    for offset in range(0, len(library_payload), LIBRARY_RECORD_SIZE):
        record = library_payload[offset:offset + LIBRARY_RECORD_SIZE]
        categories.setdefault(record[0], struct.unpack_from("<I", record, 4)[0])
    result = []
    for y in range(geometry["map_height_cells"]):
        for x in range(geometry["map_width_cells"]):
            flags = 0
            for layer in range(8):
                word = map_word(raw_map, geometry, x, y, layer)
                if word & 255:
                    if word >> 8 not in categories:
                        raise ValueError("Active terrain selector has no source category")
                    shift = layer * 4
                    # The source does not mask category to one nibble before OR.
                    flags = ((flags & ~(15 << shift)) | categories[word >> 8] << shift) & 0xffffffff
            result.append(flags)
    return struct.pack("<" + "I" * len(result), *result)


def ship_recipe(record, raw):
    if record["class_tag"] != 200:
        raise ValueError("Expected a source ShipClassTy seed")
    if len(raw) != 616 or struct.unpack_from("<I", raw, 16)[0] != 0:
        raise ValueError("Only the source ship mode0 layout is supported")
    model_value = struct.unpack_from("<I", raw, 28)[0]
    side, player, model = raw[20], raw[24], model_value & 255
    cell_x, cell_y = struct.unpack_from("<ii", raw, 36)
    heading = struct.unpack_from("<b", raw, 44)[0]
    health = struct.unpack_from("<i", raw, 48)[0]
    orders = struct.unpack_from("<I", raw, 512)[0]
    if health != 100 or orders != 0:
        raise ValueError("Frozen ship reference requires source full-health/no-order setup")
    if (model, side, player) not in SHIP_DESCRIPTORS or model_value != model:
        raise ValueError("Ship reference combination has no verified graphics recipe")
    equipment_b = (raw[56] - 3) & 255
    mask = (0x83 | ({1: 0x20, 2: 0x40}.get(raw[60], 0)) |
            ({1: 8, 2: 0x10}.get(equipment_b, 0)))
    return {"resource_name": record["resource_name"], "instance_id": record["instance_id"],
            "seed_payload_sha256": digest(raw), "owner_side": side, "owner_player": player,
            "model_value": model_value, "model_variant": model, "runtime_class_tag": (model_value + 200) & 0xffffffff,
            "cell_x": cell_x, "cell_y": cell_y, "heading": heading,
            "requested_health_percent": health, "source_order_count": orders,
            "descriptor_resource": SHIP_DESCRIPTORS[model, side, player],
            "reference_state": 1, "reference_frame_index": heading << 2, "component_mask": mask}


def compose(source_root):
    sources = {}
    for name, expected in SOURCE_HASHES.items():
        raw = (Path(source_root) / name).read_bytes()
        if digest(raw) != expected:
            raise ValueError("Original source hash differs: " + name)
        sources[name] = raw
    mission_data = sources["installed/missions/miss000.dkd"]
    mission_entries = inspect_pair(sources["installed/missions/miss000.dkx"], mission_data)
    map_data = sources["installed/missions/maplib.dkd"]
    map_entries = inspect_pair(sources["installed/missions/maplib.dkx"], map_data)
    object_data = sources["files/DATA/OBJECTS.DKD"]
    object_entries = inspect_pair(sources["files/DATA/OBJECTS.DKX"], object_data)
    maps = {(e["type"], e["name"]): e for e in map_entries}
    mission = {(e["type"], e["name"]): e for e in mission_entries}
    objects = {(e["type"], e["name"]): e for e in object_entries}
    map_entry = mission[17, "b_MAPA"]
    raw_map = resource_payload(map_entry, mission_data)
    geometry = parse_map(map_entry["metadata_hex"], raw_map)
    flags = cell_flags(raw_map, geometry, resource_payload(maps[16, "b_ALIB"], map_data))
    palette = dib_palette(resource_payload(maps[1, "PALETTE"], map_data))
    blob, records = pack_seeds([(e["name"], resource_payload(e, mission_data), e)
                               for e in mission_entries if e["type"] == 12 and e["name"].startswith("OBJ_")])
    ships, images = [], {}
    for record in records:
        if record["class_tag"] != 200:
            continue
        raw = blob[record["payload_offset"]:record["payload_offset"] + record["payload_length"]]
        ship = ship_recipe(record, raw)
        frame = decode_composite_frame(objects[8, ship["descriptor_resource"]], object_data, object_entries,
                                       ship["reference_frame_index"], ship["component_mask"])
        width, height = frame["width"], frame["height"]
        # Real source logical dimensions are even; the C# adapter separately
        # verifies signed x86 wrapping and truncation for stress dimensions.
        ship.update(logical_width=width, logical_height=height,
                    world_pixel_x=ship["cell_x"] * 64 + int((64 - width) / 2),
                    world_pixel_y=ship["cell_y"] * 64 + int((64 - height) / 2))
        ship["reference_depth"] = max(10000, 20000 - height - ship["world_pixel_y"])
        ship["inline_draw_order"] = [part["source_index"] for part in frame["inline_components"]]
        selected = []
        for component in frame["components"]:
            name = component["name"]
            image = base_palette_sprite(component["sprite"], palette)
            if name not in images:
                images[name] = image
            elif image.tobytes() != images[name].tobytes():
                raise ValueError("A source component name produced conflicting pixels")
            selected.append({key: component[key] for key in
                             ("name", "source_index", "offset_x", "offset_y", "depth", "payload_sha256")})
        ship["components"] = selected
        ships.append(ship)
    if len(ships) != 8:
        raise ValueError("Unexpected source ship cohort")
    # This recipe covers the verified initialization sequence: all eight
    # detached shadows have level21000; equal-depth registration is reversed
    # by the original render traversal. Parent levels are distinct here.
    shadows = [(ship, part) for ship in ships for part in ship["components"] if part["depth"] < 0]
    if any(part["depth"] != -21000 for _, part in shadows):
        raise ValueError("Detached source component is outside the verified shadow order")
    if len({ship["reference_depth"] for ship in ships}) != len(ships):
        raise ValueError("Frozen ship parent order requires a verified tie recipe")
    draw_order = [{"instance_id": ship["instance_id"], "source_index": part["source_index"], "depth": 21000}
                  for ship, part in reversed(shadows)]
    for ship in sorted(ships, key=lambda item: item["reference_depth"], reverse=True):
        draw_order.extend({"instance_id": ship["instance_id"], "source_index": index,
                           "depth": ship["reference_depth"]} for index in ship["inline_draw_order"])
    atlas = Image.new("RGBA", (sum(i.width for i in images.values()), max(i.height for i in images.values())))
    if atlas.width > 8192 or atlas.height > 8192:
        raise ValueError("Reference components exceed the bounded atlas")
    frames, cursor = [], 0
    for name, image in images.items():
        atlas.paste(image, (cursor, 0))
        frames.append({"name": name, "atlas_x": cursor, "atlas_y": 0, "width": image.width,
                       "height": image.height, "rgba_sha256": digest(image.tobytes())})
        cursor += image.width
    metadata = {"schema_version": 1, "mission": "miss000", "native_canvas_width": 1920,
                "native_canvas_height": 1080, "map_width_cells": geometry["map_width_cells"],
                "map_height_cells": geometry["map_height_cells"], "ship_count": len(ships),
                "component_instance_count": sum(len(s["components"]) for s in ships),
                "ships": ships, "frames": frames, "draw_order": draw_order,
                "draw_order_scope": "Source eight-ship frozen initialization; no full-world ordering/fog lifecycle",
                "atlas_width": atlas.width, "atlas_height": atlas.height,
                "format": "RGBA32", "row_order": "bottom-to-top", "cell_flags_layout": "uint32LE, y outer/x inner",
                "sources": {name: {"bytes": len(raw), "sha256": digest(raw)} for name, raw in sources.items()},
                "base_palette_sha256": digest(palette),
                "scope": "Frozen full-health/no-order source ship references; no constructors, simulation, fog or final2026art"}
    return {"CellFlags.bytes": flags, "ShipComponentsRgba.bytes": bottom_up_rgba(atlas)}, metadata, atlas


def stage(source_root, project, *, replace_generated=False, preview=None):
    payloads, metadata, atlas = compose(source_root)
    report = write_payloads(Path(project) / "Assets/Resources/MissionUnitsGenerated", payloads, metadata,
                            replace_generated, manifest_name=MANIFEST_NAME)
    if preview is not None:
        preview = Path(preview)
        preview.mkdir(parents=True, exist_ok=True)
        atlas.save(preview / "ship-components.png")
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
    print(json.dumps({key: report[key] for key in ("ship_count", "component_instance_count", "payloads")}, indent=2))


if __name__ == "__main__":
    main()
