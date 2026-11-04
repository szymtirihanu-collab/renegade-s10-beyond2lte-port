# Research references

These links are starting points for source review. They do not establish that a Renegade/UEFI port already works on beyond2lte.

## Renegade Project

- [Renegade Project FAQ](https://renegade-project.tech/en/faq) — describes the project as an EDK2 UEFI environment targeting Qualcomm Snapdragon devices and links to its device support information.
- [Renegade Project porting guide](https://renegade-doc.readthedocs.io/en/latest/edk2/port.html) — historical Qualcomm-oriented porting workflow.
- [EDK2-SDM845 repository](https://github.com/edk2-porting/edk2-sdm845) — Qualcomm Snapdragon 845 implementation; not an Exynos base port.

## Galaxy S10+ / Exynos 9820

- [LineageOS device information: beyond2lte](https://lineageos.github.io/lineage_wiki/devices/beyond2lte/) — device codename, supported model identifiers, SoC and hardware overview.
- [LineageOS Exynos 9820 kernel source](https://github.com/ExtremeXT/android_kernel_samsung_exynos9820) — kernel source useful for identifying hardware blocks and existing initialization.
- [Exynos 9820 device tree sources](https://github.com/ExtremeXT/android_device_samsung_exynos9820) — recovery/device configuration reference; not an EDK2 platform package.
- [exynos-linux project](https://exynos-linux.github.io/) — community mainline Linux work and porting methodology for Samsung Exynos devices.
- [exynos-linux porting guide](https://exynos-linux.github.io/port) — explains the work expected for a new Exynos Linux device port.

## Source-handling rules

- Prefer primary source repositories and vendor documentation over copied snippets.
- Record exact commit hashes for any source used in a build.
- Respect each source repository's license and attribution requirements.
- Never infer physical addresses, register layouts, partition offsets or boot arguments from a different SoC or device.
- Mark every hardware claim as verified, inferred, or unknown.
