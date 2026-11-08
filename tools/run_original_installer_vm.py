"""Observe original installer in an offline guest with a private writable Wine prefix."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import time
from tools import run_source_vtable_vm as runtime

ROOT = runtime.ROOT
PHASE = ROOT / 'artifacts/original-install-vm'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(automate=False):
    mode = 'automate-v4' if automate else 'observe-v4'
    base = Path('/workspace/toolchains/original-installer-' + mode)
    manifest = PHASE / ('preparation-' + mode + '.json')
    if manifest.exists():
        data = json.loads(manifest.read_text())
        assert digest(Path(data['initramfs'])) == data['sha256']
        return data
    assert not base.exists()
    tree = base / 'initramfs'
    shutil.copytree('/workspace/toolchains/queued-crt-vm-desktop/initramfs', tree, symlinks=True)
    (tree / 'disc').mkdir()
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
for tag in wine libs prefix probe disc;do mount -t 9p -o trans=virtio,version=9p2000.L,ro "$tag" "/$tag";done
mount -t 9p -o trans=virtio,version=9p2000.L out /out
# The copied initramfs already aliases/workspace/toolchains/wine11-root to/wine.
# Assert its target instead of attempting to create a link inside a read-only mount.
test -f /workspace/toolchains/wine11-root/opt/wine-stable/lib/wine/i386-windows/ddraw.dll || poweroff -f
mkdir -p /tmp/native-prefix /tmp/runtime /tmp/cache/fontconfig /var/cache/fontconfig /tmp/.X11-unix
cp -a /prefix/. /tmp/native-prefix/
# cp -a retains host UID1000; Wine inside this private initramfs runs as root.
/bin/busybox chown 0:0 /tmp/native-prefix
ln -s /disc /tmp/native-prefix/dosdevices/d:
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
 timeout -s KILL 60 /opt/wine-stable/bin/wine 'C:\windows\syswow64\regsvr32.exe' /s ddraw.dll >/out/ddraw-register.stdout 2>/out/ddraw-register.stderr
 registration=$?
 echo DDRAW_REGISTER_EXIT=$registration
 sha256sum /disc/SETUP.EXE >/out/guest-setup-sha256.txt
 timeout -s KILL 80 /opt/wine-stable/bin/wine 'Z:\probe\installer-probe.exe' >/out/trace.jsonl 2>/out/trace.stderr
 echo INSTALLER_OBSERVATION_EXIT=$?
fi
sync
poweroff -f
'''
    if automate:
        init = init.replace('installer-probe.exe', 'installer-automation.exe').replace('timeout -s KILL 80 ', 'timeout -s KILL 300 ')
        init = init.replace('sync\npoweroff -f', r'''
find /tmp/native-prefix/drive_c -iname ancient.exe > /out/installed-ancient-paths.txt
while IFS= read -r executable;do
 sha256sum "$executable" >> /out/installed-ancient-sha256.txt
 parent=${executable%/*}
 if [ ! -e /out/installed-game ];then cp -a "$parent" /out/installed-game;fi
done < /out/installed-ancient-paths.txt
timeout -s KILL 30 /opt/wine-stable/bin/wine 'C:\windows\syswow64\reg.exe' export 'HKLM\SOFTWARE\Megamedia\Megamedia Australia\Ancient conquest' 'Z:\out\game-registry.reg' /y > /out/registry-export.stdout 2> /out/registry-export.stderr
echo REGISTRY_EXPORT_EXIT=$?
sync
poweroff -f''')
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
    image = base / 'initramfs.cpio.gz'
    image.write_bytes(gzip.compress(archive, mtime=0))
    data = dict(initramfs=str(image), sha256=digest(image), network=False,
                private_writable_prefix=True, host_prefix_read_only=True, observation_only=not automate,
                original_builtin_dll_links_resolved_in_guest=True, official_ddraw_registration=True)
    manifest.write_text(json.dumps(data, indent=2) + '\n')
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--automate', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.parent == PHASE and not output.exists()
    meta = prepare(args.automate)
    output.mkdir()
    program = 'installer-automation' if args.automate else 'installer-probe'
    source = 'win32_original_installer_automation.c' if args.automate else 'win32_original_installer_probe.c'
    shutil.copy2(ROOT / 'tools' / source, output / 'probe-source.c')
    shutil.copy2(PHASE / 'vm-input' / (program + '.exe'), output / 'probe.exe')
    disc = ROOT / 'reference/raw/ancient-conquest/files'
    setup_sha = digest(disc / 'SETUP.EXE')
    assert setup_sha == json.loads((PHASE / 'setup-resources.json').read_text())['sha256']
    mounts = dict(wine=runtime.RUNTIME / 'guest-wine', libs=runtime.RUNTIME / 'hostlibs',
                  prefix=ROOT / 'artifacts/runtime-original/prefix-wine11',
                  probe=PHASE / 'vm-input', disc=disc, out=output)
    command = [str(runtime.QEMU / 'usr/bin/qemu-system-x86_64'), '-L', str(runtime.QEMU / 'usr/share/qemu'),
        '-bios', str(runtime.QEMU / 'usr/share/seabios/bios-256k.bin'), '-machine', 'q35',
        '-accel', 'tcg,thread=multi', '-cpu', 'max', '-smp', '2', '-m', '8192',
        '-nodefaults', '-no-reboot', '-display', 'none', '-serial', 'stdio', '-monitor', 'none', '-nic', 'none',
        '-kernel', str(runtime.QEMU / 'boot/vmlinuz-6.12.113+deb13-amd64'), '-initrd', meta['initramfs'],
        '-append', 'console=ttyS0 panic=-1 quiet']
    for tag, path in mounts.items():
        command += ['-virtfs', f'local,path={path},mount_tag={tag},security_model=none' + ('' if tag == 'out' else ',readonly=on')]
    timeout = 480 if args.automate else 240
    (output / 'launch.json').write_text(json.dumps(dict(command=command, timeout=timeout, setup_sha256=setup_sha,
        probe_sha256=digest(output / 'probe.exe'), network=False,
        host_prefix_read_only=True, guest_prefix_private=True, observation_only=not args.automate), indent=2) + '\n')
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = str(runtime.QEMU / 'usr/lib/x86_64-linux-gnu')
    started = time.monotonic()
    try:
        with (output / 'serial.log').open('w') as stream:
            run = subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
        status = dict(exit_code=run.returncode, timed_out=False)
    except subprocess.TimeoutExpired:
        status = dict(exit_code=None, timed_out=True)
    status.update(seconds=time.monotonic() - started, original_setup_unchanged=digest(disc / 'SETUP.EXE') == setup_sha)
    (output / 'host-status.json').write_text(json.dumps(status, indent=2) + '\n')
    print(status)


if __name__ == '__main__':
    main()
