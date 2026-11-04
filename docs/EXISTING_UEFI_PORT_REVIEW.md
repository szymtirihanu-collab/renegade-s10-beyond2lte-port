# Existing SM-G975F UEFI work: source review

Last reviewed: 2026-11-04

## Finding

A public project named [beyond2lte-uefi](https://github.com/orhunnx/beyond2lte-uefi) describes a Project Silicium / EDK2-based UEFI implementation for the Samsung Galaxy S10+ SM-G975F (Exynos 9820). Its README identifies the repository as an overlay on Mu-Silicium rather than a fork. A related [beyond2lte-ios](https://github.com/orhunnx/beyond2lte-ios) repository identifies this UEFI project as an external firmware dependency.

This is directly relevant to this port: it is a more specific starting point than a generic Qualcomm Renegade port or a blank EDK2 platform package.

## Claims in the upstream project documentation

The upstream README and STATUS document report the following:

| Area | Upstream-reported state | Review note |
|---|---|---|
| UEFI entry | Working | Self-reported in project documentation; not independently reproduced here |
| Display / framebuffer | Working | Self-reported |
| Physical side keys | Working | Self-reported |
| Exynos UFS | Five LUNs and Block I/O | Self-reported; read/write details need source and test-log audit |
| EFI Shell | Working | Self-reported |
| USB | Not working | Explicitly listed as incomplete |
| Linux | ACPI boot reaches initramfs on eight CPUs | Self-reported; not a complete Linux installation |
| Windows | Boot Manager graphics and early kernel progress reported | The documentation also reports unresolved reset/early-boot issues; this is not a usable Windows port |

These are upstream claims, not results produced by this repository. Do not describe them as independently verified until source review, reproducible build, and device logs are available.

## Important distinction from official Renegade

The existing project is based on **Project Silicium / Mu-Silicium**, not a direct port of Renegade's Qualcomm platform package. That is a sensible architectural basis for Exynos 9820, but it should be described accurately. This repository's goal is to investigate a Renegade-like UEFI outcome for the SM-G975F, not to claim that the official Qualcomm Renegade firmware already supports Exynos.

## Proposed direction

1. Audit the existing UEFI repository's source tree, build scripts, licenses, and pinned upstream revisions.
2. Determine whether its current target really matches the owner's SM-G975F hardware and firmware assumptions.
3. Reproduce a clean host build without connecting or modifying a phone.
4. Compare its board package, device-tree-derived data, ACPI tables, memory layout and UFS implementation with the available Exynos 9820 kernel/device-tree sources.
5. Only after those checks, decide whether this project should become a documented downstream overlay, a clean fork, or a set of upstream contributions.

## Safety and evidence boundary

This document intentionally contains no flashing procedure, partition-writing commands, or firmware image. The current repository remains a research scaffold. No claim is made that a binary has been built, installed, or booted by this project.

## Sources

- [beyond2lte-uefi README](https://github.com/orhunnx/beyond2lte-uefi)
- [beyond2lte-uefi status notes](https://github.com/orhunnx/beyond2lte-uefi/blob/master/STATUS.md)
- [beyond2lte-ios README](https://github.com/orhunnx/beyond2lte-ios)
- [Project Silicium](https://github.com/Project-Silicium/Mu-Silicium)
- [LineageOS device page for beyond2lte](https://lineageos.github.io/lineage_wiki/devices/beyond2lte/)
