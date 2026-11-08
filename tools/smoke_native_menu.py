#!/usr/bin/env python3
"""Validate real native-menu pointer input in the Windows player under local Wine/X11."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from PIL import Image, ImageChops, ImageGrab


REPOSITORY = Path(__file__).resolve().parents[1]
TOOLCHAIN = Path("/workspace/toolchains/wine11-root")
DISPLAY = ":79"
DISPLAY_SOCKET = Path("/tmp/.X11-unix/X79")
EXPECTED_COMMANDS = [1042, 101, 1027, 1026, 1000]
MANIFEST = (REPOSITORY / "Unity/AncientConquest/Assets/Resources/ReferenceGenerated/"
            "MenuRgbaManifest.json")


def require(condition, message):
    """Keep checks active even when Python runs with -O."""
    if not condition:
        raise AssertionError(message)


def file_sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def load_native_layout():
    manifest = json.loads(MANIFEST.read_text())
    size = manifest["native_canvas_width"], manifest["native_canvas_height"]
    require(size == (1920, 1080), "Current target must be 1920x1080; restage before smoke")
    controls = manifest["ui"]["controls"]
    require([control["resource_id"] for control in controls] == EXPECTED_COMMANDS + [103],
            "Unexpected menu command order in manifest")
    for control in controls:
        rect = control["native_rect"]
        require(len(rect) == 4 and all(isinstance(value, int) for value in rect),
                "Menu rectangle must contain four integers")
        x, y, width, height = rect
        require(x >= 0 and y >= 0 and width > 2 and height > 2
                and x + width <= size[0] and y + height <= size[1],
                "Menu rectangle is outside the native canvas")
    return manifest, size, controls


def control_center(control):
    x, y, width, height = control["native_rect"]
    return x + width // 2, y + height // 2


def outside_point(size, controls):
    for point in ((5, 5), (size[0] - 5, 5),
                  (5, size[1] - 5), (size[0] - 5, size[1] - 5)):
        if not any(x <= point[0] <= x + width and y <= point[1] <= y + height
                   for x, y, width, height in (control["native_rect"] for control in controls)):
            return point
    raise AssertionError("No unoccupied corner point found in menu layout")


def validate_display(geometry, log, size):
    values = dict(line.split("=", 1) for line in geometry.splitlines() if "=" in line)
    require(tuple(int(values[key]) for key in ("X", "Y", "WIDTH", "HEIGHT"))
            == (0, 0, *size), "Player window does not fill the native screen: " + geometry)
    expected = (f"Native menu display: {size[0]}x{size[1]}; "
                "fullscreen=True; mode=ExclusiveFullScreen")
    require(expected in log, "Native exclusive-fullscreen display log not found")
    require("Exception" not in log and "LegacyRuntime" not in log, log)


def run_command(environment, *arguments):
    result = subprocess.run(arguments, env=environment, text=True,
                            capture_output=True, timeout=12)
    if result.returncode:
        raise RuntimeError(f"{arguments}: {result.stderr}{result.stdout}")
    return result.stdout.strip()


def xdotool(environment, *arguments):
    return run_command(environment, str(TOOLCHAIN / "usr/bin/xdotool"),
                       *map(str, arguments))


def capture(environment, output, name):
    path = output / (name + ".png")
    # PNG compression must not consume the bounded replay stage. Capture the
    # actual framebuffer directly and store it losslessly without compression.
    frame = ImageGrab.grab(xdisplay=environment["DISPLAY"])
    frame.save(path, "PNG", compress_level=0)
    return path


def atlas_cells():
    """Read the exact staged reference; match opaque pixels after GPU presentation."""
    metadata = json.loads(MANIFEST.read_text())
    path = MANIFEST.parent / "MenuButtonsRgba.bytes"
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == metadata["buttons_payload_sha256"],
            "Staged button atlas hash changed")
    width, height = metadata["button_atlas_width"], metadata["button_atlas_height"]
    atlas = Image.frombytes("RGBA", (width, height), raw).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    cell_width, cell_height = width // 6, height // 4
    return [[list(atlas.crop((button * cell_width, state * cell_height,
                             (button + 1) * cell_width, (state + 1) * cell_height)).get_flattened_data())
             for state in range(4)] for button in range(6)]


def match_presented_state(path, rect, references, expected):
    x, y, width, height = rect
    with Image.open(path) as frame:
        pixels = list(frame.convert("RGB").crop((x, y, x + width, y + height)).get_flattened_data())
    errors = []
    for reference in references:
        pairs = [(source, actual) for source, actual in zip(reference, pixels) if source[3] == 255]
        require(len(pairs) > 100, "Reference button contains too few opaque pixels")
        errors.append(sum(sum(abs(source[channel] - actual[channel]) for channel in range(3))
                          for source, actual in pairs) / (3 * len(pairs)))
    best = min(range(4), key=lambda state: errors[state])
    return best == expected and errors[expected] < 4, {
        "expected_state": expected, "closest_state": best, "mean_rgb_errors": errors}


def wait_for_display(xvfb):
    for _ in range(100):
        if DISPLAY_SOCKET.exists():
            return
        if xvfb.poll() is not None:
            raise RuntimeError("Xvfb failed")
        time.sleep(.05)
    raise RuntimeError("Xvfb did not create the display79 socket within 5 seconds")


def wait_for_player(player, environment, player_log):
    deadline = time.monotonic() + 50
    while time.monotonic() < deadline:
        if player.poll() is not None:
            raise RuntimeError("Player exited early " + str(player.returncode))
        result = subprocess.run(
            [str(TOOLCHAIN / "usr/bin/xdotool"), "search", "--name", "^AncientConquest$"],
            env=environment, capture_output=True, text=True, timeout=5)
        if (result.returncode == 0 and player_log.exists()
                and "Native menu display:" in player_log.read_text()):
            return result.stdout.strip().splitlines()[-1]
        time.sleep(.2)
    raise AssertionError("No player window")


def require_no_commands(player_log, message):
    require("Native menu command:" not in player_log.read_text(), message)


def validate_state_images(output, size, button_rect):
    with (Image.open(output / "idle.png") as idle,
          Image.open(output / "hover.png") as hover,
          Image.open(output / "pressed.png") as pressed,
          Image.open(output / "cancelled.png") as cancelled):
        require(idle.size == hover.size == pressed.size == cancelled.size == size,
                f"State screenshots are not all {size[0]}x{size[1]}")
        normal = idle.convert("RGB")
        require(ImageChops.difference(normal, cancelled.convert("RGB")).getbbox() is None,
                "Cancellation did not restore normal frame")
        for changed in (hover, pressed):
            bounds = ImageChops.difference(normal, changed.convert("RGB")).getbbox()
            x, y, width, height = button_rect
            require(bounds and bounds[0] >= x and bounds[1] >= y
                    and bounds[2] <= x + width and bounds[3] <= y + height,
                    ("Button state changed outside expected region", bounds))
        require(ImageChops.difference(hover.convert("RGB"), pressed.convert("RGB")).getbbox(),
                "Hover/pressed look identical")


def replay_stages(log):
    return re.findall(r"Menu input replay stage: ([^;\r\n]+);", log)


def validate_replay_prefix(observed, expected):
    require(len(observed) <= len(expected) and observed == expected[:len(observed)],
            f"Unexpected input replay stages: {observed}")


def run_input_replay(player, environment, output, player_log, controls, size):
    """Observe the explicit synthetic Input System replay, never inject OS input.

    Every required capture must begin and end in its logged 0.75-second stage.
    A slow capture or a missed stage fails rather than borrowing a later frame.
    """
    expected = ["idle", "hover-first", "pressed-first", "drag-outside-cancel",
                "reenter-while-held", "release-after-cancel"]
    for control in controls[:-1]:
        identifier = control["resource_id"]
        expected.extend(f"{action}-{identifier}" for action in ("hover", "pressed", "release"))
        if identifier == 101:
            expected.extend(("briefing-cancel-hover", "briefing-cancel-pressed", "briefing-cancel-release"))
    expected.extend(("hover-quit", "pressed-quit", "release-quit"))
    capture_names = {"idle": "idle", "hover-first": "hover", "pressed-first": "pressed",
                     "drag-outside-cancel": "cancelled", "pressed-quit": "quit-pressed"}
    expected_states = {"idle": 1, "hover-first": 3, "pressed-first": 2,
                       "drag-outside-cancel": 1, "pressed-quit": 2}
    references = atlas_cells()
    captured = {}
    deadline = time.monotonic() + 60
    while True:
        log = player_log.read_text()
        observed = replay_stages(log)
        validate_replay_prefix(observed, expected)
        require(not re.search(r"Menu input replay:.*(?:missing|invalid|failed|timeout|"
                              r"did not obtain focus|remained alive)", log),
                "Input replay reported a failure; see player.log")
        require("Exception" not in log, "Input replay raised an exception; see player.log")
        if observed:
            latest = observed[-1]
            latest_index = expected.index(latest)
            for required in capture_names:
                require(required in captured or expected.index(required) >= latest_index,
                        "Missed required input replay capture stage: " + required)
            if latest in capture_names and latest not in captured:
                # The stage is logged during Update; allow that frame to reach OnGUI/present.
                time.sleep(.05)
                before = replay_stages(player_log.read_text())
                validate_replay_prefix(before, expected)
                require(before and before[-1] == latest,
                        "Input replay advanced before capture of " + latest)
                started = time.monotonic()
                attempts = 0
                while True:
                    path = capture(environment, output, capture_names[latest])
                    attempts += 1
                    button = 5 if latest == "pressed-quit" else 0
                    matched, visual_match = match_presented_state(
                        path, controls[button]["native_rect"], references[button], expected_states[latest])
                    after = replay_stages(player_log.read_text())
                    require(after and after[-1] == latest,
                            "Replay advanced before the expected state reached the framebuffer: " + latest)
                    if matched:
                        break
                    require(time.monotonic() - started < .65,
                            f"Expected state was not presented during {latest}: {visual_match}")
                    time.sleep(.02)
                duration = time.monotonic() - started
                after = replay_stages(player_log.read_text())
                validate_replay_prefix(after, expected)
                require(duration <= .75,
                        f"Capture of {latest} took {duration:.3f}s, beyond the 0.75s stage")
                require(after and after[-1] == latest,
                        "Input replay advanced during capture of " + latest)
                captured[latest] = {"png": capture_names[latest] + ".png",
                                    "capture_seconds": duration,
                                    "presentation_samples": attempts,
                                    "visual_state_match": visual_match,
                                    "observed_stage_before": before[-1],
                                    "observed_stage_after": after[-1]}
        if player.poll() is not None:
            break
        require(time.monotonic() < deadline, "Input replay did not exit within 60 seconds")
        time.sleep(.02)

    exit_code = player.wait(timeout=20)
    require(exit_code == 0, f"Input replay player exited with {exit_code}")
    require(set(captured) == set(capture_names),
            "Input replay ended without all required captures: " + str(sorted(captured)))
    # Application.Quit may stop the coroutine before it logs release-quit,
    # after the regular menu callback already processed that queued release.
    require(len(observed) >= len(expected) - 1,
            "Input replay ended before the pressed-quit stage")
    log = player_log.read_text()
    commands = [int(value) for value in re.findall(r"Native menu command: (\d+)", log)]
    require(commands == EXPECTED_COMMANDS + [103],
            "Unexpected synthetic input replay commands: " + str(commands))
    require(re.findall(r"Briefing command: (\d+)", log) == ["1002"],
            "Menu regression replay did not return through exactly one briefing Cancel")
    screens = re.findall(r"Native screen: ([^\r\n]+)", log)
    if screens and screens[0] == "menu":
        screens = screens[1:]
    require(screens == ["briefing; mission=miss000; difficulty=0", "menu"],
            "Menu regression replay did not visit the default briefing and return to menu")
    require("Menu input replay: application quit observed; Quit release queued=True" in log,
            "Normal application Quit was not observed after the queued release")
    validate_state_images(output, size, controls[0]["native_rect"])
    with Image.open(output / "quit-pressed.png") as screenshot:
        require(screenshot.size == size, "Quit-pressed screenshot size mismatch")
    return log, exit_code, {"observed_stages": observed, "captures": captured,
                            "poll_seconds": .02, "capture_settle_seconds": .05,
                            "stage_hold_seconds": .75}


def stop_owned_process(process, label):
    """Only signal the exact Popen child created by this invocation.

    Wine's shared prefix may contain unrelated applications. An image-name
    taskkill or wineserver shutdown would also affect them, so neither is used.
    """
    if process is None or process.poll() is not None:
        return None
    try:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"process": label, "pid": process.pid,
                "failure_type": type(error).__name__, "failure": str(error)}
    return None


def run_smoke(output, diagnostics=False, presentation_only=False, input_replay=False):
    if presentation_only and input_replay:
        raise ValueError("Presentation-only and input-replay modes are mutually exclusive")
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError("Select a fresh output directory; previous evidence is preserved")
    output.mkdir(parents=True)

    environment = os.environ.copy()
    environment["DISPLAY"] = DISPLAY
    environment["LD_LIBRARY_PATH"] = str(TOOLCHAIN / "usr/lib/x86_64-linux-gnu")
    executable = REPOSITORY / "artifacts/unity-reference/Windows/AncientConquestReference.exe"
    assembly = executable.parent / "AncientConquestReference_Data/Managed/Assembly-CSharp.dll"
    player_log = output / "player.log"
    metadata = {
        "diagnostics": diagnostics,
        "presentation_only": presentation_only,
        "input_replay": input_replay,
        "display": DISPLAY,
        "scope": "Windows64 player under Wine11; native Windows11 and target GPU not validated",
    }
    xvfb = player = xvfb_log = wine_log = None
    failure = None
    cleanup_failures = []
    report = None
    replay_evidence = None
    stage = "preflight"

    try:
        manifest, size, controls = load_native_layout()
        first_x, first_y = control_center(controls[0])
        outside_x, outside_y = outside_point(size, controls)
        metadata.update(exe_sha256=file_sha256(executable),
                        assembly_sha256=file_sha256(assembly),
                        manifest_sha256=file_sha256(MANIFEST),
                        native_canvas=list(size),
                        background_upscale_draft=manifest.get("background_upscale_draft"))
        write_json(output / "launch.json", metadata)
        require(not DISPLAY_SOCKET.exists(), "Display79 already owned; refuse reuse")

        stage = "Xvfb startup"
        xvfb_log = (output / "xvfb.log").open("w")
        xvfb = subprocess.Popen(
            [str(TOOLCHAIN / "usr/bin/Xvfb"), DISPLAY, "-screen", "0",
             f"{size[0]}x{size[1]}x24", "-nolisten", "tcp", "-ac"],
            env=environment, stdout=xvfb_log, stderr=subprocess.STDOUT)
        wait_for_display(xvfb)

        stage = "player startup"
        wine_log = (output / "wine-launch.log").open("w")
        launch = ["bash", str(REPOSITORY / "tools/run_wine11_reference.sh"),
                  str(executable), "-logFile", str(player_log)]
        if diagnostics:
            launch.append("--menu-input-diagnostics")
        if input_replay:
            launch.append("--menu-input-replay")
        player = subprocess.Popen(launch, cwd=executable.parent, env=environment,
                                  stdout=wine_log, stderr=subprocess.STDOUT)
        window = wait_for_player(player, environment, player_log)

        if input_replay:
            stage = "synthetic Input System replay"
            geometry = xdotool(environment, "getwindowgeometry", "--shell", window)
            log, exit_code, replay_evidence = run_input_replay(
                player, environment, output, player_log, controls, size)
        elif presentation_only:
            stage = "presentation only"
            time.sleep(.3)  # Start logs before the first rendered frame can be presented.
            geometry = xdotool(environment, "getwindowgeometry", "--shell", window)
            capture(environment, output, "idle")
            with Image.open(output / "idle.png") as screenshot:
                require(screenshot.size == size, "Presentation screenshot size mismatch")
            log = player_log.read_text()
            exit_code = None  # Presentation mode does not exercise Quit.
        else:
            stage = "idle, hover, pressed and drag cancellation"
            xdotool(environment, "windowfocus", "--sync", window)
            xdotool(environment, "mousemove", outside_x, outside_y)
            time.sleep(.3)
            geometry = xdotool(environment, "getwindowgeometry", "--shell", window)
            capture(environment, output, "idle")
            xdotool(environment, "mousemove", first_x, first_y)
            time.sleep(.2)
            capture(environment, output, "hover")
            xdotool(environment, "mousedown", 1)
            time.sleep(.2)
            capture(environment, output, "pressed")
            xdotool(environment, "mousemove", outside_x, outside_y)
            xdotool(environment, "mouseup", 1)
            time.sleep(.2)
            capture(environment, output, "cancelled")
            require_no_commands(player_log, "Drag outside unexpectedly activated")
            validate_state_images(output, size, controls[0]["native_rect"])

            stage = "focus loss while held"
            # A held press must not rearm when the application regains focus.
            root_info = run_command(environment, "/usr/bin/xwininfo", "-root")
            root_match = re.search(r"Window id: (0x[0-9a-fA-F]+)", root_info)
            require(root_match is not None, "Could not identify the X11 root window")
            root_window = root_match.group(1)
            xdotool(environment, "mousemove", first_x, first_y)
            xdotool(environment, "mousedown", 1)
            time.sleep(.15)
            xdotool(environment, "windowfocus", root_window)
            time.sleep(.2)
            xdotool(environment, "windowfocus", window)
            time.sleep(.2)
            xdotool(environment, "mousemove", first_x + 1, first_y + 1)
            xdotool(environment, "mouseup", 1)
            time.sleep(.2)
            require_no_commands(player_log, "Focus return unexpectedly activated")

            stage = "leave and reenter while held"
            xdotool(environment, "mousemove", first_x, first_y)
            xdotool(environment, "mousedown", 1)
            xdotool(environment, "mousemove", outside_x, outside_y)
            xdotool(environment, "mousemove", first_x, first_y)
            xdotool(environment, "mouseup", 1)
            time.sleep(.2)
            require_no_commands(player_log, "Reentry unexpectedly activated")

            stage = "outside press then inside release"
            xdotool(environment, "mousemove", outside_x, outside_y)
            xdotool(environment, "mousedown", 1)
            xdotool(environment, "mousemove", first_x, first_y)
            xdotool(environment, "mouseup", 1)
            time.sleep(.2)
            require_no_commands(player_log, "Outside press unexpectedly activated")
            xdotool(environment, "click", 3)
            time.sleep(.2)
            require_no_commands(player_log, "Right button unexpectedly activated")

            stage = "five destination commands"
            for control in controls[:-1]:
                x, y = control_center(control)
                xdotool(environment, "mousemove", x, y)
                xdotool(environment, "click", 1)
                time.sleep(.15)
                if control["resource_id"] == 101:
                    briefing_path = MANIFEST.parent.parent / "BriefingGenerated/BriefingManifest.json"
                    briefing = json.loads(briefing_path.read_text())
                    cancel = next(item for item in briefing["controls"] if item["resource_id"] == 1002)
                    cancel_x, cancel_y = control_center(cancel)
                    xdotool(environment, "mousemove", cancel_x, cancel_y)
                    xdotool(environment, "click", 1)
                    time.sleep(.15)
            lines = [line for line in player_log.read_text().splitlines()
                     if "Native menu command:" in line]
            require(len(lines) == 5, lines)
            commands = [int(re.search(r"command: (\d+)", line).group(1)) for line in lines]
            require(commands == EXPECTED_COMMANDS, lines)

            stage = "Quit only on release"
            quit_x, quit_y = control_center(controls[-1])
            xdotool(environment, "mousemove", quit_x, quit_y)
            xdotool(environment, "mousedown", 1)
            time.sleep(.15)
            capture(environment, output, "quit-pressed")
            require(player.poll() is None, "Quit fired on down")
            xdotool(environment, "mouseup", 1)
            exit_code = player.wait(timeout=20)
            require(exit_code == 0, exit_code)
            log = player_log.read_text()
            require("Native menu command: 103 (Quit game)" in log, "Quit command was not logged")
            require("Exception" not in log and "LegacyRuntime" not in log, log)

        stage = "report"
        validate_display(geometry, log, size)
        report = {
            "scope": ("Windows64 player presentation under Wine11; pointer input not exercised"
                      if presentation_only else
                      "Windows64 player synthetic Input System replay through regular onEvent; not OS/hardware input validation"
                      if input_replay else
                      "Windows64 player input/rendering under Wine11, not native Windows11"),
            "build_report": json.loads((executable.parent / "build-report.json").read_text()),
            "exe_sha256": file_sha256(executable),
            "assembly_sha256": file_sha256(assembly),
            "geometry": geometry,
            "native_canvas": list(size),
            "manifest_sha256": file_sha256(MANIFEST),
            "background_upscale_draft": manifest.get("background_upscale_draft"),
            "presentation_only": presentation_only,
            "input_replay": input_replay,
            "replay_evidence": replay_evidence,
            "commands": [line for line in log.splitlines() if "Native menu command:" in line],
            "display": [line for line in log.splitlines() if "Native menu display:" in line],
            "exit_code": exit_code,
            "screenshots": {path.name: file_sha256(path) for path in sorted(output.glob("*.png"))},
            "checks": (["exclusive-fullscreen display log matches native canvas",
                        "window geometry fills native screen", "native-size screenshot captured"]
                       if presentation_only else [
                "idle/hover/pressed pixel changes confined to first button; cancellation restores identical frame",
                "all required captures remained inside their logged replay stage",
                "six synthetic Input System commands in exact order",
                "normal application Quit after queued release, exit0"]
                       if input_replay else [
                "idle/hover/pressed pixel changes confined to button, cancellation restores identical frame",
                "focus loss while held does not rearm", "drag outside cancels",
                "leave/reenter cancels", "outside-down inside-up cancels", "right click ignored",
                "five destination commands emitted once without fake transitions",
                "Quit only on release, exit0"]),
            "limitations": ["Quit HLS fade not implemented",
                            "Only first-mission static briefing is connected; gameplay, briefing audio and other destination screens are incomplete",
                            "Native Windows11 / RTX3050Ti not tested"]
                           + (["Pointer input and Quit not exercised; owned process stopped after presentation capture"]
                              if presentation_only else [])
                           + (["Input generated by explicit synthetic Input System device; OS, Wine RAWINPUT, hardware and focus-loss routing not validated"]
                              if input_replay else []),
        }
    except Exception as error:
        failure = error
    finally:
        for process, label in ((player, "player"), (xvfb, "Xvfb")):
            cleanup_failure = stop_owned_process(process, label)
            if cleanup_failure:
                cleanup_failures.append(cleanup_failure)
        for stream in (wine_log, xvfb_log):
            if stream is not None:
                stream.close()

    if cleanup_failures:
        write_json(output / "cleanup-failure.json", cleanup_failures)
        if failure is None:
            stage = "cleanup"
            failure = RuntimeError("Could not stop an owned process; see cleanup-failure.json")
    if failure is not None:
        write_json(output / "failure.json", dict(metadata, stage=stage,
                   failure_type=type(failure).__name__, failure=str(failure)))
        raise failure
    report["player_returncode_after_cleanup"] = player.returncode if player is not None else None
    report["termination"] = ("owned-process cleanup; not an application Quit test"
                             if presentation_only else "application Quit")
    write_json(output / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--diagnostics", action="store_true")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--presentation-only", action="store_true",
                        help="Validate native display and capture it without injecting pointer input or exercising Quit")
    modes.add_argument("--input-replay", action="store_true",
                       help="Observe explicit synthetic Input System replay and normal Quit; no OS input is injected")
    arguments = parser.parse_args(argv)
    # Reject existing evidence before touching any source, service or process.
    if arguments.output.resolve().exists():
        parser.error("Select a fresh output directory; previous evidence is preserved")
    report = run_smoke(arguments.output, arguments.diagnostics,
                       arguments.presentation_only, arguments.input_replay)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
