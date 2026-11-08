"""Create a complete private transfer archive, then verify every payload without extraction."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path('/workspace/toolchains')
BUNDLE_ROOT = 'AncientConquest-ClaudeCode'
SKIP_DIRS = {'Library', 'Temp', 'Obj', 'Logs', 'UserSettings', '.venv', '__pycache__'}
SKIP_NAMES = {'TRANSFER_MANIFEST.json', 'index.lock', 'config-draft-verified.json',
              'previous-start-skill.txt', 'next-start-skill.txt'}
TOOLCHAINS = {
    'mono-unity-6000.3.27f2': TOOLS / 'Unity/6000.3.27f2/Editor/Data/MonoBleedingEdge',
    'wine11-root': TOOLS / 'wine11-root',
    'original-vm': TOOLS / 'original-vm',
    'original-vm-root': TOOLS / 'original-vm-root',
    'queued-crt-vm-desktop': TOOLS / 'queued-crt-vm-desktop',
    'queued-crt-vm': TOOLS / 'queued-crt-vm',
    'queued-crt-vm-final': TOOLS / 'queued-crt-vm-final',
    'source-vtable-vm': TOOLS / 'source-vtable-vm',
    'original-installer-vm': TOOLS / 'original-installer-vm',
    'original-installer-vm-v2': TOOLS / 'original-installer-vm-v2',
    'original-installer-vm-v3': TOOLS / 'original-installer-vm-v3',
    'original-installer-automate-v4': TOOLS / 'original-installer-automate-v4',
    'mingw32-crt/root': TOOLS / 'mingw32-crt/root',
    'mingw-probe/root': TOOLS / 'mingw-probe/root',
    'ghidra_12.2_PUBLIC': TOOLS / 'ghidra_12.2_PUBLIC',
    'jdk-25.0.5+8': TOOLS / 'jdk-25.0.5+8',
}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def walk(source, target, project=False):
    yield source, target
    for base, directories, files in os.walk(source, followlinks=False):
        base = Path(base)
        allowed = []
        for name in sorted(directories):
            if project and (name in SKIP_DIRS or name.lower().startswith('prefix')):
                continue
            path = base / name
            yield path, target + '/' + str(path.relative_to(source))
            if not path.is_symlink():
                allowed.append(name)
        directories[:] = allowed
        for name in sorted(files):
            path = base / name
            if project and (name in SKIP_NAMES or name.endswith(('.pyc', '.pyo', '.ulf')) or name.startswith('.env')):
                continue
            if path.is_file() or path.is_symlink():
                yield path, target + '/' + str(path.relative_to(source))


def collect():
    entries = list(walk(ROOT, BUNDLE_ROOT + '/gierka', True))
    for name, source in TOOLCHAINS.items():
        assert source.is_dir(), source
        entries.extend(walk(source, BUNDLE_ROOT + '/toolchains/' + name))
    entries.sort(key=lambda pair: pair[1])
    project, tools = {}, {}
    inode_hashes = {}
    for index, (source, target) in enumerate(entries):
        if source.is_symlink():
            meta = dict(type='symlink', target=os.readlink(source))
        elif source.is_file():
            stat = source.stat()
            key = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
            if key not in inode_hashes:
                inode_hashes[key] = digest(source)
            meta = dict(type='file', bytes=stat.st_size, sha256=inode_hashes[key])
        else:
            continue
        project_prefix = BUNDLE_ROOT + '/gierka/'
        if target.startswith(project_prefix):
            project[target[len(project_prefix):]] = meta
        else:
            tools[target[len(BUNDLE_ROOT + '/toolchains/'):]] = meta
        if index and index % 10000 == 0:
            print('manifest entries:', index, flush=True)
    manifest = dict(schema_version=1, bundle_root=BUNDLE_ROOT,
        project_files=project, toolchain_files=tools,
        exclusions=['Unity Library/Temp/Obj/Logs/UserSettings', 'Python venv/cache', 'private Wine prefix directories',
                    'Unity activation files', 'cloud start-skill/draft receipts', 'full Unity Editor and downloaded package caches'],
        full_worktree_including_untracked=True, full_game_complete=False,
        source_checkpoint='docs/evidence/milestone-20261104-source-app-activation.json',
        toolchains=dict((name, str(path)) for name, path in TOOLCHAINS.items()),
        manifest_self_hash_excluded=True)
    return entries, manifest


def make(output):
    output = output.resolve()
    assert ROOT not in output.parents, 'Output must be outside the project'
    assert not output.exists() and not output.with_suffix(output.suffix + '.partial').exists()
    assert shutil.disk_usage(ROOT).free > 3 * 1024 ** 3
    output.parent.mkdir(parents=True, exist_ok=True)
    entries, manifest = collect()
    data = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
    (ROOT / 'handoff/TRANSFER_MANIFEST.json').write_bytes(data)
    expected = {BUNDLE_ROOT + '/gierka/' + n: m for n, m in manifest['project_files'].items()}
    expected.update({BUNDLE_ROOT + '/toolchains/' + n: m for n, m in manifest['toolchain_files'].items()})
    partial = output.with_suffix(output.suffix + '.partial')
    started = time.monotonic()
    with partial.open('wb') as compressed:
        process = subprocess.Popen(['pigz', '-p', '4', '-6'], stdin=subprocess.PIPE, stdout=compressed)
        try:
            with tarfile.open(fileobj=process.stdin, mode='w|', format=tarfile.PAX_FORMAT) as archive:
                for index, (source, target) in enumerate(entries):
                    info = archive.gettarinfo(str(source), arcname=target)
                    info.uid = info.gid = 0
                    info.uname = info.gname = ''
                    info.mode &= ~0o6000
                    if info.isfile():
                        with source.open('rb') as stream:
                            archive.addfile(info, stream)
                    else:
                        archive.addfile(info)
                    if index and index % 5000 == 0:
                        print('packed:', index, 'archive MiB:', partial.stat().st_size // 2**20, flush=True)
                        if shutil.disk_usage(output.parent).free < 512 * 1024**2:
                            raise RuntimeError('Insufficient free space;preserved original project')
                info = tarfile.TarInfo(BUNDLE_ROOT + '/gierka/handoff/TRANSFER_MANIFEST.json')
                info.size = len(data)
                info.mode = 0o644
                archive.addfile(info, io.BytesIO(data))
            process.stdin.close()
            assert process.wait(timeout=60) == 0, 'pigz failed'
        except BaseException:
            process.kill()
            process.wait()
            raise
    print('archive written; starting full payload verification', flush=True)
    seen, hashes, count, bytes_checked = set(), {}, 0, 0
    with tarfile.open(partial, mode='r|gz') as archive:
        for member in archive:
            if member.isdir():
                continue
            name = member.name
            if name == BUNDLE_ROOT + '/gierka/handoff/TRANSFER_MANIFEST.json':
                assert archive.extractfile(member).read() == data
                continue
            meta = expected[name]
            if member.issym():
                assert meta['type'] == 'symlink' and member.linkname == meta['target'], name
            elif member.islnk():
                assert member.linkname in hashes, 'Forward archive hardlink'
                assert hashes[member.linkname] == meta['sha256'], name
                hashes[name] = meta['sha256']
            else:
                h = hashlib.sha256()
                stream = archive.extractfile(member)
                for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
                    h.update(block)
                    bytes_checked += len(block)
                assert member.size == meta['bytes'] and h.hexdigest() == meta['sha256'], name
                hashes[name] = h.hexdigest()
            seen.add(name)
            count += 1
            if count % 10000 == 0:
                print('verified payloads:', count, flush=True)
    assert seen == set(expected), 'Incomplete transfer archive'
    partial.rename(output)
    sha = digest(output)
    output.with_suffix(output.suffix + '.sha256').write_text(sha + '  ' + output.name + '\n')
    report = dict(passed=True, archive=str(output), archive_bytes=output.stat().st_size, sha256=sha,
        project_files=len(manifest['project_files']), toolchain_files=len(manifest['toolchain_files']),
        verified_payloads=count, decompressed_bytes_checked=bytes_checked,
        verification='Every payload hash/link plus gzip integrity;no full extraction',
        seconds=time.monotonic() - started, published=False,
        unity_editor_activation_included=False, private_wine_profiles_included=False)
    output.with_suffix(output.suffix + '.verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    make(args.output)


if __name__ == '__main__':
    main()
