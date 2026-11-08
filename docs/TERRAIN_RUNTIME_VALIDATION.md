# Diagnostic terrain runtime validation

`tools/smoke_terrain.py` checks the opt-in `--terrain-reference` mode in the
Windows Mono player under local Wine11 and Xvfb. It observes actual Unity
SpriteRenderer output across the complete 1920×1080 framebuffer. The mode is a
static terrain reference, not an implemented playable mission or a reconstruction
of the original camera. SpriteRenderer displays the single already-composed
`TerrainRgba` texture; the player does not redraw the eight map layers from
individual source frames. The planar C# map parser has separate x86 evidence and
provides map geometry here. The pixel test confirms presentation of the staged
composition, not runtime equivalence of the original terrain renderer.

Run after rebuilding the Windows reference player:

```sh
.venv/bin/python tools/smoke_terrain.py --output artifacts/terrain/runtime-<fresh-name>
```

The output directory must not exist. Existing evidence is never overwritten.
The player, `Assembly-CSharp.dll`, manifest, Wine launcher and both terrain
payloads must be present. Display `:79` must be free; the script refuses to take
over an existing X11 server. It launches three sessions sequentially, each with
its own Xvfb and player process. Cleanup signals only processes created by that
invocation. It does not inject OS input, send menu commands, kill Wine globally,
or reuse a running player.

## Viewport contract

The verified staged source is a 1536×1536 RGBA32 terrain image, with bottom-to-top
rows. It represents mission `miss000`, a 24×24 map of 64×64 cells and eight source
layers. The test verifies both the manifest declaration and fixed source hashes:

| Payload | Bytes | SHA-256 |
| --- | ---: | --- |
| `TerrainRgba.bytes` | 9,437,184 | `f6606a33654577a9e19ec1a2e1f79d9ee6d3454cc49849d87d02d24ca43fde04` |
| `MapPlanar.bytes` | 9,216 | `931138965e7ff49641ff28e389a48104f113d66666badf6de027c8d6e716cfe3` |

The diagnostic display scale is exactly two output pixels per source pixel.
A 1920×1080 frame therefore samples 960×540 source pixels. Clamping reserves
`ceil(960/64)=15` horizontal and `ceil(540/64)=9` vertical cells. This deliberately
tests the diagnostic viewport contract; it does not establish original FOV.

| Session | Requested origin in cells | Expected clamped origin | Source rectangle `(x,y,width,height)` |
| --- | --- | --- | --- |
| `origin-0-0` | `(0,0)` | `(0,0)` | `(0,0,960,540)` |
| `interior-4-4` | `(4,4)` | `(4,4)` | `(256,256,960,540)` |
| `clamped-999-999` | `(999,999)` | `(9,15)` | `(576,960,960,540)` |

For each case, the reference decoder flips the staged bottom-up image into
top-down image coordinates, crops the stated source rectangle, and scales it
with nearest-neighbor sampling. The complete resulting RGB image is compared to
an X11 framebuffer screenshot. There are no UI masks or handpicked sample areas.

## Acceptance and evidence

A session must report the expected exclusive-fullscreen display contract,
clamped origin, source rectangle, scale, world dimensions and eight layers. It
must emit `Terrain reference ready: mission=miss000; rendering=SpriteRenderer;
diagnostic-only=True`. The X11 window geometry must be `(0,0,1920,1080)`.
Logs alone do not pass the test: the actual rendered frame must match the
hash-verified source crop.

Full-frame mean absolute RGB channel error must be **strictly below 1.0**.
At most **0.5% of pixels** may differ by more than four levels in any RGB channel.
These small tolerances accommodate a limited display artifact while still
rejecting broad color drift, wrong origin, upside-down output and resampling.
Missing captures, wrong dimensions, single-colored frames and more than 1%
magenta pixels fail explicitly. The script records the exact-pixel fraction,
maximum channel error, RGB hashes and every attempted capture. It waits up to
five seconds after readiness for the rendered frame to be presented.

The player receives `--terrain-reference-exit-after 8`. Exit must be code 0
without test-induced termination, with the corresponding
`Terrain reference diagnostic exit: requested_seconds=8; code=0` log marker.
At least six observed seconds must elapse after readiness, allowing two seconds
for readiness polling and process observation. This is **diagnostic timed Application.Quit**,
not evidence that a product/menu Quit interaction works. Forced cleanup never
turns a failed timed-exit check into a pass.

Each case preserves `launch.json`, `geometry.txt`, `player.log`, Wine/Xvfb logs,
`expected.png`, attempted actual frames, `frame-attempts.json`, and a report or
failure record. A final root `report.json` is emitted only when all three cases
pass. Build/manifest/payload hashes must remain unchanged throughout the run. Failed
captures and logs are preserved; a final difference image is saved when pixel
matching times out.

## Current verification boundary

The helper was checked with 19 pure Python positive and negative controls in
`artifacts/terrain/qa-helper-controls-20261102/report.json`: exact references for
all three crops pass; wrong origin, blank, shader-magenta, vertical flip,
blurred sampling, wrong dimensions, missing frame, wrong origin logs, missing
renderer readiness and exception logs are rejected. `--help` also runs without
starting services. These controls validate the checker, not the Unity player.

Actual player evidence now exists in
`artifacts/terrain/runtime-final/report.json`. The matching build report is
`artifacts/terrain/build-report-final.json`: Unity6000.3.27f2,
StandaloneWindows64 Mono, 0 errors, 0 warnings, 143660987 bytes. The tested
Assembly-CSharp DLL SHA-256 is
`a3d98c1d40911cf0205e5ae553542edaeb2207383d1d3f88720e7a266db6d19f`.

All three sessions passed fullscreen display logs and actual X11 window geometry
`(0,0,1920,1080)`. Every matched capture has **mean RGB error0, maximum channel
error0 and exact-pixel fraction1.0**. No tolerance was needed for the accepted
frames. Each session exited itself after the requested eight seconds with code0
and the explicit diagnostic-exit marker. In `origin-0-0`, the first capture was
blank before the presented frame was observed; the checker rejected it and
accepted the second, exact image. Both attempts and their metrics remain in the
evidence. The other two sessions matched on the first capture.

The full analysis suite passed **94 tests with no skips** in
`artifacts/terrain/full-tests-terrain.txt`. Menu and briefing regressions on the
same tested DLL also passed: `artifacts/terrain/menu-regression-final/report.json`
records 27 stages, five captures and six commands; `briefing-regression-final/report.json`
records 39 stages and eleven captures. Both exited through the ordinary product
Quit with code0. These UI replays inject synthetic MouseState events through the
normal Input System adapter; they do not establish OS-input routing.

Both UI runs preserve the pre-existing runtime warning:
`GarbageCollector disposing of ComputeBuffer. Please use ComputeBuffer.Release() or .Dispose() to manually release the buffer.`
The identical message appears in the earlier
`artifacts/briefing/player-native-ui-sampling/player.log` and
`artifacts/briefing/menu-regression-final/player.log`. It is not a new terrain
regression; the underlying cause remains unresolved. The build's zero-warning
result concerns compilation/build output and does not erase this runtime warning.

Wine/Xvfb does not establish behavior on native Windows11 or the requested
i5/16GB/RTX3050Ti laptop. Static captures do not establish frame rate, input
routing, animation or performance. This check does not validate original camera
behavior, panning, zoom, units, AI, simulation, audio, mission completion, or
final 2026 artwork. Normal menu and briefing paths have their separate passing
regression reports listed above. Source terrain art remains a fidelity reference, not finished
modernized graphics.
