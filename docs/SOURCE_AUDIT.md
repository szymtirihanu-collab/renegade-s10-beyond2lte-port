# Existing UEFI source audit

Last reviewed: 2026-11-04

## Candidate codebase

The most directly relevant public implementation found is [orhunnx/beyond2lte-uefi](https://github.com/orhunnx/beyond2lte-uefi). Its README says it is an overlay for [Project Silicium / Mu-Silicium](https://github.com/Project-Silicium/Mu-Silicium), not a direct fork of official Renegade firmware.

The candidate's documentation identifies these source areas:

- `mu-silicium-overlay/Platforms/Samsung/beyond2ltePkg/`: board package and platform descriptions.
- `mu-silicium-overlay/Silicon/Samsung/S5E9820Pkg/`: Exynos 9820 silicon support.
- `mu-silicium-overlay/Resources/Configs/beyond2lte.toml`: platform build configuration.
- `mu-silicium-overlay/Resources/DTBs/beyond2lte.dtb`: device tree used by the build.
- `silicium-acpi-overlay/SoCs/Samsung/S5E9820/`: ACPI source material.

This is a source-audit map based on the upstream repository's documentation. The files have not yet been imported into this repository.

## Hardware and firmware details reported upstream

The candidate's `HARDWARE.md` says its device tree was derived from a stock SM-G975F firmware package and describes an Exynos 9820 board. It reports register mappings cross-checked against the device tree, a framebuffer handoff rather than a fresh panel initialization, and an Exynos-specific UFS implementation.

The same document reports board-revision-specific information and a particular firmware baseline. Those details must **not** be assumed to match every SM-G975F handset. The owner's model confirmation establishes SM-G975F only; it does not establish board revision, installed firmware, memory SKU, region, or bootloader state.

## Build reproducibility review

The candidate's `BUILD.md` documents a Mu-Silicium build using recursive submodules and a local overlay. This is useful as a lead for a reproducible, host-only build. Before adopting it, record exact commit hashes for:

1. The candidate overlay repository.
2. Mu-Silicium and every submodule.
3. Toolchain and Python dependencies.
4. Any generated DTB and ACPI inputs, including their source provenance.

Do not rely on a moving default branch for a reproducible build. The local overlay should be reviewed as a patch series against pinned upstream sources.

## What is not established here

- This repository has not cloned or built the candidate source.
- No output firmware image has been produced here.
- No device has been tested by this project.
- Upstream status tables are maintainer-reported claims, not independent verification.
- A successful UEFI build does not imply Windows or Linux hardware support.
- The candidate's Windows notes describe unresolved early-boot/reset problems; they do not establish a usable Windows port.

## Next engineering milestone

The next safe milestone is a **host-only source audit and reproducible build**. Compare the candidate's actual platform package with upstream Mu-Silicium, inspect licensing, pin every dependency, and run the documented static/build checks without connecting or modifying the phone.

Do not import opaque binaries or copy code without checking its license and provenance. Do not treat Android recovery trees as UEFI platform packages.

## References

- [Candidate UEFI project](https://github.com/orhunnx/beyond2lte-uefi)
- [Candidate hardware notes](https://github.com/orhunnx/beyond2lte-uefi/blob/master/HARDWARE.md)
- [Candidate build notes](https://github.com/orhunnx/beyond2lte-uefi/blob/master/BUILD.md)
- [Project Silicium / Mu-Silicium](https://github.com/Project-Silicium/Mu-Silicium)
- [Exynos 9820 device tree](https://github.com/ExtremeXT/android_device_samsung_exynos9820)
- [Exynos 9820 kernel source](https://github.com/ExtremeXT/android_kernel_samsung_exynos9820)
