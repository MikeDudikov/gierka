#!/usr/bin/env python3
"""Validate diagnostic terrain pixels in a Windows Mono player under Wine/X11.

No OS input is injected. Three separate player sessions test the explicit
terrain-reference viewport; this is not a gameplay or original-camera test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from PIL import Image, ImageChops, ImageStat

if __package__:
    from . import smoke_native_menu as menu
else:
    import smoke_native_menu as menu


MANIFEST = (menu.REPOSITORY / "Unity/AncientConquest/Assets/Resources/"
            "TerrainGenerated/TerrainManifest.json")
EXECUTABLE = (menu.REPOSITORY / "artifacts/unity-reference/Windows/"
              "AncientConquestReference.exe")
ASSEMBLY = EXECUTABLE.parent / "AncientConquestReference_Data/Managed/Assembly-CSharp.dll"
LAUNCHER = menu.REPOSITORY / "tools/run_wine11_reference.sh"
SIZE = (1920, 1080)
WORLD_SIZE = (1536, 1536)
SOURCE_VIEW = (960, 540)
SCALE = 2
EXIT_AFTER = 8
MAX_MEAN_RGB_ERROR = 1.0
CHANNEL_ERROR_THRESHOLD = 4
MAX_BAD_PIXEL_FRACTION = 0.005
READY = ("Terrain reference ready: mission=miss000; rendering=SpriteRenderer; "
         "diagnostic-only=True")
DIAGNOSTIC_EXIT = f"Terrain reference diagnostic exit: requested_seconds={EXIT_AFTER}; code=0"
PINNED_PAYLOADS = {
    "TerrainRgba.bytes": (9437184, "f6606a33654577a9e19ec1a2e1f79d9ee6d3454cc49849d87d02d24ca43fde04"),
    "MapPlanar.bytes": (9216, "931138965e7ff49641ff28e389a48104f113d66666badf6de027c8d6e716cfe3"),
}
CASES = (
    {"name": "origin-0-0", "requested": (0, 0), "actual": (0, 0)},
    {"name": "interior-4-4", "requested": (4, 4), "actual": (4, 4)},
    {"name": "clamped-999-999", "requested": (999, 999), "actual": (9, 15)},
)
LIMITATIONS = [
    "Windows Mono player under Wine/X11; native Windows11 and RTX3050Ti laptop not tested",
    "Diagnostic SpriteRenderer viewport only; original camera/FOV, controls and gameplay not validated",
    "No OS input injected; no player-input, navigation, panning or zoom test",
    "Timed diagnostic Application.Quit(0) is not a product/menu Quit test",
    "Static base-palette original terrain; no unit AI, simulation, audio or final2026art claim",
    "Static screenshots do not establish frame rate, animation quality or hardware performance",
]


def require(condition, message):
    menu.require(condition, message)


def provenance():
    files = {"executable": EXECUTABLE, "assembly": ASSEMBLY,
             "terrain_manifest": MANIFEST, "wine_launcher": LAUNCHER}
    files.update({filename: MANIFEST.parent / filename for filename in PINNED_PAYLOADS})
    result = {}
    for label, path in files.items():
        require(path.is_file() and not path.is_symlink(), "Missing or symbolic file: " + str(path))
        result[label] = {"path": str(path), "bytes": path.stat().st_size,
                         "sha256": menu.file_sha256(path)}
    return result


def load_reference():
    manifest = json.loads(MANIFEST.read_text())
    require(manifest["schema_version"] == 1 and manifest["mission"] == "miss000",
            "Unexpected terrain schema or mission")
    require((manifest["map_width_cells"], manifest["map_height_cells"],
             manifest["tile_width"], manifest["tile_height"], manifest["layer_count"])
            == (24, 24, 64, 64, 8), "Terrain map dimensions or layer contract changed")
    require((manifest["native_canvas_width"], manifest["native_canvas_height"]) == SIZE,
            "Terrain reference canvas must be 1920x1080")
    require((manifest["world_width_px"], manifest["world_height_px"]) == WORLD_SIZE
            and (manifest["source_rgba_width"], manifest["source_rgba_height"]) == WORLD_SIZE,
            "Terrain world dimensions changed")
    require(manifest["row_order"] == "bottom-to-top" and manifest["format"] == "RGBA32",
            "Unexpected terrain pixel orientation or format")
    evidence = {}
    terrain_raw = None
    for filename, (length, digest) in PINNED_PAYLOADS.items():
        path = MANIFEST.parent / filename
        require(path.is_file() and not path.is_symlink(), "Missing or symbolic terrain payload: " + filename)
        raw = path.read_bytes()
        declared = manifest["payloads"][filename]
        actual_hash = hashlib.sha256(raw).hexdigest()
        require(len(raw) == length == declared["bytes"], "Terrain payload length changed: " + filename)
        require(actual_hash == digest == declared["sha256"], "Terrain payload hash changed: " + filename)
        evidence[filename] = {"bytes": len(raw), "sha256": actual_hash}
        if filename == "TerrainRgba.bytes":
            terrain_raw = raw
    world = Image.frombytes("RGBA", WORLD_SIZE, terrain_raw).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    require(world.getchannel("A").getextrema() == (255, 255), "Terrain must fully cover the framebuffer")
    return world.convert("RGB"), evidence


def source_rect(case):
    x, y = case["actual"]
    return (x * 64, y * 64, *SOURCE_VIEW)


def expected_image(world, case):
    x, y, width, height = source_rect(case)
    require(x >= 0 and y >= 0 and x + width <= world.width and y + height <= world.height,
            "Diagnostic crop extends outside staged terrain")
    return world.crop((x, y, x + width, y + height)).resize(SIZE, Image.Resampling.NEAREST)


def frame_metrics(actual, expected):
    """Compare every RGB pixel; no UI masks or source-selected sample regions."""
    actual = actual.convert("RGB")
    expected = expected.convert("RGB")
    if actual.size != SIZE or expected.size != SIZE:
        return False, {"actual_size": list(actual.size), "expected_size": list(expected.size),
                       "failure": "Framebuffer dimensions differ from 1920x1080"}
    difference = ImageChops.difference(actual, expected)
    channels = difference.split()
    worst_channel = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
    histogram = worst_channel.histogram()
    total = SIZE[0] * SIZE[1]
    bad_fraction = sum(histogram[CHANNEL_ERROR_THRESHOLD + 1:]) / total
    mean_error = sum(ImageStat.Stat(difference).mean) / 3
    uniform = all(low == high for low, high in actual.getextrema())
    red, green, blue = actual.split()
    magenta = ImageChops.multiply(ImageChops.multiply(red.point(lambda value: 255 if value > 240 else 0),
                                                   green.point(lambda value: 255 if value < 16 else 0)),
                                 blue.point(lambda value: 255 if value > 240 else 0))
    magenta_fraction = magenta.histogram()[255] / total
    matched = (not uniform and magenta_fraction < 0.01
               and mean_error < MAX_MEAN_RGB_ERROR and bad_fraction <= MAX_BAD_PIXEL_FRACTION)
    return matched, {
        "actual_size": list(actual.size), "expected_size": list(expected.size),
        "mean_rgb_error": mean_error,
        "max_channel_error": max(high for _, high in difference.getextrema()),
        "pixels_any_channel_error_above_4_fraction": bad_fraction,
        "exact_pixel_fraction": histogram[0] / total,
        "single_colored": uniform, "magenta_fraction": magenta_fraction,
        "actual_rgb_sha256": hashlib.sha256(actual.tobytes()).hexdigest(),
        "expected_rgb_sha256": hashlib.sha256(expected.tobytes()).hexdigest(),
        "matched": matched,
    }


def validate_frame(path, expected):
    require(path.is_file(), "Framebuffer capture is missing: " + str(path))
    with Image.open(path) as actual:
        return frame_metrics(actual, expected)


def read_log(path):
    return path.read_text(errors="replace") if path.exists() else ""


def validate_log(log, case):
    expected_display = ("Terrain reference display: 1920x1080; "
                        "fullscreen=True; mode=ExclusiveFullScreen")
    x, y = case["actual"]
    rect = ",".join(map(str, source_rect(case)))
    expected_view = (f"Terrain reference view: origin_cells={x},{y}; source_rect={rect}; "
                     "scale=2; world=1536x1536; layers=8")
    require(expected_display in log, "Terrain fullscreen display contract not logged")
    require(expected_view in log, "Expected clamped terrain crop not logged: " + expected_view)
    require(READY in log, "SpriteRenderer diagnostic readiness not logged")
    require("Exception" not in log and "LegacyRuntime" not in log,
            "Player exception or legacy runtime detected; inspect player.log")
    require("Native menu command:" not in log, "Diagnostic session unexpectedly executed a menu command")


def wait_for_ready(player, environment, player_log):
    deadline = time.monotonic() + 50
    while time.monotonic() < deadline:
        require(player.poll() is None, "Player exited before diagnostic readiness: " + str(player.returncode))
        log = read_log(player_log)
        require("Exception" not in log, "Player exception before diagnostic readiness; inspect player.log")
        if READY in log:
            result = subprocess.run(
                [str(menu.TOOLCHAIN / "usr/bin/xdotool"), "search", "--name", "^AncientConquest$"],
                env=environment, capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().splitlines()[-1]
        time.sleep(.1)
    raise AssertionError("No ready terrain SpriteRenderer/player window within 50 seconds")


def observe_pixels(player, environment, output, expected):
    attempts = []
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and len(attempts) < 12:
        require(player.poll() is None, "Player exited before a matching terrain framebuffer")
        path = menu.capture(environment, output, f"frame-{len(attempts) + 1:02d}")
        matched, metrics = validate_frame(path, expected)
        attempts.append({"screenshot": path.name, **metrics})
        menu.write_json(output / "frame-attempts.json", attempts)
        if matched:
            return path, metrics, attempts
        time.sleep(.15)
    last = output / attempts[-1]["screenshot"] if attempts else None
    if last:
        with Image.open(last) as actual:
            if actual.size == SIZE:
                ImageChops.difference(actual.convert("RGB"), expected).save(output / "difference.png")
    raise AssertionError("Terrain framebuffer never matched the hash-verified crop; inspect frame-attempts.json")


def run_case(output, case, expected, baseline, payloads):
    output.mkdir()
    expected.save(output / "expected.png", compress_level=0)
    environment = os.environ.copy()
    environment["DISPLAY"] = menu.DISPLAY
    environment["LD_LIBRARY_PATH"] = str(menu.TOOLCHAIN / "usr/lib/x86_64-linux-gnu")
    player_log = output / "player.log"
    launch = ["bash", str(LAUNCHER), str(EXECUTABLE), "-logFile", str(player_log),
              "--terrain-reference", "--terrain-origin-x", str(case["requested"][0]),
              "--terrain-origin-y", str(case["requested"][1]),
              "--terrain-reference-exit-after", str(EXIT_AFTER)]
    metadata = {
        "case": case["name"], "requested_origin_cells": list(case["requested"]),
        "clamped_origin_cells": list(case["actual"]), "source_rect": list(source_rect(case)),
        "display_size": list(SIZE), "scale": SCALE,
        "launch": launch, "provenance": baseline, "verified_payloads": payloads,
        "runtime": "Windows Mono player under Wine11/Xvfb",
        "input_injection": "none", "diagnostic_exit_after_seconds": EXIT_AFTER,
        "thresholds": {"mean_rgb_error_strictly_below": MAX_MEAN_RGB_ERROR,
                       "bad_pixel_channel_error_above": CHANNEL_ERROR_THRESHOLD,
                       "bad_pixel_fraction_at_most": MAX_BAD_PIXEL_FRACTION},
    }
    menu.write_json(output / "launch.json", metadata)
    player = xvfb = wine_log = xvfb_log = None
    failure = None
    cleanup_failures = []
    stage = "preflight"
    report = None
    started = time.monotonic()
    try:
        require(provenance() == baseline, "Build or manifest changed between terrain cases")
        require(not menu.DISPLAY_SOCKET.exists(), "Display79 already owned; refuse reuse")
        stage = "Xvfb startup"
        xvfb_log = (output / "xvfb.log").open("w")
        xvfb = subprocess.Popen([str(menu.TOOLCHAIN / "usr/bin/Xvfb"), menu.DISPLAY,
                                 "-screen", "0", "1920x1080x24", "-nolisten", "tcp", "-ac"],
                                env=environment, stdout=xvfb_log, stderr=subprocess.STDOUT)
        menu.wait_for_display(xvfb)
        stage = "player startup"
        wine_log = (output / "wine-launch.log").open("w")
        player = subprocess.Popen(launch, cwd=EXECUTABLE.parent, env=environment,
                                  stdout=wine_log, stderr=subprocess.STDOUT)
        window = wait_for_ready(player, environment, player_log)
        ready_at = time.monotonic()
        stage = "fullscreen geometry"
        geometry = menu.xdotool(environment, "getwindowgeometry", "--shell", window)
        (output / "geometry.txt").write_text(geometry + "\n")
        values = dict(line.split("=", 1) for line in geometry.splitlines() if "=" in line)
        require(tuple(int(values[key]) for key in ("X", "Y", "WIDTH", "HEIGHT"))
                == (0, 0, *SIZE), "Player window does not fill 1920x1080: " + geometry)
        validate_log(read_log(player_log), case)
        stage = "actual framebuffer pixels"
        screenshot, metrics, attempts = observe_pixels(player, environment, output, expected)
        stage = "diagnostic timed exit"
        code = player.wait(timeout=20)
        exited_at = time.monotonic()
        require(code == 0, "Diagnostic player did not exit with code0: " + str(code))
        log = read_log(player_log)
        validate_log(log, case)
        require(DIAGNOSTIC_EXIT in log, "Timed diagnostic exit marker not logged")
        require(exited_at - ready_at >= EXIT_AFTER - 2,
                "Player exited materially before the requested diagnostic timer")
        require(provenance() == baseline, "Build or manifest changed during terrain run")
        report = dict(metadata, passed=True, geometry=geometry, framebuffer=metrics,
                      matched_screenshot=screenshot.name, capture_attempt_count=len(attempts),
                      exit_code=code, termination="diagnostic timed Application.Quit(0)",
                      ready_to_observed_exit_seconds=exited_at - ready_at,
                      elapsed_seconds=exited_at - started,
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
            failure = RuntimeError("Could not stop own process; inspect cleanup-failure.json")
    if failure is not None:
        menu.write_json(output / "failure.json", dict(metadata, stage=stage,
                        failure_type=type(failure).__name__, failure=str(failure),
                        player_returncode_after_cleanup=player.returncode if player is not None else None))
        raise failure
    report["player_returncode_after_cleanup"] = player.returncode
    menu.write_json(output / "report.json", report)
    return report


def run_smoke(output):
    output = Path(output).resolve()
    require(not output.exists(), "Select a fresh output directory; previous evidence is preserved")
    output.mkdir(parents=True)
    stage = "reference preflight"
    reports = []
    try:
        baseline = provenance()
        world, payloads = load_reference()
        for case in CASES:
            stage = case["name"]
            reports.append(run_case(output / case["name"], case, expected_image(world, case), baseline, payloads))
        require(provenance() == baseline, "Build or manifest changed during terrain validation")
        report = {"passed": True, "runtime": "Windows Mono player under Wine11/Xvfb",
                  "provenance": baseline, "verified_payloads": payloads,
                  "cases": reports, "limitations": LIMITATIONS}
        menu.write_json(output / "report.json", report)
        return report
    except Exception as error:
        menu.write_json(output / "failure.json", {"passed": False, "stage": stage,
                        "completed_cases": [report["case"] for report in reports],
                        "failure_type": type(error).__name__, "failure": str(error),
                        "limitations": LIMITATIONS})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="Fresh evidence directory; never overwrite a previous run")
    arguments = parser.parse_args(argv)
    if arguments.output.resolve().exists():
        parser.error("Select a fresh output directory; previous evidence is preserved")
    report = run_smoke(arguments.output)
    print(json.dumps({"passed": report["passed"], "output": str(arguments.output.resolve()),
                      "cases": [case["case"] for case in report["cases"]]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
