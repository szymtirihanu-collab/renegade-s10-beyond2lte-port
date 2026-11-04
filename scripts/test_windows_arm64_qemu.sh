#!/usr/bin/env bash
set -euo pipefail
IMAGE="\${1:-$HOME/beyond2lte-windows11-aio/windows11-arm64-gpt-disk.img}"
QEMU="\${QEMU:-qemu-system-aarch64}"
CODE="\${UEFI_CODE:-}"
VARS="\${UEFI_VARS:-}"
if [[ ! -f "$IMAGE" ]]; then
  echo "ERROR: media image not found: $IMAGE" >&2
  echo "Build it first with scripts/build_windows11_beyond2lte_aio.py" >&2
  exit 2
fi
if ! command -v "$QEMU" >/dev/null 2>&1; then
  echo "ERROR: qemu-system-aarch64 is not installed." >&2
  exit 2
fi
find_first() {
  for p in "$@"; do
    [[ -f "$p" ]] && { printf '%s\n' "$p"; return 0; }
  done
  return 1
}
if [[ -z "$CODE" ]]; then
  CODE="$(find_first /usr/share/qemu/aavmf-aarch64-code.bin /usr/share/qemu/edk2-aarch64-code.fd /usr/share/edk2/aarch64/QEMU_EFI.fd /usr/share/AAVMF/AAVMF_CODE.fd /usr/share/edk2-armvirt/edk2-armvirt-code.fd || true)"
fi
if [[ -z "$VARS" ]]; then
  VARS="$(find_first /usr/share/qemu/aavmf-aarch64-vars.bin /usr/share/qemu/edk2-aarch64-vars.fd /usr/share/AAVMF/AAVMF_VARS.fd /usr/share/edk2-armvirt/edk2-armvirt-vars.fd || true)"
fi
if [[ -z "$CODE" || ! -f "$CODE" ]]; then
  echo "ERROR: AArch64 UEFI CODE firmware not found. Set UEFI_CODE=/path/to/AAVMF_CODE.fd" >&2
  exit 2
fi
if [[ -z "$VARS" || ! -f "$VARS" ]]; then
  echo "ERROR: AArch64 UEFI VARS template not found. Set UEFI_VARS=/path/to/AAVMF_VARS.fd" >&2
  exit 2
fi
OUTDIR="$(dirname "$IMAGE")"
VARS_COPY="$OUTDIR/qemu-aarch64-vars-test.fd"
cp --reflink=auto "$VARS" "$VARS_COPY"
echo "QEMU test only: generic virtual ARM machine, NOT Samsung hardware."
echo "Expected: Windows Boot Manager or Windows Setup appears."
exec "$QEMU" \
  -machine virt,gic-version=max -cpu max -smp 4 -m 4096 \
  -drive if=pflash,format=raw,readonly=on,file="$CODE" \
  -drive if=pflash,format=raw,file="$VARS_COPY" \
  -drive if=none,id=winmedia,format=raw,file="$IMAGE" \
  -device nvme,drive=winmedia,serial=WIN11ARM64 \
  -device ramfb -device qemu-xhci -device usb-kbd -device usb-tablet \
  -display gtk -serial stdio
