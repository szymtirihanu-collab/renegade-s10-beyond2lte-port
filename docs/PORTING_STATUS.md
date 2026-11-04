# Porting status

Last reviewed: 2026-11-04

## Summary

The target is the **Samsung Galaxy S10+ SM-G975F (`beyond2lte`)**, Exynos 9820, AArch64. The user reports Android 16 / Evolution X. An existing device-specific UEFI implementation has been identified and pinned; this repository is a downstream integration and reproducibility workspace.

**A host-only candidate firmware build has succeeded (run 41887574178, commit 3f426bf). The current artifact ZIP, Android boot-image-v1 wrapper, embedded FD, FDT bounds and reset-vector-to-SEC-TE linkage have been independently inspected. No firmware has been tested on the handset, and no hardware boot has been independently verified here.**

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
| Candidate host build | Run 41887574178 succeeded; artifact uploaded | ARM64 CI build from pinned overlay/reference snapshot; dependency snapshot may differ from maintainer's original build. Package and reset-vector audits pass; no hardware boot proof. |
| Boot chain / handoff | Reset vector exactly matches SEC TE entry; SEC source requires EL1/EL2 | Exact handset bootloader entry level remains unknown; EL3 would loop. Verify boot-chain acceptance and recovery before any device test |
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
- Added a reproducible ARM64 candidate host-build workflow and temporary-workspace build script. Build #8 succeeded and published a short-lived CI artifact; no handset was connected or modified.\n- Inspected the candidate Android boot-image container and verified the embedded FD/FDT offsets, FD size/hash, and FD/stack placement in the active overlay.\n- Added `scripts/audit_firmware_entry.py`; it confirms the FD reset-vector branch target exactly matches the AArch64 SEC TE image entry point and that the TE image base matches `0xC9000000`. The same check is now part of the candidate build workflow.\n- Traced SEC startup: the Exynos 9820 `PlatformAssemblyInitialize()` is a no-op; the startup macro accepts EL1/EL2 and deliberately loops at EL3. The user's exact bootloader entry level is not known.\n- Confirmed the appended DTB is not currently shown being consumed by UEFI: SEC startup reuses x0, and the platform FDF's Device Tree driver/blob are disabled.

## Next milestones

1. Run the manual ARM64 candidate host build and resolve any compile errors.
2. Ask the maintainer which exact Mu-Silicium commit and submodule set produced their reported working build.
3. Record the exact conditions of permission before publishing adapted source or distributing firmware binaries.
4. Review dependency license notices and add required attribution.
5. Audit the existing Exynos USB/PHY and Type-C implementation path before writing a DWC3 host driver.
6. Independently verify display, USB input, and OS handoff on hardware before making any device-support claim.

A source checkout check is not a build. A metadata/tree audit is not a full source-code audit. A host build and a static entry-point audit are not a successful device boot. A successful UEFI boot is not proof that Linux or Windows drivers are complete.


## UFS write-path correction

The pinned upstream `STATUS.md` now resolves the apparent `LUN 2 / LBA 0` failure: `map -r` showed GPT partitions on LUN 0 and LUN 3, while LUN 2 has no GPT partition and is a protected Samsung boot LU. `bootmgfw` attempts a write there, the device rejects it, and boot continues. This is expected protection behavior, not a failed write to the Windows ESP or ordinary data LU. Normal nonzero-LBA writes and FAT metadata updates are recorded as successful. The remaining driver correction is accurate `BlockIo.Media.ReadOnly` reporting from the Unit Descriptor's `bLUWriteProtect` field. See [`UFS_WRITE_AUDIT.md`](UFS_WRITE_AUDIT.md). The reviewed patch is applied in the temporary host-build tree; CI compilation is pending.


A source-level audit of the pinned upstream DEBUG evidence is documented in [`UFS_WRITE_AUDIT.md`](UFS_WRITE_AUDIT.md). The earlier blanket DMA-cache-coherency diagnosis is not supported: an instrumented nonzero-LBA UFS write and FAT directory metadata update succeeded. A later Windows-triggered write to LUN 2, LBA 0 was rejected by the UFS target (`OCS=0x07`, SCSI response `0x01`). The failing LUN-to-partition mapping remains unresolved. Do not treat `Media.ReadOnly = FALSE` as proof that a LU is writable; upstream notes that this field is currently forced false rather than derived from the LU write-protect descriptor. No speculative cache patch or device-write test is authorized by this audit.

## Latest source-level I/O findings

- The pinned Samsung DTS overlay explicitly configures a Synopsys DWC3 USB-DRD node for OTG and SuperSpeed Plus, and configures a PHY-related node.
- The same overlay enables a DisplayPort node and configures HPD/AUX/SBU/USB connector routing controls.
- These are Android device-tree facts, not a completed UEFI implementation. Base-DTB phandle/resource resolution remains necessary before driver work.
- Detailed sequence: [USB OTG and DisplayPort implementation notes](USB_OTG_DP_IMPLEMENTATION_NOTES.md).
