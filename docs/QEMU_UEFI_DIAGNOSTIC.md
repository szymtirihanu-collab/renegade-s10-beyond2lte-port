# QEMU-only UEFI diagnostic harness

This harness provides a **host baseline**, not a simulated Galaxy S10+ and not a
Windows boot test.

## What it does

It starts generic AArch64 UEFI firmware (AAVMF) under QEMU's generic `virt`
machine, keeps the VM alive for a bounded interval, captures serial output,
and writes a JSON report with the firmware hash and process outcome.

## Why it does not boot SILICIUM_UEFI.fd

The current firmware is built for the Exynos 9820 / beyond2lte platform. QEMU's
`virt` machine has a different interrupt controller, timers, memory map,
devices, and firmware interface. Passing the Exynos image to that unrelated
machine would produce a misleading failure (or worse, a misleading apparent
success). This harness therefore tests the host's QEMU/AAVMF baseline only.

## Requirements

- Linux host with `qemu-system-aarch64`
- A generic AArch64 AAVMF code image, commonly packaged as
  `AAVMF_CODE.fd` by the distribution's AArch64 UEFI firmware package

## Run

```sh
python3 scripts/qemu_uefi_diagnostic.py \
  --aavmf-code /usr/share/AAVMF/AAVMF_CODE.fd \
  --seconds 8 \
  --report qemu-uefi-diagnostic.json
```

A passing result means only that QEMU launched and kept the generic AAVMF guest
alive until the timeout. Inspect the JSON serial log as well.

## Explicit exclusions

- Does not boot or write to a phone.
- Does not prove that Samsung S-Boot accepts any image.
- Does not test the Exynos UEFI firmware.
- Does not prove Windows Boot Manager or Windows can boot.
- Does not test UFS, USB, display, touch, ACPI correctness, or the live S-Boot
  execution state.

A handset test remains a separate, unverified milestone. This report must not
be described as a phone-boot result.
