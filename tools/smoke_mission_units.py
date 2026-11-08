#!/usr/bin/env python3
"""Observe eight frozen source ship references in a real Windows Mono player.

Three isolated Wine/Xvfb sessions cover all eight complete ship planes.
Expected pixels come from pinned source seeds, original type8/RLE resources
and native-order fixtures, independently of renderer placement declarations.
No OS input, constructors, animation, simulation or playable mission is tested.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import time

from PIL import Image, ImageChops, ImageStat

if __package__:
    from . import smoke_native_menu as menu, smoke_terrain as terrain, smoke_mission_objects as objects
    from .decode_composite_sprite import decode_composite_frame
    from .decode_sprite import dib_palette, resource_payload
    from .inspect_dkx import inspect_pair
    from .inspect_world_reference import base_palette_sprite
    from .stage_mission_objects import SOURCE_HASHES
    from .validate_mission_ship_seed import FIXTURE as SHIP_FIXTURE, FIXTURE_SHA256 as SHIP_FIXTURE_SHA256
else:
    import smoke_native_menu as menu
    import smoke_terrain as terrain
    import smoke_mission_objects as objects
    from decode_composite_sprite import decode_composite_frame
    from decode_sprite import dib_palette, resource_payload
    from inspect_dkx import inspect_pair
    from inspect_world_reference import base_palette_sprite
    from stage_mission_objects import SOURCE_HASHES
    from validate_mission_ship_seed import FIXTURE as SHIP_FIXTURE, FIXTURE_SHA256 as SHIP_FIXTURE_SHA256

MANIFEST = menu.REPOSITORY / "Unity/AncientConquest/Assets/Resources/MissionUnitsGenerated/MissionUnitsManifest.json"
MANIFEST_SHA256 = "2ec3b9ef431b1a36f1d267740605d2a2334988d1da2747160af69a081294fe2e"
COMPOSITE_FIXTURE = menu.REPOSITORY / "tests/fixtures/composite_original_selection.json"
COMPOSITE_FIXTURE_SHA256 = "25e59c7365666e669edb6705b9c85fd5947cae5ba9c016a3563411a6d0818e50"
ORDER_FIXTURE = menu.REPOSITORY / "tests/fixtures/mission_ship_world_order.json"
ORDER_FIXTURE_SHA256 = "0ee61b970675c19a0cdfc021ba223752d6694721074cbba0c900dd428f2be0c6"
SOURCE_ROOT = menu.REPOSITORY / "reference/raw/ancient-conquest"
EXECUTABLE, ASSEMBLY, LAUNCHER = terrain.EXECUTABLE, terrain.ASSEMBLY, terrain.LAUNCHER
SIZE, EXIT_AFTER = terrain.SIZE, terrain.EXIT_AFTER
READY = "Mission unit reference ready: state=1; frozen=True; renderers=29; full_world_order=False"
CLEANUP = "Mission unit reference cleanup: claimed_released=8; visual_refs_cleared=True"
PINNED_PAYLOADS = {
    "CellFlags.bytes": (2304, "eb8c22b2dc3a3d6de5be5c5a28560701333cbc8610e8dd687052f4f93b260283"),
    "ShipComponentsRgba.bytes": (317952, "b5fe5fd59554f82ca710a9fdce4999ca7044b7c5dddb52e724dafbfb79de284c"),
}
CASES = (
    {"name": "home-fleet", "requested": (9, 0), "actual": (9, 0), "visible_ids": (11, 12, 13)},
    {"name": "south-fleet", "requested": (0, 15), "actual": (0, 15), "visible_ids": (16, 39, 40)},
    {"name": "adjacent-ships", "requested": (0, 10), "actual": (0, 10), "visible_ids": (41, 42)},
)
# These four exact combinations were observed in original4e1bb0/4e0120.
# The native type8 fixture independently verifies each descriptor/mask/frame.
SOURCE_GRAPHICS = {(0, 1, 1): "SHIP_A1110", (7, 1, 1): "SHIP_H1110",
                   (1, 4, 0): "SHIP_B4400", (6, 4, 0): "SHIP_G4400"}
LIMITATIONS = [
    "Windows Mono player under Wine/Xvfb; native Windows11 and target laptop not tested",
    "Eight frozen full-health/no-order ship references and five frozen reefs; not complete initial world state",
    "Source component sprites, masks, anchors and known-cohort ordering only; other classes, fog and full-world order excluded",
    "Partial576-cell occupancy grid with8claims and cleanup; no original constructors, movement, collision lifecycle or simulation",
    "No OS input, navigation, panning, animation, AI, mission audio or playable mission validated",
    "Timed diagnostic Application.Quit(0) is not evidence for the product/menu Quit callback",
    "Source base-palette art is a fidelity reference, not final2026art or target hardware performance proof",
    "Image comparisons can prove ordering only where source alpha coverage makes order observable",
]
require = menu.require


def pinned_json(path, expected):
    require(path.is_file() and not path.is_symlink(), "Missing/symbolic pinned fixture: " + str(path))
    require(menu.file_sha256(path) == expected, "Pinned fixture/manifest changed: " + str(path))
    return json.loads(path.read_text())


def provenance():
    result = objects.provenance()
    files = {"units_manifest": MANIFEST, "qa_helper": Path(__file__).resolve(), "native_ship_seed_fixture": SHIP_FIXTURE,
             "native_type8_fixture": COMPOSITE_FIXTURE, "native_world_order_fixture": ORDER_FIXTURE}
    files.update({name: MANIFEST.parent / name for name in PINNED_PAYLOADS})
    files.update({"source:" + name: SOURCE_ROOT / name for name in SOURCE_HASHES})
    for label, path in files.items():
        require(path.is_file() and not path.is_symlink(), "Missing/symbolic reference: " + str(path))
        result[label] = {"path": str(path), "bytes": path.stat().st_size, "sha256": menu.file_sha256(path)}
    return result


def native_frame_proof(fixture, descriptor, mask, frame):
    matches = [row for case in fixture["cases"] if case["descriptor"] == descriptor and case["mask"] == mask
               for row in case["frames"] if row["frame_index"] == frame["frame_index"]]
    require(len(matches) == 1, "Missing/ambiguous original type8 frame proof")
    native = matches[0]
    components = [{key: component[key] for key in ("name", "offset_x", "offset_y", "depth")}
                  for component in frame["components"]]
    require(native["components"] == components, "Decoded type8 selection differs from executed native loader")
    require(native["inline_names"] == [component["name"] for component in frame["inline_components"]],
            "Type8 inline draw order differs from native frame proof")


def load_reference():
    base = objects.load_reference()
    manifest = pinned_json(MANIFEST, MANIFEST_SHA256)
    seeds = pinned_json(SHIP_FIXTURE, SHIP_FIXTURE_SHA256)
    composite_proof = pinned_json(COMPOSITE_FIXTURE, COMPOSITE_FIXTURE_SHA256)
    order_proof = pinned_json(ORDER_FIXTURE, ORDER_FIXTURE_SHA256)
    require((manifest["schema_version"], manifest["mission"], manifest["native_canvas_width"],
             manifest["native_canvas_height"], manifest["map_width_cells"], manifest["map_height_cells"],
             manifest["ship_count"], manifest["component_instance_count"], manifest["atlas_width"],
             manifest["atlas_height"], manifest["format"], manifest["row_order"])
            == (1, "miss000", 1920, 1080, 24, 24, 8, 29, 1104, 72, "RGBA32", "bottom-to-top"),
            "Unit manifest geometry/scope changed")
    payloads = dict(base["payloads"])
    raw_payloads = {}
    for name, (length, digest) in PINNED_PAYLOADS.items():
        path = MANIFEST.parent / name
        require(path.is_file() and not path.is_symlink(), "Missing/symbolic unit payload: " + name)
        raw = path.read_bytes()
        require(len(raw) == length == manifest["payloads"][name]["bytes"], "Unit payload length changed: " + name)
        require(hashlib.sha256(raw).hexdigest() == digest == manifest["payloads"][name]["sha256"],
                "Unit payload SHA changed: " + name)
        payloads[name] = {"bytes": len(raw), "sha256": digest}
        raw_payloads[name] = raw
    source_data = {}
    for name, digest in SOURCE_HASHES.items():
        path = SOURCE_ROOT / name
        require(path.is_file() and not path.is_symlink(), "Missing/symbolic original source: " + name)
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == digest, "Original source changed: " + name)
        source_data[name] = raw
    object_data = source_data["files/DATA/OBJECTS.DKD"]
    object_entries = inspect_pair(source_data["files/DATA/OBJECTS.DKX"], object_data)
    resources = {(entry["type"], entry["name"]): entry for entry in object_entries}
    map_data = source_data["installed/missions/maplib.dkd"]
    map_entries = inspect_pair(source_data["installed/missions/maplib.dkx"], map_data)
    palette = dib_palette(resource_payload(next(entry for entry in map_entries
                          if (entry["type"], entry["name"]) == (1, "PALETTE")), map_data))
    require(hashlib.sha256(palette).hexdigest() == manifest["base_palette_sha256"], "World base palette changed")
    atlas = Image.frombytes("RGBA", (1104, 72), raw_payloads["ShipComponentsRgba.bytes"]).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    staged_frames = {frame["name"]: frame for frame in manifest["frames"]}
    require(len(staged_frames) == len(manifest["frames"]) == 17, "Atlas frame names are missing/duplicated")
    staged_ships = {ship["instance_id"]: ship for ship in manifest["ships"]}
    require(len(staged_ships) == len(manifest["ships"]) == 8, "Ship declarations are missing/duplicated")
    ships, unique_frames = {}, {}
    object_manifest = json.loads(objects.MANIFEST.read_text())
    blob = (objects.MANIFEST.parent / "ObjectSeeds.bytes").read_bytes()
    source_seed_bytes = {record["instance_id"]: blob[record["payload_offset"]:
                         record["payload_offset"] + record["payload_length"]] for record in object_manifest["records"]}
    for native in seeds["records"]:
        identifier = native["instance_id"]
        require(identifier not in ships, "Duplicate native ship ID")
        raw = bytes.fromhex(native["payload_hex"])
        require(raw == source_seed_bytes[identifier] and hashlib.sha256(raw).hexdigest() == native["payload_sha256"],
                "Staged source seed differs from original initialization fixture")
        require(len(raw) == 616 and struct.unpack_from("<I", raw, 16)[0] == 0, "Ship seed is not the observed mode0")
        side, player, variant = raw[20], raw[24], raw[28]
        x, y = struct.unpack_from("<ii", raw, 36)
        heading = struct.unpack_from("<b", raw, 44)[0]
        require((x, y, side, player, variant, heading) ==
                (native["cell_x"], native["cell_y"], native["owner_side"], native["owner_player"],
                 native["model_variant"], native["heading"]), "Native seed fields/bytes disagree")
        require(native["requested_health_percent"] == 100 and native["source_order_count"] == 0,
                "Reference requires the observed full-health/no-order source cohort")
        descriptor = SOURCE_GRAPHICS[variant, side, player]
        equipment_b = (raw[56] - 3) & 255
        mask = 0x83 | {1: 0x20, 2: 0x40}.get(raw[60], 0) | {1: 8, 2: 0x10}.get(equipment_b, 0)
        frame = decode_composite_frame(resources[8, descriptor], object_data, object_entries, heading << 2, mask)
        native_frame_proof(composite_proof, descriptor, mask, frame)
        width, height = frame["width"], frame["height"]
        world_x, world_y = x * 64 + int((64 - width) / 2), y * 64 + int((64 - height) / 2)
        depth = max(10000, 20000 - height - world_y)
        ship = {"instance_id": identifier, "resource_name": native["resource_name"], "cell": (x, y),
                "model": variant, "owner_side": side, "owner_player": player, "heading": heading,
                "frame_index": heading << 2, "mask": mask, "descriptor": descriptor,
                "world_pixel": (world_x, world_y), "width": width, "height": height,
                "reference_depth": depth, "parts": [], "inline_order": [part["source_index"] for part in frame["inline_components"]]}
        staged = staged_ships[identifier]
        expected_fields = {"cell_x": x, "cell_y": y, "owner_side": side, "owner_player": player,
                           "model_variant": variant, "heading": heading, "reference_frame_index": heading << 2,
                           "component_mask": mask, "world_pixel_x": world_x, "world_pixel_y": world_y,
                           "logical_width": width, "logical_height": height, "reference_state": 1,
                           "descriptor_resource": descriptor, "reference_depth": depth}
        require(all(staged[key] == value for key, value in expected_fields.items()),
                "Staged ship recipe differs from independent source/native fixture")
        alpha = Image.new("L", (width, height))
        for component in frame["components"]:
            image = base_palette_sprite(component["sprite"], palette)
            require(image.size == (width, height) and (component["offset_x"], component["offset_y"]) == (0, 0),
                    "Source cohort left its verified full-plane component contract")
            require(set(image.getchannel("A").getdata()).issubset({0, 255}), "Fractional source component alpha")
            saved = staged_frames[component["name"]]
            rect = (saved["atlas_x"], saved["atlas_y"], saved["atlas_x"] + saved["width"],
                    saved["atlas_y"] + saved["height"])
            require(atlas.crop(rect).tobytes() == image.tobytes(), "Staged atlas component differs from source decoder")
            require(hashlib.sha256(image.tobytes()).hexdigest() == saved["rgba_sha256"], "Component plane hash changed")
            unique_frames[component["name"]] = image
            alpha = ImageChops.lighter(alpha, image.getchannel("A"))
            ship["parts"].append({"kind": "ship", "instance_id": identifier,
                "source_index": component["source_index"], "name": component["name"],
                "depth": -component["depth"] if component["detached"] else depth,
                "local_depth": component["depth"], "detached": component["detached"],
                "x": world_x + component["offset_x"], "y": world_y + component["offset_y"], "image": image})
        ship["alpha"] = alpha
        ships[identifier] = ship
    require(tuple(ships) == (11, 12, 13, 16, 39, 40, 41, 42), "Native ship cohort/order changed")
    require(len(unique_frames) == 17 and sum(len(ship["parts"]) for ship in ships.values()) == 29,
            "Source-selected frame/component count changed")
    reefs = {reef["name"]: reef for reef in base["reefs"]}
    by_name = {ship["resource_name"]: ship for ship in ships.values()}
    draws = []
    for group in order_proof["groups_back_to_front"]:
        if group["kind"] == "reef":
            reef = reefs[group["resource_name"]]
            draws.append({"kind": "reef", "instance_id": reef["instance_id"], "depth": group["depth"],
                          "x": reef["world_pixel"][0], "y": reef["world_pixel"][1],
                          "image": base["frames"][reef["variant"]]})
            continue
        ship = by_name[group["resource_name"]]
        if group["kind"] == "separate_shadow":
            parts = [part for part in ship["parts"] if part["detached"] and part["name"] == group["component_name"]]
            require(len(parts) == 1 and parts[0]["depth"] == group["depth"], "Native detached group differs from source part")
        else:
            require(group["kind"] == "inline_parent" and group["depth"] == ship["reference_depth"], "Native parent group differs")
            parts = [next(part for part in ship["parts"] if part["source_index"] == source_index)
                     for source_index in ship["inline_order"]]
        draws.extend(parts)
    require(len(draws) == 34 and sum(draw["kind"] == "ship" for draw in draws) == 29,
            "Native group flattening did not cover29ship parts and5reefs")
    expected_ship_order = [{"instance_id": draw["instance_id"], "source_index": draw["source_index"], "depth": draw["depth"]}
                           for draw in draws if draw["kind"] == "ship"]
    require(manifest["draw_order"] == expected_ship_order, "Staged ship-only traversal differs from native group/inline order")
    reference = {"terrain": base["terrain"], "objects": base, "ships": ships, "draws": draws,
                 "frames": unique_frames, "payloads": payloads}
    reference["world"] = compose_world(reference)
    return reference


def compose_world(reference, draws=None):
    world = reference["terrain"].convert("RGBA")
    for draw in reference["draws"] if draws is None else draws:
        world.alpha_composite(draw["image"], (draw["x"], draw["y"]))
    return world.convert("RGB")


def expected_image(reference, case):
    return terrain.expected_image(reference["world"], case)


def ship_regions(reference, case):
    result = []
    source_x, source_y, _, _ = terrain.source_rect(case)
    for identifier in case["visible_ids"]:
        ship = reference["ships"][identifier]
        left, top = (ship["world_pixel"][0] - source_x) * 2, (ship["world_pixel"][1] - source_y) * 2
        width, height = ship["width"] * 2, ship["height"] * 2
        rect = (left, top, left + width, top + height)
        require(left >= 0 and top >= 0 and rect[2] <= SIZE[0] and rect[3] <= SIZE[1], "Expected ship plane is clipped")
        result.append({"instance_id": identifier, "rect": rect,
                       "alpha": ship["alpha"].resize((width, height), Image.Resampling.NEAREST)})
    require(len(result) == len(case["visible_ids"]), "Missing expected ship ROI")
    return result


def frame_metrics(actual, expected, regions):
    matched, global_metrics = terrain.frame_metrics(actual, expected)
    values = []
    if actual.size != SIZE or expected.size != SIZE:
        return False, {"global": global_metrics, "ship_regions": [], "matched": False}
    for region in regions:
        difference = ImageChops.difference(actual.convert("RGB").crop(region["rect"]),
                                            expected.convert("RGB").crop(region["rect"]))
        mean = sum(ImageStat.Stat(difference).mean) / 3
        covered_mean = sum(ImageStat.Stat(difference, region["alpha"]).mean) / 3
        maximum = max(high for _, high in difference.getextrema())
        passed = mean < 1 and covered_mean < 1 and maximum <= 4
        values.append({"instance_id": region["instance_id"], "rect": list(region["rect"]),
                       "mean_rgb_error": mean, "covered_pixel_mean_rgb_error": covered_mean,
                       "max_channel_error": maximum, "matched": passed})
        matched = matched and passed
    return matched, {"global": global_metrics, "ship_regions": values, "matched": matched}


def validate_draw_log(log, reference):
    ship_pattern = re.compile(r"Mission unit reference draw: order=(-?\d+); id=([0-9a-f]{8}); part=(-?\d+); depth=(-?\d+)")
    reef_pattern = re.compile(r"Mission unit reference reef draw: order=(-?\d+); id=([0-9a-f]{8}); depth=(-?\d+)")
    actual = []
    for line in log.splitlines():
        if line.startswith("Mission unit reference draw:"):
            match = ship_pattern.fullmatch(line)
            require(match is not None, "Malformed ship renderer draw declaration")
            order, identifier, part, depth = match.groups()
            actual.append({"sorting_order": int(order), "kind": "ship", "instance_id": int(identifier, 16),
                           "source_index": int(part), "depth": int(depth)})
        elif line.startswith("Mission unit reference reef draw:"):
            match = reef_pattern.fullmatch(line)
            require(match is not None, "Malformed reef renderer draw declaration")
            order, identifier, depth = match.groups()
            actual.append({"sorting_order": int(order), "kind": "reef", "instance_id": int(identifier, 16),
                           "source_index": None, "depth": int(depth)})
    expected = [{"sorting_order": index + 10, "kind": draw["kind"], "instance_id": draw["instance_id"],
                 "source_index": draw.get("source_index"), "depth": draw["depth"]}
                for index, draw in enumerate(reference["draws"])]
    actual.sort(key=lambda row: row["sorting_order"])
    require(actual == expected, "Renderer queue differs from native34-part ordering (missing, duplicate, tie or depth)")
    return actual


def validate_log(log, case, reference, *, after_exit=False):
    objects.validate_log(log, case, reference["objects"])
    require("Mission unit reference seeds: ships=8; components=29; source_constructors_executed=0" in log,
            "Source ship/component/zero-constructor contract missing")
    require("Mission unit reference grid: cells=576; claimed=8; pending_orders=0; simulation=False" in log,
            "Partial occupancy-grid contract missing")
    require(READY in log, "Frozen ship readiness/scope missing")
    pattern = re.compile(r"Mission unit reference ship: id=([0-9a-f]{8}); cell=(-?\d+),(-?\d+); model=(\d+); heading=(-?\d+); frame=(-?\d+); mask=(\d+); anchor=(-?\d+),(-?\d+); depth=(-?\d+)")
    actual = []
    for line in log.splitlines():
        if line.startswith("Mission unit reference ship:"):
            match = pattern.fullmatch(line)
            require(match is not None, "Malformed ship declaration")
            actual.append(tuple(int(value, 16 if index == 0 else 10) for index, value in enumerate(match.groups())))
    expected = [(ship["instance_id"], *ship["cell"], ship["model"], ship["heading"], ship["frame_index"],
                 ship["mask"], *ship["world_pixel"], ship["reference_depth"]) for ship in reference["ships"].values()]
    require(sorted(actual) == sorted(expected), "Ship declarations are missing/duplicated or differ from native fixture")
    draw_order = validate_draw_log(log, reference)
    if after_exit:
        require(CLEANUP in log, "Eight source occupancy claims were not released/visual references not cleared")
    return draw_order


def wait_for_ready(player, environment, player_log):
    deadline = time.monotonic() + 50
    while time.monotonic() < deadline:
        require(player.poll() is None, "Player exited before frozen unit readiness: " + str(player.returncode))
        log = terrain.read_log(player_log)
        require("Exception" not in log, "Player exception before unit readiness")
        if READY in log:
            result = subprocess.run([str(menu.TOOLCHAIN / "usr/bin/xdotool"), "search", "--name", "^AncientConquest$"],
                                    env=environment, capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().splitlines()[-1]
        time.sleep(.1)
    raise AssertionError("No ready mission-unit reference/player window within50seconds")


def observe_pixels(player, environment, output, expected, regions):
    attempts = []
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and len(attempts) < 12:
        require(player.poll() is None, "Player exited before matching source ship framebuffer")
        path = menu.capture(environment, output, f"frame-{len(attempts) + 1:02d}")
        with Image.open(path) as actual:
            matched, metrics = frame_metrics(actual, expected, regions)
        attempts.append({"screenshot": path.name, **metrics})
        menu.write_json(output / "frame-attempts.json", attempts)
        if matched:
            return path, metrics, attempts
        time.sleep(.15)
    if attempts:
        with Image.open(output / attempts[-1]["screenshot"]) as actual:
            if actual.size == SIZE:
                ImageChops.difference(actual.convert("RGB"), expected).save(output / "difference.png")
    raise AssertionError("Source unit framebuffer or individual ship ROI never matched; inspect frame-attempts.json")


def run_case(output, case, reference, baseline):
    output.mkdir()
    expected, regions = expected_image(reference, case), ship_regions(reference, case)
    expected.save(output / "expected.png", compress_level=0)
    environment = os.environ.copy()
    environment["DISPLAY"] = menu.DISPLAY
    environment["LD_LIBRARY_PATH"] = str(menu.TOOLCHAIN / "usr/lib/x86_64-linux-gnu")
    player_log = output / "player.log"
    launch = ["bash", str(LAUNCHER), str(EXECUTABLE), "-logFile", str(player_log), "--mission-unit-reference",
              "--terrain-origin-x", str(case["requested"][0]), "--terrain-origin-y", str(case["requested"][1]),
              "--terrain-reference-exit-after", str(EXIT_AFTER)]
    metadata = {"case": case["name"], "requested_origin_cells": list(case["requested"]),
                "clamped_origin_cells": list(case["actual"]), "source_rect": list(terrain.source_rect(case)),
                "expected_full_ship_ids": list(case["visible_ids"]), "display_size": list(SIZE), "scale": 2,
                "launch": launch, "provenance": baseline, "verified_payloads": reference["payloads"],
                "runtime": "Windows Mono player under Wine11/Xvfb", "input_injection": "none",
                "diagnostic_exit_after_seconds": EXIT_AFTER,
                "thresholds": {"global": {"mean_rgb_error_strictly_below": 1, "bad_pixel_channel_error_above": 4,
                                          "bad_pixel_fraction_at_most": .005},
                               "each_ship_plane_mean_rgb_error_strictly_below": 1,
                               "each_ship_source_coverage_mean_rgb_error_strictly_below": 1,
                               "each_ship_plane_max_channel_error_at_most": 4}}
    menu.write_json(output / "launch.json", metadata)
    player = xvfb = wine_log = xvfb_log = None
    failure = None
    cleanup_failures = []
    report = None
    stage = "preflight"
    started = time.monotonic()
    try:
        require(provenance() == baseline, "Build/source changed between unit cases")
        require(not menu.DISPLAY_SOCKET.exists(), "Display79 already owned; refuse reuse")
        stage = "Xvfb startup"
        xvfb_log = (output / "xvfb.log").open("w")
        xvfb = subprocess.Popen([str(menu.TOOLCHAIN / "usr/bin/Xvfb"), menu.DISPLAY, "-screen", "0", "1920x1080x24",
                                 "-nolisten", "tcp", "-ac"], env=environment, stdout=xvfb_log, stderr=subprocess.STDOUT)
        menu.wait_for_display(xvfb)
        stage = "player startup"
        wine_log = (output / "wine-launch.log").open("w")
        player = subprocess.Popen(launch, cwd=EXECUTABLE.parent, env=environment, stdout=wine_log, stderr=subprocess.STDOUT)
        window = wait_for_ready(player, environment, player_log)
        ready_at = time.monotonic()
        stage = "fullscreen geometry"
        geometry = menu.xdotool(environment, "getwindowgeometry", "--shell", window)
        (output / "geometry.txt").write_text(geometry + "\n")
        values = dict(line.split("=", 1) for line in geometry.splitlines() if "=" in line)
        require(tuple(int(values[key]) for key in ("X", "Y", "WIDTH", "HEIGHT")) == (0, 0, *SIZE),
                "Player does not fill1920x1080")
        validate_log(terrain.read_log(player_log), case, reference)
        stage = "actual framebuffer and individual ship regions"
        screenshot, metrics, attempts = observe_pixels(player, environment, output, expected, regions)
        stage = "diagnostic timed exit and source claim release"
        code = player.wait(timeout=20)
        exited_at = time.monotonic()
        require(code == 0, "Unit diagnostic did not exit0: " + str(code))
        log = terrain.read_log(player_log)
        draw_order = validate_log(log, case, reference, after_exit=True)
        require(terrain.DIAGNOSTIC_EXIT in log, "Diagnostic timed-exit marker missing")
        require(exited_at - ready_at >= EXIT_AFTER - 2, "Unit reference exited before diagnostic timer")
        require(provenance() == baseline, "Build/source changed during unit validation")
        report = dict(metadata, passed=True, geometry=geometry, framebuffer=metrics,
            matched_screenshot=screenshot.name, capture_attempt_count=len(attempts), exit_code=code,
            termination="diagnostic timed Application.Quit(0)", ready_to_observed_exit_seconds=exited_at-ready_at,
            elapsed_seconds=exited_at-started, source_claims_released=8,
            renderer_draw_order=draw_order, source_order_fixture_sha256=ORDER_FIXTURE_SHA256,
            screenshots={path.name: menu.file_sha256(path) for path in sorted(output.glob("*.png"))},
            player_log_sha256=menu.file_sha256(player_log), limitations=LIMITATIONS)
    except Exception as error:
        failure = error
    finally:
        for process, label in ((player, "player"), (xvfb, "Xvfb")):
            issue = menu.stop_owned_process(process, label)
            if issue:
                cleanup_failures.append(issue)
        for stream in (wine_log, xvfb_log):
            if stream is not None:
                stream.close()
    if cleanup_failures:
        menu.write_json(output / "cleanup-failure.json", cleanup_failures)
        if failure is None:
            stage = "cleanup"
            failure = RuntimeError("Could not stop own process")
    if failure is not None:
        menu.write_json(output / "failure.json", dict(metadata, stage=stage, failure_type=type(failure).__name__,
                        failure=str(failure), player_returncode_after_cleanup=player.returncode if player is not None else None))
        raise failure
    report["player_returncode_after_cleanup"] = player.returncode
    menu.write_json(output / "report.json", report)
    return report


def run_smoke(output):
    output = Path(output).resolve()
    require(not output.exists(), "Select a fresh output directory")
    output.mkdir(parents=True)
    reports = []
    stage = "reference preflight"
    try:
        baseline, reference = provenance(), load_reference()
        for case in CASES:
            stage = case["name"]
            reports.append(run_case(output / case["name"], case, reference, baseline))
        require(provenance() == baseline, "Build/source changed during unit validation")
        require({identifier for case in reports for identifier in case["expected_full_ship_ids"]}
                == {11, 12, 13, 16, 39, 40, 41, 42}, "Not all8source ships received a complete ROI check")
        report = {"passed": True, "runtime": "Windows Mono player under Wine11/Xvfb", "provenance": baseline,
                  "verified_payloads": reference["payloads"], "cases": reports, "limitations": LIMITATIONS}
        menu.write_json(output / "report.json", report)
        return report
    except Exception as error:
        menu.write_json(output / "failure.json", {"passed": False, "stage": stage,
            "completed_cases": [report["case"] for report in reports], "failure_type": type(error).__name__,
            "failure": str(error), "limitations": LIMITATIONS})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.resolve().exists():
        parser.error("Select a fresh output directory")
    report = run_smoke(args.output)
    print(json.dumps({"passed": report["passed"], "output": str(args.output.resolve()),
                      "cases": [case["case"] for case in report["cases"]]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
