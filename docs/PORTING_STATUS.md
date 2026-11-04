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
| Upstream license | Unclear / not declared | Obtain clarification before copying or adapting source |
| Upstream source tree | Metadata/tree audit added to hosted CI | No USB/Type-C/DP-named paths found at pinned revision; path-name audit only |
| Mu-Silicium revisions | Not yet pinned in this repository | Resolve every submodule to exact commit IDs |
| Host build | Not reproduced here | Licensing/provenance gate first; then isolated host-only build |
| Boot chain / handoff | Upstream implementation exists; independent validation absent | Review exact boot path and record evidence |
| DRAM / memory map | Upstream-specific assumptions; not independently confirmed | Compare with reliable sources; do not infer from Android version |
| Display / keys / UFS | Upstream reports support | Reproduce and distinguish reported status from independent validation |
| USB | Upstream reports incomplete; source tree has no USB-named driver path | Audit controller and Type-C support in source/device-tree evidence |
| Linux / Windows handoff | Upstream reports partial progress and remaining issues | OS integration is separate from UEFI build |
| Hardware validation | Not performed by this repository | Requires dedicated test plan and recovery oversight |

## Completed in this repository

- Selected Windows 11 ARM64 as the primary OS experiment and documented Microsoft's platform requirements, upstream-reported progress, and remaining blockers.
- Confirmed exact target model and architecture.
- Identified the existing Exynos-specific UEFI project rather than attempting to reuse Qualcomm board code.
- Pinned the reviewed upstream commit in `UPSTREAM.lock.json`.
- Added a read-only checker for repository origin, commit identity, cleanliness, and expected source files.
- Added a hosted ARM64 workflow that validates documentation and queries upstream repository/tree metadata without cloning or executing upstream code.
- Audited the pinned tree: no paths are named for USB, xHCI, EHCI, Type-C, or DisplayPort; this is a filename/path inventory, not proof that no generic USB support exists.
- Documented license uncertainty and excluded upstream partition/installation assets from this repository.

## Next milestones

1. Resolve upstream licensing and source provenance.
2. Pin Mu-Silicium and all submodule revisions used by the upstream platform build.
3. Reproduce a clean host-only build without a connected handset or device-writing steps.
4. Record toolchain versions, static-check results, and artifact hashes.
5. Independently verify device boot and OS handoff before making any bootability claim.

A source checkout check is not a build. A metadata/tree audit is not a source-code audit. A build is not a successful device boot. A successful UEFI boot is not proof that Linux or Windows drivers are complete.
