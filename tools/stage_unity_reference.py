#!/usr/bin/env python3
"""Stage a verified 800x600 diagnostic only; the native runtime does not load it.

This historical data does not define the native 1920x1080 game canvas.
Existing generated files are verified and reused; different contents are refused.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

REPOSITORY = Path(__file__).resolve().parents[1]
EXPECTED_SOURCE_SUFFIXES = {
    "installed/ancient.exe", "installed/missions/controlm.dkx",
    "installed/missions/controlm.dkd",
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def bottom_up_rgba(image):
    return image.convert("RGBA").transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes()


def stage_reference(reference, project, *, repository=REPOSITORY):
    reference, project, repository = Path(reference), Path(project), Path(repository)
    manifest_path = reference / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("size") != [800, 600] or manifest.get("runtime_screenshot") is not False:
        raise ValueError("Expected the measured 800x600 static reference")
    sources = manifest.get("sources", [])
    if len(sources) != 3:
        raise ValueError("Reference must identify all three original source files")
    suffixes = set()
    for source in sources:
        path = Path(source["path"])
        resolved = path if path.is_absolute() else repository / path
        expected_root = (repository / "reference/raw/ancient-conquest").resolve()
        try:
            relative = resolved.resolve().relative_to(expected_root)
        except ValueError as error:
            raise ValueError("Reference source is outside the expected original-data directory") from error
        suffixes.add(relative.as_posix())
        if sha256(resolved.read_bytes()) != source["sha256"]:
            raise ValueError("Original source hash changed: " + str(relative))
    if suffixes != EXPECTED_SOURCE_SUFFIXES:
        raise ValueError("Unexpected reference source set")

    png_bytes = (reference / "main-menu-state0.png").read_bytes()
    if sha256(png_bytes) != manifest["png_sha256"]:
        raise ValueError("Reference PNG hash mismatch")
    with Image.open(reference / "main-menu-state0.png") as image:
        if image.size != (800, 600) or sha256(image.convert("RGB").tobytes()) != manifest["pixels_sha256"]:
            raise ValueError("Reference dimensions or pixel hash mismatch")
        payload = bottom_up_rgba(image)
    output = project / "Assets/Resources/LegacyReferenceGenerated"
    metadata = {
        "schema_version": 1, "kind": "historical 800x600 diagnostic data",
        "width": 800, "height": 600, "format": "RGBA32",
        "row_order": "bottom-to-top", "payload_sha256": sha256(payload),
        "source_png_sha256": manifest["png_sha256"],
        "source_manifest_sha256": sha256(manifest_bytes),
        "runtime_reference_comparison": "not yet performed",
    }
    encoded = (json.dumps(metadata, indent=2) + "\n").encode()
    targets = {output / "MenuRgba.bytes": payload, output / "MenuRgbaManifest.json": encoded}
    for path, data in targets.items():
        if path.is_symlink() or (path.exists() and path.read_bytes() != data):
            raise FileExistsError("Refusing to overwrite different staged data: " + str(path))
    if output.resolve() != output.absolute():
        raise ValueError("Staging path must not contain symlinks")
    output.mkdir(parents=True, exist_ok=True)
    for path, data in targets.items():
        if not path.exists():
            with path.open("xb") as destination:
                destination.write(data)
    return metadata


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path,
                        default=REPOSITORY / "artifacts/original/main-menu-reference")
    parser.add_argument("--project", type=Path,
                        default=REPOSITORY / "artifacts/legacy-unity-reference",
                        help="Diagnostic staging root; the native Unity renderer does not load this data")
    args = parser.parse_args(argv)
    print(json.dumps(stage_reference(args.reference, args.project), indent=2))


if __name__ == "__main__":
    main()
