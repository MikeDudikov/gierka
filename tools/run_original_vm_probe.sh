#!/usr/bin/env bash
# Isolated full-system TCG probe. No host-root mount, KVM or guest networking.
set -euo pipefail
if [[ $# != 1 ]]; then
    echo 'Usage: bash tools/run_original_vm_probe.sh /workspace/gierka/artifacts/runtime-original/vm/FRESH_RUN' >&2
    exit 2
fi
VM_PROBE_BASE=/workspace/toolchains/original-vm
VM_PROBE_QEMU=/workspace/toolchains/original-vm-root
VM_PROBE_OUTPUT=$(realpath -m -- "$1")
case "$VM_PROBE_OUTPUT" in
    /workspace/gierka/artifacts/runtime-original/vm/*) ;;
    *) echo 'Output must be a fresh subdirectory of artifacts/runtime-original/vm.' >&2; exit 2 ;;
esac
if [[ -e "$VM_PROBE_OUTPUT" || -L "$VM_PROBE_OUTPUT" ]]; then
    echo 'Refusing to replace an existing run.' >&2
    exit 2
fi
for VM_PROBE_FILE in \
    "$VM_PROBE_QEMU/usr/bin/qemu-system-x86_64" \
    "$VM_PROBE_QEMU/usr/share/seabios/bios-256k.bin" \
    "$VM_PROBE_QEMU/boot/vmlinuz-6.12.113+deb13-amd64" \
    "$VM_PROBE_BASE/initramfs.cpio.gz"; do
    test -f "$VM_PROBE_FILE"
done
mkdir -p -- "$VM_PROBE_OUTPUT"
sha256sum \
    "$VM_PROBE_QEMU/boot/vmlinuz-6.12.113+deb13-amd64" \
    "$VM_PROBE_QEMU/usr/share/seabios/bios-256k.bin" \
    "$VM_PROBE_BASE/initramfs.cpio.gz" > "$VM_PROBE_OUTPUT/boot-input-sha256.txt"
# VM receives only readonly tool/data directories and one fresh writable report directory.
LD_LIBRARY_PATH="$VM_PROBE_QEMU/usr/lib/x86_64-linux-gnu" \
    timeout 360 "$VM_PROBE_QEMU/usr/bin/qemu-system-x86_64" \
    -L "$VM_PROBE_QEMU/usr/share/qemu" \
    -bios "$VM_PROBE_QEMU/usr/share/seabios/bios-256k.bin" \
    -machine q35 -accel tcg,thread=multi -cpu max -smp 2 -m 4096 \
    -nodefaults -no-reboot -display none -serial stdio -monitor none -nic none \
    -kernel "$VM_PROBE_QEMU/boot/vmlinuz-6.12.113+deb13-amd64" \
    -initrd "$VM_PROBE_BASE/initramfs.cpio.gz" \
    -append 'console=ttyS0 panic=-1 quiet' \
    -virtfs "local,path=$VM_PROBE_BASE/guest-wine,mount_tag=wine,security_model=none,readonly=on" \
    -virtfs "local,path=$VM_PROBE_BASE/hostlibs,mount_tag=libs,security_model=none,readonly=on" \
    -virtfs 'local,path=/workspace/gierka/artifacts/runtime-original/game,mount_tag=game,security_model=none,readonly=on' \
    -virtfs "local,path=$VM_PROBE_OUTPUT,mount_tag=out,security_model=none" \
    > "$VM_PROBE_OUTPUT/serial.log" 2>&1
