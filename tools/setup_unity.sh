#!/usr/bin/env bash
# Exact official Unity toolchain; does not activate licenses or publish anything.
set -euo pipefail

task_toolchain_root=/workspace/toolchains
unity_build_version=6000.3.27f2
unity_cli_version=1.0.0-beta.15
unity_revision=22188f149405
unity_editor_root="$task_toolchain_root/Unity/$unity_build_version"
unity_downloads="$task_toolchain_root/unity-downloads"
mkdir -p "$unity_downloads" "$task_toolchain_root/unity-config"

verify_artifact() {
  python3 - "$1" "$2" "$3" "$4" <<'PY'
import base64
import hashlib
from pathlib import Path
import sys
path = Path(sys.argv[1])
expected_size, expected_md5, expected_sha256 = int(sys.argv[2]), sys.argv[3], sys.argv[4]
md5, sha256 = hashlib.md5(), hashlib.sha256()
with path.open('rb') as source:
    while chunk := source.read(8 * 1024 * 1024):
        md5.update(chunk)
        sha256.update(chunk)
if (path.stat().st_size != expected_size
        or base64.b64encode(md5.digest()).decode() != expected_md5
        or sha256.hexdigest() != expected_sha256):
    raise SystemExit('Artifact integrity verification failed: ' + str(path))
print('Verified: ' + path.name)
PY
}

if [[ ! -x "$task_toolchain_root/unity-cli/bin/unity" ]]; then
  curl -fsSL https://unity.com/install.sh -o "$task_toolchain_root/install-unity-cli.sh"
  UNITY_CLI_HOME="$task_toolchain_root/unity-cli" \
    UNITY_CLI_VERSION="$unity_cli_version" \
    XDG_CONFIG_HOME="$task_toolchain_root/unity-config" SHELL=/bin/sh \
    bash "$task_toolchain_root/install-unity-cli.sh"
fi
[[ "$("$task_toolchain_root/unity-cli/bin/unity" --version)" == "$unity_cli_version" ]]

unity_license_client="$task_toolchain_root/unity-config/unityhub/external-modules/licensingClient/Unity.Licensing.Client"
if [[ ! -x "$unity_license_client" ]]; then
  XDG_CONFIG_HOME="$task_toolchain_root/unity-config" \
    UNITY_NO_CRASH_REPORT=1 UNITY_NO_CLI_INVOKED_TELEMETRY=1 \
    "$task_toolchain_root/unity-cli/bin/unity" plugin install licensingClient --offline --json --non-interactive
fi
[[ "$("$unity_license_client" --version)" == 'Unity.Licensing.Client 1.19.0+4cc3dda' ]]

unity_editor_archive="$unity_downloads/Unity-$unity_build_version.tar.xz"
unity_windows_archive="$unity_downloads/UnitySetup-Windows-Mono-$unity_build_version.pkg"
if [[ ! -f "$unity_editor_archive" ]]; then
  curl -fSL --retry 2 \
    "https://download.unity3d.com/download_unity/$unity_revision/LinuxEditorInstaller/Unity-$unity_build_version.tar.xz" \
    -o "$unity_editor_archive"
fi
verify_artifact "$unity_editor_archive" 4571351400 '1WhJJDM14mFKV0fkRle2Ng==' \
  44d25a121717b71f096f2db8ae69b46505a66c34e56055c0a566f975ea817e6d

if [[ ! -f "$unity_windows_archive" ]]; then
  curl -fSL --retry 2 \
    "https://download.unity3d.com/download_unity/$unity_revision/MacEditorTargetInstaller/UnitySetup-Windows-Mono-Support-for-Editor-$unity_build_version.pkg" \
    -o "$unity_windows_archive"
fi
verify_artifact "$unity_windows_archive" 384750585 'vd7+rGn6hsTLKInSw+niZw==' \
  08d8310a9c966a3f38c530e2ccc09e0b6ad928c1044bf8ec8505a4b0ae0fae5f

unity_stage=$(mktemp -d "$task_toolchain_root/unity-install-stage.XXXXXX")
trap 'rm -rf "$unity_stage"' EXIT
if [[ ! -x "$unity_editor_root/Editor/Unity" ]]; then
  if [[ -e "$unity_editor_root/Editor" ]]; then
    echo 'Refusing to replace an existing incomplete Editor directory.' >&2
    exit 1
  fi
  mkdir -p "$unity_editor_root"
  tar -xJf "$unity_editor_archive" -C "$unity_stage"
  mv "$unity_stage/Editor" "$unity_editor_root/Editor"
fi
[[ "$("$unity_editor_root/Editor/Unity" -version)" == "$unity_build_version" ]]

unity_windows_root="$unity_editor_root/Editor/Data/PlaybackEngines/WindowsStandaloneSupport"
if [[ ! -f "$unity_windows_root/UnityEditor.WindowsStandalone.Extensions.dll" ]]; then
  if [[ -e "$unity_windows_root" ]]; then
    echo 'Refusing to replace an existing incomplete Windows module.' >&2
    exit 1
  fi
  unity_sevenzip="$task_toolchain_root/7zip/usr/lib/7zip/7z"
  [[ -x "$unity_sevenzip" ]] || {
    echo 'Install the verified 7-Zip helper first: bash tools/setup_7zip.sh' >&2
    exit 1
  }
  mkdir -p "$unity_stage/xar" "$unity_stage/cpio" "$unity_windows_root"
  "$unity_sevenzip" x -y "-o$unity_stage/xar" "$unity_windows_archive" TargetSupport.pkg.tmp/Payload >/dev/null
  "$unity_sevenzip" x -y "-o$unity_stage/cpio" "$unity_stage/xar/TargetSupport.pkg.tmp/Payload" >/dev/null
  "$unity_sevenzip" x -y "-o$unity_windows_root" "$unity_stage/cpio/Payload~" >/dev/null
fi
python3 - "$unity_windows_root" <<'PY'
import hashlib
from pathlib import Path
import sys
root = Path(sys.argv[1])
checks = {
    'UnityEditor.WindowsStandalone.Extensions.dll': 'e6faedcbf44b04eaca4353c722a41398fbbbe6029c6aa7dba6d1d740c2df27d2',
    'Variations/win64_player_nondevelopment_mono/UnityPlayer.dll': '2ba2e277918300e650158688bf94242c386eb21244574766aa17f687092d53b4',
}
for name, expected in checks.items():
    with (root / name).open('rb') as source:
        if hashlib.file_digest(source, 'sha256').hexdigest() != expected:
            raise SystemExit('Installed Windows module check failed: ' + name)
print('Windows Mono module files verified.')
PY

XDG_CONFIG_HOME="$task_toolchain_root/unity-config" \
  UNITY_NO_CRASH_REPORT=1 UNITY_NO_CLI_INVOKED_TELEMETRY=1 \
  "$task_toolchain_root/unity-cli/bin/unity" editors --installed --json > "$unity_stage/installed.json"
if ! python3 - "$unity_stage/installed.json" "$unity_editor_root/Editor/Unity" <<'PY'
import json
from pathlib import Path
import sys
items = json.loads(Path(sys.argv[1]).read_text())['data']['items']
raise SystemExit(0 if any(item['location'] == sys.argv[2] for item in items) else 1)
PY
then
  XDG_CONFIG_HOME="$task_toolchain_root/unity-config" \
    UNITY_NO_CRASH_REPORT=1 UNITY_NO_CLI_INVOKED_TELEMETRY=1 \
    "$task_toolchain_root/unity-cli/bin/unity" editors add "$unity_editor_root/Editor/Unity" --json
fi

cat > "$unity_stage/unity-env.sh" <<'ENV'
# Source before Unity commands in this environment.
export UNITY_CLI_HOME=/workspace/toolchains/unity-cli
export XDG_CONFIG_HOME=/workspace/toolchains/unity-config
export XDG_DATA_HOME=/workspace/toolchains/unity-data
export XDG_CACHE_HOME=/workspace/toolchains/unity-cache
export PATH=/workspace/toolchains/unity-cli/bin:/workspace/toolchains/Unity/6000.3.27f2/Editor:$PATH
ENV
if [[ ! -e "$task_toolchain_root/unity-env.sh" ]]; then
  cp "$unity_stage/unity-env.sh" "$task_toolchain_root/unity-env.sh"
elif ! cmp -s "$unity_stage/unity-env.sh" "$task_toolchain_root/unity-env.sh"; then
  echo 'Preserved customized unity-env.sh; review paths before sourcing it.' >&2
fi

echo "Installed Unity $unity_build_version at $unity_editor_root/Editor/Unity"
echo 'A valid Unity Editor license is still required for import, tests and builds.'
