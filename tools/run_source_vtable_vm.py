"""Offline original PE32 entry probe;read-only host inputs and one owned output."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import time

ROOT = Path('/workspace/gierka')
PHASE = ROOT / 'artifacts/native-base-vtable'
BASE = Path('/workspace/toolchains/source-vtable-vm')
QEMU = Path('/workspace/toolchains/original-vm-root')
RUNTIME = Path('/workspace/toolchains/original-vm')
EXPECTED = 'cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    manifest = PHASE / 'preparation.json'
    if manifest.exists():
        meta = json.loads(manifest.read_text())
        assert digest(Path(meta['initramfs'])) == meta['sha256']
        return meta
    assert not BASE.exists()
    tree = BASE / 'initramfs'
    shutil.copytree('/workspace/toolchains/queued-crt-vm-desktop/initramfs', tree, symlinks=True)
    (tree / 'game').mkdir()
    probe = PHASE / 'vm-input'
    shutil.copy2(ROOT / 'artifacts/queued-crt-context/control32.exe', probe / 'control32.exe')
    init = r'''#!/bin/sh
export PATH=/bin:/usr/bin:/opt/wine-stable/bin
mount -t devtmpfs devtmpfs /dev
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t tmpfs tmpfs /tmp
/bin/busybox ip addr add 127.0.0.1/8 dev lo
/bin/busybox ip link set lo up
insmod /modules/netfs.ko
insmod /modules/9pnet.ko
insmod /modules/9pnet_virtio.ko
insmod /modules/9p.ko
for tag in wine libs prefix probe game;do mount -t 9p -o trans=virtio,version=9p2000.L,ro "$tag" "/$tag";done
mount -t 9p -o trans=virtio,version=9p2000.L out /out
mkdir -p /tmp/native-prefix/dosdevices /tmp/runtime /tmp/cache/fontconfig /var/cache/fontconfig /tmp/.X11-unix
cp /prefix/*.reg /tmp/native-prefix/
cp /prefix/.update-timestamp /tmp/native-prefix/
ln -s /prefix/drive_c /tmp/native-prefix/drive_c
ln -s ../drive_c /tmp/native-prefix/dosdevices/c:
ln -s / /tmp/native-prefix/dosdevices/z:
export LD_LIBRARY_PATH=/wine/usr/lib/x86_64-linux-gnu:/libs
export WINEARCH=wow64 WINEPREFIX=/tmp/native-prefix WINEDEBUG=err+all
export WINEDLLOVERRIDES=mscoree,mshtml,winemenubuilder.exe=d
export WINESERVER=/opt/wine-stable/bin/wineserver
export XDG_RUNTIME_DIR=/tmp/runtime XDG_CACHE_HOME=/tmp/cache
export DISPLAY=:0 FONTCONFIG_PATH=/wine/etc/fonts FONTCONFIG_FILE=/wine/etc/fonts/fonts.conf
chmod 700 /tmp/runtime
/wine/usr/bin/Xvfb :0 -screen 0 800x600x24 -nolisten tcp -ac >/out/xvfb.log 2>&1 &
sleep 1
uname -a
/bin/ia32-probe
echo IA32_EXIT=$?
timeout -s KILL 45 /opt/wine-stable/bin/wine 'Z:\probe\control32.exe' >/out/control32.stdout 2>/out/control32.stderr
control=$?
echo CONTROL32_EXIT=$control
if [ "$control" = 0 ];then
 cp -a /game /tmp/original-game
 sha256sum /tmp/original-game/ancient.exe >/out/guest-original-sha256.txt
 timeout -s KILL 110 /opt/wine-stable/bin/wine 'Z:\probe\vtable-probe.exe' >/out/trace.jsonl 2>/out/trace.stderr
 echo SOURCE_PROBE_EXIT=$?
else
 echo SOURCE_PROBE_SKIPPED_NO_PE32
fi
sync
poweroff -f
'''
    (tree / 'init').write_text(init)
    (tree / 'init').chmod(0o755)
    archive = bytearray()
    for index, path in enumerate([tree, *sorted(tree.rglob('*'))], 1):
        name = '.' if path == tree else str(path.relative_to(tree))
        info = path.lstat()
        payload = os.readlink(path).encode() if path.is_symlink() else path.read_bytes() if path.is_file() else b''
        values = [index, info.st_mode, 0, 0, 1, 0, len(payload), 0, 0, 0, 0, len(name.encode()) + 1, 0]
        archive.extend(('070701' + ''.join(f'{v:08x}' for v in values)).encode())
        archive.extend(name.encode() + b'\0'); archive.extend(b'\0' * (-len(archive) % 4))
        archive.extend(payload); archive.extend(b'\0' * (-len(archive) % 4))
    name = 'TRAILER!!!'
    values = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, len(name) + 1, 0]
    archive.extend(('070701' + ''.join(f'{v:08x}' for v in values)).encode() + name.encode() + b'\0')
    archive.extend(b'\0' * (-len(archive) % 4))
    image = BASE / 'initramfs.cpio.gz'
    image.write_bytes(gzip.compress(archive, mtime=0))
    meta = dict(initramfs=str(image), sha256=digest(image), network=False,
                host_root_mounted=False, original_files_read_only=True, guest_game_copy_private=True)
    manifest.write_text(json.dumps(meta, indent=2) + '\n')
    return meta


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.parent == PHASE and not output.exists()
    source = ROOT / 'artifacts/runtime-original/game/ancient.exe'
    assert digest(source) == EXPECTED
    meta = prepare()
    output.mkdir()
    shutil.copy2(ROOT / 'tools/win32_source_vtable_probe.c', output / 'probe-source.c')
    shutil.copy2(PHASE / 'vm-input/vtable-probe.exe', output / 'probe.exe')
    paths = dict(wine=RUNTIME / 'guest-wine', libs=RUNTIME / 'hostlibs',
                 prefix=ROOT / 'artifacts/runtime-original/prefix-wine11',
                 probe=PHASE / 'vm-input', game=source.parent, out=output)
    command = [str(QEMU / 'usr/bin/qemu-system-x86_64'), '-L', str(QEMU / 'usr/share/qemu'),
               '-bios', str(QEMU / 'usr/share/seabios/bios-256k.bin'), '-machine', 'q35',
               '-accel', 'tcg,thread=multi', '-cpu', 'max', '-smp', '2', '-m', '4096',
               '-nodefaults', '-no-reboot', '-display', 'none', '-serial', 'stdio',
               '-monitor', 'none', '-nic', 'none', '-kernel', str(QEMU / 'boot/vmlinuz-6.12.113+deb13-amd64'),
               '-initrd', meta['initramfs'], '-append', 'console=ttyS0 panic=-1 quiet']
    for tag, path in paths.items():
        command.extend(['-virtfs', f'local,path={path},mount_tag={tag},security_model=none' + ('' if tag == 'out' else ',readonly=on')])
    (output / 'launch.json').write_text(json.dumps(dict(command=command, network=False, timeout=210,
        read_only_tags=[k for k in paths if k != 'out'], source_sha256=EXPECTED,
        probe_sha256=digest(PHASE / 'vm-input/vtable-probe.exe')), indent=2) + '\n')
    env = os.environ.copy(); env['LD_LIBRARY_PATH'] = str(QEMU / 'usr/lib/x86_64-linux-gnu')
    started = time.monotonic()
    try:
        with (output / 'serial.log').open('w') as stream:
            result = subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=210)
        status = dict(qemu_exit_code=result.returncode, timed_out=False)
    except subprocess.TimeoutExpired:
        status = dict(qemu_exit_code=None, timed_out=True)
    status['seconds'] = time.monotonic() - started
    status['original_file_unchanged'] = digest(source) == EXPECTED
    (output / 'host-status.json').write_text(json.dumps(status, indent=2) + '\n')
    print(status)


if __name__ == '__main__':
    main()
