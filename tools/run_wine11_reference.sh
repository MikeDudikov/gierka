#!/usr/bin/env bash
# Native64 Wine reference launcher. This is compatibility-layer validation,
# not evidence of execution on Windows11 or on the requested laptop.
set -euo pipefail

if [[ $# == 0 ]]; then
    echo "Usage: bash tools/run_wine11_reference.sh /absolute/path/program.exe [args...]" >&2
    exit 2
fi
WINE_REFERENCE_ROOT=/workspace/toolchains/wine11-root
WINE_REFERENCE_RUNTIME="$WINE_REFERENCE_ROOT/opt/wine-stable"
if [[ ! -x "$WINE_REFERENCE_RUNTIME/bin/wine" ]]; then
    echo "Wine11 is missing; run tools/setup_wine_wow64.sh first." >&2
    exit 2
fi

export WINEARCH=wow64
export WINEPREFIX=/workspace/gierka/artifacts/runtime-original/prefix-wine11
export DISPLAY="${DISPLAY:-:79}"
export WINEDEBUG="${WINEDEBUG:--all}"
export WINEDLLOVERRIDES=winemenubuilder.exe=d
export LD_LIBRARY_PATH="$WINE_REFERENCE_ROOT/usr/lib/x86_64-linux-gnu"
export WINESERVER="$WINE_REFERENCE_RUNTIME/bin/wineserver"
exec "$WINE_REFERENCE_RUNTIME/bin/wine" "$@"
