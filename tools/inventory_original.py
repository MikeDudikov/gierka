#!/usr/bin/env python3
"""Inventory an original-media ZIP without extracting or executing its files.

Filename extensions identify candidates only. Metadata inventory does not verify
contents; --verify-contents performs bounded streaming CRC and SHA-256 checks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import ntpath
import os
from pathlib import Path, PurePosixPath
import sys
import zipfile
import zlib


DEFAULT_MAX_EXPANDED_BYTES = 2 * 1024**3
_CHUNK_BYTES = 1024 * 1024
_CANDIDATE_EXTENSIONS = {
    "disc_image_candidate": {".iso", ".img", ".bin", ".cue", ".mdf", ".mds", ".nrg", ".ccd", ".sub"},
    "source_code_candidate": {".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".cs", ".pas", ".asm", ".s", ".py", ".lua"},
    "executable_candidate": {".exe", ".dll", ".com", ".msi", ".bat", ".cmd", ".ps1", ".sh"},
    "font_candidate": {".ttf", ".otf", ".fon", ".fnt", ".woff", ".woff2"},
    "nested_archive_candidate": {".zip", ".7z", ".rar", ".tar", ".gz", ".bz2", ".xz"},
}
_READ_ERRORS = (OSError, RuntimeError, ValueError, EOFError, zipfile.BadZipFile,
                NotImplementedError, zlib.error, lzma.LZMAError)


def path_issues(name: str) -> list[str]:
    """Identify paths unsafe for later cross-platform extraction; extract nothing."""
    issues = []
    if "\0" in name:
        issues.append("nul_byte")
    normalized = name.replace("\\", "/")
    if normalized.startswith("//"):
        issues.append("windows_unc_path")
    if normalized.startswith("/"):
        issues.append("absolute_path")
    drive, _ = ntpath.splitdrive(name)
    if drive and not normalized.startswith("//"):
        issues.append("windows_drive_path")
    if ".." in normalized.split("/"):
        issues.append("parent_traversal")
    return issues


def candidate_labels(name: str) -> list[str]:
    suffix = PurePosixPath(name.replace("\\", "/")).suffix.casefold()
    return [label for label, extensions in _CANDIDATE_EXTENSIONS.items() if suffix in extensions]


def _failure(report: dict, code: str, detail: str) -> dict:
    report["success"] = False
    report["errors"].append({"code": code, "detail": detail})
    return report


def inventory_zip(source: Path, *, verify_contents: bool = False,
                  max_expanded_bytes: int = DEFAULT_MAX_EXPANDED_BYTES) -> dict:
    """Return a JSON-compatible report, including explicit failure/integrity state.

    Metadata may describe archives larger than the limit without expanding them.
    The limit is enforced before and during optional content verification.
    """
    if type(max_expanded_bytes) is not int or max_expanded_bytes < 0:
        raise ValueError("max_expanded_bytes must be a nonnegative integer")
    source = Path(source)
    report = {
        "schema_version": 1,
        "success": True,
        "source": {"path": str(source.absolute()), "size_bytes": None, "sha256": None},
        "inventory_status": "incomplete",
        "content_integrity": "not_checked",
        "classification_basis": "filename_extension_only; candidate labels do not establish file type or usable game/source content",
        "members": [],
        "candidates": {label: [] for label in _CANDIDATE_EXTENSIONS},
        "totals": {"members": 0, "compressed_bytes": 0, "uncompressed_bytes": 0,
                   "encrypted_members": 0, "unsafe_members": 0},
        "verification": {"requested": verify_contents, "status": "not_requested",
                         "max_expanded_bytes": max_expanded_bytes,
                         "verified_members": 0, "bytes_read": 0},
        "errors": [],
    }
    try:
        with source.open("rb") as stream:
            before = os.fstat(stream.fileno())
            report["source"]["size_bytes"] = before.st_size
            source_hash = hashlib.sha256()
            while chunk := stream.read(_CHUNK_BYTES):
                source_hash.update(chunk)
            report["source"]["sha256"] = source_hash.hexdigest()
            stream.seek(0)
            with zipfile.ZipFile(stream) as archive:
                infos = archive.infolist()
                for index, info in enumerate(infos):
                    name = info.orig_filename  # Retains a NUL that ZipInfo.filename truncates.
                    issues = path_issues(name)
                    labels = [] if info.is_dir() else candidate_labels(name)
                    encryption_flags = {
                        "encrypted": bool(info.flag_bits & 1),
                        "strong_encryption": bool(info.flag_bits & (1 << 6)),
                        "masked_headers": bool(info.flag_bits & (1 << 13)),
                    }
                    encrypted = any(encryption_flags.values())
                    member = {
                        "index": index, "path": name, "is_directory": info.is_dir(),
                        "compressed_bytes": info.compress_size, "uncompressed_bytes": info.file_size,
                        "compression_method": info.compress_type, "general_purpose_flags": info.flag_bits,
                        "encrypted": encrypted, "encryption_flags": encryption_flags,
                        "unsafe_path_issues": issues, "candidate_labels": labels,
                        "crc32_declared": f"{info.CRC:08x}", "content_integrity": "not_checked",
                        "content_sha256": None,
                    }
                    report["members"].append(member)
                    for label in labels:
                        report["candidates"][label].append({"index": index, "path": name})
                    totals = report["totals"]
                    totals["members"] += 1
                    totals["compressed_bytes"] += info.compress_size
                    totals["uncompressed_bytes"] += info.file_size
                    totals["encrypted_members"] += int(encrypted)
                    totals["unsafe_members"] += int(bool(issues))
                report["inventory_status"] = "complete"
                if verify_contents:
                    _verify_members(archive, infos, report)
            after = os.fstat(stream.fileno())
            if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_size, after.st_mtime_ns, after.st_ctime_ns
            ):
                report["content_integrity"] = "not_checked"
                report["verification"]["status"] = "failed"
                _failure(report, "source_changed", "Archive changed during inventory; hashes are not a stable-source verification")
    except _READ_ERRORS as error:
        report["verification"]["status"] = "failed" if verify_contents else "not_requested"
        _failure(report, "archive_read_failed", f"{type(error).__name__}: {error}")
    return report


def _verify_members(archive: zipfile.ZipFile, infos: list[zipfile.ZipInfo], report: dict) -> None:
    verification = report["verification"]
    totals = report["totals"]
    if totals["unsafe_members"] or totals["encrypted_members"]:
        verification["status"] = "blocked"
        _failure(report, "unsafe_or_encrypted_members", "Content verification refuses unsafe paths or encrypted members")
        return
    if totals["uncompressed_bytes"] > verification["max_expanded_bytes"]:
        verification["status"] = "blocked"
        _failure(report, "expanded_size_limit", "Declared expanded size exceeds the verification limit; no member contents were read")
        return
    verification["status"] = "in_progress"
    for info, member in zip(infos, report["members"]):
        digest = hashlib.sha256()
        member_bytes = 0
        try:
            with archive.open(info, "r") as member_stream:
                while True:
                    remaining = verification["max_expanded_bytes"] - verification["bytes_read"]
                    chunk = member_stream.read(min(_CHUNK_BYTES, remaining + 1))
                    if not chunk:
                        break
                    verification["bytes_read"] += len(chunk)
                    member_bytes += len(chunk)
                    if verification["bytes_read"] > verification["max_expanded_bytes"]:
                        raise ValueError("Actual expanded size exceeds the verification limit")
                    digest.update(chunk)
            if member_bytes != info.file_size:
                raise ValueError("Read size differs from the declared ZIP member size")
        except _READ_ERRORS as error:
            member["content_integrity"] = "failed"
            report["content_integrity"] = "failed"
            verification["status"] = "failed"
            _failure(report, "member_verification_failed", f"Member {member['index']}: {type(error).__name__}: {error}")
            return
        member["content_integrity"] = "verified"
        member["content_sha256"] = digest.hexdigest()
        verification["verified_members"] += 1
    report["content_integrity"] = "verified"
    verification["status"] = "complete"


def _nonnegative_integer(value: str) -> int:
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Expected a nonnegative byte count") from error
    if number < 0:
        raise argparse.ArgumentTypeError("Expected a nonnegative byte count")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Original ZIP to inspect read-only")
    parser.add_argument("--verify-contents", action="store_true", help="Stream member contents, verify ZIP CRC and calculate SHA-256")
    parser.add_argument("--max-expanded-bytes", type=_nonnegative_integer, default=DEFAULT_MAX_EXPANDED_BYTES)
    parser.add_argument("--output", type=Path, help="Create a new JSON report; existing files are never overwritten")
    args = parser.parse_args(argv)
    report = inventory_zip(args.source, verify_contents=args.verify_contents,
                           max_expanded_bytes=args.max_expanded_bytes)
    serialized = json.dumps(report, ensure_ascii=True, indent=2) + "\n"
    try:
        if args.output:
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(serialized)
        else:
            sys.stdout.write(serialized)
    except OSError as error:
        print(f"Could not create inventory report: {error}", file=sys.stderr)
        return 1
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
