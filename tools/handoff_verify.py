"""Read-only handoff verification;stdlib-only and usable before environment setup."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import tempfile

CHECKPOINT = 'docs/evidence/milestone-20261104-source-app-activation.json'
CHECKPOINT_SHA = '97300b269a9662eeeffffbdb8ed9ff6c359f1a21d2e27612beac39efd5925669'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


def contained(root, name):
    path = root / name
    if Path(name).is_absolute() or '..' in Path(name).parts:
        raise ValueError('Unsafe manifest path: ' + name)
    return path


def verify_manifest(root, files):
    failures = []
    for name, meta in files.items():
        path = contained(root, name)
        if meta.get('type') == 'symlink':
            if not path.is_symlink() or os.readlink(path) != meta['target']:
                failures.append(name)
        elif not path.is_file() or path.is_symlink() or path.stat().st_size != meta['bytes'] or digest(path) != meta['sha256']:
            failures.append(name)
    if failures:
        raise AssertionError('Missing/changed files: ' + ', '.join(failures[:12]))
    return len(files)


def verify(root, include_transfer=True):
    root = root.resolve()
    assert digest(root / CHECKPOINT) == CHECKPOINT_SHA, 'Checkpoint manifest differs'
    project = json.loads((root / 'artifacts/source-app-activation/project-frozen.json').read_text())
    assert verify_manifest(root, project) == 279
    checkpoint = json.loads((root / CHECKPOINT).read_text())
    source_root = root / 'reference/raw/ancient-conquest'
    for name, sha in checkpoint['original_source_hashes_verified'].items():
        assert digest(source_root / name) == sha, 'Original source differs: ' + name
    version = (root / 'Unity/AncientConquest/ProjectSettings/ProjectVersion.txt').read_text()
    assert 'm_EditorVersion: 6000.3.27f2\n' in version
    manifest = root / 'handoff/TRANSFER_MANIFEST.json'
    transferred = 0
    tools = 0
    if include_transfer and manifest.exists():
        data = json.loads(manifest.read_text())
        transferred = verify_manifest(root, data['project_files'])
        tools = verify_manifest(root.parent / 'toolchains', data['toolchain_files'])
    assert (root / 'CLAUDE.md').is_file() and (root / 'handoff/STAN_I_PLAN.md').is_file()
    return dict(passed=True, project_files=279, original_sources=len(checkpoint['original_source_hashes_verified']),
                transferred_project_files=transferred, transferred_toolchain_files=tools,
                editor='6000.3.27f2', read_only=True,
                physical_windows11_validated=False, full_game_complete=False)


def self_test():
    detected = []
    with tempfile.TemporaryDirectory(prefix='handoff-verifier-') as temporary:
        root = Path(temporary)
        path = root / 'sample.txt'
        path.write_bytes(b'original-transfer-data')
        record = {'sample.txt': dict(bytes=path.stat().st_size, sha256=digest(path))}
        assert verify_manifest(root, record) == 1
        path.write_bytes(b'changed-transfer-data!')
        try:
            verify_manifest(root, record)
        except AssertionError:
            detected.append('changed_content')
        path.unlink()
        try:
            verify_manifest(root, record)
        except AssertionError:
            detected.append('missing_file')
        try:
            verify_manifest(root, {'../escape': dict(bytes=1, sha256='')})
        except ValueError:
            detected.append('path_traversal')
    assert len(detected) == 3
    return dict(passed=True, negative_controls=detected)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--baseline-only', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    result = self_test() if args.self_test else verify(args.root, not args.baseline_only)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
