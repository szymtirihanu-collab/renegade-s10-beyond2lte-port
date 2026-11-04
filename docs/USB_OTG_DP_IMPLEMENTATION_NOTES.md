# Exynos 9820 USB OTG and DisplayPort implementation notes

Last reviewed: 2026-11-04

## Evidence source

The pinned beyond2lte source includes the Samsung device-tree overlay
`dtb-analiz/beyond2lte-rev17.dts` at commit
`f122c7024c5eeef2c8c78dfd08c62708c9ef823d`. The entries below are literal
properties from that overlay. This file is a decompiled/overlay-style DTS;
its `target = <0xffffffff>` placeholders and external phandle references must
be resolved against the matching base device tree before any register mapping
or firmware initialization is attempted.

## USB device/controller configuration

The overlay's `fragment@69` sets:

- `dr_mode = "otg"`
- `maximum-speed = "super-speed-plus"`
- Synopsys DWC3 tuning/quirk properties, including frame-length adjustment,
  U1/U2 exit, elastic buffer, LPM and SOF-accuracy settings.

The overlay's `fragment@70` enables a PHY-related node, selects a pinctrl
state, and supplies GPIO/HS/SS tuning references.

This is strong evidence that the Android device tree configures a DWC3
USB-DRD controller and an associated PHY path. It does **not** by itself
establish the controller's physical MMIO base, interrupt, clock IDs, reset
IDs, regulator dependencies, Type-C role-switch implementation, or whether
the existing UEFI has initialized any of them.

## OTG implementation sequence

1. Recover the exact base DTB and resolve the controller/PHY phandles and
   address/interrupt/clock/reset resources.
2. Map the SoC integration: DWC3 core, Exynos wrapper/glue, USB2 PHY, USB3
   PHY, PMU/sysreg, Type-C MUIC/role switch, VBUS supply and pinctrl.
3. Identify the correct host role and safe power sequencing from source and
   hardware documentation; do not assume that setting DWC3 host mode alone
   powers VBUS or configures the Type-C port.
4. Decide whether the Exynos integration can expose a standards-compliant
   xHCI controller to the EDK2 xHCI driver through a non-discoverable-device
   registration path. Confirm register layout, DMA addressability, cache
   coherency, interrupt routing and reset semantics first.
5. Only then add a platform DXE driver to initialize glue/PHY/role and publish
   the host controller. Reuse EDK2 USB bus and HID keyboard/mouse drivers.
6. Add ACPI description only after the controller is stable and resources are
   known. Windows needs a correct ACPI device/resource description; an EDK2
   driver alone does not make Windows enumerate USB.

## DisplayPort Alt Mode

The overlay's `fragment@111` configures a pinctrl state named `dp_hpd` on
Samsung pin `gpa2-7`. Its `fragment@112` enables a DisplayPort-related node
and supplies `dp,aux_sw_oe`, `dp,sbu_sw_sel`, and `dp,usb_con_sel`
switch-control properties.

This confirms that the Android device tree contains a DP path and board
routing controls. It does not provide enough information to initialize
DisplayPort from UEFI: the Type-C controller/PD policy, lane mux, AUX/HPD
handling, PHY clocks/resets/rails, link training and EDID/GOP integration
still need to be traced.

## Internal panel versus external display

The currently reported 1440x3040 simple framebuffer is a boot-chain-provided
display path. Preserve it first. This is distinct from implementing the
Exynos display controller or a Windows Mali graphics driver. External
DisplayPort Alt Mode is a separate later milestone.

## Safety and validation boundary

This work is source analysis and host-side firmware development only. No
partition map, PIT, bootloader, flashing, or device-write procedure belongs
in the build workflow. A successful host compile is not proof of hardware
operation. Track evidence separately as source-audited, host-built, and
device-validated.
