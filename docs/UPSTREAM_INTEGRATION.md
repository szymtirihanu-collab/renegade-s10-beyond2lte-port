# Upstream integration and port status

## Decision

The SM-G975F does not need a fresh Qualcomm Renegade port. A device-specific Exynos 9820 UEFI implementation already exists in [orhunnx/beyond2lte-uefi](https://github.com/orhunnx/beyond2lte-uefi). This project will treat that repository as the implementation upstream and this repository as a downstream integration, provenance, and validation workspace.

Renegade's published firmware is for Qualcomm Snapdragon devices. Its platform packages and boot assumptions are not interchangeable with Samsung Exynos 9820. See the [Renegade FAQ](https://renegade-project.tech/en/faq) and [supported-device list](https://renegade-project.tech/en/devices).

## Pinned source

The reviewed upstream reference is pinned in [UPSTREAM.lock.json](../UPSTREAM.lock.json):

- Repository: `orhunnx/beyond2lte-uefi`
- Ref: `master`
- Commit: `f122c7024c5eeef2c8c78dfd08c62708c9ef823d`
- Commit date: 2026-08-27
- Target declared by upstream: Samsung Galaxy S10+ SM-G975F / `beyond2lte`, Exynos 9820, AArch64.

The pin is a reproducibility reference, not a claim that this revision has been built or tested here. Upstream's default branch currently points at this commit as observed during this review.

## What the upstream README reports

The upstream README reports UEFI entry, a simple framebuffer, physical side-key input, UFS Block I/O, an embedded EFI Shell, Linux boot reaching initramfs, and Windows Boot Manager / kernel progress. It also reports USB as incomplete and a Windows early-userspace reset. These are maintainer-reported project results, not independently reproduced by this repository.

Important: upstream's own `BUILD.md` and README have different/stale descriptions of storage and OS support. The current status must be checked against the pinned source and its detailed status log before treating any feature as complete.

## Licensing and source handling

The GitHub repository metadata did not declare a license, and no `LICENSE` file was verified in the reviewed root. Therefore this repository does not vendor, mirror, or copy its implementation files. Ask the upstream maintainer to clarify licensing before redistributing or adapting source.

The upstream tree includes a PIT partition-table file and scripts/documentation related to device installation. They are deliberately not copied or invoked here. This repository will not generate partition layouts, flash packages, or commands that write to a handset.

## Android 16 relevance

Android 16 / Evolution X is the user's current operating-system environment. It does not change the Exynos 9820 UEFI platform identity, and it does not establish the device's Samsung bootloader revision or stock firmware build. The Android ROM can matter later for collecting read-only device facts and kernel/device-tree comparisons, but it is not a substitute for boot-chain evidence.

## Next engineering milestones

1. Confirm upstream licensing and pin all Mu-Silicium and submodule revisions used by the chosen upstream build.
2. Reproduce the source build in an isolated host environment, without connecting a phone or producing a flash package.
3. Run static checks and record toolchain versions and artifact hashes.
4. Compare the resulting source configuration with the exact SM-G975F board data; keep unverified memory and register assumptions clearly marked.
5. Treat hardware boot, OS handoff, and device drivers as separate milestones requiring independent evidence.

## Validation script

Run `python3 scripts/verify_upstream.py /path/to/beyond2lte-uefi` after obtaining the upstream source separately. The script checks repository identity, exact commit pin, and a small set of expected source files. It does not download code, build firmware, or communicate with a phone.
