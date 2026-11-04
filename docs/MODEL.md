# Target model: Samsung Galaxy S10+ SM-G975F

## Confirmed identity

The project target is the international Exynos model **SM-G975F**, codename **beyond2lte**.

| Property | Value |
|---|---|
| Commercial name | Samsung Galaxy S10+ |
| Model | SM-G975F |
| Device codename | beyond2lte |
| SoC | Samsung Exynos 9820 |
| CPU architecture | AArch64 |
| GPU | ARM Mali-G76 MP12 |
| Display | 3040 × 1440 |
| RAM configurations | 8 GB or 12 GB, depending on handset SKU |
| Kernel baseline in existing device references | Linux 4.14 |

References: [LineageOS device page](https://lineageos.github.io/lineage_wiki/devices/beyond2lte/), [Exynos 9820 device tree](https://github.com/ExtremeXT/android_device_samsung_exynos9820), and [Exynos 9820 kernel source](https://github.com/ExtremeXT/android_kernel_samsung_exynos9820).

## Variant boundaries

- SM-G975F is the target for this project.
- SM-G975F/DS is a dual-SIM sales variant in the same device family; do not assume every board/firmware detail without checking.
- SM-G975N is the Korean variant and uses the related `beyond2lteks` codename. It is not the target.
- S10e, S10, S10 5G and Note10 Exynos boards are not interchangeable with this target.

## Still unknown for this handset

The model number alone does not identify the installed bootloader revision, region/CSC, firmware build, bootloader lock state, partition layout, DRAM map, board revision, or which debug interfaces are available. These must remain unknown until supported evidence is collected.

## Scope warning

A device tree used to build Android recovery or an Android kernel is not an EDK2 platform package. It can help identify peripherals and board configuration, but it does not prove that UEFI can be entered or that those devices can be initialized outside Samsung's existing firmware and kernel environment.

No firmware image is provided by this document. No flashing or partition modification is part of the research stage.
