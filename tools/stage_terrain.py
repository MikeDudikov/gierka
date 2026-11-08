#!/usr/bin/env python3
"""Stage the source-derived static miss000 terrain, not a playable mission.

All original inputs are hash-guarded. Exact mfALibLoad names and source draw
order are retained. The world PALETTE is used without animation or lighting.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct

from PIL import Image

try:
    from .inspect_dkx import inspect_pair
    from .decode_sprite import decode_sprite, dib_palette, resource_payload
    from .render_reference_menu import indexed_dib
    from .inspect_world_reference import base_palette_sprite, used_palette_differences
    from .stage_unity_reference import bottom_up_rgba
except ImportError:
    from inspect_dkx import inspect_pair
    from decode_sprite import decode_sprite, dib_palette, resource_payload
    from render_reference_menu import indexed_dib
    from inspect_world_reference import base_palette_sprite, used_palette_differences
    from stage_unity_reference import bottom_up_rgba

ROOT = Path(__file__).resolve().parents[1]
LAYERS, LIBRARY_RECORD_SIZE = 8, 211
SOURCE_HASHES = {
    "installed/ancient.exe": "cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021",
    "installed/missions/maplib.dkx": "05484166ca374630f7c29c26e561656a11941ef331fb014e52f72aed81c23650",
    "installed/missions/maplib.dkd": "7fe0623d957e196e5279c6bced55db292648b5c9ebc6f1420fcd293c0685b685",
    "installed/missions/miss000.dkx": "b4b2fda60bb38e837b6d0548caa86229e1fbebf8cb9fd806c4f39c9bd75835ce",
    "installed/missions/miss000.dkd": "a77e801a93baafd6942db9087d7541f8c85ed2f3c88d440b9f9e81b45ba9a0d1",
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_sources(source_root):
    sources = {}
    for name, expected in SOURCE_HASHES.items():
        raw = (Path(source_root) / name).read_bytes()
        if digest(raw) != expected:
            raise ValueError("Original source hash differs: " + name)
        sources[name] = raw
    return sources


def parse_map(metadata_hex, raw):
    metadata = bytes.fromhex(metadata_hex)
    if len(metadata) < 8:
        raise ValueError("Truncated map metadata")
    width, height, tile_width, tile_height = struct.unpack_from("<4h", metadata)
    if min(width, height, tile_width, tile_height) <= 0 or max(width, height) > 4096:
        raise ValueError("Invalid map dimensions")
    if len(raw) != width * height * LAYERS * 2:
        raise ValueError("Planar map byte count mismatch")
    return {"map_width_cells": width, "map_height_cells": height,
            "tile_width": tile_width, "tile_height": tile_height, "layer_count": LAYERS}


def map_word(raw, geometry, x, y, layer):
    width, height = geometry["map_width_cells"], geometry["map_height_cells"]
    if not (0 <= x < width and 0 <= y < height and 0 <= layer < LAYERS):
        raise IndexError("Map coordinates outside source bounds")
    return struct.unpack_from("<H", raw, 2 * ((layer * height + y) * width + x))[0]


def rebuild_libraries(payload, metadata_hex, entries):
    """Port 5447b0/544710; never use serialized pointers as current addresses."""
    count = struct.unpack_from("<h", bytes.fromhex(metadata_hex))[0]
    if count < 0 or len(payload) != count * LIBRARY_RECORD_SIZE:
        raise ValueError("Library record count mismatch")
    resources = {}
    for entry in entries:
        key = entry["type"], entry["name"]
        if key in resources:
            raise ValueError("Ambiguous duplicate DKX resource")
        resources[key] = entry
    libraries, owners = [], {}
    for ordinal in range(count):
        record = payload[ordinal * LIBRARY_RECORD_SIZE:(ordinal + 1) * LIBRARY_RECORD_SIZE]
        prefix_bytes = record[8:40]
        if b"\0" not in prefix_bytes:
            raise ValueError("Unterminated library prefix")
        prefix = prefix_bytes.split(b"\0", 1)[0].decode("ascii", errors="strict")
        # A serialized owner could affect 544710's scan of later records. The
        # guarded original has no such candidates; refuse an unexplained variant.
        if struct.unpack_from("<I", record, 41)[0] and record[45] == 1:
            raise ValueError("Unexpected serialized library owner pointer")
        library = {"ordinal": ordinal, "library_id": record[0], "flags": record[1],
                   "prefix": prefix, "drawing_type": record[40], "frames": [],
                   "alias_of_ordinal": None, "enabled": record[1] < 0x80}
        if library["enabled"]:
            kind = library["drawing_type"]
            if kind not in (1, 4, 5, 6, 18):
                raise ValueError("Unsupported enabled library drawing type")
            key = prefix, kind
            if key in owners:
                owner = owners[key]
                library["frames"] = owner["frames"]
                library["alias_of_ordinal"] = owner["ordinal"]
            else:
                # Source5443e0 builds %s%03d, then5447b0 stops at first miss.
                number = 1
                while (kind, prefix + f"{number:03d}") in resources:
                    library["frames"].append(resources[kind, prefix + f"{number:03d}"])
                    number += 1
                owners[key] = library
        libraries.append(library)
    return libraries


def resolve_word(word, libraries):
    selector = word & 255
    if not selector:
        return None
    library = next((item for item in libraries if item["library_id"] == word >> 8), None)
    if library is None or not library["enabled"] or selector > len(library["frames"]):
        raise ValueError("Active map selector has no loaded library frame")
    return library, selector - 1, library["frames"][selector - 1]


def decode_frame(entry, data, palette):
    raw = resource_payload(entry, data)
    details = {"drawing_type": entry["type"], "name": entry["name"],
               "offset": entry["offset"], "stored_size": entry["stored_size"],
               "stored_sha256": entry["sha256"], "decoded_payload_sha256": digest(raw)}
    if entry["type"] == 1:
        size, indices, stored_palette = indexed_dib(raw)
        image = Image.frombytes("P", size, indices)
        image.putpalette(palette)
        image = image.convert("RGBA")  # All indices are opaque, including0/6.
        details.update(mode="opaque-index-copy", indices_sha256=digest(indices),
                       used_indices=sorted(set(indices)),
                       embedded_palette_used_index_mismatches=
                       used_palette_differences(indices, stored_palette, palette))
    elif entry["type"] == 6:
        sprite = decode_sprite(raw)
        if sprite["flags"] & 0x100:
            raise ValueError("Terrain sprite flag0x100 is outside verified path")
        image = base_palette_sprite(sprite, palette)
        details.update(mode="rle-coverage-index-copy", flags=sprite["flags"],
                       content_bounds=[sprite[key] for key in ("left", "top", "box_width", "box_height")],
                       indices_sha256=digest(sprite["indices"]),
                       coverage_sha256=digest(sprite["coverage"]),
                       used_indices=sorted({value for value, covered in
                                            zip(sprite["indices"], sprite["coverage"]) if covered}))
    else:
        raise ValueError("Active terrain uses unverified drawing type")
    details.update(width=image.width, height=image.height, rgba_top_down_sha256=digest(image.tobytes()))
    return image, details


def load_terrain(source_root):
    sources = checked_sources(source_root)
    mission_data, library_data = (sources["installed/missions/" + name + ".dkd"]
                                  for name in ("miss000", "maplib"))
    mission_entries = inspect_pair(sources["installed/missions/miss000.dkx"], mission_data)
    entries = inspect_pair(sources["installed/missions/maplib.dkx"], library_data)
    map_entry = next(item for item in mission_entries if (item["type"], item["name"]) == (17, "b_MAPA"))
    library_entry = next(item for item in entries if (item["type"], item["name"]) == (16, "b_ALIB"))
    palette_entry = next(item for item in entries if (item["type"], item["name"]) == (1, "PALETTE"))
    raw_map = resource_payload(map_entry, mission_data)
    geometry = parse_map(map_entry["metadata_hex"], raw_map)
    libraries = rebuild_libraries(resource_payload(library_entry, library_data), library_entry["metadata_hex"], entries)
    palette = dib_palette(resource_payload(palette_entry, library_data))
    return sources, raw_map, geometry, libraries, palette, library_data, (map_entry, library_entry, palette_entry)


def compose_terrain(source_root):
    sources, raw_map, geometry, libraries, palette, data, resource_entries = load_terrain(source_root)
    width, height = geometry["map_width_cells"], geometry["map_height_cells"]
    tw, th = geometry["tile_width"], geometry["tile_height"]
    world = Image.new("RGBA", (width * tw, height * th))
    layers = [Image.new("RGBA", world.size) for _ in range(LAYERS)]
    frames, trace, counts = {}, [], [0] * LAYERS
    # Source519b50/51a0b0: x outer, y inner, then5196e0 layers0..7.
    for x in range(width):
        for y in range(height):
            for layer in range(LAYERS):
                word = map_word(raw_map, geometry, x, y, layer)
                resolved = resolve_word(word, libraries)
                if resolved is None:
                    continue
                library, frame_index, entry = resolved
                key = entry["type"], entry["name"]
                if key not in frames:
                    frames[key] = decode_frame(entry, data, palette)
                image, info = frames[key]
                if image.size != (tw, th):
                    raise ValueError("Active frame extends beyond verified cell-size scope")
                world.alpha_composite(image, (x * tw, y * th))
                layers[layer].alpha_composite(image, (x * tw, y * th))
                trace.append({"draw_index": len(trace), "x": x, "y": y, "layer": layer,
                              "word": word, "library_id": library["library_id"],
                              "library_ordinal": library["ordinal"], "selector": word & 255,
                              "frame_index": frame_index, "drawing_type": entry["type"],
                              "name": entry["name"], "destination": [x * tw, y * th],
                              "rgba_top_down_sha256": info["rgba_top_down_sha256"]})
                counts[layer] += 1
    if world.getextrema()[3] != (255, 255):
        raise ValueError("Static terrain has uncovered world pixels")
    active_ids = sorted({row["library_id"] for row in trace})
    metadata = {"schema_version": 1, "mission": "miss000", **geometry,
        "native_canvas_width": 1920, "native_canvas_height": 1080,
        "native_canvas_meaning": "reference output contract; not source FOV or world dimensions",
        "world_width_px": world.width, "world_height_px": world.height,
        "source_rgba_width": world.width, "source_rgba_height": world.height,
        "format": "RGBA32", "row_order": "bottom-to-top", "map_byte_order": "little-endian",
        "map_layout": "8 planar uint16 layers; offset=2*((layer*height+y)*width+x)",
        "draw_order": "x outer, y inner, layer0..7; every sprite full-plane anchored at cellbase",
        "state": "static base-PALETTE terrain; no object simulation",
        "active_counts_by_layer": counts, "draw_count": len(trace), "unique_frame_count": len(frames),
        "palette_rgb_sha256": digest(palette),
        "sources": [{"path": name, "bytes": len(raw), "sha256": digest(raw)} for name, raw in sources.items()],
        "map_resource": resource_entries[0], "library_resource": resource_entries[1],
        "palette_resource": resource_entries[2],
        "active_libraries": [{key: value for key, value in library.items() if key != "frames"} |
                             {"loaded_frame_count": len(library["frames"])} for library in libraries
                             if library["library_id"] in active_ids],
        "frames": [frames[key][1] for key in sorted(frames)], "draw_trace": trace,
        "source_code_evidence": {
            "library_loader": "0x5447b0; alias0x544710; frame-name formatter0x5443e0 (%s%03d from001)",
            "map_accessor": "0x545190 ->0x544fc0 ->0x544ba0 ->0x544c10 ->0x55b440",
            "draw_order": "0x519b50/0x51a0b0 x then y;0x5196e0 layers0..7",
            "dib": "0x4e9370 ->0x562230 ->0x561ed0 ->0x562700; opaque index copy",
            "sprite": "0x4e9370 ->0x562260 ->0x574290 ->0x574d50; RLE coverage only",
            "palette": "InitMapaBig0x51bcb0 selects maplib type1 PALETTE; static base state"},
        "limitations": ["Reference terrain only; not a playable or complete mission",
                        "Static map-selected bitmap state; no animated palette, lighting, fog or dynamic redraw",
                        "LIST_OBJ/OBJ_* objects, units, UI, AI and gameplay are not drawn",
                        "Source64x64 art retained; this is not final2026 artwork",
                        "Output1920x1080 does not establish original camera framing or remake FOV",
                        "No screenshot comparison with the running original game"]}
    return world, layers, raw_map, metadata


def write_payloads(output, terrain, raw_map, metadata, replace_generated=False):
    output = Path(output).absolute()
    if output.resolve() != output:
        raise ValueError("Generated output must not contain symlinks")
    payloads = {"TerrainRgba.bytes": bottom_up_rgba(terrain), "MapPlanar.bytes": raw_map}
    metadata = dict(metadata, payloads={name: {"bytes": len(raw), "sha256": digest(raw)}
                                       for name, raw in payloads.items()})
    files = dict(payloads, **{"TerrainManifest.json": (json.dumps(metadata, indent=2) + "\n").encode()})
    if any((output / name).is_symlink() for name in files):
        raise ValueError("Generated files must not be symlinks")
    changed = [name for name, raw in files.items() if (output / name).exists()
               and (output / name).read_bytes() != raw]
    if changed and not replace_generated:
        raise FileExistsError("Changed terrain data requires explicit --replace-generated")
    if changed:
        old = json.loads((output / "TerrainManifest.json").read_text())
        if set(old["payloads"]) != set(payloads):
            raise ValueError("Previous terrain manifest has unexpected payloads")
        for name, entry in old["payloads"].items():
            path = output / name
            if path.is_symlink() or not path.is_file() or digest(path.read_bytes()) != entry["sha256"]:
                raise ValueError("Previous generated terrain hash mismatch")
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


def stage_terrain(source_root, project, *, replace_generated=False, preview=None):
    terrain, layers, raw_map, metadata = compose_terrain(source_root)
    report = write_payloads(Path(project) / "Assets/Resources/TerrainGenerated", terrain,
                            raw_map, metadata, replace_generated)
    if preview is not None:
        preview = Path(preview)
        preview.mkdir(parents=True, exist_ok=True)
        terrain.save(preview / "terrain-static-base-palette.png")
        for number, image in enumerate(layers):
            image.save(preview / f"layer-{number}.png")
        (preview / "TerrainManifest.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def original_lookup_oracle(source_root):
    """Run original545190 and all lookup callees, with no intercepted code.

    Only the in-memory library/DArray construction is supplied by this tool.
    Resource decoding and mfALibLoad itself are not executed by this oracle.
    Returns 5-byte <HhB rows in x/y/layer draw order: original word, selected
    zero-based frame index (-1 for no bitmap), returned drawing type (255 null).
    """
    import pefile
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
    from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX, UC_X86_REG_EIP

    sources, raw_map, geometry, libraries, _, _, _ = load_terrain(source_root)
    pe = pefile.PE(data=sources["installed/ancient.exe"])
    if pe.OPTIONAL_HEADER.ImageBase != 0x400000:
        raise ValueError("Unexpected original image base")
    image = pe.get_memory_mapped_image()
    engine = Uc(UC_ARCH_X86, UC_MODE_32)
    engine.mem_map(0x400000, (len(image) + 0xfff) & ~0xfff)
    engine.mem_write(0x400000, image)
    engine.mem_map(0x70000000, 0x100000)
    engine.mem_map(0x7ff00000, 0x100000)
    map_address, library_address, type_address, stop = 0x70000000, 0x70010000, 0x700ff000, 0x700ff100
    engine.mem_write(map_address, struct.pack("<4h", *[geometry[key] for key in
        ("map_width_cells", "map_height_cells", "tile_width", "tile_height")]) + raw_map)
    engine.mem_write(library_address, struct.pack("<II", len(libraries), 0))
    cursor, tags, owners = 0x70020000, {}, {}
    for library in libraries:
        record = bytearray(LIBRARY_RECORD_SIZE)
        record[0], record[40] = library["library_id"], library["drawing_type"]
        array = 0
        if library["enabled"]:
            if library["alias_of_ordinal"] is not None:
                array = owners[library["alias_of_ordinal"]]
            else:
                array = cursor
                cursor += 32 + 4 * len(library["frames"])
                engine.mem_write(array, struct.pack("<8I", 0, 0, 4,
                    len(library["frames"]), len(library["frames"]), 10, 0, array + 32))
                for index, entry in enumerate(library["frames"]):
                    tag = 0x73000000 + 16 * (len(tags) + 1)
                    tags[tag] = (index, entry["type"], entry["name"])
                    engine.mem_write(array + 32 + 4 * index, struct.pack("<I", tag))
                owners[library["ordinal"]] = array
        struct.pack_into("<I", record, 41, array)
        engine.mem_write(library_address + 8 + library["ordinal"] * LIBRARY_RECORD_SIZE, bytes(record))
    if cursor >= type_address:
        raise ValueError("Oracle library memory exceeds reserved range")

    def execute(x, y, layer):
        stack = 0x7ffff000
        engine.mem_write(type_address, b"\x7e")
        engine.mem_write(stack, struct.pack("<8I", stop, map_address, library_address,
                         x & 0xffffffff, y & 0xffffffff, layer & 0xffffffff, type_address, 0))
        engine.reg_write(UC_X86_REG_ESP, stack)
        engine.emu_start(0x545190, stop, count=4000)
        if engine.reg_read(UC_X86_REG_EIP) != stop:
            raise ValueError("Original map lookup did not return within instruction bound")
        pointer = engine.reg_read(UC_X86_REG_EAX)
        drawing_type = bytes(engine.mem_read(type_address, 1))[0]
        if pointer:
            if pointer not in tags or drawing_type != tags[pointer][1]:
                raise ValueError("Original map lookup returned unknown bitmap/type")
            return tags[pointer][0], drawing_type, tags[pointer][2]
        if drawing_type != 0x7e:
            raise ValueError("Null lookup unexpectedly changed drawing type")
        return -1, 255, None

    rows, active = bytearray(), 0
    for x in range(geometry["map_width_cells"]):
        for y in range(geometry["map_height_cells"]):
            for layer in range(LAYERS):
                index, kind, name = execute(x, y, layer)
                word = map_word(raw_map, geometry, x, y, layer)
                resolved = resolve_word(word, libraries)
                predicted = (-1, 255, None) if resolved is None else (
                    resolved[1], resolved[2]["type"], resolved[2]["name"])
                if (index, kind, name) != predicted:
                    raise ValueError(f"Original map lookup differs at{x},{y},{layer}")
                rows.extend(struct.pack("<HhB", word, index, kind))
                active += index >= 0
    bounds = [(-1, 0, 0), (24, 0, 0), (0, -1, 0), (0, 24, 0), (0, 0, -1), (0, 0, 8)]
    if any(execute(*case) != (-1, 255, None) for case in bounds):
        raise ValueError("Original lookup accepted out-of-bounds coordinate")
    report = {"schema_version": 1, "original_exe_sha256": SOURCE_HASHES["installed/ancient.exe"],
              "map_sha256": digest(raw_map), "cases": len(rows) // 5, "active_cases": active,
              "bounds_cases": len(bounds), "row_format": "<HhB: word, frame_index(-1 null), drawing_type(255 null)",
              "row_order": "x outer, y inner, layer0..7", "rows_sha256": digest(rows),
              "entry_va": "0x00545190", "intercepted_functions": [],
              "scope": "Original accessor code and callees; reconstructed runtime libraries/DArray inputs, loader excluded"}
    return bytes(rows), report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=ROOT / "reference/raw/ancient-conquest")
    parser.add_argument("--project", type=Path, default=ROOT / "Unity/AncientConquest")
    parser.add_argument("--replace-generated", action="store_true")
    parser.add_argument("--preview", type=Path)
    parser.add_argument("--lookup-proof", type=Path, help="Also run original x86 lookup and write evidence here")
    args = parser.parse_args(argv)
    report = stage_terrain(args.source_root, args.project, replace_generated=args.replace_generated,
                           preview=args.preview)
    if args.lookup_proof is not None:
        rows, proof = original_lookup_oracle(args.source_root)
        args.lookup_proof.mkdir(parents=True, exist_ok=True)
        (args.lookup_proof / "original-lookup.bin").write_bytes(rows)
        (args.lookup_proof / "original-lookup.json").write_text(json.dumps(proof, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("draw_count", "unique_frame_count", "payloads")}, indent=2))


if __name__ == "__main__":
    main()
