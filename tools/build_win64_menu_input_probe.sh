#!/usr/bin/env bash
# Use the locally extracted official Debian MinGW compiler and import libraries.
set -euo pipefail
probe_repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
probe_out="${1:-$probe_repo/artifacts/unity-reference/input-probe/build}"
probe_mingw=/workspace/toolchains/mingw-probe/root/usr
if [[ -e "$probe_out" ]]; then
  echo "Select a fresh probe build directory: $probe_out" >&2
  exit 1
fi
mkdir -p "$probe_out"
export PATH="$probe_mingw/bin:$PATH"
"$probe_mingw/bin/x86_64-w64-mingw32-gcc-posix" -O2 -ffreestanding -fno-builtin \
  -fno-stack-protector -mno-red-zone -Wall -Wextra -nostdlib \
  -Wl,--entry,mainCRTStartup -Wl,--subsystem,console \
  "$probe_repo/tools/win64_menu_input_probe.c" -o "$probe_out/probe.exe" -luser32 -lkernel32
file "$probe_out/probe.exe"
sha256sum "$probe_repo/tools/win64_menu_input_probe.c" "$probe_out/probe.exe"
"$probe_mingw/bin/x86_64-w64-mingw32-gcc-posix" -O2 -ffreestanding -fno-builtin \
  -fno-stack-protector -mno-red-zone -Wall -Wextra -nostdlib \
  -Wl,--entry,mainCRTStartup -Wl,--subsystem,console \
  "$probe_repo/tools/win64_raw_input_probe.c" -o "$probe_out/raw-probe.exe" -luser32 -lkernel32
file "$probe_out/raw-probe.exe"
sha256sum "$probe_repo/tools/win64_raw_input_probe.c" "$probe_out/raw-probe.exe"
