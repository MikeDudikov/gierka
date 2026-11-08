#!/usr/bin/env python3
"""Read a single-file MODE1/2352 BIN/CUE without mounting or executing it.

Supports one data track followed by CD audio. Inventories the ISO9660 namespace,
streams SHA-256 for every file, and optionally extracts into a new directory.
Optional CD audio export preserves exact BIN bytes in .cdda files. No WAV
conversion is attempted because sample byte order has not been established.
Hashes identify bytes; this tool does not validate CD EDC/ECC or game behavior.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import io
import json
import ntpath
import os
import operator
from pathlib import Path, PurePosixPath
import re
import sys

import pycdlib

SECTOR_BYTES = 2352
PAYLOAD_BYTES = 2048
SYNC = b'\x00' + b'\xff' * 10 + b'\x00'
MAX_BYTES = 2 * 1024**3
CHUNK_BYTES = 1024 * 1024


@dataclass
class Track:
    number: int
    mode: str
    index01: int | None = None
    index00: int | None = None
    pregap: int = 0
    end_sector: int | None = None


def frames(value: str) -> int:
    match = re.fullmatch(r'(\d{2,}):(\d{2}):(\d{2})', value)
    if not match:
        raise ValueError('Invalid CUE time')
    minutes, seconds, sectors = map(int, match.groups())
    if seconds >= 60 or sectors >= 75:
        raise ValueError('CUE seconds or frames out of range')
    return (minutes * 60 + seconds) * 75 + sectors


def resolve_bin(cue: Path, name: str) -> Path:
    if (not name or name in ('.', '..') or any(x in name for x in ('/', '\\', '\0'))
            or ntpath.splitdrive(name)[0]):
        raise ValueError('CUE FILE must be a plain local filename')
    candidates = [p for p in cue.parent.iterdir() if p.name.casefold() == name.casefold()]
    if len(candidates) != 1:
        raise ValueError('CUE FILE is missing or ambiguous under case-insensitive matching')
    path = candidates[0]
    if path.is_symlink() or not path.is_file():
        raise ValueError('CUE FILE must be a regular file, not a symlink')
    return path


def parse_cue(cue: Path) -> tuple[Path, list[Track]]:
    cue = Path(cue)
    if cue.is_symlink():
        raise ValueError('CUE must not be a symlink')
    name = None
    tracks = []
    pregaps_seen = set()
    for line_number, raw in enumerate(cue.read_text(encoding='utf-8-sig').splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('REM '):
            continue
        file_match = re.fullmatch(r'FILE "([^"\r\n]+)" BINARY', line)
        track_match = re.fullmatch(r'TRACK (\d{2}) (MODE1/2352|AUDIO)', line)
        index_match = re.fullmatch(r'INDEX (00|01) (\S+)', line)
        pregap_match = re.fullmatch(r'PREGAP (\S+)', line)
        if file_match and name is None and not tracks:
            name = file_match.group(1)
        elif track_match and name is not None:
            number = int(track_match.group(1))
            if number != len(tracks) + 1:
                raise ValueError('Track numbers must be consecutive starting at 01')
            tracks.append(Track(number, track_match.group(2)))
        elif index_match and tracks:
            field = 'index' + index_match.group(1)
            if getattr(tracks[-1], field) is not None:
                raise ValueError('Duplicate track index')
            setattr(tracks[-1], field, frames(index_match.group(2)))
        elif pregap_match and tracks and tracks[-1].number not in pregaps_seen:
            tracks[-1].pregap = frames(pregap_match.group(1))
            pregaps_seen.add(tracks[-1].number)
        else:
            raise ValueError(f'Unsupported or misplaced CUE directive at line {line_number}')
    if not name or not tracks:
        raise ValueError('CUE needs FILE and TRACK entries')
    binary = resolve_bin(cue, name)
    size = binary.stat().st_size
    if size == 0 or size % SECTOR_BYTES:
        raise ValueError('BIN size must be a positive multiple of 2352 bytes')
    total = size // SECTOR_BYTES
    if tracks[0].mode != 'MODE1/2352' or any(t.mode != 'AUDIO' for t in tracks[1:]):
        raise ValueError('Only one MODE1/2352 data track followed by AUDIO is supported')
    for i, track in enumerate(tracks):
        if track.index01 is None:
            raise ValueError('Every track requires INDEX 01')
        start = track.index00 if track.index00 is not None else track.index01
        if start < 0 or start > track.index01 or track.index01 >= total:
            raise ValueError('Track index outside BIN or INDEX 00 after INDEX 01')
        if i + 1 < len(tracks):
            following = tracks[i + 1]
            if following.index01 is None:
                raise ValueError('Every track requires INDEX 01')
            end = following.index00 if following.index00 is not None else following.index01
        else:
            end = total
        if end <= track.index01:
            raise ValueError('Track indexes must be strictly increasing')
        track.end_sector = end
    return binary, tracks


class Mode1View(io.RawIOBase):
    """Seekable 2048-byte ISO payload view of bounded 2352-byte sectors."""
    def __init__(self, binary: Path, start_sector: int, end_sector: int):
        super().__init__()
        self._source = None
        size = Path(binary).stat().st_size
        if (type(start_sector) is not int or type(end_sector) is not int
                or start_sector < 0 or end_sector <= start_sector
                or size % SECTOR_BYTES or end_sector * SECTOR_BYTES > size):
            raise ValueError('Invalid raw-sector bounds or truncated BIN')
        self._source = Path(binary).open('rb')
        self._start = start_sector
        self.length = (end_sector - start_sector) * PAYLOAD_BYTES
        self._position = 0
        self._cached_number = None
        self._cached_payload = None
        self.validated_sector_count = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        self._checkClosed()
        return self._position

    def seek(self, offset, whence=os.SEEK_SET):
        self._checkClosed()
        offset = operator.index(offset)
        whence = operator.index(whence)
        if whence not in (os.SEEK_SET, os.SEEK_CUR, os.SEEK_END):
            raise ValueError('Invalid whence')
        position = offset + (0 if whence == os.SEEK_SET else self._position if whence == os.SEEK_CUR else self.length)
        if position < 0:
            raise ValueError('Negative seek position')
        self._position = position
        return position

    def read(self, size=-1):
        self._checkClosed()
        size = -1 if size is None else operator.index(size)
        if size < 0:
            size = max(0, self.length - self._position)
        size = min(size, max(0, self.length - self._position))
        result = bytearray()
        while size:
            sector, offset = divmod(self._position, PAYLOAD_BYTES)
            if sector != self._cached_number:
                self._source.seek((self._start + sector) * SECTOR_BYTES)
                raw = self._source.read(SECTOR_BYTES)
                if len(raw) != SECTOR_BYTES or raw[:12] != SYNC or raw[15] != 1:
                    raise ValueError(f'Invalid MODE1 sync/header or short sector at {self._start + sector}')
                self._cached_number = sector
                self._cached_payload = raw[16:16 + PAYLOAD_BYTES]
                self.validated_sector_count += 1
            count = min(size, PAYLOAD_BYTES - offset)
            result += self._cached_payload[offset:offset + count]
            self._position += count
            size -= count
        return bytes(result)

    def readinto(self, buffer):
        data = self.read(len(buffer))
        buffer[:len(data)] = data
        return len(data)

    def close(self):
        if not self.closed and self._source is not None:
            self._source.close()
        super().close()


def _hash_file(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def _safe_relative(iso_path):
    if not iso_path.startswith('/') or '\\' in iso_path or '\0' in iso_path:
        raise ValueError('Unsafe ISO path')
    parts = iso_path[1:].split('/')
    parts[-1] = re.sub(r';\d+$', '', parts[-1])
    if any(not p or p in ('.', '..') or ':' in p for p in parts):
        raise ValueError('Unsafe ISO path component')
    return PurePosixPath(*parts)


def _check_fresh_directory(path: Path):
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise FileExistsError('Output requires a fresh directory')
    if any(p.is_symlink() for p in path.parents):
        raise ValueError('Output directory ancestors must not be symlinks')


def export_audio(binary: Path, tracks: list[Track], output: Path, *, max_bytes=MAX_BYTES):
    """Export exact track bytes, excluding INDEX 00 and synthetic PREGAP silence.

    Each sector represents 588 stereo PCM sample frames at 44100 Hz. The CUE
    AUDIO directive identifies CD audio; this exporter preserves bytes without
    asserting a PCM sample byte order or converting to WAV.
    """
    if type(max_bytes) is not int or max_bytes < 0:
        raise ValueError('max_bytes must be a nonnegative integer')
    binary = Path(binary)
    output = Path(output)
    _check_fresh_directory(output)
    if binary.is_symlink() or not binary.is_file():
        raise ValueError('Audio source must be a regular file, not a symlink')
    before = binary.stat()
    audio_tracks = [t for t in tracks if t.mode == 'AUDIO']
    if not audio_tracks:
        raise ValueError('CUE contains no audio tracks')
    total_bytes = 0
    last_end = tracks[0].end_sector
    for track in audio_tracks:
        if (track.index01 is None or track.end_sector is None
                or track.index01 < last_end or track.end_sector <= track.index01
                or track.end_sector * SECTOR_BYTES > before.st_size):
            raise ValueError('Audio ranges overlap or lie outside BIN')
        total_bytes += (track.end_sector - track.index01) * SECTOR_BYTES
        last_end = track.end_sector
    if total_bytes > max_bytes:
        raise ValueError('Audio data exceeds byte quota')
    manifest = {
        'schema_version': 1, 'success': False,
        'source': {'bin_path': str(binary.absolute()), 'bin_size_bytes': before.st_size,
                   'bin_sha256': _hash_file(binary)},
        'format': 'raw CDDA sectors copied verbatim from CUE AUDIO tracks',
        'channels': 2, 'sample_rate_hz': 44100, 'bits_per_sample': 16,
        'pcm_sample_byte_order': 'unverified; no WAV conversion performed',
        'range_policy': 'INDEX 01 through next INDEX 00 (if present), otherwise next INDEX 01, or BIN end',
        'pregap_policy': 'INDEX 00 bytes and synthetic PREGAP silence excluded; synthetic PREGAP has no source bytes',
        'total_bytes': total_bytes, 'tracks': [],
    }
    output.mkdir(parents=True, exist_ok=False)
    with binary.open('rb') as source:
        for track in audio_tracks:
            filename = f'track{track.number:02d}.cdda'
            sectors = track.end_sector - track.index01
            remaining = sectors * SECTOR_BYTES
            source.seek(track.index01 * SECTOR_BYTES)
            digest = hashlib.sha256()
            with (output / filename).open('xb') as target:
                while remaining:
                    chunk = source.read(min(CHUNK_BYTES, remaining))
                    if not chunk:
                        raise ValueError('BIN truncated while exporting audio')
                    target.write(chunk)
                    digest.update(chunk)
                    remaining -= len(chunk)
            manifest['tracks'].append({
                'number': track.number, 'file': filename,
                'start_sector': track.index01, 'end_sector_exclusive': track.end_sector,
                'source_byte_offset': track.index01 * SECTOR_BYTES,
                'size_bytes': sectors * SECTOR_BYTES, 'sectors': sectors,
                'stereo_sample_frames': sectors * 588, 'duration_seconds': sectors / 75,
                'synthetic_pregap_sectors_excluded': track.pregap,
                'stored_pregap_sectors_excluded': (track.index01 - track.index00) if track.index00 is not None else 0,
                'sha256': digest.hexdigest(),
            })
    after = binary.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError('BIN changed during audio export')
    manifest['success'] = True
    with (output / 'audio-manifest.json').open('x', encoding='utf-8') as target:
        json.dump(manifest, target, indent=2)
        target.write('\n')
    return manifest


def inventory_disc(cue: Path, *, extract_to: Path | None = None,
                   audio_to: Path | None = None, max_bytes=MAX_BYTES):
    if type(max_bytes) is not int or max_bytes < 0:
        raise ValueError('max_bytes must be a nonnegative integer')
    cue = Path(cue)
    binary, tracks = parse_cue(cue)
    before = {p: p.stat() for p in (cue, binary)}
    for output in (extract_to, audio_to):
        if output is not None:
            _check_fresh_directory(output)
    if extract_to is not None and audio_to is not None:
        first, second = Path(extract_to).resolve(), Path(audio_to).resolve()
        if first == second or first in second.parents or second in first.parents:
            raise ValueError('Extraction and audio output directories must not overlap')
    report = {
        'schema_version': 1, 'success': False,
        'source': {'cue_path': str(cue.absolute()), 'cue_sha256': _hash_file(cue),
                   'bin_path': str(binary.absolute()), 'bin_size_bytes': binary.stat().st_size,
                   'bin_sha256': _hash_file(binary)},
        'tracks': [asdict(t) for t in tracks],
        'namespace': 'ISO9660 (not Rock Ridge or Joliet)',
        'verification': 'SHA-256 of source, data-track payload and files; every data-track MODE1 sync/header checked; CD EDC/ECC not checked',
        'files': [], 'total_file_bytes': 0,
    }
    track = tracks[0]
    with Mode1View(binary, track.index01, track.end_sector) as view:
        payload_hash = hashlib.sha256()
        while chunk := view.read(CHUNK_BYTES):
            payload_hash.update(chunk)
        report['data_track'] = {'number': track.number, 'mode': track.mode,
                                'start_sector': track.index01, 'end_sector_exclusive': track.end_sector,
                                'payload_size_bytes': view.length, 'payload_sha256': payload_hash.hexdigest()}
        view.seek(0)
        iso = pycdlib.PyCdlib()
        try:
            iso.open_fp(view)
            catalog = []
            paths = set()
            for directory, directories, files in iso.walk(iso_path='/'):
                for filename in sorted(files):
                    iso_path = directory.rstrip('/') + '/' + filename
                    relative = _safe_relative(iso_path)
                    folded = str(relative).casefold()
                    if folded in paths:
                        raise ValueError('Case-insensitive output collision in ISO namespace')
                    paths.add(folded)
                    size = iso.get_record(iso_path=iso_path).data_length
                    if size < 0:
                        raise ValueError('Negative ISO file length')
                    report['total_file_bytes'] += size
                    if report['total_file_bytes'] > max_bytes:
                        raise ValueError('ISO file data exceeds byte quota')
                    catalog.append((iso_path, relative, size))
            # Refuse file/directory collisions before creating the output directory.
            for _, relative, _ in catalog:
                if any(str(p).casefold() in paths for p in relative.parents if str(p) != '.'):
                    raise ValueError('File/directory collision in ISO namespace')
            output_root = None
            if extract_to is not None:
                output_root = Path(extract_to)
                _check_fresh_directory(output_root)
                output_root.mkdir(parents=True, exist_ok=False)
            for iso_path, relative, expected in sorted(catalog):
                digest = hashlib.sha256()
                count = 0
                target = None
                try:
                    if output_root:
                        destination = output_root.joinpath(*relative.parts)
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        target = destination.open('xb')
                    with iso.open_file_from_iso(iso_path=iso_path) as source:
                        while chunk := source.read(CHUNK_BYTES):
                            count += len(chunk)
                            if count > expected:
                                raise ValueError('ISO stream exceeded declared length')
                            digest.update(chunk)
                            if target:
                                target.write(chunk)
                finally:
                    if target:
                        target.close()
                if count != expected:
                    raise ValueError('ISO stream shorter than declared length')
                report['files'].append({'iso_path': iso_path, 'relative_path': str(relative),
                                        'size_bytes': count, 'sha256': digest.hexdigest()})
        finally:
            iso.close()
    for path, old in before.items():
        now = path.stat()
        if (old.st_size, old.st_mtime_ns, old.st_ctime_ns) != (now.st_size, now.st_mtime_ns, now.st_ctime_ns):
            raise ValueError('Source changed during inventory')
    if audio_to is not None:
        report['audio_export'] = export_audio(binary, tracks, audio_to, max_bytes=max_bytes)
    report['success'] = True
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cue', type=Path)
    parser.add_argument('--output', type=Path, help='New JSON report; existing files are never overwritten')
    parser.add_argument('--extract-to', type=Path, help='Fresh directory for ISO files; audio is not extracted')
    parser.add_argument('--audio-to', type=Path, help='Fresh directory for exact raw .cdda tracks and hash manifest; no WAV conversion')
    parser.add_argument('--max-bytes', type=int, default=MAX_BYTES)
    args = parser.parse_args(argv)
    if args.output and args.output.exists():
        print('Refusing to overwrite existing report', file=sys.stderr)
        return 1
    try:
        report = inventory_disc(args.cue, extract_to=args.extract_to, audio_to=args.audio_to, max_bytes=args.max_bytes)
        data = json.dumps(report, indent=2, ensure_ascii=True) + '\n'
        if args.output:
            with args.output.open('x', encoding='utf-8') as target:
                target.write(data)
        else:
            print(data, end='')
    except Exception as error:
        print(f'{type(error).__name__}: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
