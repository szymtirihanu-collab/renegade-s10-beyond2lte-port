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

### USB-C external display: second display path

The SM-G975F hardware supports wired video output over USB-C (DisplayPort/HDMI adapters) according to device specifications. For a UEFI implementation, this is not simply another framebuffer address.

Work areas to investigate from source and device-tree evidence:

- USB-C port controller and Type-C orientation / role state.
- USB Power Delivery negotiation and DisplayPort Alt Mode entry.
- DisplayPort lane assignment, mux / PHY setup, clocks, resets and power rails.
- External monitor EDID discovery and mode selection.
- A UEFI graphics output implementation for the external connector, plus a policy for internal and external displays.

The phone's stock Android/Samsung display stack supporting DeX or wired display does not prove that the UEFI port has the required Type-C, PD, mux, PHY, or DP driver code. Keep this as a separate milestone after the internal panel path is stable.

### USB OTG keyboard and mouse: critical input milestone

The upstream UEFI status currently marks USB as unavailable / no USB driver. OTG keyboard and mouse therefore require real USB host support; they will not work just because USB-C charging or data works in Android.

Work areas:

- Identify the exact Exynos USB controller instance(s) from the pinned board DTB and kernel sources.
- Determine the controller generation and whether it is xHCI-compatible.
- Implement or integrate the host-controller driver and USB bus enumeration.
- Handle Type-C host/device role selection, VBUS power, orientation and required PHY/clock/reset sequencing.
- Add USB HID keyboard and mouse drivers and expose keyboard input through the UEFI input protocol.
- Describe the controller and resources correctly to Windows through ACPI so Windows ARM64 can bind its inbox xHCI driver where compatible.

A Windows inbox xHCI driver can support a standards-compliant host controller, but firmware must still provide correct platform power, clocks, pinmux and ACPI resources. Microsoft documents the ACPI identifiers and resources Windows uses for USB host controllers. This is not proof that this particular Exynos USB block is already supported.

## Recommended order

| Priority | Milestone | Reason |
|---|---|---|
| P0 | Preserve and validate existing internal framebuffer | Already reported working; smallest scope |
| P1 | Read-only source audit of USB controller, Type-C/PD and PHY | Establish actual hardware topology before writing code |
| P2 | UEFI USB host + HID keyboard/mouse | Gives input during boot and helps Windows setup |
| P3 | Windows ACPI description for USB host | Allows Windows to enumerate a standard host controller |
| P4 | USB-C DisplayPort Alt Mode | Separate, more complex display path |
| P5 | Windows display driver / graphics acceleration | Separate from UEFI framebuffer output |

The user's wording allows either the internal panel or external display initially. The engineering plan starts with the internal panel because upstream already reports it working. USB OTG keyboard/mouse is the next high-value feature. External DP Alt Mode remains a distinct follow-on milestone.

## openSUSE host environment

The user has confirmed they are working on openSUSE. The next host-side phase is source review and a reproducible build environment.

Before selecting packages or writing distro-specific setup instructions, record the exact openSUSE release and architecture. Keep all initial work host-side: source checkout, dependency inventory, build, static checks, and artifact hashes. Do not connect a handset or perform device-writing operations as part of this phase.

## References

- [beyond2lte UEFI upstream README](https://github.com/orhunnx/beyond2lte-uefi)
- [beyond2lte UEFI upstream status](https://github.com/orhunnx/beyond2lte-uefi/blob/master/STATUS.md)
- [beyond2lte UEFI hardware notes](https://github.com/orhunnx/beyond2lte-uefi/blob/master/HARDWARE.md)
- [Microsoft: USB host controllers and devices in ACPI](https://learn.microsoft.com/en-us/windows-hardware/drivers/bringup/other-acpi-namespace-objects)
- [Microsoft: UEFI requirements for Windows platforms](https://learn.microsoft.com/en-us/windows-hardware/drivers/bringup/uefi-requirements-that-apply-to-all-windows-platforms)
- [Samsung Galaxy S10+ wired display and OTG specifications](https://www.notebookcheck.net/Samsung-Galaxy-S10-Smartphone-Review.410629.0.html)

## Evidence rules

Label every feature as one of:
- **Upstream-reported:** described by the upstream maintainer.
- **Source-audited:** implementation and device description reviewed in source.
- **Host-validated:** built or checked on openSUSE without a handset.
- **Device-validated:** directly observed on an SM-G975F.

Do not upgrade a feature's status without the corresponding evidence.
