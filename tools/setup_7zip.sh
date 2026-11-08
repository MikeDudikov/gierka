#!/usr/bin/env bash
set -euo pipefail
cd /workspace/toolchains
mkdir -p apt/empty-parts apt/lists/partial apt/cache/archives/partial apt/downloads 7zip
cat > apt/apt.conf <<'APT'
Dir::Etc::parts "/workspace/toolchains/apt/empty-parts";
Dir::Etc::main "-";
Dir::Etc::sourcelist "/workspace/toolchains/apt/sources.list";
Dir::Etc::sourceparts "-";
Dir::State::lists "/workspace/toolchains/apt/lists";
Dir::Cache "/workspace/toolchains/apt/cache";
Dir::Cache::archives "/workspace/toolchains/apt/cache/archives";
Acquire::Languages "none";
Acquire::Retries "0";
APT::Get::List-Cleanup "0";
APT
cat > apt/sources.list <<'APT'
deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://deb.debian.org/debian trixie main non-free
APT
export APT_CONFIG=/workspace/toolchains/apt/apt.conf
/usr/bin/apt-get update
cd apt/downloads
/usr/bin/apt-get download '7zip=25.01+dfsg-1~deb13u2' '7zip-rar=25.00+ds-1+deb13u1'
printf '%s\n' 'b2cb210bee3be6a10230b38b8645d71846d19364b157f44fd08e1a54cae1652f  7zip_25.01+dfsg-1~deb13u2_amd64.deb' 'c2ab6330552d9d48b74eb4618081f2638ba0b559da85c56d22dde16255c64efa  7zip-rar_25.00+ds-1+deb13u1_amd64.deb' | sha256sum -c -
dpkg-deb -x '7zip_25.01+dfsg-1~deb13u2_amd64.deb' /workspace/toolchains/7zip
dpkg-deb -x '7zip-rar_25.00+ds-1+deb13u1_amd64.deb' /workspace/toolchains/7zip
/workspace/toolchains/7zip/usr/lib/7zip/7z i
