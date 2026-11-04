# Porting status

Last reviewed: 2026-11-04

## Summary

This is a research-stage feasibility project for the **Samsung Galaxy S10+ SM-G975F (beyond2lte)**. The owner has confirmed the model. No firmware has been built or tested on a Galaxy S10+. No device-specific EDK2 package exists here yet.

| Area | Status | Evidence needed |
|---|---|---|
| Device identity | Confirmed: SM-G975F | Verify against the handset's own model information before any future device-specific test |
| CPU/SoC | Documented from public device references | Samsung Exynos 9820 technical documentation |
| Existing SM-G975F UEFI candidate | Identified; source audit started | Review actual source tree, license, pinned revisions, and reproduce a host build |
| Boot entry / hand-off | Unknown | Verified Samsung boot firmware behavior and supported boot method |
| DRAM map | Unknown | Reliable boot-time memory map from the target |
| GIC / timer | Unknown | Exynos 9820 integration documentation and kernel sources |
| UART / early console | Unknown | Board-specific pinout and safe debug access |
| Display | Not started | Panel and display-controller initialization details |
| UFS / SD | Not started | Controller and firmware interface documentation |
| USB | Not started | PHY/controller integration details |
| Windows ARM64 | Not evaluated | Requires stable UEFI and suitable device drivers |
| Hardware validation | Not started | Dedicated test device and recovery plan |

## Immediate research tasks

1. Audit the existing [SM-G975F UEFI candidate](EXISTING_UEFI_PORT_REVIEW.md) and its [source/build notes](SOURCE_AUDIT.md); pin all repositories and submodules to exact commits.
2. Check the candidate's source licensing and compare its platform overlay with the matching Mu-Silicium upstream revision.
3. Reproduce a clean host-only build and static checks without connecting to or modifying a handset.
4. Record the handset's firmware build and bootloader state from normal device information screens; do not infer these from the model number.
5. Compare the candidate's hardware assumptions with public Exynos 9820 kernel/device-tree sources. Treat board revision and memory details as unknown until confirmed.
6. Only after source provenance and build reproducibility are established, decide whether this repository should be a downstream overlay, fork, or patch series.

## Acceptance gates

A milestone is complete only when its evidence is checked into the repository:

- **Buildable:** clean build from documented source revisions and pinned tools.
- **Bootable:** repeatable UEFI entry on the exact handset model, with captured logs.
- **Useful UEFI:** stable console, memory map and device enumeration.
- **OS-capable:** a separately validated OS loader and required drivers.

A successful cross-compile is not evidence of a working phone port.
