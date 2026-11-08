"""Bounded offline CRT VM;read-only inputs and one fresh output directory."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,time
ROOT=Path('/workspace/gierka');OUT=ROOT/'artifacts/queued-crt-context'


def main():
 p=argparse.ArgumentParser();p.add_argument('--preparation',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 run=a.output.resolve();assert run.parent==OUT and not run.exists();meta=json.loads(a.preparation.read_text());image=Path(meta['initramfs'])
 assert hashlib.sha256(image.read_bytes()).hexdigest()==meta['sha256'];run.mkdir()
 q=Path('/workspace/toolchains/original-vm-root');b=Path('/workspace/toolchains/original-vm')
 paths={'wine':b/'guest-wine','libs':b/'hostlibs','prefix':ROOT/'artifacts/runtime-original/prefix-wine11','probe':Path(meta['probe_directory']),'out':run}
 args=[str(q/'usr/bin/qemu-system-x86_64'),'-L',str(q/'usr/share/qemu'),'-bios',str(q/'usr/share/seabios/bios-256k.bin'),'-machine','q35','-accel','tcg,thread=multi','-cpu','max','-smp','2','-m','4096','-nodefaults','-no-reboot','-display','none','-serial','stdio','-monitor','none','-nic','none','-kernel',str(q/'boot/vmlinuz-6.12.113+deb13-amd64'),'-initrd',str(image),'-append','console=ttyS0 panic=-1 quiet']
 for tag,path in paths.items():args+=['-virtfs',f'local,path={path},mount_tag={tag},security_model=none'+(''if tag=='out'else',readonly=on')]
 (run/'input-files.json').write_text(json.dumps({str(x):hashlib.sha256(x.read_bytes()).hexdigest()for x in paths['probe'].iterdir()if x.is_file()},indent=2)+'\n')
 (run/'launch.json').write_text(json.dumps(dict(args=args,read_only_tags=['wine','libs','prefix','probe'],network=False,timeout_seconds=150),indent=2)+'\n')
 env=os.environ.copy();env['LD_LIBRARY_PATH']=str(q/'usr/lib/x86_64-linux-gnu');start=time.monotonic()
 try:
  with(run/'serial.log').open('w')as stream:r=subprocess.run(args,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=150)
  status=dict(qemu_exit_code=r.returncode,timed_out=False,seconds=time.monotonic()-start)
 except subprocess.TimeoutExpired:status=dict(qemu_exit_code=None,timed_out=True,seconds=time.monotonic()-start)
 (run/'host-status.json').write_text(json.dumps(status,indent=2)+'\n');print(status)


if __name__=='__main__':main()
