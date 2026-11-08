#!/usr/bin/env python3
"""Validate the first briefing in the Windows player using explicit Input System replay.

This observes real player rendering and normal menu callbacks. It does not
inject OS input, call presentation/domain methods, or validate Windows hardware.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from PIL import Image, ImageChops, ImageStat

if __package__:
    from . import smoke_native_menu as menu
else:
    import smoke_native_menu as menu


BRIEFING_MANIFEST = (menu.REPOSITORY / "Unity/AncientConquest/Assets/Resources/"
                     "BriefingGenerated/BriefingManifest.json")
STAGES = [
    "menu-idle", "open-hover", "open-down", "open-release", "briefing-easy",
    "disabled-start-hover", "disabled-start-down", "disabled-start-release",
    "hard-hover", "hard-down", "hard-release", "hard-current-down", "hard-current-release",
    "normal-label-hover", "normal-label-down", "normal-label-release",
    "cancel-hover", "cancel-down", "cancel-drag-outside", "cancel-outside-release",
    "briefing-after-cancelled-drag", "valid-cancel-hover", "valid-cancel-down",
    "valid-cancel-release", "menu-after-cancel", "reopen-hover", "reopen-down",
    "reopen-release", "briefing-retained-hard", "normal-hover", "normal-down",
    "normal-release", "second-cancel-hover", "second-cancel-down", "second-cancel-release",
    "final-menu", "quit-hover", "quit-down", "quit-release",
]
CAPTURES = {
    "menu-idle": "menu-idle",
    "briefing-easy": "briefing-easy",
    "disabled-start-down": "disabled-start",
    "hard-down": "briefing-hard-on-down",
    "briefing-after-cancelled-drag": "briefing-cancelled-drag",
    "valid-cancel-down": "briefing-cancel-pressed",
    "menu-after-cancel": "menu-after-cancel",
    "briefing-retained-hard": "briefing-retained-hard",
    "normal-down": "briefing-normal-on-down",
    "final-menu": "final-menu",
    "quit-down": "quit-pressed",
}


def require(condition, message):
    menu.require(condition, message)


def decode_payload(manifest, filename, width, height):
    path = BRIEFING_MANIFEST.parent / filename
    require(not path.is_symlink(), "Briefing payload must not be a symlink")
    raw = path.read_bytes()
    source = manifest["payloads"][filename]
    require(len(raw) == width * height * 4 == source["bytes"],
            "Briefing payload dimensions/length differ: " + filename)
    require(hashlib.sha256(raw).hexdigest() == source["sha256"],
            "Briefing payload hash changed: " + filename)
    return Image.frombytes("RGBA", (width, height), raw).transpose(Image.Transpose.FLIP_TOP_BOTTOM)


def reference_pair(image):
    mask = image.getchannel("A").point(lambda alpha: 255 if alpha == 255 else 0)
    require(ImageStat.Stat(mask).sum[0] / 255 > 100,
            "Reference layer has too few opaque pixels")
    return image.convert("RGB"), mask


def load_references(size):
    manifest = json.loads(BRIEFING_MANIFEST.read_text())
    require(manifest["schema_version"] == 1 and manifest["mission"] == "miss000",
            "Unexpected briefing manifest schema or mission")
    require((manifest["native_canvas_width"], manifest["native_canvas_height"]) == size,
            "Briefing canvas differs from menu")
    require(manifest["default_difficulty"] == 0, "Fresh-profile difficulty must be source-verified Easy")
    require([control["resource_id"] for control in manifest["controls"]] == [1010, 1002],
            "Unexpected briefing controls")
    require([control["value"] for control in manifest["difficulty_controls"]] == [0, 1, 2],
            "Unexpected difficulty ordering")
    static = decode_payload(manifest, "StaticUiRgba.bytes", *size)
    width, height = manifest["button_atlas_width"], manifest["button_atlas_height"]
    atlas = decode_payload(manifest, "ButtonsRgba.bytes", width, height)
    button_width, button_height = width // 2, height // 4
    buttons = [[reference_pair(atlas.crop((button * button_width, state * button_height,
                                          (button + 1) * button_width, (state + 1) * button_height)))
                for state in range(4)] for button in range(2)]
    width, height = manifest["difficulty_atlas_width"], manifest["difficulty_atlas_height"]
    atlas = decode_payload(manifest, "DifficultyRgba.bytes", width, height)
    choices = [reference_pair(atlas.crop((value * width // 3, 0, (value + 1) * width // 3, height)))
               for value in range(3)]
    return manifest, {"static": reference_pair(static), "buttons": buttons, "choices": choices}


def mean_error(actual, reference):
    expected, mask = reference
    difference = ImageChops.difference(expected, actual)
    return sum(ImageStat.Stat(difference, mask).mean) / 3


def crop_rect(image, rect):
    x, y, width, height = rect
    return image.crop((x, y, x + width, y + height))


def validate_briefing_frame(path, manifest, references, difficulty, cancel_state=1):
    with Image.open(path) as source:
        frame = source.convert("RGB")
    static_error = mean_error(frame, references["static"])
    start = crop_rect(frame, manifest["controls"][0]["native_rect"])
    cancel = crop_rect(frame, manifest["controls"][1]["native_rect"])
    choices = crop_rect(frame, manifest["difficulty_rect"])
    start_errors = [mean_error(start, candidate) for candidate in references["buttons"][0]]
    cancel_errors = [mean_error(cancel, candidate) for candidate in references["buttons"][1]]
    choice_errors = [mean_error(choices, candidate) for candidate in references["choices"]]
    matched = (static_error < 4 and min(range(4), key=start_errors.__getitem__) == 0
               and start_errors[0] < 4
               and min(range(4), key=cancel_errors.__getitem__) == cancel_state
               and cancel_errors[cancel_state] < 4
               and min(range(3), key=choice_errors.__getitem__) == difficulty
               and choice_errors[difficulty] < 4)
    return matched, {"static_ui_mean_rgb_error": static_error,
                     "start_expected_state": 0, "start_mean_rgb_errors": start_errors,
                     "cancel_expected_state": cancel_state, "cancel_mean_rgb_errors": cancel_errors,
                     "difficulty_expected": difficulty, "difficulty_mean_rgb_errors": choice_errors}


def stages(log):
    return re.findall(r"Briefing input replay stage: ([^;\r\n]+);", log)


def validate_stage_prefix(observed):
    require(observed == STAGES[:len(observed)], "Unexpected briefing replay stages: " + str(observed))


def frame_expectation(stage):
    if stage in ("briefing-easy", "disabled-start-down"):
        return 0, 1
    if stage == "valid-cancel-down":
        return 2, 2
    if stage == "normal-down":
        return 1, 1
    if stage in ("hard-down", "briefing-after-cancelled-drag", "briefing-retained-hard"):
        return 2, 1
    return None


def validate_capture(path, stage, manifest, references, menu_controls, menu_references):
    expected = frame_expectation(stage)
    if expected is not None:
        return validate_briefing_frame(path, manifest, references, *expected)
    index = 5 if stage == "quit-down" else 0
    state = 2 if stage == "quit-down" else 1
    return menu.match_presented_state(path, menu_controls[index]["native_rect"],
                                      menu_references[index], state)


def identical(first, second):
    with Image.open(first) as left, Image.open(second) as right:
        return ImageChops.difference(left.convert("RGB"), right.convert("RGB")).getbbox() is None


def observe_replay(player, environment, output, player_log, manifest, references, menu_controls, size):
    captured = {}
    menu_references = menu.atlas_cells()
    deadline = time.monotonic() + 90
    observed = []
    while True:
        log = player_log.read_text()
        observed = stages(log)
        validate_stage_prefix(observed)
        require("Exception" not in log and "LegacyRuntime" not in log, log)
        require(not re.search(r"Briefing input replay:.*(?:missing|invalid|failed|timeout|"
                              r"did not obtain focus|remained alive)", log),
                "Briefing replay reported failure; inspect player.log")
        if observed:
            latest = observed[-1]
            latest_index = STAGES.index(latest)
            for required in CAPTURES:
                require(required in captured or STAGES.index(required) >= latest_index,
                        "Missed briefing capture stage: " + required)
            if latest in CAPTURES and latest not in captured:
                time.sleep(.05)
                before = stages(player_log.read_text())
                require(before and before[-1] == latest, "Replay advanced before capture: " + latest)
                started = time.monotonic()
                attempts = 0
                while True:
                    path = menu.capture(environment, output, CAPTURES[latest])
                    attempts += 1
                    matched, visual = validate_capture(path, latest, manifest, references,
                                                       menu_controls, menu_references)
                    after = stages(player_log.read_text())
                    require(after and after[-1] == latest,
                            "Replay advanced before expected frame was presented: " + latest)
                    if matched:
                        break
                    require(time.monotonic() - started < .85,
                            f"Expected frame not presented during {latest}: {visual}")
                    time.sleep(.02)
                require(time.monotonic() - started < 1,
                        "Capture exceeded its one-second replay stage: " + latest)
                with Image.open(path) as image:
                    require(image.size == size, "Replay screenshot does not fill native canvas")
                captured[latest] = {"png": path.name, "samples": attempts,
                                    "capture_seconds": time.monotonic() - started,
                                    "observed_stage_before": before[-1],
                                    "observed_stage_after": after[-1], "visual_match": visual}
        if player.poll() is not None:
            break
        require(time.monotonic() < deadline, "Briefing player did not exit within 90 seconds")
        time.sleep(.02)
    code = player.wait(timeout=10)
    require(code == 0, f"Briefing player exited with {code}")
    require(set(captured) == set(CAPTURES), "Briefing replay missed required screenshots")
    require(len(observed) >= len(STAGES) - 1, "Briefing replay ended before Quit press")
    log = player_log.read_text()
    require(re.findall(r"Native menu command: (\d+)", log) == ["101", "101", "103"],
            "Main-menu commands did not match two opens and normal Quit")
    require(re.findall(r"Briefing command: (\d+)", log) == ["1002", "1002"],
            "Disabled Start or cancelled drag emitted an unexpected briefing command")
    require(re.findall(r"Briefing difficulty: (\d+)", log) == ["2", "1"],
            "Difficulty changed on release, repeated choice, hover, or label click")
    screens = re.findall(r"Native screen: ([^\r\n]+)", log)
    if screens and screens[0] == "menu":
        screens = screens[1:]
    require(screens == ["briefing; mission=miss000; difficulty=0", "menu",
                        "briefing; mission=miss000; difficulty=2", "menu"],
            "Briefing did not open at Easy, return twice, and retain Hard after reopening")
    require("Briefing input replay: application quit observed; Quit release queued=True" in log,
            "Normal application Quit was not observed after the queued release")
    require(identical(output / "menu-idle.png", output / "menu-after-cancel.png")
            and identical(output / "menu-idle.png", output / "final-menu.png"),
            "Returning from briefing did not restore the original menu frame")
    require(identical(output / "briefing-easy.png", output / "disabled-start.png"),
            "Disabled Start changed the briefing")
    require(identical(output / "briefing-hard-on-down.png", output / "briefing-cancelled-drag.png")
            and identical(output / "briefing-hard-on-down.png", output / "briefing-retained-hard.png"),
            "Cancelled drag or reopening changed the retained Hard briefing frame")
    with Image.open(output / "briefing-hard-on-down.png") as hard, Image.open(output / "briefing-normal-on-down.png") as normal:
        bounds = ImageChops.difference(hard.convert("RGB"), normal.convert("RGB")).getbbox()
        x, y, width, height = manifest["difficulty_rect"]
        require(bounds and bounds[0] >= x and bounds[1] >= y and bounds[2] <= x + width and bounds[3] <= y + height,
                "Changing difficulty altered pixels outside its UI region")
    return log, code, {"observed_stages": observed, "captures": captured,
                        "stage_hold_seconds": 1, "poll_seconds": .02}


def run_smoke(output, diagnostics=False):
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError("Select a fresh output directory; previous evidence is preserved")
    output.mkdir(parents=True)
    environment = os.environ.copy()
    environment["DISPLAY"] = menu.DISPLAY
    environment["LD_LIBRARY_PATH"] = str(menu.TOOLCHAIN / "usr/lib/x86_64-linux-gnu")
    executable = menu.REPOSITORY / "artifacts/unity-reference/Windows/AncientConquestReference.exe"
    assembly = executable.parent / "AncientConquestReference_Data/Managed/Assembly-CSharp.dll"
    player_log = output / "player.log"
    metadata = {"scope": "Windows64 first-briefing synthetic Input System replay through ordinary onEvent; not OS/hardware input validation",
                "display": menu.DISPLAY, "diagnostics": diagnostics}
    xvfb = player = xvfb_log = wine_log = None
    failure = None
    report = None
    cleanup_failures = []
    stage = "preflight"
    try:
        menu_manifest, size, controls = menu.load_native_layout()
        manifest, references = load_references(size)
        metadata.update(exe_sha256=menu.file_sha256(executable), assembly_sha256=menu.file_sha256(assembly),
                        menu_manifest_sha256=menu.file_sha256(menu.MANIFEST),
                        briefing_manifest_sha256=menu.file_sha256(BRIEFING_MANIFEST), native_canvas=list(size))
        menu.write_json(output / "launch.json", metadata)
        require(not menu.DISPLAY_SOCKET.exists(), "Display79 already owned; refuse reuse")
        stage = "Xvfb startup"
        xvfb_log = (output / "xvfb.log").open("w")
        xvfb = subprocess.Popen([str(menu.TOOLCHAIN / "usr/bin/Xvfb"), menu.DISPLAY, "-screen", "0",
                                 f"{size[0]}x{size[1]}x24", "-nolisten", "tcp", "-ac"],
                                env=environment, stdout=xvfb_log, stderr=subprocess.STDOUT)
        menu.wait_for_display(xvfb)
        stage = "player startup"
        wine_log = (output / "wine-launch.log").open("w")
        launch = ["bash", str(menu.REPOSITORY / "tools/run_wine11_reference.sh"), str(executable),
                  "-logFile", str(player_log), "--briefing-input-replay"]
        if diagnostics:
            launch.append("--menu-input-diagnostics")
        player = subprocess.Popen(launch, cwd=executable.parent, env=environment,
                                  stdout=wine_log, stderr=subprocess.STDOUT)
        window = menu.wait_for_player(player, environment, player_log)
        geometry = menu.xdotool(environment, "getwindowgeometry", "--shell", window)
        stage = "synthetic first-briefing replay"
        log, code, evidence = observe_replay(player, environment, output, player_log,
                                            manifest, references, controls, size)
        menu.validate_display(geometry, log, size)
        report = dict(metadata, build_report=json.loads((executable.parent / "build-report.json").read_text()),
                      mission=manifest["mission"], mission_title=manifest["mission_title"], geometry=geometry,
                      menu_background_upscale_draft=menu_manifest.get("background_upscale_draft"),
                      briefing_background_upscale_draft=manifest.get("background_upscale_draft"),
                      replay_evidence=evidence, exit_code=code, termination="application Quit",
                      screenshots={path.name: menu.file_sha256(path) for path in sorted(output.glob("*.png"))},
                      checks=["native1920x1080/fullscreen presentation", "source-derived static briefing text and controls rendered",
                              "fresh-profile Easy", "Start unavailable without fake gameplay",
                              "Hard selected on left down; release, repeated choice and label ignored",
                              "Cancel drag outside stays in briefing", "Cancel returns to identical menu frame",
                              "difficulty persists after reopening", "Normal selected on down",
                              "normal Quit through ordinary menu callback, exit0"],
                      limitations=["Synthetic Input System events do not validate OS/Wine RAWINPUT/hardware routing",
                                   "Native Windows11 and target RTX3050Ti laptop not tested",
                                   "StartGame, gameplay, briefing audio and original Quit HLS fade not implemented",
                                   "Cosmetic backgrounds and bitmap UI remain drafts, not final2026art"])
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
                        failure_type=type(failure).__name__, failure=str(failure)))
        raise failure
    report["player_returncode_after_cleanup"] = player.returncode
    menu.write_json(output / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--diagnostics", action="store_true")
    arguments = parser.parse_args(argv)
    if arguments.output.resolve().exists():
        parser.error("Select a fresh output directory; previous evidence is preserved")
    print(json.dumps(run_smoke(arguments.output, arguments.diagnostics), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
