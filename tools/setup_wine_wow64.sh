#!/usr/bin/env bash
# Local official WineHQ installation; does not change system APT or publish.
# Wine11 supports WINEARCH=wow64. Actual PE32 execution remains executor-dependent.
set -euo pipefail

WINE_SETUP_BASE=/workspace/toolchains/winehq-apt
WINE_SETUP_ROOT=/workspace/toolchains/wine11-root
WINE_SETUP_VERSION=11.0.0.0~trixie-1
WINE_SETUP_FINGERPRINT=D43F640145369C51D786DDEA76F1A20FF987672F

mkdir -p "$WINE_SETUP_BASE"/{empty-parts,lists/partial,cache/archives/partial,gnupg} "$WINE_SETUP_ROOT"
chmod 700 "$WINE_SETUP_BASE/gnupg"
export GNUPGHOME="$WINE_SETUP_BASE/gnupg"
curl -fsSL https://dl.winehq.org/wine-builds/debian/dists/trixie/winehq-trixie.sources \
    -o "$WINE_SETUP_BASE/winehq-trixie.sources"
# Key URL is documented by WineHQ's official Debian/Ubuntu installation guide.
curl -fsSL https://dl.winehq.org/wine-builds/winehq.key -o "$WINE_SETUP_BASE/winehq.key"
WINE_SETUP_OBSERVED=$(gpg --batch --show-keys --with-colons "$WINE_SETUP_BASE/winehq.key" \
    | awk -F: '$1 == "fpr" { print $10; exit }')
if [[ "$WINE_SETUP_OBSERVED" != "$WINE_SETUP_FINGERPRINT" ]]; then
    echo "WineHQ signing key fingerprint changed; investigate official key rotation." >&2
    exit 1
fi
gpg --batch --yes --dearmor --output "$WINE_SETUP_BASE/winehq-archive.gpg" "$WINE_SETUP_BASE/winehq.key"

cat > "$WINE_SETUP_BASE/apt.conf" <<'APT'
Dir::Etc::parts "/workspace/toolchains/winehq-apt/empty-parts";
Dir::Etc::main "-";
Dir::Etc::sourcelist "/workspace/toolchains/winehq-apt/sources.list";
Dir::Etc::sourceparts "-";
Dir::State::lists "/workspace/toolchains/winehq-apt/lists";
Dir::Cache "/workspace/toolchains/winehq-apt/cache";
Dir::Cache::archives "/workspace/toolchains/winehq-apt/cache/archives";
Acquire::Languages "none";
Acquire::Retries "0";
APT::Get::List-Cleanup "0";
APT::Architecture "amd64";
APT::Architectures { "amd64"; "i386"; };
APT
cat > "$WINE_SETUP_BASE/sources.list" <<'APT'
deb [arch=amd64,i386 signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://deb.debian.org/debian trixie main non-free
deb [arch=amd64,i386 signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://security.debian.org/debian-security trixie-security main
deb [arch=amd64,i386 signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://deb.debian.org/debian trixie-updates main
deb [arch=amd64,i386 signed-by=/workspace/toolchains/winehq-apt/winehq-archive.gpg] https://dl.winehq.org/wine-builds/debian trixie main
APT
export APT_CONFIG="$WINE_SETUP_BASE/apt.conf"
/usr/bin/apt-get update
# Trixie stable packages are split; i386 PE DLLs are needed even when only the
# native64 loader is used with WINEARCH=wow64. No i386 ELF or QEMU is launched.
/usr/bin/apt-get -y --download-only -o Debug::NoLocking=1 --no-install-recommends \
    install "winehq-stable=$WINE_SETUP_VERSION" xvfb xdotool fonts-liberation

python3 - <<'PY'
from pathlib import Path
import hashlib
import json
import subprocess

root = Path('/workspace/toolchains/wine11-root')
records = []
for package in sorted(Path('/workspace/toolchains/winehq-apt/cache/archives').glob('*.deb')):
    # The current task reused an earlier signed cache. Its old Wine and QEMU
    # binaries are deliberately excluded from this independent installation.
    if package.name.startswith(('libwine_', 'wine32_', 'wine64_', 'wine64-preloader_', 'qemu-user_')):
        continue
    subprocess.run(['dpkg-deb', '-x', str(package), str(root)], check=True)
    with package.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    records.append({'file': package.name, 'sha256': digest})
Path('/workspace/toolchains/winehq-apt/extracted-packages.json').write_text(
    json.dumps(records, indent=2) + '\n')
PY
test "$("$WINE_SETUP_ROOT/opt/wine-stable/bin/wine" --version)" = wine-11.0
echo "Official Wine11.0 installed locally; runtime controls must still be checked."
