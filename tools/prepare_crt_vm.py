"""Fresh minimal IA32 guest for CRT controls;no network or host-root export."""
from pathlib import Path
import argparse,gzip,hashlib,json,os,shutil,stat
parser=argparse.ArgumentParser();parser.add_argument("--desktop",action="store_true");options=parser.parse_args()
ROOT=Path('/workspace/gierka');BASE=Path('/workspace/toolchains/queued-crt-vm-desktop'if options.desktop else'/workspace/toolchains/queued-crt-vm-final');OLD=Path('/workspace/toolchains/original-vm/initramfs')
OUT=ROOT/'artifacts/queued-crt-context';TREE=BASE/'initramfs';PROBE=OUT/'vm-input-final'
assert not TREE.exists();TREE.mkdir(parents=True);PROBE.mkdir(exist_ok=True)
for name in('bin','lib64','modules'):shutil.copytree(OLD/name,TREE/name,symlinks=True)
for name in('dev','proc','sys','tmp','root','etc','lib','wine','libs','prefix','probe','out','workspace/toolchains'):(TREE/name).mkdir(parents=True,exist_ok=True)
for name,target in(('usr','/wine/usr'),('opt','/wine/opt'),('lib/x86_64-linux-gnu','/libs'),('lib/i386-linux-gnu','/wine/usr/lib/i386-linux-gnu'),('workspace/toolchains/wine11-root','/wine')):(TREE/name).symlink_to(target)
for name in('passwd','group','nsswitch.conf','hosts','hostname'):shutil.copy2(OLD/'etc'/name,TREE/'etc'/name)
for name in('probe.exe','control32.exe','control64.exe'):shutil.copy2(OUT/name,PROBE/name)
source=ROOT/'reference/raw/ancient-conquest/installed/ancient.exe';assert hashlib.sha256(source.read_bytes()).hexdigest()=='cb7746b288d23de2a0343ba51c154f961b3e3683b73bcc31e9a38b2c6b1e2021';shutil.copy2(source,PROBE/'ancient.exe')
init=r'''#!/bin/sh
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
for tag in wine libs prefix probe;do mount -t 9p -o trans=virtio,version=9p2000.L,ro "$tag" "/$tag";done
mount -t 9p -o trans=virtio,version=9p2000.L out /out
mkdir -p /tmp/crt-prefix/dosdevices /tmp/runtime
cp /prefix/*.reg /tmp/crt-prefix/
cp /prefix/.update-timestamp /tmp/crt-prefix/
ln -s /prefix/drive_c /tmp/crt-prefix/drive_c
ln -s ../drive_c /tmp/crt-prefix/dosdevices/c:
ln -s / /tmp/crt-prefix/dosdevices/z:
export LD_LIBRARY_PATH=/wine/usr/lib/x86_64-linux-gnu:/libs
export WINEARCH=wow64 WINEPREFIX=/tmp/crt-prefix WINEDEBUG=err+all
export WINEDLLOVERRIDES=mscoree,mshtml,winemenubuilder.exe=d
export WINESERVER=/opt/wine-stable/bin/wineserver
export XDG_RUNTIME_DIR=/tmp/runtime
chmod 700 /tmp/runtime
uname -a
/bin/ia32-probe
echo IA32_EXIT=$?
timeout -s KILL 45 /opt/wine-stable/bin/wine 'Z:\probe\control32.exe' >/out/control32.stdout 2>/out/control32.stderr
control=$?
echo CONTROL32_EXIT=$control
if [ "$control" = 0 ];then
 timeout -s KILL 45 /opt/wine-stable/bin/wine 'Z:\probe\probe.exe' 'Z:\probe\ancient.exe' 0 >/out/crt.jsonl 2>/out/crt.stderr
 echo CRT_EXIT=$?
else
 echo CRT_SKIPPED_NO_PE32
fi
sync
poweroff -f
'''
if options.desktop:
 init=init.replace('uname -a\n','''export DISPLAY=:0
export FONTCONFIG_PATH=/wine/etc/fonts
export FONTCONFIG_FILE=/wine/etc/fonts/fonts.conf
export XDG_CACHE_HOME=/tmp/cache
mkdir -p /tmp/cache/fontconfig /var/cache/fontconfig /tmp/.X11-unix
/wine/usr/bin/Xvfb :0 -screen 0 800x600x24 -nolisten tcp -ac >/out/xvfb.log 2>&1 &
sleep 1
uname -a
''')
(TREE/'init').write_text(init);(TREE/'init').chmod(0o755)
#newc archive,only this fresh owned tree.
archive=bytearray();ino=1
for path in [TREE,*sorted(TREE.rglob('*'))]:
 name='.'if path==TREE else str(path.relative_to(TREE));st=path.lstat()
 payload=os.readlink(path).encode()if path.is_symlink()else path.read_bytes()if path.is_file()else b''
 values=[ino,st.st_mode,0,0,1,0,len(payload),0,0,0,0,len(name.encode())+1,0];ino+=1
 archive.extend(('070701'+''.join(f'{v:08x}'for v in values)).encode());archive.extend(name.encode()+b'\0')
 archive.extend(b'\0'*((-len(archive))%4));archive.extend(payload);archive.extend(b'\0'*((-len(archive))%4))
name='TRAILER!!!';archive.extend(('070701'+''.join(f'{v:08x}'for v in[ino,0,0,0,1,0,0,0,0,0,0,len(name)+1,0])).encode()+name.encode()+b'\0');archive.extend(b'\0'*((-len(archive))%4))
image=BASE/'initramfs.cpio.gz';image.write_bytes(gzip.compress(archive,mtime=0))
(OUT/('vm-preparation-desktop.json'if options.desktop else'vm-preparation.json')).write_text(json.dumps(dict(probe_directory=str(PROBE),desktop=options.desktop,initramfs=str(image),sha256=hashlib.sha256(image.read_bytes()).hexdigest(),network=False,host_root_mounted=False,source_pe_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),prefix_read_only=True),indent=2)+'\n')
print('Prepared fresh CRT VM',len(archive),'bytes uncompressed')
