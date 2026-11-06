# Windows 11 ARM64 target plan — SM-G975F

Last reviewed: 2026-11-04

## Target and scope

- Device: Samsung Galaxy S10+ international Exynos model, SM-G975F (`beyond2lte`).
- SoC: Samsung Exynos 9820, AArch64.
- User-reported Android environment: Android 16 / Evolution X.
- Primary OS experiment: Windows 11 ARM64.
- Firmware basis: the existing [beyond2lte UEFI implementation](https://github.com/orhunnx/beyond2lte-uefi), not Qualcomm Renegade board code.

This is an experimental community port, not a Microsoft-supported Windows 11 PC. The S10+ is a phone with a 6.4-inch display; Microsoft's published Windows 11 minimum requirements specify a display greater than 9 inches except for desktop PCs, and also specify UEFI, Secure Boot and TPM 2.0. This device has not been demonstrated to meet the Windows 11 platform requirements. Do not describe it as supported or recommend bypassing requirements.

## Upstream-reported Windows progress

At the pinned upstream revision in `UPSTREAM.lock.json`, the upstream README reports:

- Windows Boot Manager starts, draws to the display, and reads the EFI System Partition.
- The Windows kernel (`ntoskrnl`) starts.
- Early Windows user mode is not stable; upstream reports a reset after roughly 12 seconds and no reliable diagnostic channel.
- USB is reported as not working.

The upstream project also contains extensive Windows/ACPI investigation notes. These are upstream maintainer reports, not results independently reproduced by this repository. The README's top-level status and detailed notes are not fully synchronized; re-check the exact pinned revision before treating individual milestones as current.

## Windows boot requirements to validate

Windows on Arm needs more than an EFI executable launch:

1. **UEFI contract:** correct EFI System Table, Boot Services, memory map, runtime services behavior, and clean `ExitBootServices()` handoff.
2. **ACPI:** valid RSDP/XSDT and platform tables, including CPU topology, interrupt controller, timers, PSCI description, and devices. Microsoft documents Windows-specific UEFI and ACPI requirements; Linux ACPI documentation is useful for cross-checking the Arm model but is not a substitute for Windows requirements.
3. **Boot-critical storage:** the Windows boot environment must read its boot files through a supported Arm64 storage driver. A driver merely being present in an image does not prove the controller survives handoff.
4. **CPU and SMP:** stable boot CPU feature reporting and secondary CPU startup using the platform's actual PSCI conduit.
5. **Diagnostics:** a working, documented debug channel is necessary to distinguish a kernel failure from an early-userspace failure.
6. **Device drivers:** Windows requires drivers built for Arm64 and compatible with the actual hardware. A working framebuffer in UEFI does not provide a Windows GPU driver.

## Current evidence matrix

| Milestone | Evidence | Status in this repository |
|---|---|---|
| UEFI entry | Upstream README reports UEFI boot | Not independently reproduced |
| Display during UEFI | Upstream reports 1440×3040 display | Not independently reproduced |
| UFS Block I/O | Upstream README reports five LUNs and Block I/O | Not independently reproduced |
| ACPI tables | Upstream reports ACPI validation and Linux ACPI boot | Not independently reproduced |
| Windows Boot Manager | Upstream reports it launches and draws | Not independently reproduced |
| Windows kernel | Upstream reports `ntoskrnl` starts | Not independently reproduced |
| Windows 11 early userspace | Upstream reports reset after about 12 seconds | Known upstream blocker |
| USB | Upstream reports unavailable | Blocker for normal interactive setup |
| Windows hardware drivers | No complete driver set demonstrated | Not complete |
| Windows 11 requirements | Device not shown to meet requirements | Unsupported experiment |

## Work sequence

The current host-build ACPI integration and its validation limits are documented in [ACPI_BUILD_INTEGRATION.md](ACPI_BUILD_INTEGRATION.md). The firmware build must compile and embed the Exynos tables; merely copying their source files is insufficient. A separate source-level review found an APIC OEM Table ID mismatch between the decoded header and raw table bytes, and confirmed that the current MADT/DSDT processor declarations expose only CPU0; see [ACPI_STATIC_REVIEW.md](ACPI_STATIC_REVIEW.md). These findings remain unresolved and prevent any claim of validated eight-core support.

The upstream Windows UFS miniport has been reviewed at source level; see [UFS_DRIVER_SOURCE_REVIEW.md](UFS_DRIVER_SOURCE_REVIEW.md). It is write-capable, depends on firmware-initialized UFS state, requires a Windows MSVC/WDK build environment, and has unresolved licensing terms. It has not been integrated or independently built.

### Stage 1 — source provenance and reproducibility

- Resolve the upstream repository's licensing status before copying or adapting source.
- Pin Mu-Silicium and all submodules to exact commits.
- Reproduce a clean host-only build from the pinned source.
- Record build environment, compiler/tool versions, source hashes and build logs.
- Do not create or publish a device-installable image until the build is independently reviewed.

### Stage 2 — boot-contract validation

- Audit the UEFI memory map and handoff behavior.
- Audit ACPI tables against Microsoft's Arm UEFI requirements and applicable ACPI specifications.
- Cross-check CPU topology, PSCI, GIC and timer descriptions against the actual Exynos platform sources.
- Keep upstream claims separate from tests performed by this repository.

### Stage 3 — diagnose the Windows reset

- Establish a supported diagnostic path before attempting to infer the cause.
- Review the exact upstream logs and code for the pinned revision.
- Track one hypothesis per test and record observable evidence.
- Do not treat a Windows Boot Manager screen or kernel entry as a successful Windows boot.

### Stage 4 — device support

- Inventory which devices have usable Windows ARM64 drivers and which do not.
- Treat storage, display/GPU, touch/input, USB, networking, audio, battery/power and thermal management as separate driver work.
- Do not claim general usability until the necessary drivers and power/thermal behavior are validated.

## Official references

- [Microsoft: UEFI requirements that apply to all Windows platforms](https://learn.microsoft.com/en-us/windows-hardware/drivers/bringup/uefi-requirements-that-apply-to-all-windows-platforms)
- [Microsoft: Windows on Arm device manufacturing](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/arm64-device-manufacturing?view=windows-11)
- [Microsoft: Windows 11 minimum hardware requirements](https://download.microsoft.com/download/7/8/8/788bf5ab-0751-4928-a22c-dffdc23c27f2/Minimum%20Hardware%20Requirements%20for%20Windows%2011.pdf)
- [Microsoft: Windows 11 Arm64 download page](https://www.microsoft.com/en-us/software-download/windows11arm64)
- [Linux kernel: ACPI on Arm systems](https://www.kernel.org/doc/html/latest/arch/arm64/arm-acpi.html)

## Safety and integrity boundary

This repository does not provide partition-writing, firmware-flashing, bootloader-unlocking, or Windows installation instructions. Current work is limited to source review, documentation, and host-side reproducibility. Any future hardware experiment requires an independently reviewed, model-specific plan and appropriate recovery support.
