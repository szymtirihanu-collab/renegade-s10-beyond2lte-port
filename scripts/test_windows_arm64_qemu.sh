#!/usr/bin/env bash
set -euo pipefail

# Generic ARM64 QEMU validation only. This is not the Samsung device boot path.
MEDIA_IMAGE="${1:-$HOME/beyond2lte-windows11-aio/windows11-arm64-gpt-disk.img}"
QEMU="${QEMU:-qemu-system-aarch64}"
QEMU_IMG="${QEMU_IMG:-qemu-img}"
CODE="${UEFI_CODE:-}"
VARS="${UEFI_VARS:-}"
ISO="${WINDOWS_ISO:-}"
TARGET="${QEMU_TARGET_DISK:-}"
TARGET_SIZE="${QEMU_TARGET_SIZE:-32G}"

if [[ ! -f "$MEDIA_IMAGE" ]]; then
  echo "ERROR: validated media bundle not found: $MEDIA_IMAGE" >&2
  echo "Build it first with scripts/build_windows11_beyond2lte_aio.py" >&2
  exit 2
fi
OUTDIR="$(dirname "$MEDIA_IMAGE")"

if [[ -z "$ISO" ]]; then
  shopt -s nullglob
  ISOS=("$OUTDIR"/*.iso)
  shopt -u nullglob
  if [[ ${#ISOS[@]} -ne 1 ]]; then
    echo "ERROR: expected exactly one Windows ISO in $OUTDIR; set WINDOWS_ISO=/path/to/windows-arm64.iso" >&2
    exit 2
  fi
  ISO="${ISOS[0]}"
fi
if [[ ! -f "$ISO" ]]; then echo "ERROR: Windows ISO not found: $ISO" >&2; exit 2; fi
if ! command -v "$QEMU" >/dev/null 2>&1; then echo "ERROR: qemu-system-aarch64 is not installed." >&2; exit 2; fi
if ! command -v "$QEMU_IMG" >/dev/null 2>&1; then echo "ERROR: qemu-img is not installed (install the QEMU utilities package)." >&2; exit 2; fi

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
if [[ -z "$CODE" || ! -f "$CODE" ]]; then echo "ERROR: AArch64 UEFI CODE firmware not found. Set UEFI_CODE=/path/to/AAVMF_CODE.fd" >&2; exit 2; fi
if [[ -z "$VARS" || ! -f "$VARS" ]]; then echo "ERROR: AArch64 UEFI VARS template not found. Set UEFI_VARS=/path/to/AAVMF_VARS.fd" >&2; exit 2; fi

# Use the original Windows ISO as a USB optical device for setup source files.
# Keep the installation target separate and expose it as NVMe.
VARS_COPY="$OUTDIR/qemu-aarch64-vars-test.fd"
TARGET="${TARGET:-$OUTDIR/windows11-qemu-install-target.qcow2}"
cp --reflink=auto "$VARS" "$VARS_COPY"
if [[ ! -e "$TARGET" ]]; then "$QEMU_IMG" create -f qcow2 "$TARGET" "$TARGET_SIZE"; else echo "Reusing existing QEMU target disk: $TARGET"; fi

echo "QEMU test only: generic virtual ARM machine, NOT Samsung hardware."
echo "Windows source: $ISO (USB optical device)"
echo "Separate install target: $TARGET"
echo "The GPT/FAT32 media image is retained for validation but is not used as the install target."
exec "$QEMU" \
  -machine virt,gic-version=max -cpu max -smp 4 -m 4096 \
  -boot menu=on \
  -drive if=pflash,format=raw,readonly=on,file="$CODE" \
  -drive if=pflash,format=raw,file="$VARS_COPY" \
  -drive if=none,id=winiso,media=cdrom,format=raw,readonly=on,file="$ISO" \
  -device qemu-xhci,id=xhci \
  -device usb-storage,drive=winiso,bootindex=1 \
  -drive if=none,id=installtarget,format=qcow2,file="$TARGET" \
  -device nvme,drive=installtarget,serial=WIN11TARGET \
  -device ramfb -device usb-kbd,bus=xhci.0 -device usb-tablet,bus=xhci.0 \
  -display gtk -serial stdio
