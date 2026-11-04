# Porting status

Last reviewed: 2026-11-04

## Summary

This is a research-stage feasibility project. No firmware has been built or tested on a Galaxy S10+. No device-specific EDK2 package exists here yet.

| Area | Status | Evidence needed |
|---|---|---|
| Device identity | Documented | Confirm exact handset model |
| CPU/SoC | Documented from public device references | Samsung Exynos 9820 technical documentation |
| EDK2 platform package | Not started | Platform specification and upstream code review |
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

1. Confirm the exact model identifier (for example, SM-G975F) and region variant.
2. Review Samsung's public Exynos 9820 kernel source and device tree for hardware topology.
3. Identify the earliest boot stage that can be observed without modifying partitions.
4. Establish whether a third-party UEFI payload can be launched through a documented, supported path. Do not assume the Qualcomm Renegade chain applies.
5. Build a minimal EDK2 AArch64 host/toolchain environment independently of device boot.
6. Only after the boot hand-off is understood, define the platform package and implement initialization in small, reviewable steps.

## Acceptance gates

A milestone is complete only when its evidence is checked into the repository:

- **Buildable:** clean build from documented source revisions and pinned tools.
- **Bootable:** repeatable UEFI entry on the exact handset model, with captured logs.
- **Useful UEFI:** stable console, memory map and device enumeration.
- **OS-capable:** a separately validated OS loader and required drivers.

A successful cross-compile is not evidence of a working phone port.
