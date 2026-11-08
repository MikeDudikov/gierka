#!/usr/bin/env python3
"""Inspect the observed DKBT/DKFM format without executing original programs.

Windows DIB (type 1), PCM (type 2), and observed bitmap fonts (type 3) are
decoded. Compression flag 1 uses the verified original installer LZ codec.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import io
import json
from pathlib import Path
import struct
import wave

try:
    from .extract_setup import decompress_block
except ImportError:
    from extract_setup import decompress_block


class FormatError(ValueError):
    pass


def inspect_pair(index: bytes, data: bytes) -> list[dict]:
    if len(index) < 64 or index[:8] != b"DKBT\x01\x01\x00\x08":
        raise FormatError("Unsupported DKX header")
    if len(index) != struct.unpack_from("<I", index, 8)[0] or (len(index)-64) % 2048:
        raise FormatError("Invalid DKX length")
    if len(data) < 32 or data[:8] != b"DKFM\x01\x01\x00\x00":
        raise FormatError("Unsupported DKD header")
    if struct.unpack_from("<I", data, 8)[0] != len(data):
        raise FormatError("Invalid DKD length")
    root = struct.unpack_from("<I", index, 36)[0]
    pending, seen, entries, keys = [root], set(), [], set()
    while pending:
        node = pending.pop()
        if node == 0xffffffff:
            continue
        if node in seen:
            raise FormatError("Cycle or multiply referenced node")
        if node < 64 or (node-64) % 2048 or node+2048 > len(index):
            raise FormatError("Node outside aligned DKX pages")
        seen.add(node)
        # Bytes 10..15 can contain stale memory; only the uint16 is used length.
        used = struct.unpack_from("<H", index, node+8)[0]
        if used > 2032:
            raise FormatError("Oversized node")
        pos, end = node+16, node+16+used
        pending.append(struct.unpack_from("<I", index, node+4)[0])
        while pos < end:
            if pos+32 > end:
                raise FormatError("Truncated index record")
            child, offset = struct.unpack_from("<II", index, pos)
            kind = index[pos+8]
            size = struct.unpack_from("<I", index, pos+9)[0]
            flag = index[pos+13]
            raw_size = struct.unpack_from("<I", index, pos+14)[0]
            name_size = struct.unpack_from("<H", index, pos+30)[0]
            if pos+32+name_size > end or not name_size:
                raise FormatError("Truncated or empty name")
            name_bytes = index[pos+32:pos+32+name_size]
            if b"\0" in name_bytes:
                raise FormatError("NUL in resource name")
            name = name_bytes.decode("cp1252", errors="strict")
            if (kind, name) in keys:
                raise FormatError("Duplicate resource key")
            keys.add((kind, name))
            if offset < 36 or offset % 4 or offset+size > len(data) or not size:
                raise FormatError("Payload outside DKD")
            marker = struct.unpack_from("<I", data, offset-4)[0]
            block_size = marker & ~3
            # Edited maps can retain a larger allocation than the live payload
            # (e.g. SINGLE06/DISCRIPTION has 10 bytes of allocation slack).
            if marker & 3 != 1 or block_size < size+4:
                raise FormatError("DKFM allocation marker does not fit payload")
            if offset-4+block_size > len(data):
                raise FormatError("Block padding outside DKD")
            if flag not in (0, 1) or (flag == 0 and size != raw_size):
                raise FormatError("Unsupported compression metadata")
            payload = data[offset:offset+size]
            entries.append({
                "name": name, "type": kind, "offset": offset,
                "stored_size": size, "raw_size": raw_size, "compression": flag,
                "allocation_size": block_size, "allocation_slack": block_size-4-size,
                "metadata_hex": index[pos+18:pos+30].hex(),
                "width_hint": struct.unpack_from("<H", index, pos+18)[0],
                "height_hint": struct.unpack_from("<H", index, pos+20)[0],
                "index_offset": pos, "sha256": hashlib.sha256(payload).hexdigest(),
            })
            pending.append(child)
            pos += 32+name_size
    ordered = sorted(entries, key=lambda entry: entry["offset"])
    for left, right in zip(ordered, ordered[1:]):
        if left["offset"]-4+left["allocation_size"] > right["offset"]-4:
            raise FormatError("Overlapping payload blocks")
    return sorted(entries, key=lambda entry: (entry["type"], entry["name"]))


def decode_dib(payload: bytes):
    from PIL import Image
    if len(payload) < 40:
        raise FormatError("Truncated DIB")
    header, width, height, planes, bits, compression = struct.unpack_from("<IiiHHI", payload)
    if header != 40 or planes != 1 or bits != 8 or compression != 0:
        raise FormatError("Only uncompressed 8-bit BITMAPINFOHEADER is supported")
    palette_count = struct.unpack_from("<I", payload, 32)[0] or 256
    if not 0 < width <= 8192 or not 0 < abs(height) <= 8192 or palette_count > 256:
        raise FormatError("Invalid DIB dimensions or palette")
    pixel_offset = 40+palette_count*4
    expected = pixel_offset+((width+3)//4)*4*abs(height)
    if len(payload) != expected:
        raise FormatError("DIB byte count does not match dimensions")
    bmp = b"BM"+struct.pack("<IHHI", 14+len(payload), 0, 0, 14+pixel_offset)+payload
    image = Image.open(io.BytesIO(bmp))
    image.load()
    return image.convert("RGB")


def decode_pcm(payload: bytes) -> tuple[dict, bytes]:
    if len(payload) < 26:
        raise FormatError("Truncated PCM header")
    encoding, channels, rate, byte_rate, align, bits, extra, count = struct.unpack_from("<HHIIHHHI", payload)
    if encoding != 1 or channels not in (1, 2) or bits not in (8, 16) or extra != 0:
        raise FormatError("Unsupported PCM layout")
    if not 8000 <= rate <= 192000 or align != channels*bits//8 or byte_rate != rate*align:
        raise FormatError("Invalid PCM format")
    if count != len(payload)-26 or count % align:
        raise FormatError("PCM byte count mismatch")
    return {"channels": channels, "sample_rate": rate, "bits": bits,
            "frames": count//align}, payload[26:]


def allocation_blocks(data: bytes) -> list[tuple[int, int]]:
    """Return live allocation payload offsets and padded lengths.

    DKFM has a 32-byte header and an 8-byte trailer. The low two allocation
    marker bits are flags; only the live (1) layout observed here is supported.
    """
    result, pos = [], 32
    while pos < len(data)-8:
        marker = struct.unpack_from("<I", data, pos)[0]
        size = marker & ~3
        if marker & 3 != 1 or size < 4 or pos+size > len(data)-8:
            raise FormatError("Unsupported DKFM allocation chain")
        result.append((pos+4, size-4))
        pos += size
    if pos != len(data)-8:
        raise FormatError("Invalid DKFM trailer boundary")
    return result


def decode_font(entry: dict, data: bytes, blocks: list[tuple[int, int]]) -> tuple[dict, list]:
    payload = data[entry["offset"]:entry["offset"]+entry["stored_size"]]
    if len(payload) < 112 or entry["compression"]:
        raise FormatError("Unsupported font header")
    count = struct.unpack_from("<H", payload, 100)[0]
    variants = struct.unpack_from("<H", payload)[0]
    metadata = bytes.fromhex(entry["metadata_hex"])
    expected_count, atlas_width, atlas_height = struct.unpack_from("<HHH", metadata)
    if count != expected_count or len(payload) != 112+10*count or not 1 <= variants <= 4:
        raise FormatError("Font count/variant layout mismatch")
    offsets = {offset: number for number, (offset, _) in enumerate(blocks)}
    number = offsets.get(entry["offset"], -1)
    if number < variants:
        raise FormatError("Font atlas allocation missing")
    atlases, sources = [], []
    for offset, padded_size in blocks[number-variants:number]:
        # Infer the exact DIB size from its validated header, excluding padding.
        if padded_size < 40:
            raise FormatError("Truncated atlas")
        header, width, height = struct.unpack_from("<Iii", data, offset)
        if header != 40 or (width, abs(height)) != (atlas_width, atlas_height):
            raise FormatError("Adjacent allocation does not match font atlas")
        colors = struct.unpack_from("<I", data, offset+32)[0] or 256
        size = 40+4*colors+((width+3)//4)*4*abs(height)
        if size > padded_size or padded_size-size > 3:
            raise FormatError("Font atlas size mismatch")
        raw = data[offset:offset+size]
        image = decode_dib(raw)
        atlases.append(image)
        sources.append({"offset": offset, "size": size,
                        "sha256": hashlib.sha256(raw).hexdigest()})
    glyphs = []
    for number in range(count):
        # The executable lookup (0x547100) reads code at +110 + 10*index.
        # The first record is the fallback glyph; ten reserved bytes trail it.
        x, y, width, height, code = struct.unpack_from("<5H", payload, 102+number*10)
        if x+width > atlas_width or y+height > atlas_height:
            raise FormatError("Glyph rectangle outside atlas")
        glyphs.append(dict(x=x, y=y, width=width, height=height, code=code))
    return {"atlas_width": atlas_width, "atlas_height": atlas_height,
            "variants": variants, "glyphs": glyphs, "atlas_sources": sources,
            "header_hex": payload[:102].hex(), "trailer_hex": payload[-10:].hex(),
            "unknowns": "Variant use, character encoding, baseline/advance and blending require executable/runtime confirmation."}, atlases


def export_known(entries: list[dict], data: bytes, dest: Path) -> dict:
    dest.mkdir(parents=True, exist_ok=False)
    counts = collections.Counter()
    blocks = allocation_blocks(data)
    for number, entry in enumerate(entries):
        if entry["type"] not in (1, 2, 3):
            counts["unsupported"] += 1
            continue
        payload = data[entry["offset"]:entry["offset"]+entry["stored_size"]]
        if entry["compression"]:
            if entry["raw_size"] > 256*1024*1024:
                raise FormatError("Decompressed resource exceeds 256 MiB quota")
            payload = decompress_block(payload, max_output=entry["raw_size"])
            if len(payload) != entry["raw_size"]:
                raise FormatError("Decompressed resource size mismatch")
            entry["decoded_sha256"] = hashlib.sha256(payload).hexdigest()
            counts["lz_decompressed"] += 1
        # Numeric filenames keep resource names entirely out of filesystem paths.
        stem = f"{number:06d}"
        try:
            if entry["type"] == 1:
                image = decode_dib(payload)
                path = dest/(stem+".png")
                image.save(path)
                entry["export_pixels"] = {"mode": "RGB", "width": image.width,
                    "height": image.height, "sha256": hashlib.sha256(image.tobytes()).hexdigest()}
                counts["png"] += 1
            elif entry["type"] == 2:
                fmt, samples = decode_pcm(payload)
                path = dest/(stem+".wav")
                with wave.open(str(path), "wb") as wav:
                    wav.setnchannels(fmt["channels"])
                    wav.setsampwidth(fmt["bits"]//8)
                    wav.setframerate(fmt["sample_rate"])
                    wav.writeframes(samples)
                entry["pcm"] = fmt
                entry["pcm"]["samples_sha256"] = hashlib.sha256(samples).hexdigest()
                counts["wav"] += 1
            else:
                font, atlases = decode_font(entry, data, blocks)
                for variant, image in enumerate(atlases):
                    atlas_path = dest/(stem+f"-font-{variant}.png")
                    image.save(atlas_path)
                    font["atlas_sources"][variant].update({
                        "export": atlas_path.name,
                        "export_sha256": hashlib.sha256(atlas_path.read_bytes()).hexdigest(),
                        "rgb_pixels_sha256": hashlib.sha256(image.tobytes()).hexdigest()})
                path = dest/(stem+"-font.json")
                path.write_text(json.dumps(font, indent=2)+"\n", encoding="utf-8")
                entry["font"] = font
                counts["font"] += 1
                counts["font_atlas_png"] += len(atlases)
            entry["export"] = path.name
            entry["export_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        except FormatError as error:
            entry["export_error"] = str(error)
            counts["unsupported_layout"] += 1
    return dict(counts)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index", type=Path)
    parser.add_argument("data", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--export-known", type=Path, metavar="NEW_DIRECTORY")
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("Output already exists")
    index, data = args.index.read_bytes(), args.data.read_bytes()
    entries = inspect_pair(index, data)
    report = {
        "format": "observed DKBT 0x0101 / DKFM 0x0101", "entries": entries,
        "sources": [{"path": str(p), "size_bytes": len(b),
                     "sha256": hashlib.sha256(b).hexdigest()}
                    for p, b in ((args.index, index), (args.data, data))],
        "type_counts": dict(collections.Counter(e["type"] for e in entries)),
        "compression_counts": dict(collections.Counter(e["compression"] for e in entries)),
        "unknowns": "Sprite RLE, font rendering rules, game semantics and AI remain unverified.",
    }
    if args.export_known:
        report["exports"] = export_known(entries, data, args.export_known)
    with args.output.open("x", encoding="utf-8") as out:
        json.dump(report, out, ensure_ascii=False, indent=2)
        out.write("\n")
    print(json.dumps({"entries": len(entries), "type_counts": report["type_counts"],
                      "exports": report.get("exports")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
