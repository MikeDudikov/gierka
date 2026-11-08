#!/usr/bin/env bash
# Reproducible freestanding diagnostic; no Unity/game changes or input injection.
set -euo pipefail
pointer_focus_repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
pointer_focus_out="${1:-$pointer_focus_repo/artifacts/pointer-input/win32-focus-probe}"
pointer_focus_sdk=/workspace/toolchains/mingw-probe/root/usr
[[ ! -L "$pointer_focus_out" ]] || { echo "Refuse a symbolic output directory" >&2; exit 1; }
mkdir -p "$pointer_focus_out"
[[ ! -L "$pointer_focus_out/probe.exe" ]] || { echo "Refuse a symbolic probe executable" >&2; exit 1; }
pointer_focus_tmp="$(mktemp "$pointer_focus_out/.focus.XXXXXX.exe")"
trap 'rm -f -- "$pointer_focus_tmp"' EXIT
PATH="$pointer_focus_sdk/bin:$PATH" "$pointer_focus_sdk/bin/x86_64-w64-mingw32-gcc-posix" \
  -O2 -ffreestanding -fno-builtin -fno-stack-protector -mno-red-zone \
  -Wall -Wextra -Werror -nostdlib -Wl,--entry,mainCRTStartup \
  -Wl,--subsystem,windows -Wl,--no-insert-timestamp \
  "$pointer_focus_repo/tools/win64_pointer_focus_probe.c" -o "$pointer_focus_tmp" -luser32 -lkernel32
if ! cmp -s -- "$pointer_focus_tmp" "$pointer_focus_out/probe.exe"; then
  mv -f -- "$pointer_focus_tmp" "$pointer_focus_out/probe.exe"
fi
sha256sum "$pointer_focus_repo/tools/win64_pointer_focus_probe.c" "$pointer_focus_out/probe.exe"
