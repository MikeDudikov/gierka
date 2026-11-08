#!/usr/bin/env bash
# Recreate local dependencies; never activates Unity or publishes the project.
set -euo pipefail
task_project="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$task_project"
if [[ ! -x .venv/bin/python ]]; then python3 -m venv .venv; fi
if ! .venv/bin/python - <<'PY'
from importlib.metadata import version
expected={'pycdlib':'1.22.0','pefile':'2024.8.26','Pillow':'13.0.0','unicorn':'2.1.4'}
try:
    assert all(version(name)==value for name,value in expected.items())
except Exception:
    raise SystemExit(1)
PY
then
    .venv/bin/python -m pip install -r tools/requirements-analysis.txt
fi
source tools/handoff_env.sh
for task_option in "$@"; do
    case "$task_option" in
        --unity) bash tools/setup_unity.sh ;;
        --wine) bash tools/setup_wine_wow64.sh ;;
        --wine-prefix)
            if [[ "$task_project" != /workspace/gierka ]]; then
                echo 'Wine launchers require /workspace/gierka; use the supplied Dev Container.' >&2
                exit 2
            fi
            task_wine=/workspace/toolchains/wine11-root
            [[ -x "$task_wine/opt/wine-stable/bin/wine" ]] || { echo 'Wine missing; use --wine.' >&2; exit 2; }
            mkdir -p artifacts/runtime-original
            WINEARCH=wow64 WINEPREFIX="$task_project/artifacts/runtime-original/prefix-wine11" \
              WINEDLLOVERRIDES=winemenubuilder.exe,mscoree,mshtml=d \
              LD_LIBRARY_PATH="$task_wine/usr/lib/x86_64-linux-gnu" \
              WINESERVER="$task_wine/opt/wine-stable/bin/wineserver" \
              "$task_wine/opt/wine-stable/bin/wine" wineboot -i
            ;;
        *) echo "Unknown option: $task_option" >&2; exit 2 ;;
    esac
done
echo 'Python dependencies ready. Source tools/handoff_env.sh, then run tools/handoff_verify.py.'
