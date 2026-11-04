# Porting status

Last reviewed: 2026-11-04

## Summary

The target is the **Samsung Galaxy S10+ SM-G975F (`beyond2lte`)**, Exynos 9820, AArch64. The user reports Android 16 / Evolution X. An existing device-specific UEFI implementation has been identified and pinned; this repository is a downstream integration and reproducibility workspace.

**No firmware has been built or tested by this repository. No hardware boot has been independently verified here.**

| Area | Status | Evidence / next step |
|---|---|---|
| Device identity | Confirmed by owner: SM-G975F | Verify handset identity again before any device-specific test |
| SoC / architecture | Exynos 9820 / AArch64 | Public device references |
| Android environment | Android 16 / Evolution X, user-reported | Does not identify Samsung bootloader or stock firmware revision |
| Existing UEFI implementation | Identified and commit-pinned | `orhunnx/beyond2lte-uefi`, commit in `UPSTREAM.lock.json` |
| Upstream license / permission | No repository license; maintainer permission reported by owner | Permission is recorded in `docs/UPSTREAM_PERMISSION.md`; exact redistribution terms remain unconfirmed |
| USB hardware | Source-audited | DTB describes Exynos DWC3 OTG and USB2/USB3 PHYs |
| USB UEFI support | Not present in board DSC/FDF | No explicit DWC3/xHCI/USB host driver module; upstream says USB unavailable |
| External display hardware | Source-audited | DTB describes Exynos DisplayPort and connector mux properties |
| External display UEFI support | Not present in board DSC/FDF | No explicit DisplayPort DXE driver; no external output validated |
| Mu-Silicium base | Reference snapshot pinned | Exact main commit and six submodule gitlinks recorded; not proven to match upstream build |
| Mu-Silicium license | BSD-2-Clause metadata | Individual submodule license review remains necessary |
| Candidate host build | Workflow added; not yet run | Manual ARM64 build uses pinned upstream overlay and pinned Mu-Silicium snapshot; dependency snapshot may differ from maintainer's original build |
| Boot chain / handoff | Upstream implementation exists; independent validation absent | Review exact boot path and record evidence |
| DRAM / memory map | Upstream-specific assumptions; not independently confirmed | Compare with reliable sources; do not infer from Android version |
| Display / keys / UFS | Upstream reports support | Reproduce and distinguish reported status from independent validation |
| Linux / Windows handoff | Upstream reports partial progress and remaining issues | OS integration is separate from UEFI build |
| Hardware validation | Not performed by this repository | Requires dedicated test plan and recovery oversight |

## Completed in this repository

- Selected Windows 11 ARM64 as the primary OS experiment and documented Microsoft's platform requirements, upstream-reported progress, and remaining blockers.
- Confirmed exact target model and architecture.
- Identified the existing Exynos-specific UEFI project rather than attempting to reuse Qualcomm board code.
- Pinned the reviewed upstream commit in `UPSTREAM.lock.json`.
- Added read-only checkers for repository origin, commit identity, cleanliness, expected files, upstream metadata/tree, USB/display source markers, and the Mu-Silicium reference snapshot.
- Audited the pinned board DTS: Exynos DWC3, USB2/USB3 PHY, OTG role, Exynos DisplayPort, and connector mux properties are described.
- Audited the board DSC/FDF: no explicit USB/xHCI/DWC3 or DisplayPort DXE driver module is listed.
- Recorded a separate Mu-Silicium snapshot and exact submodule gitlinks; this is not claimed to be the device upstream's actual build base.
- Recorded the owner's report of maintainer permission; source remains fetched transiently at build time rather than mirrored.
- Added a manual ARM64 candidate host-build workflow and a temporary-workspace build script. It does not publish artifacts or interact with a handset.

## Next milestones

1. Run the manual ARM64 candidate host build and resolve any compile errors.
2. Ask the maintainer which exact Mu-Silicium commit and submodule set produced their reported working build.
3. Record the exact conditions of permission before publishing adapted source or distributing firmware binaries.
4. Review dependency license notices and add required attribution.
5. Audit the existing Exynos USB/PHY and Type-C implementation path before writing a DWC3 host driver.
6. Independently verify display, USB input, and OS handoff on hardware before making any device-support claim.

A source checkout check is not a build. A metadata/tree audit is not a full source-code audit. A build is not a successful device boot. A successful UEFI boot is not proof that Linux or Windows drivers are complete.


## Latest source-level I/O findings

- The pinned Samsung DTS overlay explicitly configures a Synopsys DWC3 USB-DRD node for OTG and SuperSpeed Plus, and configures a PHY-related node.
- The same overlay enables a DisplayPort node and configures HPD/AUX/SBU/USB connector routing controls.
- These are Android device-tree facts, not a completed UEFI implementation. Base-DTB phandle/resource resolution remains necessary before driver work.
- Detailed sequence: [USB OTG and DisplayPort implementation notes](USB_OTG_DP_IMPLEMENTATION_NOTES.md).
