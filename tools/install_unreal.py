#!/usr/bin/env python3
"""Download a verified stable UE5 source release from Epic's official repository.

Requires existing Epic/GitHub access. This does not build the editor or install a
Windows toolchain. No tokens, account linking, or third-party mirrors are used.
"""

from __future__ import annotations

import argparse
import ctypes
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


REMOTE = "https://github.com/EpicGames/UnrealEngine.git"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
_TAG = re.compile(r"5\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)-release\Z")
_COMMIT = re.compile(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})\Z")


@dataclass(frozen=True)
class Release:
    version: tuple[int, int, int]
    tag: str
    commit: str


def select_release(text: str) -> Release:
    """Select the numerically newest stable UE5 tag, peeling annotated tags."""
    refs: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) != 2 or not _COMMIT.fullmatch(fields[0]):
            continue
        commit, ref = fields
        if not ref.startswith("refs/tags/"):
            continue
        tag = ref.removeprefix("refs/tags/")
        peeled = tag.endswith("^{}")
        if peeled:
            tag = tag[:-3]
        if not _TAG.fullmatch(tag):
            continue
        key = "peeled" if peeled else "object"
        entries = refs.setdefault(tag, {})
        normalized = commit.lower()
        if key in entries and entries[key] != normalized:
            raise ValueError(f"Conflicting official refs for {tag}")
        entries[key] = normalized
    candidates = []
    for tag, entries in refs.items():
        if "object" not in entries:
            continue
        match = _TAG.fullmatch(tag)
        assert match is not None
        version = (5, int(match[1]), int(match[2]))
        candidates.append(Release(version, tag, entries.get("peeled", entries["object"])))
    if not candidates:
        raise ValueError("No stable UE5 release tags were returned by Epic's repository")
    return max(candidates, key=lambda release: release.version)


def _git(*args: str, cwd: Path | None = None) -> str:
    environment = os.environ.copy()
    environment["GIT_TERMINAL_PROMPT"] = "0"
    try:
        result = subprocess.run(
            ["git", *args], cwd=cwd, env=environment, capture_output=True,
            text=True, check=False,
        )
    except FileNotFoundError as error:
        raise RuntimeError("Git is required but was not found") from error
    if result.returncode:
        # Git/proxy output can contain authentication data; do not echo it.
        raise RuntimeError(
            f"Git operation failed (exit {result.returncode}). Check network policy "
            "and authenticated access to EpicGames/UnrealEngine. Epic/GitHub account "
            "linking cannot be performed by this installer."
        )
    return result.stdout.strip()


def discover_release() -> Release:
    return select_release(_git("ls-remote", "--tags", REMOTE))


def _validate_release(release: Release) -> None:
    match = _TAG.fullmatch(release.tag)
    if (
        match is None or release.version != (5, int(match[1]), int(match[2]))
        or not _COMMIT.fullmatch(release.commit)
    ):
        raise ValueError("Invalid stable UE5 release identity")


def verify_engine(path: Path, release: Release) -> None:
    """Raise on a different source commit or Major/Minor/Patch version."""
    _validate_release(release)
    root = Path(path).resolve(strict=True)
    version_file = root / "Engine" / "Build" / "Build.version"
    with version_file.open(encoding="utf-8-sig") as stream:
        metadata = json.load(stream)
    if not isinstance(metadata, dict):
        raise RuntimeError("Engine version metadata must be a JSON object")
    fields = [metadata.get(key) for key in ("MajorVersion", "MinorVersion", "PatchVersion")]
    if any(type(value) is not int for value in fields) or tuple(fields) != release.version:
        raise RuntimeError("Downloaded engine version does not match the selected UE5 tag")
    git_root = Path(_git("rev-parse", "--show-toplevel", cwd=root)).resolve()
    if git_root != root:
        raise RuntimeError("Engine source is not a standalone Git checkout")
    commit = _git("rev-parse", "--verify", "HEAD^{commit}", cwd=root)
    if commit.lower() != release.commit.lower():
        raise RuntimeError("Downloaded engine commit differs from the resolved official tag")


def _rename_without_overwrite(source: Path, destination: Path) -> None:
    """Publish atomically and refuse even a concurrently created empty directory."""
    if sys.platform.startswith("linux"):
        libc = ctypes.CDLL(None, use_errno=True)
        try:
            rename = libc.renameat2
        except AttributeError as error:
            raise RuntimeError("Atomic no-overwrite rename is unavailable on this host") from error
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        if rename(-100, os.fsencode(source), -100, os.fsencode(destination), 1) != 0:
            error_number = ctypes.get_errno()
            raise OSError(error_number, os.strerror(error_number), str(destination))
    elif os.name == "nt":
        os.rename(source, destination)  # Windows refuses an existing destination.
    else:
        raise RuntimeError("Atomic no-overwrite installation is unsupported on this host")


def install_release(destination: Path, release: Release) -> Path:
    """Clone into a temporary sibling, verify, then atomically install once."""
    _validate_release(release)
    requested = Path(destination).expanduser().absolute()
    if os.path.lexists(requested):
        raise FileExistsError(f"Destination already exists; nothing overwritten: {requested}")
    target = requested.resolve()
    project = PROJECT_ROOT.resolve()
    if target == project or project in target.parents:
        raise ValueError("Engine destination must be outside the project checkout")
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.download-", dir=target.parent))
    try:
        _git("clone", "--depth=1", "--single-branch", "--branch", release.tag,
             "--no-tags", REMOTE, str(staging))
        verify_engine(staging, release)
        manifest = {
            "remote": REMOTE, "version": list(release.version),
            "tag": release.tag, "commit": release.commit.lower(),
        }
        with (staging / ".git" / "codex-unreal-install.json").open("x", encoding="utf-8") as stream:
            json.dump(manifest, stream, indent=2)
            stream.write("\n")
        _rename_without_overwrite(staging, target)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-access", action="store_true", help="Discover the release without writing files")
    parser.add_argument("--destination", type=Path, default=Path("/workspace/toolchains/UnrealEngine"))
    args = parser.parse_args(argv)
    try:
        release = discover_release()
        print(json.dumps({"version": list(release.version), "tag": release.tag, "commit": release.commit}))
        if args.check_access:
            return 0
        target = install_release(args.destination, release)
        print(f"Verified official UE5 source downloaded to {target}")
        print("The editor is NOT built. A Windows toolchain is NOT installed.")
        return 0
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Installation stopped: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
