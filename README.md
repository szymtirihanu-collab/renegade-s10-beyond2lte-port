# Renegade-style UEFI integration for Galaxy S10+ / beyond2lte

**Target: Samsung Galaxy S10+ SM-G975F, Exynos 9820, AArch64.** The user reports Android 16 / Evolution X as the current Android environment.

## Important project decision

A device-specific Exynos UEFI implementation already exists: [orhunnx/beyond2lte-uefi](https://github.com/orhunnx/beyond2lte-uefi). This repository is being developed as a downstream integration and reproducibility workspace around that existing implementation—not as a second independent EDK2 platform implementation.

The official Renegade Project's published EDK2 targets Qualcomm Snapdragon platforms. Its Qualcomm board code is not directly portable to this Exynos device. See [Renegade's FAQ](https://renegade-project.tech/en/faq) and [supported devices](https://renegade-project.tech/en/devices).

## Windows 11 ARM64 target

Windows 11 ARM64 is now the primary OS experiment for this port. The existing UEFI upstream reports Windows Boot Manager and kernel entry, but also an early-userspace reset; these claims have not been independently reproduced here. The S10+ is not a Microsoft-supported Windows 11 PC, and its hardware has not been shown to meet the published requirements. See [WINDOWS11_ARM64_PLAN.md](docs/WINDOWS11_ARM64_PLAN.md) for the requirements, evidence matrix, and work sequence.

## Current status

- [x] Confirm target model: SM-G975F / `beyond2lte`
- [x] Identify existing Exynos 9820 UEFI implementation
- [x] Pin reviewed upstream commit in [UPSTREAM.lock.json](UPSTREAM.lock.json)
- [x] Add read-only source provenance checker
- [x] Add hosted ARM64 metadata, USB, and display source-audit workflow
- [x] Pin a separate Mu-Silicium reference snapshot and all six submodule gitlinks
- [x] Document Android 16's relevance and limits
- [x] Select Windows 11 ARM64 as the primary OS experiment
- [x] Document Windows boot requirements and upstream-reported blockers
- [x] Record maintainer permission report for transient source use; exact redistribution terms remain open
- [ ] Confirm which Mu-Silicium revision the beyond2lte maintainer actually used
- [ ] Complete the candidate ARM64 host-only build
- [ ] Record static validation and artifact hashes
- [ ] Independently validate hardware boot and OS handoff

See the [Samsung S-Boot → BootShim handoff audit](docs/BOOT_HANDOFF_AUDIT.md), including revision-limited upstream S-Boot disassembly evidence. Also see [upstream integration notes](docs/UPSTREAM_INTEGRATION.md), [permission record](docs/UPSTREAM_PERMISSION.md), [model profile](docs/MODEL.md), [USB/display source audit](docs/USB_DISPLAY_SOURCE_AUDIT.md), [DWC3 host-driver design](docs/USB_DWC3_DRIVER_DESIGN.md), [Mu-Silicium dependency snapshot](docs/MU_SILICIUM_DEPENDENCIES.md), [cloud CI boundary](docs/CLOUD_CI.md), and [porting status](docs/PORTING_STATUS.md).

## Windows ARM64 installation-media packager

A host-side media packager is available at [`scripts/make_windows_arm64_media.py`](scripts/make_windows_arm64_media.py). The AIO builder [`scripts/build_windows11_beyond2lte_aio.py`](scripts/build_windows11_beyond2lte_aio.py) combines the Windows ARM64 ISO, an existing `Mu-beyond2lte.img` candidate, and a GPT disk image containing a FAT32 EFI System Partition. See [`docs/WINDOWS_MEDIA_PACKAGER.md`](docs/WINDOWS_MEDIA_PACKAGER.md) and [`docs/WINDOWS_AIO_BUNDLE.md`](docs/WINDOWS_AIO_BUNDLE.md). This is a host-side media bundle, not a complete phone storage layout or proven handset boot chain.

## Safe scope

This repository contains documentation, source-audit scripts, and a manual host-build workflow. The candidate build runs in a temporary GitHub runner and does not publish its image. No validated firmware image is provided. The project can create a GPT partition table inside a host-side Windows installation-media image. It does not repartition the phone, generate a device flash package, or provide device-writing instructions. A successful host build is not proof that firmware is safe or bootable on a handset.

## Verify a local upstream checkout

After obtaining the upstream source separately, run:

```sh
python3 scripts/verify_upstream.py /path/to/beyond2lte-uefi
```

This checks the remote URL, exact commit, clean working tree, and expected source files. It does not download, build, flash, or contact a device.
