#!/usr/bin/env bash
set -euo pipefail

# Generic ARM64 QEMU validation only. This is not the Samsung device boot path.
MEDIA_IMAGE="${1:-$HOME/beyond2lte-windows11-aio/windows11-arm64-gpt-disk.img}"
QEMU="${QEMU:-qemu-system-aarch64}"
QEMU_IMG="${QEMU_IMG:-qemu-img}"
SWTPM="${SWTPM:-swtpm}"
CODE="${UEFI_CODE:-}"
VARS="${UEFI_VARS:-}"
ISO="${WINDOWS_ISO:-}"
TARGET="${QEMU_TARGET_DISK:-}"
TARGET_SIZE="${QEMU_TARGET_SIZE:-64G}"

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
if ! command -v "$SWTPM" >/dev/null 2>&1; then echo "ERROR: swtpm is not installed." >&2; exit 2; fi

find_first() {
  for p in "$@"; do
    [[ -f "$p" ]] && { printf '%s\\n' "$p"; return 0; }
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

# Preserve UEFI variables and TPM state between launches so the installed guest
# retains its boot entries and TPM-sealed state across VM reboots.
VARS_COPY="$OUTDIR/qemu-aarch64-vars-test.fd"
TARGET="${TARGET:-$OUTDIR/windows11-qemu-install-target.qcow2}"
TPM_STATE="$OUTDIR/qemu-swtpm-state"
TPM_SOCKET="$OUTDIR/qemu-swtpm.sock"
TPM_LOG="$OUTDIR/qemu-swtpm.log"
mkdir -p "$TPM_STATE"
if [[ ! -e "$VARS_COPY" ]]; then cp --reflink=auto "$VARS" "$VARS_COPY"; fi
if [[ ! -e "$TARGET" ]]; then
  "$QEMU_IMG" create -f qcow2 "$TARGET" "$TARGET_SIZE"
else
  # Grow an existing target if it is below the Windows Setup minimum. Never shrink it.
  CURRENT_BYTES="$("$QEMU_IMG" info --output=json "$TARGET" | python3 -c 'import json,sys; print(json.load(sys.stdin)["virtual-size"])')"
  REQUIRED_BYTES="$(python3 -c 'import re,sys; s=sys.argv[1].strip().upper(); m=re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)([KMGTP]?)",s); assert m, "Unsupported QEMU_TARGET_SIZE"; print(int(float(m.group(1)) * (1024 ** {"":0,"K":1,"M":2,"G":3,"T":4,"P":5}[m.group(2)])))' "$TARGET_SIZE")"
  if (( CURRENT_BYTES < REQUIRED_BYTES )); then
    echo "Expanding existing QEMU target disk to at least $TARGET_SIZE ..."
    "$QEMU_IMG" resize -f qcow2 "$TARGET" "$TARGET_SIZE"
  else
    echo "Existing QEMU target disk is already large enough: $TARGET"
  fi
fi
if [[ -e "$TPM_SOCKET" ]]; then
  echo "ERROR: TPM socket already exists: $TPM_SOCKET" >&2
  echo "Check for an older QEMU/swtpm process before removing a stale socket." >&2
  exit 2
fi

"$SWTPM" socket --tpm2 --tpmstate dir="$TPM_STATE" --ctrl type=unixio,path="$TPM_SOCKET" --log file="$TPM_LOG" &
TPM_PID=$!
cleanup() {
  kill "$TPM_PID" 2>/dev/null || true
  wait "$TPM_PID" 2>/dev/null || true
  rm -f "$TPM_SOCKET"
}
trap cleanup EXIT INT TERM

for _ in {1..50}; do
  [[ -S "$TPM_SOCKET" ]] && break
  if ! kill -0 "$TPM_PID" 2>/dev/null; then
    echo "ERROR: swtpm exited during startup. Log: $TPM_LOG" >&2
    exit 2
  fi
  sleep 0.1
done
if [[ ! -S "$TPM_SOCKET" ]]; then
  echo "ERROR: swtpm did not create its control socket. Log: $TPM_LOG" >&2
  exit 2
fi

echo "QEMU test only: generic virtual ARM machine, NOT Samsung hardware."
echo "Windows source: $ISO (USB optical device)"
echo "Separate install target: $TARGET"
echo "TPM 2.0: software-emulated by swtpm; state persists in $TPM_STATE"
echo "UEFI variables persist in $VARS_COPY"
echo "The GPT/FAT32 media image is retained for validation but is not used as the install target."
"$QEMU" \
  -machine virt,gic-version=max -cpu max -smp 4 -m 4096 \
  -boot menu=on \
  -drive if=pflash,format=raw,readonly=on,file="$CODE" \
  -drive if=pflash,format=raw,file="$VARS_COPY" \
  -chardev socket,id=chrtpm,path="$TPM_SOCKET" \
  -tpmdev emulator,id=tpm0,chardev=chrtpm \
  -device tpm-tis-device,tpmdev=tpm0 \
  -drive if=none,id=winiso,media=cdrom,format=raw,readonly=on,file="$ISO" \
  -device qemu-xhci,id=xhci \
  -device usb-storage,drive=winiso,bootindex=1 \
  -drive if=none,id=installtarget,format=qcow2,file="$TARGET" \
  -device nvme,drive=installtarget,serial=WIN11TARGET \
  -device ramfb -device usb-kbd,bus=xhci.0 -device usb-tablet,bus=xhci.0 \
  -display gtk -serial stdio
