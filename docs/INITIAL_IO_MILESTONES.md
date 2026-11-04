# Initial I/O milestones: panel / USB-C display / USB OTG

Last reviewed: 2026-11-04

Target: SM-G975F (beyond2lte), Exynos 9820, Windows 11 ARM64 experiment.

## User's first usable milestone

The first goal is deliberately narrow:

1. Get a visible display during UEFI and Windows boot, preferably the built-in panel first.
2. Investigate USB-C wired display output (DisplayPort Alt Mode) as an alternative or second output.
3. Get USB host / OTG working for a wired keyboard and mouse.

This is not a claim that the full Windows desktop, GPU acceleration, touch, sound, Wi-Fi, or battery management will work.

## What the evidence currently says

### Built-in panel: best first target

The existing `orhunnx/beyond2lte-uefi` upstream README and STATUS report a working 1440×3040 display using a simple framebuffer. Its hardware notes say the current implementation inherits the framebuffer established by the Samsung boot chain; it does not perform a complete native panel bring-up itself.

Implications:

- This is the lowest-scope first milestone because the existing UEFI display path is already reported working.
- The first validation target is that the framebuffer remains visible through the Windows loader and after `ExitBootServices()`.
- UEFI GOP/framebuffer output is not a Windows Mali-G76 graphics driver. Windows may need a separate display driver for continued native-resolution output and acceleration.
- The current upstream result is maintainer-reported and has not been reproduced by this repository.

### USB-C external display: hardware path is described, UEFI path is missing

The pinned upstream device-tree sources describe a Samsung Exynos DisplayPort controller and board-revision overlay properties for the DisplayPort SBU switch and USB connector selection.

This is stronger evidence than a generic phone specification, but it still does not prove UEFI output. The board's UEFI DSC/FDF does not list an explicit DisplayPort DXE driver, and this project has not validated external-monitor output.

Remaining areas include Type-C/PD negotiation, Alt Mode entry, lane routing, mux/PHY setup, clocks/resets/power, EDID discovery, and a UEFI graphics output implementation. These are separate from the existing internal framebuffer.

### USB OTG keyboard and mouse: hardware path exists, UEFI host driver is missing

The pinned device-tree sources describe:

- An Exynos USB dual-role controller with a Synopsys DWC3 child node.
- USB2 and USB3 PHY bindings.
- An OTG role in the beyond2lte revision overlay.

The upstream engineering notes explicitly say the current UEFI board configuration has no DWC3/xHCI/USB bus DXE driver. The README marks USB unavailable. This means the hardware is described for the Android/Linux stack, but the UEFI implementation does not yet provide the host-controller path needed for a wired keyboard or mouse.

Work areas remain:

- Review the controller/PHY and Type-C role dependencies from source evidence.
- Identify a suitable Exynos DWC3 host-controller implementation or determine what new UEFI integration is required.
- Integrate a host-controller driver with USB enumeration and HID input.
- Describe the controller and platform resources correctly to Windows through ACPI.

Mu-Silicium has generic EDK II USB bus and keyboard modules in other platform configurations, but the examples pair them with Qualcomm-specific xHCI components. Those components are not an Exynos driver and are not interchangeable.

### Windows driver boundary

A standards-compliant xHCI controller may be supported by a Windows inbox driver, but the platform must still expose correct ACPI resources and working clocks, PHY, power, and role configuration. The device-tree node is not a Windows ACPI description and does not guarantee Windows will bind a driver.

## Recommended order

| Priority | Milestone | Reason |
|---|---|---|
| P0 | Preserve and validate existing internal framebuffer | Already reported working; smallest scope |
| P1 | Review Exynos DWC3 / USB PHY / Type-C source integration | Hardware path is described; UEFI host driver is missing |
| P2 | UEFI USB host + HID keyboard/mouse | Gives input during boot and helps Windows setup |
| P3 | Windows ACPI description for USB host | Allows Windows to enumerate a supported host controller |
| P4 | USB-C DisplayPort Alt Mode | DTB describes the controller and mux properties, but UEFI output driver is missing |
| P5 | Windows display driver / graphics acceleration | Separate from UEFI framebuffer output |

## Cloud development

The repository now has a hosted ARM64 source-audit workflow. It checks the pinned upstream metadata, selected USB/display source markers, and a separately pinned Mu-Silicium reference snapshot. It does not build firmware yet because the beyond2lte overlay has no declared license.

See [USB/display source audit](USB_DISPLAY_SOURCE_AUDIT.md), [Mu-Silicium dependencies](MU_SILICIUM_DEPENDENCIES.md), and [cloud CI boundary](CLOUD_CI.md).

## Evidence rules

Label every feature as one of:
- **Upstream-reported:** described by the upstream maintainer.
- **Source-audited:** implementation and device description reviewed in source.
- **Host-validated:** built or checked on openSUSE or hosted CI without a handset.
- **Device-validated:** directly observed on an SM-G975F.

Do not upgrade a feature's status without the corresponding evidence.
