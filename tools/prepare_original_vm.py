from pathlib import Path
import os,subprocess,re,shutil,lzma,gzip,stat,hashlib,json
T=Path('/workspace/toolchains');Q=T/'original-vm-root'; W=T/'wine11-root'; B=T/'original-vm'; I=B/'initramfs'; L=B/'hostlibs'; O=Path('/workspace/gierka/artifacts/runtime-original/vm')
I.mkdir(parents=True,exist_ok=True);L.mkdir(exist_ok=True)
G=B/'guest-wine'
if not G.exists():subprocess.run(['cp','-al',str(W),str(G)],check=True)
(G/'usr/share/X11').mkdir(parents=True,exist_ok=True)
if not (G/'usr/share/X11/xkb').exists():
 shutil.copytree('/usr/share/X11/xkb',G/'usr/share/X11/xkb',symlinks=True)
else:
 for source in Path('/usr/share/X11/xkb').rglob('*'):
  target=G/'usr/share/X11/xkb'/source.relative_to('/usr/share/X11/xkb')
  if source.is_symlink():assert target.is_symlink() and os.readlink(target)==os.readlink(source)
  elif source.is_file():assert target.read_bytes()==source.read_bytes()

shutil.copyfile('/usr/bin/xkbcomp',G/'usr/bin/xkbcomp');(G/'usr/bin/xkbcomp').chmod(0o755)
for source,destination in [('/etc/fonts',G/'etc/fonts'),('/usr/share/fontconfig',G/'usr/share/fontconfig'),('/usr/share/fonts',G/'usr/share/fonts')]:
 destination.mkdir(parents=True,exist_ok=True)
 for entry in Path(source).rglob('*'):
  target=destination/entry.relative_to(source)
  if entry.is_symlink():
   if not target.exists() and not target.is_symlink():target.symlink_to(entry.readlink())
  elif entry.is_dir():target.mkdir(parents=True,exist_ok=True)
  elif entry.is_file() and not target.exists():shutil.copyfile(entry,target)


env=os.environ.copy();env['LD_LIBRARY_PATH']=str(W/'usr/lib/x86_64-linux-gnu')
files=list((W/'opt/wine-stable/lib/wine/x86_64-unix').glob('*.so'))+[W/'opt/wine-stable/bin/wine',W/'opt/wine-stable/bin/wineserver',W/'usr/bin/Xvfb',W/'usr/bin/xdotool',Path('/usr/bin/xkbcomp')]
libs={Path('/lib/x86_64-linux-gnu/libgcc_s.so.1'), Path('/lib/x86_64-linux-gnu/libstdc++.so.6')}
for p in files:
 r=subprocess.run(['ldd',str(p)],env=env,text=True,capture_output=True)
 for x in re.findall(r'(?:=>\s*)?(/[^\s]+)',r.stdout):
  path=Path(x)
  if path.is_file() and not str(path).startswith(str(W)):
   libs.add(path)
# Wine deliberately dlopens many optional system libraries; ldd alone omits
# required graphics/font libraries when the host's APT already had them.
for module in (W/'opt/wine-stable/lib/wine/x86_64-unix').glob('*.so'):
 for match in re.finditer(rb'(?<![a-zA-Z0-9_])(lib[A-Za-z0-9_+.-]+\.so(?:\.[0-9]+)*)\x00',module.read_bytes()):
  dependency=Path('/lib/x86_64-linux-gnu')/match.group(1).decode()
  if not dependency.is_file():continue
  libs.add(dependency)
  for name in re.findall(r'(?:=>\s*)?(/[^\s]+)',subprocess.run(['ldd',str(dependency)],capture_output=True,text=True).stdout):
   extra=Path(name)
   if extra.is_file():libs.add(extra)
for p in sorted(libs):
 target=L/p.name
 if target.exists():
  assert target.read_bytes()==p.read_bytes(),str(p)
 else:shutil.copyfile(p,target)
for d in ['bin','dev','proc','sys','tmp','root','etc','lib64','modules','wine','libs','game','out','disc']:(I/d).mkdir(exist_ok=True)
shutil.copyfile(Q/'usr/bin/busybox',I/'bin/busybox');(I/'bin/busybox').chmod(0o755)
for app in ['sh','mount','mkdir','sleep','insmod','cp','ls','ln','cat','echo','poweroff','timeout','dmesg','sync','uname','ps','kill','chmod']:
 p=I/'bin'/app
 if not p.exists() and not p.is_symlink():p.symlink_to('busybox')
shutil.copyfile('/lib64/ld-linux-x86-64.so.2',I/'lib64/ld-linux-x86-64.so.2');(I/'lib64/ld-linux-x86-64.so.2').chmod(0o755)
for name,target in [('usr','/wine/usr'),('opt','/wine/opt')]:
 p=I/name
 if not p.exists() and not p.is_symlink():p.symlink_to(target)
(I/'lib').mkdir(exist_ok=True)
for name,target in [('x86_64-linux-gnu','/libs'),('i386-linux-gnu','/wine/usr/lib/i386-linux-gnu')]:
 p=I/'lib'/name
 if not p.exists() and not p.is_symlink():p.symlink_to(target)
modulebase=Q/'usr/lib/modules/6.12.113+deb13-amd64/kernel'
for rel in ['fs/netfs/netfs.ko.xz','net/9p/9pnet.ko.xz','net/9p/9pnet_virtio.ko.xz','fs/9p/9p.ko.xz']:
 (I/'modules'/Path(rel).stem).write_bytes(lzma.decompress((modulebase/rel).read_bytes()))
(I/'etc/passwd').write_text('root:x:0:0:root:/root:/bin/sh\n');(I/'etc/group').write_text('root:x:0:\n');(I/'etc/nsswitch.conf').write_text('passwd: files\ngroup: files\nhosts: files\n');(I/'etc/hosts').write_text('127.0.0.1 localhost ancient-reference-vm\n');(I/'etc/hostname').write_text('ancient-reference-vm\n')
assembly=B/'ia32-probe.s'
assembly.write_text('.global _start\n.section .text\n_start:\n mov $4,%eax\n mov $1,%ebx\n mov $message,%ecx\n mov $14,%edx\n int $0x80\n mov $1,%eax\n xor %ebx,%ebx\n int $0x80\n.section .rodata\nmessage: .ascii "IA32_PROBE_OK\\n"\n')
subprocess.run(['as','--32',str(assembly),'-o',str(B/'ia32-probe.o')],check=True)
subprocess.run(['ld','-m','elf_i386',str(B/'ia32-probe.o'),'-o',str(I/'bin/ia32-probe')],check=True)
init='''#!/bin/sh
export PATH=/bin:/usr/bin:/opt/wine-stable/bin
mount -t devtmpfs devtmpfs /dev
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t tmpfs tmpfs /tmp
/bin/busybox hostname ancient-reference-vm
/bin/busybox ip addr add 127.0.0.1/8 dev lo
/bin/busybox ip link set lo up
insmod /modules/netfs.ko
insmod /modules/9pnet.ko
insmod /modules/9pnet_virtio.ko
insmod /modules/9p.ko
mount -t 9p -o trans=virtio,version=9p2000.L,ro wine /wine
mount -t 9p -o trans=virtio,version=9p2000.L,ro libs /libs
mount -t 9p -o trans=virtio,version=9p2000.L,ro game /game
mount -t 9p -o trans=virtio,version=9p2000.L out /out
export LD_LIBRARY_PATH=/wine/usr/lib/x86_64-linux-gnu:/libs
export WINEARCH=wow64
export WINEPREFIX=/tmp/prefix
export WINEDEBUG=err+all
export WINEDLLOVERRIDES=mscoree,mshtml,winemenubuilder.exe=d
export WINESERVER=/opt/wine-stable/bin/wineserver
export DISPLAY=:0
export FONTCONFIG_PATH=/wine/etc/fonts
export FONTCONFIG_FILE=/wine/etc/fonts/fonts.conf
export XDG_RUNTIME_DIR=/tmp/runtime
export XDG_CACHE_HOME=/tmp/cache
mkdir -p /tmp/runtime /tmp/.X11-unix /tmp/framebuffer /tmp/cache/fontconfig /var/cache/fontconfig
chmod 700 /tmp/runtime
uname -a
/bin/ia32-probe
echo IA32_EXIT=$?
/opt/wine-stable/bin/wine --version
/wine/usr/bin/Xvfb :0 -screen 0 800x600x24 -nolisten tcp -ac -fbdir /tmp/framebuffer >/out/xvfb.log 2>&1 &
sleep 2
timeout 240 /opt/wine-stable/bin/wine wineboot -u >/out/wineboot.log 2>&1
echo WINEBOOT_EXIT=$?
timeout 45 /opt/wine-stable/bin/wine /opt/wine-stable/lib/wine/i386-windows/cmd.exe /c ver >/out/control32.log 2>&1
echo CONTROL32_EXIT=$?
/bin/busybox du -sk /tmp/prefix >/out/prefix-size.txt
/bin/busybox df -h >/out/filesystems.txt
/bin/busybox ps >/out/processes.txt
cat /proc/sys/kernel/random/entropy_avail >/out/entropy.txt
cat /out/control32.log
cp /tmp/framebuffer/Xvfb_screen0 /out/guest-screen0.xwd
sync
poweroff -f
'''
(I/'init').write_text(init);(I/'init').chmod(0o755)
# GNU newc: archive paths are relative, metadata stable and no device privileges needed.
out=bytearray(); ino=1
for p in [I]+sorted(I.rglob('*')):
 name='.' if p==I else str(p.relative_to(I));st=p.lstat()
 mode=st.st_mode;data=os.readlink(p).encode() if p.is_symlink() else p.read_bytes() if p.is_file() else b''
 fields=[ino,mode,0,0,1,0,len(data),0,0,0,0,len(name.encode())+1,0];ino+=1
 out+=b'070701'+''.join(f'{v:08x}' for v in fields).encode()+name.encode()+b'\0';out+=b'\0'*(-len(out)%4);out+=data;out+=b'\0'*(-len(out)%4)
name=b'TRAILER!!!\0';fields=[0,0,0,0,1,0,0,0,0,0,0,len(name),0]
out+=b'070701'+''.join(f'{v:08x}' for v in fields).encode()+name;out+=b'\0'*(-len(out)%4)
archive=B/'initramfs.cpio.gz';archive.write_bytes(gzip.compress(out,mtime=0))
(O/'prepared.json').write_text(json.dumps({'initramfs_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'host_library_count':len(libs),'host_libraries':[{'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(libs)]},indent=2)+'\n')
print('initramfs',archive.stat().st_size,'hostlibs',len(libs),sum(p.stat().st_size for p in L.iterdir()))
