# Exynos DWC3 / xHCI integration design

Last reviewed: 2026-11-04

Target: SM-G975F / beyond2lte / Exynos 9820.

## Source facts

The pinned device upstream's decompiled Exynos 9820 base DTS describes:

- Exynos USB wrapper at MMIO `0x10C00000`, size `0x10000`.
- Child Synopsys DWC3 controller at the same base and extent.
- Two named PHY connections: USB2 and USB3.
- Wrapper clocks named `aclk` and `sclk`, plus a Samsung power-domain reference.
- A board revision overlay that selects `dr_mode = "otg"`, `maximum-speed = "super-speed-plus"`, and several DWC3 quirks.
- The PHY overlay enables the Exynos USB DRD PHY and board-specific GPIO/tuning properties.

These are device-tree source facts. They do not prove that the clocks, power domain, PHY, connector role, VBUS, or controller are initialized for UEFI.

## Reusable EDK II pieces

The pinned Mu-Silicium / Mu_Basecore snapshot contains:

- `MdeModulePkg/Bus/Pci/XhciDxe`: standard EDK II xHCI host-controller driver.
- `MdeModulePkg/Bus/Usb/UsbBusDxe`: USB enumeration and bus layer.
- `MdeModulePkg/Bus/Usb/UsbKbDxe`: USB keyboard input.
- `MdeModulePkg/Bus/Pci/NonDiscoverablePciDeviceDxe`: bridge that can expose a platform-described MMIO xHCI controller through `EFI_PCI_IO_PROTOCOL`.

The important integration constraint is that the stock `XhciDxe.inf` declares `gEfiPciIoProtocolGuid` as its controller protocol, and its register-access implementation performs MMIO reads/writes through `PciIo->Mem`. It cannot bind directly to a raw MMIO handle.

The Mu_Basecore NonDiscoverablePciDeviceDxe explicitly lists the non-discoverable XHCI device type and installs a synthetic PCI I/O protocol over a supplied MMIO resource. This gives us a candidate reuse path, but its DMA mapping, alignment, cacheability, and interrupt assumptions still need auditing for Exynos 9820.

## Proposed driver sequence

1. Add a board-specific `ExynosDwc3PlatformDxe` that owns only Exynos wrapper/PHY/role setup.
2. Obtain clocks, power domain, reset, and PHY state from validated board sources; do not invent register values or power sequencing.
3. Put the DWC3 core into host mode only after the USB-C/OTG role and VBUS source are known to be safe.
4. Register the DWC3 xHCI MMIO range through the NonDiscoverableDevice registration library and the supported XHCI device type.
5. Bind the existing xHCI, USB bus, and keyboard drivers; validate enumeration and UEFI keyboard input.
6. Describe the host controller and resources in ACPI for Windows, then test Windows inbox xHCI binding separately.

## Not a ready-made solution

A small `Dwc3DebugDxe` in a OnePlus 9 Pro Mu-Silicium experiment only paints the framebuffer and writes a marker; it is not a DWC3 host driver. Qualcomm-specific ABL USB host code is also not an Exynos driver and is not a substitute for the Samsung wrapper/PHY setup.

No Exynos DWC3 initialization code has been added yet. The first implementation should be a conservative diagnostic driver that validates read-only controller identity after the existing platform has established safe clocks and power. It should not change USB role, drive VBUS, or alter Type-C mux state until those controls are mapped and reviewed.

## Validation gates

- Confirm exact board revision / DTB provenance.
- Cross-check wrapper and PHY register layout against the Exynos 9820 kernel source.
- Audit the Mu_Basecore NonDiscoverablePciDeviceDxe DMA implementation and the xHCI driver assumptions.
- Compile and run static checks before any hardware test.
- Hardware testing requires a separate recovery-aware plan; this repository does not include phone flashing or partition-writing steps.
