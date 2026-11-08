#!/usr/bin/env python3
"""Extract an official Debian cross-compiler locally for the Win32 original CRT probe."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

BASE = Path('/workspace/toolchains/mingw32-crt')
INDEX = Path('/workspace/toolchains/winehq-apt/lists/deb.debian.org_debian_dists_trixie_main_binary-amd64_Packages')
RELEASE = INDEX.with_name('deb.debian.org_debian_dists_trixie_InRelease')
NAMES = {'gcc-mingw-w64-i686-posix', 'binutils-mingw-w64-i686',
         'mingw-w64-i686-dev', 'gcc-mingw-w64-base', 'mingw-w64-common',
         'gcc-mingw-w64-i686-posix-runtime'}


def main():
    (BASE / 'gnupg').mkdir(parents=True, exist_ok=True, mode=0o700)
    subprocess.run(['gpg', '--homedir', str(BASE / 'gnupg'), '--no-default-keyring',
                    '--keyring', '/usr/share/keyrings/debian-archive-keyring.gpg',
                    '--verify', str(RELEASE)], check=True)
    raw = INDEX.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    expected = f'{sha} {len(raw):16d} main/binary-amd64/Packages'
    # Whitespace is not significant in the signed Release digest table.
    if not any(line.split() == expected.split() for line in RELEASE.read_text().splitlines()):
        raise ValueError('Debian Packages index does not match the signed Release hash')
    records = []
    for block in raw.decode().split('\n\n'):
        record = dict(line.split(': ', 1) for line in block.splitlines()
                      if ': ' in line and not line.startswith(' '))
        if record.get('Package') in NAMES:
            records.append({key: record[key] for key in ('Package', 'Version', 'Filename', 'Size', 'SHA256')})
    if {record['Package'] for record in records} != NAMES:
        raise ValueError('Incomplete MinGW package selection')
    cache = BASE / 'packages'
    cache.mkdir(exist_ok=True)

    def download(record):
        target = cache / Path(record['Filename']).name
        if not target.exists():
            with urllib.request.urlopen('https://deb.debian.org/debian/' + record['Filename'], timeout=60) as stream:
                payload = stream.read()
            if len(payload) != int(record['Size']) or hashlib.sha256(payload).hexdigest() != record['SHA256']:
                raise ValueError('Package verification failed: ' + record['Package'])
            target.write_bytes(payload)
        payload = target.read_bytes()
        if len(payload) != int(record['Size']) or hashlib.sha256(payload).hexdigest() != record['SHA256']:
            raise ValueError('Cached package verification failed: ' + record['Package'])
        return target

    with ThreadPoolExecutor(max_workers=6) as pool:
        paths = list(pool.map(download, records))
    for path in paths:
        subprocess.run(['dpkg-deb', '-x', str(path), str(BASE / 'root')], check=True)
    (BASE / 'verified-packages.json').write_text(json.dumps({'release': str(RELEASE),
        'packages_index_sha256': sha, 'packages': records}, indent=2) + '\n')
    print('Official Debian MinGW extracted locally:', len(records), 'verified packages')


if __name__ == '__main__':
    main()
