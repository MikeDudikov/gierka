#!/usr/bin/env python3
"""Source-art composition oracle for the bounded pointer diagnostic.

The caller supplies independently validated temporal/position/order rows. This
module verifies staged source planes and composes pixels; it does not infer or
prove selection/cursor timing, input behavior, or final2026art. No files, preview,
processes or services are created by this helper.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

if __package__:
    from . import smoke_ship_order as order
else:
    import smoke_ship_order as order

ROOT = Path(__file__).resolve().parents[1]
RESOURCE_ROOT = ROOT / 'Unity/AncientConquest/Assets/Resources/ShipPointerVisualsGenerated'
SOURCE_ROOT = ROOT / 'reference/raw/ancient-conquest'
MANIFEST_NAME = 'ShipPointerVisualsManifest.json'
MANIFEST_SHA256 = '27254400ed2209ddad5b19e22ccee9e3b37f506c7cc579e22970909ee1232f77'
ATLAS_NAME = 'ShipPointerVisualsRgba.bytes'
ATLAS_SHA256 = '051580f543da9e3b448036c67706d80e3c1185d4c10aa7e73cfe94e4fe9020a0'
SOURCE_HASHES = {
    'installed/ancient.exe': 'cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021',
    'installed/missions/controlm.dkx': 'b32a80c703650d8873938544ee4b0718c70a2fd5a577d1b2814bf21b97224974',
    'installed/missions/controlm.dkd': '6f4b90903c880baf938d94577f8058904fafab5008b1963104cc8253cd842cbe',
    'installed/missions/maplib.dkx': '05484166ca374630f7c29c26e561656a11941ef331fb014e52f72aed81c23650',
    'installed/missions/maplib.dkd': '7fe0623d957e196e5279c6bced55db292648b5c9ebc6f1420fcd293c0685b685',
    'files/DATA/OBJECTS.DKX': '67aa31b7e7728a1c4f215c63932b55ea66f3ac1ecdb732bfd368bae2a8375f60',
    'files/DATA/OBJECTS.DKD': '01474065782a7170d54f564df2205572f8a0675411bef0f350dab55c3fd20e50',
}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _checked_bytes(path, expected_sha256):
    path = Path(path)
    _require(path.is_file() and not path.is_symlink(), 'Missing/symbolic pointer image evidence: ' + str(path))
    raw = path.read_bytes()
    _require(hashlib.sha256(raw).hexdigest() == expected_sha256,
             'Pointer image evidence SHA differs: ' + str(path))
    return raw


def load_visual_reference(resource_root=RESOURCE_ROOT, source_root=SOURCE_ROOT):
    """Verify source inputs/atlas/all29 planes and return reusable immutable-by-contract art.

    Call once per QA run and pass the result to ``compose_overlay``. Deliberately
    no hidden cache: a second load rechecks disk contents, including tamper tests.
    Source archive hashes establish provenance; native RLE/health pixel and phase
    proofs live in their separate fixtures and are not rerun by this composer.
    """
    resource_root, source_root = Path(resource_root), Path(source_root)
    for name, digest in SOURCE_HASHES.items():
        _checked_bytes(source_root / name, digest)
    manifest = json.loads(_checked_bytes(resource_root / MANIFEST_NAME, MANIFEST_SHA256))
    raw = _checked_bytes(resource_root / ATLAS_NAME, ATLAS_SHA256)
    _require((manifest['schema_version'], manifest['native_canvas_width'], manifest['native_canvas_height'],
              manifest['atlas_width'], manifest['atlas_height'], manifest['frame_count'], len(raw)) ==
             (1, 1920, 1080, 1024, 128, 29, 524288), 'Pointer atlas geometry/scope differs')
    _require(manifest['source_hashes'] == SOURCE_HASHES and len(manifest['frames']) == 29,
             'Pointer manifest source hashes/plane count differ')
    # Payload rows run bottom-to-top. Manifest atlas_y is already bottom-origin;
    # PIL crops top-origin images, so flip the entire atlas exactly once.
    atlas = Image.frombytes('RGBA', (1024, 128), raw).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    frames = {}
    by_index = []
    for frame in manifest['frames']:
        x, bottom, width, height = (frame[key] for key in ('atlas_x', 'atlas_y', 'width', 'height'))
        _require(all(_integer(v) for v in (x, bottom, width, height)) and
                 x >= 0 and bottom >= 0 and width > 0 and height > 0 and x + width <= 1024 and bottom + height <= 128,
                 'Pointer frame extends outside source atlas')
        name = frame['name']
        _require(isinstance(name, str) and name and name not in frames, 'Missing/duplicate source pointer frame name')
        top = 128 - bottom - height
        plane = atlas.crop((x, top, x + width, top + height))
        _require(hashlib.sha256(plane.tobytes()).hexdigest() == frame['rgba_sha256'],
                 'Pointer source plane SHA differs: ' + name)
        _require(set(plane.getchannel('A').getdata()) <= {0, 255},
                 'Pointer source plane has unexpected interpolated alpha: ' + name)
        frames[name] = plane
        by_index.append(name)
    sequences = {sequence['id']: sequence['frames'] for sequence in manifest['sequences']}
    _require(len(sequences) == 10 and len(sequences['selector']) == 10 and len(sequences['confirm']) == 4,
             'Pointer source animation sequences differ')
    allowed = {
        'selector': {by_index[index] for index in sequences['selector']},
        'health': {by_index[manifest['healthbar']['frame']]},
        'confirm': {by_index[index] for index in sequences['confirm']},
        'cursor': {by_index[index] for key, indices in sequences.items() if key.startswith('cursor_') for index in indices},
    }
    _require(tuple(map(len, (allowed['selector'], allowed['health'], allowed['confirm'], allowed['cursor']))) ==
             (10, 1, 4, 14), 'Pointer image kind/plane mapping differs')
    return {'manifest': manifest, 'frames': frames, 'allowed': allowed,
            'manifest_sha256': MANIFEST_SHA256, 'atlas_sha256': ATLAS_SHA256,
            'scope': 'source-art pixel composition only; caller validates temporal state and ordering'}


def _composite_clipped(destination, plane, left, top):
    x0, y0 = max(0, left), max(0, top)
    x1, y1 = min(destination.width, left + plane.width), min(destination.height, top + plane.height)
    if x1 > x0 and y1 > y0:
        crop = plane.crop((x0 - left, y0 - top, x1 - left, y1 - top))
        destination.alpha_composite(crop, (x0, y0))


def compose_overlay(baseline1920, visual_rows, *, visual_reference=None, origin=(576, 0)):
    """Overlay source planes onto a1920x1080 world baseline and return RGB pixels.

    Rows have ``kind``, boolean ``visible``, source ``sprite`` name, integer
    ``position=[x,y]`` and ``order``. Selector/health/confirm positions are world
    pixels; cursor positions are source screen pixels after its hotspot offset.
    World rows use their independently validated integer renderer order; the
    cursor uses ``order=32767`` and is always composed last. Hidden rows do
    not draw. This function changes neither the baseline nor source frame images.
    """
    _require(isinstance(baseline1920, Image.Image) and baseline1920.size == (1920, 1080),
             'Pointer image oracle requires a1920x1080 world baseline')
    _require(isinstance(origin, (list, tuple)) and len(origin) == 2 and all(_integer(v) for v in origin),
             'Pointer camera origin must contain two integer world coordinates')
    reference = load_visual_reference() if visual_reference is None else visual_reference
    world, cursor, seen = [], [], set()
    for row in visual_rows:
        _require(isinstance(row, dict), 'Pointer visual row must be a mapping')
        kind = row.get('kind')
        _require(kind in ('selector', 'health', 'confirm', 'cursor') and kind not in seen,
                 'Unknown/duplicate pointer image kind')
        seen.add(kind)
        _require(isinstance(row.get('visible'), bool), 'Pointer visibility must be a validated boolean')
        if not row['visible']:
            continue
        name, position = row.get('sprite'), row.get('position')
        _require(name in reference['allowed'][kind], 'Source pointer sprite does not match its visual kind')
        _require(isinstance(position, (tuple, list)) and len(position) == 2 and all(_integer(v) for v in position),
                 'Pointer visual position must contain two integer source coordinates')
        if kind == 'cursor':
            _require(_integer(row.get('order')) and row['order'] == 32767,
                     'Source software cursor must follow the world draw at32767')
            cursor.append(row)
        else:
            _require(_integer(row.get('order')) and 44 <= row['order'] <= 46,
                     'Pointer world overlay left the retained34-renderer cohort')
            world.append(row)
    _require(len({row['order'] for row in world}) == len(world), 'Pointer world overlays share a renderer order')
    result = baseline1920.convert('RGBA')
    for row in sorted(world, key=lambda value: value['order']) + cursor:
        image = reference['frames'][row['sprite']]
        scaled = image.resize((image.width * 2, image.height * 2), Image.Resampling.NEAREST)
        x, y = row['position']
        if row['kind'] != 'cursor':
            x, y = x - origin[0], y - origin[1]
        _composite_clipped(result, scaled, x * 2, y * 2)
    return result.convert('RGB')


def load_reference():
    """Load the frozen native order/world oracle plus verified pointer art once."""
    reference = order.load_reference()
    reference['pointer_visuals'] = load_visual_reference()
    return reference


def compose(reference, native_case, stage, motion_sample, visual_rows):
    """Compose a native-motion checkpoint and caller-validated pointer rows.

    ``native_case`` is an existing ``smoke_ship_order`` native case dictionary;
    ``motion_sample`` must belong to it. Its source queue history supplies all34
    base renderer positions/order. Camera is the fixed reference origin9,0.
    """
    baseline = order.checkpoint_reference(reference, native_case, stage, motion_sample)['expected_image']
    return compose_overlay(baseline, visual_rows, visual_reference=reference.get('pointer_visuals'))
