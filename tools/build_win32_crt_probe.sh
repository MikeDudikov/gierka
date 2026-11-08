#!/usr/bin/env bash
# Reproducible own PE32/PE64 controls and wrapper for unchanged original CRT pages.
set -euo pipefail
crt_probe_repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
crt_probe_out="${1:-$crt_probe_repo/artifacts/queued-crt-context}"
crt_probe_sdk32=/workspace/toolchains/mingw32-crt/root/usr
crt_probe_sdk64=/workspace/toolchains/mingw-probe/root/usr
[[ ! -L "$crt_probe_out" ]]
mkdir -p "$crt_probe_out"
for crt_probe_name in probe control32 control64;do [[ ! -L "$crt_probe_out/$crt_probe_name.exe" ]];done
crt_probe_tmp=$(mktemp -d "$crt_probe_out/.build.XXXXXX")
trap 'rm -rf -- "$crt_probe_tmp"' EXIT
PATH="$crt_probe_sdk32/bin:$PATH" "$crt_probe_sdk32/bin/i686-w64-mingw32-gcc-posix" \
 -O2 -ffreestanding -fno-builtin -fno-stack-protector -Wall -Wextra -Werror -nostdlib \
 -Wl,--entry,_mainCRTStartup -Wl,--subsystem,console -Wl,--image-base,0x400000 \
 -Wl,--section-start,.origcrt=0x580000 -Wl,--disable-dynamicbase -Wl,--no-insert-timestamp \
 "$crt_probe_repo/tools/win32_original_crt_probe.c" -o "$crt_probe_tmp/probe.exe" -lkernel32
PATH="$crt_probe_sdk32/bin:$PATH" "$crt_probe_sdk32/bin/i686-w64-mingw32-gcc-posix" \
 -O2 -ffreestanding -fno-builtin -fno-stack-protector -Wall -Wextra -Werror -nostdlib \
 -Wl,--entry,_mainCRTStartup -Wl,--subsystem,console -Wl,--image-base,0x10000000 \
 -Wl,--disable-dynamicbase -Wl,--no-insert-timestamp \
 "$crt_probe_repo/tools/windows_crt_arch_control.c" -o "$crt_probe_tmp/control32.exe" -lkernel32
PATH="$crt_probe_sdk64/bin:$PATH" "$crt_probe_sdk64/bin/x86_64-w64-mingw32-gcc-posix" \
 -O2 -ffreestanding -fno-builtin -fno-stack-protector -Wall -Wextra -Werror -nostdlib \
 -Wl,--entry,mainCRTStartup -Wl,--subsystem,console -Wl,--image-base,0x10000000 \
 -Wl,--disable-dynamicbase -Wl,--no-insert-timestamp \
 "$crt_probe_repo/tools/windows_crt_arch_control.c" -o "$crt_probe_tmp/control64.exe" -lkernel32
for crt_probe_name in probe control32 control64;do
 if ! cmp -s -- "$crt_probe_tmp/$crt_probe_name.exe" "$crt_probe_out/$crt_probe_name.exe";then
  mv -- "$crt_probe_tmp/$crt_probe_name.exe" "$crt_probe_out/$crt_probe_name.exe"
 fi
done
sha256sum "$crt_probe_out/probe.exe" "$crt_probe_out/control32.exe" "$crt_probe_out/control64.exe"
