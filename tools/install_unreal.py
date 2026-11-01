#!/usr/bin/env python3
"""Download pinned UE5 sources from Epic or an explicitly chosen GitHub fork.

Requires existing Epic/GitHub access. This does not build the editor or install a
Windows toolchain. Fork contents are not certified as the latest upstream release.
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
_REPOSITORY = re.compile(r"https://github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})/([A-Za-z0-9_.-]{1,104})\Z")


@dataclass(frozen=True)
class Release:
    version: tuple[int, int, int]
    tag: str
    commit: str


@dataclass(frozen=True)
class SourceSnapshot:
    ref: str
    commit: str


def validate_repository(repository: str) -> str:
    """Accept only credential-free HTTPS GitHub repositories; normalize .git."""
    match = _REPOSITORY.fullmatch(repository)
    if match is None:
        raise ValueError("Repository must be a credential-free https://github.com/owner/repository URL")
    owner, name = match.groups()
    name = name.removesuffix(".git")
    if not name or name in {".", ".."} or len(name) > 100:
        raise ValueError("Invalid GitHub repository name")
    return f"https://github.com/{owner}/{name}.git"


def _repository(repository: str | None) -> str:
    # The built-in constant can be patched to a local fixture by offline tests.
    return REMOTE if repository is None else validate_repository(repository)


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
            raise ValueError(f"Conflicting refs for {tag}")
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
        raise ValueError("No stable UE5 release tags were returned by the selected repository; no branch fallback was used")
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
            "and authenticated access to the selected repository. Epic/GitHub account "
            "linking cannot be performed by this installer."
        )
    return result.stdout.strip()


def discover_release(repository: str | None = None) -> Release:
    """Discover the highest stable UE5 tag available in the chosen repository."""
    return select_release(_git("ls-remote", "--tags", _repository(repository)))


def _validate_ref(ref: str) -> None:
    if _COMMIT.fullmatch(ref):
        return
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", ref) or ".." in ref:
        raise ValueError("Invalid explicit Git ref")
    if any(not part or part.startswith(".") or part.endswith((".", ".lock")) for part in ref.split("/")):
        raise ValueError("Invalid explicit Git ref")


def discover_snapshot(repository: str | None, ref: str) -> SourceSnapshot:
    """Resolve an explicit branch/tag or pin an exact SHA; never call it latest."""
    chosen = _repository(repository)
    _validate_ref(ref)
    if _COMMIT.fullmatch(ref):
        # Check access now. Fetch later proves the explicitly supplied SHA exists.
        _git("ls-remote", chosen, "HEAD")
        return SourceSnapshot(ref.lower(), ref.lower())
    if ref == "HEAD" or ref.startswith(("refs/heads/", "refs/tags/")):
        names = [ref]
    elif ref.startswith("refs/"):
        raise ValueError("Only branch or tag refs are supported")
    else:
        names = [f"refs/heads/{ref}", f"refs/tags/{ref}"]
    queries = names + [name + "^{}" for name in names if name.startswith("refs/tags/")]
    text = _git("ls-remote", chosen, *queries)
    refs = {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) == 2 and _COMMIT.fullmatch(fields[0]) and fields[1] in queries:
            if fields[1] in refs and refs[fields[1]] != fields[0].lower():
                raise ValueError("Conflicting explicit ref results")
            refs[fields[1]] = fields[0].lower()
    found = [name for name in names if name in refs]
    if len(found) != 1:
        raise ValueError("Explicit ref is missing or ambiguous; use refs/heads/name or refs/tags/name")
    selected = found[0]
    return SourceSnapshot(selected, refs.get(selected + "^{}", refs[selected]))


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
    _verify_source(path, release.commit, release.version)


def _verify_source(path: Path, expected_commit: str, expected_version: tuple[int, int, int] | None = None) -> tuple[int, int, int]:
    root = Path(path).resolve(strict=True)
    version_file = root / "Engine" / "Build" / "Build.version"
    with version_file.open(encoding="utf-8-sig") as stream:
        metadata = json.load(stream)
    if not isinstance(metadata, dict):
        raise RuntimeError("Engine version metadata must be a JSON object")
    fields = [metadata.get(key) for key in ("MajorVersion", "MinorVersion", "PatchVersion")]
    if any(type(value) is not int for value in fields) or fields[0] != 5 or any(value < 0 for value in fields):
        raise RuntimeError("Downloaded source version must contain numeric UE5 Major/Minor/Patch values")
    version = tuple(fields)
    if expected_version is not None and version != expected_version:
        raise RuntimeError("Downloaded engine version does not match the selected UE5 tag")
    git_root = Path(_git("rev-parse", "--show-toplevel", cwd=root)).resolve()
    if git_root != root:
        raise RuntimeError("Engine source is not a standalone Git checkout")
    commit = _git("rev-parse", "--verify", "HEAD^{commit}", cwd=root)
    if commit.lower() != expected_commit.lower():
        raise RuntimeError("Downloaded engine commit differs from the pinned source commit")
    return version


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


def _new_staging(destination: Path) -> tuple[Path, Path]:
    requested = Path(destination).expanduser().absolute()
    if os.path.lexists(requested):
        raise FileExistsError(f"Destination already exists; nothing overwritten: {requested}")
    target = requested.resolve()
    project = PROJECT_ROOT.resolve()
    if target == project or project in target.parents:
        raise ValueError("Engine destination must be outside the project checkout")
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.download-", dir=target.parent))
    return target, staging


def install_release(destination: Path, release: Release, repository: str | None = None) -> Path:
    """Clone into a temporary sibling, verify, then atomically install once."""
    _validate_release(release)
    chosen = _repository(repository)
    target, staging = _new_staging(destination)
    try:
        _git("clone", "--depth=1", "--single-branch", "--branch", release.tag,
             "--no-tags", chosen, str(staging))
        verify_engine(staging, release)
        manifest = {
            "remote": chosen, "version": list(release.version), "source_kind": "stable-tag",
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


def install_snapshot(destination: Path, snapshot: SourceSnapshot, repository: str | None = None) -> Path:
    """Fetch the pinned commit for an explicitly requested source snapshot."""
    _validate_ref(snapshot.ref)
    if not _COMMIT.fullmatch(snapshot.commit):
        raise ValueError("Invalid pinned snapshot commit")
    chosen = _repository(repository)
    target, staging = _new_staging(destination)
    try:
        _git("init", "--quiet", str(staging))
        _git("remote", "add", "origin", chosen, cwd=staging)
        _git("fetch", "--depth=1", "--no-tags", "origin", snapshot.commit, cwd=staging)
        _git("checkout", "--quiet", "--detach", "FETCH_HEAD", cwd=staging)
        version = _verify_source(staging, snapshot.commit)
        manifest = {
            "remote": chosen, "version": list(version), "source_kind": "snapshot",
            "ref": snapshot.ref, "commit": snapshot.commit.lower(),
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
    parser.add_argument("--repository", default=REMOTE, help="Explicit HTTPS GitHub source repository; default: EpicGames/UnrealEngine")
    parser.add_argument("--ref", help="Explicit branch, tag or full SHA snapshot; never a claim of latest upstream")
    args = parser.parse_args(argv)
    try:
        chosen = validate_repository(args.repository)
        print(f"Source repository: {chosen}")
        if chosen.casefold() != REMOTE.casefold():
            print("Explicit GitHub source selected; equivalence to official upstream is NOT verified.")
        if args.ref:
            snapshot = discover_snapshot(chosen, args.ref)
            print(json.dumps({"source_kind": "snapshot", "ref": snapshot.ref, "commit": snapshot.commit}))
            print("Pinned source snapshot; latest upstream version is NOT verified.")
            if args.check_access:
                return 0
            target = install_snapshot(args.destination, snapshot, chosen)
        else:
            release = discover_release(chosen)
            print(json.dumps({"version": list(release.version), "tag": release.tag, "commit": release.commit}))
            print("Selected the highest stable UE5 tag available in this repository.")
            if args.check_access:
                return 0
            target = install_release(args.destination, release, chosen)
        print(f"Pinned UE5 source downloaded and commit/version checked at {target}")
        print("The editor is NOT built. A Windows toolchain is NOT installed.")
        return 0
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Installation stopped: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
