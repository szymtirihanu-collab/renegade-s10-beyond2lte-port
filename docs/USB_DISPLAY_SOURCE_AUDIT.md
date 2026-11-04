# USB and external-display source audit

Last reviewed: 2026-11-04

Target: SM-G975F / beyond2lte / Exynos 9820. All findings below are tied to the immutable UEFI source revision in `UPSTREAM.lock.json`.

## USB host / OTG

The upstream device-tree sources contain hardware descriptions for an Exynos USB dual-role controller:

- The base Exynos 9820 DTS identifies `samsung,exynos-dwusb` and a child `synopsys,dwc3` node.
- The DWC3 node references separate USB2 and USB3 PHYs.
- The beyond2lte revision overlay sets `dr_mode = "otg"` and enables the associated PHY overlay.
- Upstream's engineering notes identify the board's Type-C / OTG role-selection hardware.

This confirms that the Linux device tree describes an OTG-capable USB controller. It does **not** mean UEFI currently has a host-controller driver.

The same upstream engineering note explicitly says its board DSC/FDF has no DWC3, xHCI, USB bus, or USB mass-storage DXE driver. The board DSC/FDF audit in CI finds no explicit USB/xHCI/DWC3 driver INF entries. The upstream README also marks USB unavailable.

### What is missing for the requested keyboard and mouse

The firmware needs a supported host-controller path, USB enumeration, and HID input support. Windows also needs a correct ACPI description and platform resources for the host controller. A device-tree node alone is not a Windows ACPI description and does not bind a Windows driver.

Mu-Silicium contains generic EDK II USB bus and keyboard modules in other device configurations, but its platform examples pair them with Qualcomm-specific xHCI components. Those Qualcomm components are not evidence of an Exynos DWC3 host driver and must not be copied as if they were interchangeable.

**Conclusion:** OTG keyboard/mouse is a real hardware-backed target, but the missing Exynos UEFI host-controller integration is a substantial driver task. The current port cannot yet claim USB keyboard or mouse support.

## USB-C DisplayPort output

The base Exynos 9820 DTS identifies a Samsung Exynos DisplayPort controller. The beyond2lte revision overlay also contains DisplayPort SBU-switch and USB-connector selection properties.

This is useful evidence that the platform device tree describes a DisplayPort path and connector routing. It is not evidence that the UEFI implementation initializes the Type-C controller, enters DisplayPort Alt Mode, configures the mux/PHY, reads monitor EDID, or exposes an external display through GOP.

The board's current UEFI DSC/FDF does not list an explicit DisplayPort DXE driver. No external-monitor UEFI output has been validated by this project.

**Conclusion:** DP Alt Mode is a plausible later milestone, but it is not a quick substitute for the already-reported internal framebuffer. It requires its own firmware display/Type-C integration.

## Automated checks

The ARM64 hosted workflow runs:

- `scripts/audit_upstream_tree.py`: immutable upstream tree and license metadata.
- `scripts/audit_io_support.py`: selected device-tree and board DSC/FDF markers.

These are source audits only. They do not execute upstream code, compile firmware, or interact with a handset.

## Exact upstream files reviewed

- `dtb-analiz/exynos9820-base.dts`
- `dtb-analiz/beyond2lte-rev17.dts`
- `beyond2ltePkg/beyond2lte.dsc`
- `beyond2ltePkg/beyond2lte.fdf`
- `DEVIR.md`

The detailed source remains in the upstream repository; it is not copied into this repository because the upstream project has no declared license.
