#!/usr/bin/env bash
# Diagnostic launcher for the prepared local Wine reference environment.
# --game32 is currently BLOCKED by STATUS_CONFLICTING_ADDRESSES; no EXE patching.
set -euo pipefail

cd /workspace/gierka
WINE_REFERENCE_ROOT=/workspace/toolchains/wine-root
WINE_REFERENCE_ARTIFACTS=/workspace/gierka/artifacts/runtime-original
WINE_REFERENCE_MODE="${1:---control32}"

if [[ ! -x "$WINE_REFERENCE_ROOT/usr/lib/wine/wine64" ]]; then
    echo "Local verified Wine installation is missing; see docs/ORIGINAL_RUNTIME.md" >&2
    exit 2
fi

export DISPLAY="${DISPLAY:-:78}"
export WINESERVER="$WINE_REFERENCE_ROOT/usr/lib/wine/wineserver64"
export WINEDEBUG="${WINEDEBUG:--all}"

case "$WINE_REFERENCE_MODE" in
    --control32|--game32)
        export WINEPREFIX="$WINE_REFERENCE_ARTIFACTS/prefix32c"
        export WINEARCH=win32
        export WINELOADERNOEXEC=1
        export LD_LIBRARY_PATH="$WINE_REFERENCE_ROOT/usr/lib/i386-linux-gnu"
        export WINEDLLPATH="$WINE_REFERENCE_ROOT/usr/lib/i386-linux-gnu/wine"
        if [[ "$WINE_REFERENCE_MODE" == --control32 ]]; then
            set -- 'C:\windows\system32\cmd.exe' /c ver
        else
            cd "$WINE_REFERENCE_ARTIFACTS/game"
            set -- 'Z:\workspace\gierka\artifacts\runtime-original\game\ancient.exe'
        fi
        exec timeout "${ORIGINAL_PROBE_TIMEOUT:-30s}" \
            "$WINE_REFERENCE_ROOT/usr/bin/qemu-i386" -L "$WINE_REFERENCE_ROOT" \
            "$WINE_REFERENCE_ROOT/usr/lib/wine/wine" "$@"
        ;;
    --control64)
        export WINEPREFIX="$WINE_REFERENCE_ARTIFACTS/prefix64"
        export LD_LIBRARY_PATH="$WINE_REFERENCE_ROOT/usr/lib/x86_64-linux-gnu"
        exec timeout "${ORIGINAL_PROBE_TIMEOUT:-30s}" \
            "$WINE_REFERENCE_ROOT/usr/lib/wine/wine64" \
            'C:\windows\system32\cmd.exe' /c ver
        ;;
    *)
        echo "Usage: bash tools/probe_original_runtime.sh [--control32|--control64|--game32]" >&2
        exit 2
        ;;
esac
