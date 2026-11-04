# Architecture notes

## Renegade Project baseline

Renegade Project describes its EDK2 work as a UEFI environment for Qualcomm Snapdragon devices. Its published porting material relies on Qualcomm-specific firmware concepts and device packages. Those assumptions do not transfer to Exynos.

## Target platform

The international Galaxy S10+ (codename `beyond2lte`) is based on Samsung Exynos 9820 and uses AArch64-capable CPU cores. The platform includes Samsung-specific boot firmware, memory initialization, interrupt routing, clocks, power domains, storage and display integration.

The device codename alone is not a complete board description. Variants and panel/storage configurations must be identified before any hardware-specific configuration is written.

## EDK2 work breakdown

A real implementation would need, at minimum:

1. **Boot hand-off:** establish a legitimate, repeatable entry point and define register, exception-level and memory ownership contracts.
2. **Memory:** describe usable DRAM and reserved regions without overlapping secure firmware, modem, shared-memory or device-reserved ranges.
3. **CPU and exceptions:** establish the execution state, exception vectors and required architectural controls.
4. **Interrupts and time:** integrate the SoC's interrupt controller and a stable timer source.
5. **Console:** provide a documented early debug channel before relying on graphics.
6. **Platform devices:** add storage, USB and display support only after the core platform is stable.
7. **OS hand-off:** provide correct device description, memory map and boot services/runtime behavior for the selected OS.

These are engineering work areas, not claims that the hardware interfaces have already been identified.

## Why a Snapdragon binary is not a starting image

A Qualcomm firmware image contains platform-specific initialization and assumptions about the Qualcomm boot chain, SoC peripherals and memory layout. Exynos 9820 uses a different SoC and Samsung boot flow. Renaming a device folder, changing a screen resolution, or copying a Qualcomm DTB cannot create the missing Exynos platform support.

## Linux versus Windows

A Linux kernel port and a UEFI port solve different problems. Existing Exynos Linux device trees and drivers are useful evidence about hardware, but they are not automatically EDK2 drivers. Similarly, reaching a UEFI shell would not mean Windows ARM64 has drivers for the S10+ peripherals.
