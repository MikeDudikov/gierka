#!/usr/bin/env python3
"""Download verified Git LFS parts and reconstruct the original handoff archive."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import time
import urllib.request

MANIFEST = 'https://raw.githubusercontent.com/MikeDudikov/gierka/gierka/gierka/manifest.json'
EXPECTED_SHA = 'fa850d9df733e7ab8f0e295377ebbe2a255a0a25cbae1767e5372fdbc5a95060'


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024**2), b''):
            value.update(block)
    return value.hexdigest()


def validate_name(name):
    if not name or Path(name).name != name or '/' in name or '\\' in name:
        raise ValueError('Nieprawidłowa nazwa pliku w manifeście.')
    return name


def download(part, output):
    target = output / validate_name(part['name'])
    if target.is_file() and target.stat().st_size == part['bytes'] and digest(target) == part['sha256']:
        print('Już pobrano:', target.name, flush=True)
        return target
    if target.exists():
        raise ValueError('Istniejący plik ma inną sumę;przenieś go przed ponowieniem: ' + str(target))
    partial = target.with_name(target.name + '.partial')
    for attempt in range(4):
        try:
            offset = partial.stat().st_size if partial.exists() else 0
            if offset > part['bytes']:
                partial.unlink()
                offset = 0
            if offset < part['bytes']:
                request = urllib.request.Request(part['url'], headers={'User-Agent': 'AncientConquest-handoff/1'})
                if offset:
                    request.add_header('Range', 'bytes=' + str(offset) + '-')
                with urllib.request.urlopen(request, timeout=120) as response:
                    if offset and response.status != 206:
                        offset = 0
                    print('Pobieranie:', target.name, 'od bajtu', offset, flush=True)
                    with partial.open('ab' if offset else 'wb') as stream:
                        shutil.copyfileobj(response, stream, 4 * 1024**2)
            if partial.stat().st_size != part['bytes'] or digest(partial) != part['sha256']:
                partial.unlink()
                raise ValueError('Niezgodna suma pobranej części: ' + target.name)
            partial.rename(target)
            return target
        except (OSError, ValueError) as error:
            if attempt == 3:
                raise
            print('Ponawiam:', str(error), flush=True)
            time.sleep(2)


def run(manifest_url, output, expected_sha=EXPECTED_SHA):
    with urllib.request.urlopen(manifest_url, timeout=60) as response:
        manifest = json.load(response)
    if manifest['sha256'] != expected_sha:
        raise ValueError('Manifest nie dotyczy oczekiwanej paczki.')
    name = validate_name(manifest['archive'])
    if sum(p['bytes'] for p in manifest['parts']) != manifest['bytes']:
        raise ValueError('Niespójny rozmiar części w manifeście.')
    output.mkdir(parents=True, exist_ok=True)
    archive = output / name
    if archive.exists():
        if archive.stat().st_size == manifest['bytes'] and digest(archive) == expected_sha:
            print('Gotowa paczka już istnieje:', archive, flush=True)
            return archive
        raise ValueError('Istniejące archiwum ma inną sumę;przenieś je przed ponowieniem.')
    parts = [download(part, output) for part in manifest['parts']]
    temporary = archive.with_name(archive.name + '.assembling')
    print('Scalanie paczki...', flush=True)
    with temporary.open('wb') as target:
        for part in parts:
            with part.open('rb') as source:
                shutil.copyfileobj(source, target, 4 * 1024**2)
    if temporary.stat().st_size != manifest['bytes'] or digest(temporary) != expected_sha:
        raise ValueError('Końcowa suma archiwum jest niezgodna.')
    temporary.rename(archive)
    archive.with_name(archive.name + '.sha256').write_text(expected_sha + '  ' + name + '\n')
    print('Gotowe — suma SHA256 zgodna:', archive.resolve(), flush=True)
    return archive


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--katalog', type=Path, default=Path('AncientConquest-paczka'))
    args = parser.parse_args()
    run(MANIFEST, args.katalog)


if __name__ == '__main__':
    main()
