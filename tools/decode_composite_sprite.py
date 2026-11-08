#!/usr/bin/env python3
"""Decode one verified type8 composite frame; no animation or world rendering.

The original mfMSprLoad (0x554d50) selects source parts by a 32-bit mask,
transposes frame-major 44-byte source records to packed 10-byte runtime
records, and narrows x/y/depth to signed16. Negative depth creates a separate
sprite; it is not a transparent or missing part. Source pixel planes remain
indexed with explicit RLE coverage. Palette conversion belongs to the caller.
"""
from __future__ import annotations

import hashlib
import struct

try:
    from .decode_sprite import decode_sprite, resource_payload
except ImportError:
    from decode_sprite import decode_sprite, resource_payload


RECORD_BYTES = 44
MAX_PARTS = 32


def signed16(value):
    value &= 0xffff
    return value - 0x10000 if value & 0x8000 else value


def inline_draw_order(components):
    # SpriteEngine55e0e0 uses pairwise swaps, not a stable library sort. Equal
    # depths may change relative order when a later higher part is swapped in.
    result = [part for part in components if not part["detached"]]
    for first in range(len(result) - 1):
        for other in range(first + 1, len(result)):
            if result[first]["depth"] < result[other]["depth"]:
                result[first], result[other] = result[other], result[first]
    return result


def decode_composite_frame(entry, data, entries, frame_index, mask):
    """Return logical dimensions and source-selected RLE parts for one frame.

    ``components`` preserves ascending selected source-part order.
    ``inline_components`` gives the original descending-depth draw order for
    nonnegative parts. ``detached_components`` keeps separate negative-depth
    sprites in creation order; this function does not guess their world order.
    Each component contains its complete decoded ``sprite`` (indices/coverage),
    name, source_index, offset_x/y, depth, detached and payload_sha256.

    This strict adapter rejects unsupported/corrupt inputs. Such rejection is
    not a claim about original error recovery or raw-memory behavior.
    """
    if entry.get("type") != 8:
        raise ValueError("A composite descriptor must be source type8")
    try:
        metadata = bytes.fromhex(entry["metadata_hex"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Invalid type8 metadata") from error
    if len(metadata) != 12:
        raise ValueError("Type8 metadata requires twelve source bytes")
    parts, frames, width, height = struct.unpack_from("<4h", metadata)
    if not (1 <= parts <= MAX_PARTS and frames > 0 and 0 < width <= 8192 and 0 < height <= 8192):
        raise ValueError("Composite geometry is outside the verified positive signed16 path")
    if (not isinstance(frame_index, int) or isinstance(frame_index, bool)
            or not 0 <= frame_index < frames):
        raise ValueError("Composite frame index is outside source bounds")
    if (not isinstance(mask, int) or isinstance(mask, bool) or not 0 < mask <= 0xffffffff):
        raise ValueError("Composite mask must be a nonzero uint32")
    selected = [index for index in range(parts) if mask & (1 << index)]
    if not selected:
        raise ValueError("Composite mask selects no source part")
    # The original allocates/transposes using min(popcount(mask), parts), then
    # writes the real selected count into the header. A partial mask mixed with
    # out-of-range bits can therefore leave a different stride. This adapter
    # accepts the verified layouts, including all-bits masks that select every
    # source part, and refuses that unexplained sparse-stride variant.
    if min(mask.bit_count(), parts) != len(selected):
        raise ValueError("Composite mask creates an unsupported sparse runtime stride")
    payload = resource_payload(entry, data)
    if len(payload) != parts * frames * RECORD_BYTES:
        raise ValueError("Composite payload length does not match frame-major source records")
    resources = {}
    for resource in entries:
        key = resource["type"], resource["name"]
        if key in resources:
            raise ValueError("Ambiguous duplicate source resource")
        resources[key] = resource
    components = []
    for index in selected:
        record = payload[(frame_index * parts + index) * RECORD_BYTES:
                         (frame_index * parts + index + 1) * RECORD_BYTES]
        name_bytes = record[12:44]
        if b"\0" not in name_bytes:
            raise ValueError("Composite part name is not NUL terminated")
        try:
            name = name_bytes.split(b"\0", 1)[0].decode("ascii")
        except UnicodeDecodeError as error:
            raise ValueError("Composite part name must be source ASCII") from error
        if not name or (6, name) not in resources:
            raise ValueError("Selected composite part has no source type6 frame")
        raw = resource_payload(resources[6, name], data)
        sprite = decode_sprite(raw)
        if sprite["flags"] & 0x100:
            raise ValueError("Composite part uses an unverified sprite flag0x100")
        x, y, depth = (signed16(value) for value in struct.unpack_from("<3i", record))
        components.append({"source_index": index, "name": name, "offset_x": x,
                           "offset_y": y, "depth": depth, "detached": depth < 0,
                           "payload_sha256": hashlib.sha256(raw).hexdigest(), "sprite": sprite})
    return {"width": width, "height": height, "frame_count": frames,
            "source_part_count": parts, "frame_index": frame_index, "mask": mask,
            "components": components,
            "inline_components": inline_draw_order(components),
            "detached_components": [part for part in components if part["detached"]]}
