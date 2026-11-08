#!/usr/bin/env python3
"""Read the PQ installer on the supplied Ancient Conquest CD without executing it.

The decoder is derived from SETUP.EXE at virtual address 0x408b20. It is not a
general installer reader. Reports and extracted directories must be new paths.
"""

import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
import struct
import sys


class SetupFormatError(ValueError):
    """Malformed or unsupported installer data."""


def decompress_block(source, max_output=131072):
    """Decode one independently terminated PQ LZ block, rejecting trailing data.

    Sixteen flag bits are consumed least-significant first. The original reader
    eagerly loads the next flag word immediately after consuming bit sixteen.
    """
    if max_output < 0:
        raise SetupFormatError("Negative output limit")
    pos = 0

    def take(count):
        nonlocal pos
        if pos + count > len(source):
            raise SetupFormatError("Truncated compressed block")
        value = source[pos:pos + count]
        pos += count
        return value

    flags = int.from_bytes(take(2), "little")
    remaining = 16

    def bit():
        nonlocal flags, remaining
        value = flags & 1
        flags >>= 1
        remaining -= 1
        if not remaining:
            flags = int.from_bytes(take(2), "little")
            remaining = 16
        return value

    output = bytearray()
    while True:
        if bit():
            if len(output) >= max_output:
                raise SetupFormatError("Decompressed block exceeds output limit")
            output.extend(take(1))
            continue
        if bit():
            word = int.from_bytes(take(2), "little")
            length = ((word >> 8) & 7) + 2
            displacement = -8192 | ((word & 0xF800) >> 3) | (word & 0xFF)
            if length == 2:
                length = take(1)[0]
                if not length:
                    if pos != len(source):
                        raise SetupFormatError("Trailing bytes after block terminator")
                    return bytes(output)
                if length == 1:
                    continue
                length += 1
        else:
            length = ((bit() << 1) | bit()) + 2
            displacement = take(1)[0] - 256
        if -displacement > len(output):
            raise SetupFormatError("Back-reference precedes current block")
        if len(output) + length > max_output:
            raise SetupFormatError("Decompressed block exceeds output limit")
        for _ in range(length):
            output.append(output[len(output) + displacement])


def _cstring(data):
    if b"\0" not in data:
        raise SetupFormatError("Unterminated path field")
    return data.split(b"\0", 1)[0].decode("cp1252")


def _relative_path(name, folder, directory=False):
    if directory:
        if name != "*EMPTY":
            raise SetupFormatError("Unsupported zero-block entry")
        raw = folder.rstrip("\\")
    else:
        if any(char in name for char in "\\/"):
            raise SetupFormatError("Filename contains a directory separator")
        raw = folder + name
    win = PureWindowsPath(raw)
    parts = raw.replace("\\", "/").split("/")
    if (not raw or win.is_absolute() or win.drive or win.root or
            any(not part or part in (".", "..") or
                part.rstrip(" .") != part or any(c in part for c in ':*?<>|"') or
                any(ord(c) < 32 for c in part) for part in parts)):
        raise SetupFormatError("Unsafe installer path")
    if folder and not folder.endswith("\\"):
        raise SetupFormatError("Unsupported folder separator")
    return "/".join(parts)


def parse_setup(source):
    """Return checked entry metadata; payload offsets cover the archive exactly."""
    if len(source) < 91 or source[:20] != b"PQSetup data for AC\0":
        raise SetupFormatError("Unsupported PQ setup header")
    toc_offset, count = struct.unpack_from("<II", source, len(source) - 8)
    if not (83 <= toc_offset <= len(source) - 8) or count > 10000:
        raise SetupFormatError("Invalid table location or entry count")
    entries = []
    seen = set()
    cursor = toc_offset
    payload = 83
    for index in range(count):
        if cursor + 559 > len(source) - 8:
            raise SetupFormatError("Truncated entry header")
        length = struct.unpack_from("<I", source, cursor)[0]
        block_count = struct.unpack_from("<I", source, cursor + 551)[0]
        end = cursor + length + 4
        if length != 555 + 4 * block_count or end > len(source) - 8:
            raise SetupFormatError("Invalid variable entry length")
        record = source[cursor:end]
        compressed = record[8]
        if compressed not in (0, 1):
            raise SetupFormatError("Unsupported compression flag")
        name = _cstring(record[10:271])
        folder = _cstring(record[271:531])
        directory = not block_count
        path = _relative_path(name, folder, directory)
        if path.casefold() in seen:
            raise SetupFormatError("Duplicate installer path")
        seen.add(path.casefold())
        sizes = list(struct.unpack_from("<" + "I" * block_count, record, 559))
        if any(size == 0 for size in sizes) or payload + sum(sizes) > toc_offset:
            raise SetupFormatError("Invalid compressed payload bounds")
        entries.append({"path": path, "directory": directory,
                        "compressed": bool(compressed), "record_offset": cursor,
                        "payload_offset": payload, "stored_block_sizes": sizes})
        payload += sum(sizes)
        cursor = end
    if cursor != len(source) - 8 or payload != toc_offset:
        raise SetupFormatError("Table or payload coverage mismatch")
    return entries


def inspect_setup(source_path, extract_to=None, max_bytes=2 * 1024**3):
    source_path = Path(source_path)
    if source_path.stat().st_size > 64 * 1024**2:
        raise SetupFormatError("Installer exceeds supported input limit")
    source = source_path.read_bytes()
    entries = parse_setup(source)
    if max_bytes < 0:
        raise SetupFormatError("Negative total output limit")
    if extract_to is not None:
        extract_to = Path(extract_to)
        if extract_to.exists() or extract_to.is_symlink():
            raise SetupFormatError("Extraction directory must not exist")
        if extract_to.parent.resolve() != extract_to.parent.absolute():
            raise SetupFormatError("Extraction parent must not contain symlinks")
        extract_to.mkdir()
    total_bytes = 0
    for entry in entries:
        if entry["directory"]:
            if extract_to:
                (extract_to / entry["path"]).mkdir(parents=True, exist_ok=True)
            continue
        cursor = entry["payload_offset"]
        digest = hashlib.sha256()
        file_bytes = 0
        destination = None
        if extract_to:
            target = extract_to / entry["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            destination = target.open("xb")
        try:
            for size in entry["stored_block_sizes"]:
                block = source[cursor:cursor + size]
                cursor += size
                if entry["compressed"]:
                    block = decompress_block(block)
                if total_bytes + len(block) > max_bytes:
                    raise SetupFormatError("Total decoded data exceeds limit")
                digest.update(block)
                file_bytes += len(block)
                total_bytes += len(block)
                if destination:
                    destination.write(block)
        finally:
            if destination:
                destination.close()
        entry["size_bytes"] = file_bytes
        entry["sha256"] = digest.hexdigest()
    return {"format": "Ancient Conquest PQ setup", "success": True,
            "source": {"path": str(source_path), "size_bytes": len(source),
                       "sha256": hashlib.sha256(source).hexdigest()},
            "totals": {"files": sum(not e["directory"] for e in entries),
                       "directories": sum(e["directory"] for e in entries),
                       "decoded_bytes": total_bytes},
            "integrity": "All streams bounded and terminated; no internal checksum identified",
            "entries": entries}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--extract-to", type=Path)
    parser.add_argument("--max-bytes", type=int, default=2 * 1024**3)
    args = parser.parse_args(argv)
    try:
        if args.output and (args.output.exists() or args.output.is_symlink()):
            raise SetupFormatError("Report already exists")
        report = inspect_setup(args.source, args.extract_to, args.max_bytes)
        text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(text)
        else:
            print(text, end="")
        return 0
    except (OSError, ValueError, struct.error) as exc:
        print(f"Setup inspection failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
