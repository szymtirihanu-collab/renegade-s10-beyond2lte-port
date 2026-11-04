# Renegade-style UEFI integration for Galaxy S10+ / beyond2lte

**Target: Samsung Galaxy S10+ SM-G975F, Exynos 9820, AArch64.** The user reports Android 16 / Evolution X as the current Android environment.

## Important project decision

A device-specific Exynos UEFI implementation already exists: [orhunnx/beyond2lte-uefi](https://github.com/orhunnx/beyond2lte-uefi). This repository is being developed as a downstream integration and reproducibility workspace around that existing implementation—not as a second independent EDK2 platform implementation.

The official Renegade Project's published EDK2 targets Qualcomm Snapdragon platforms. Its Qualcomm board code is not directly portable to this Exynos device. See [Renegade's FAQ](https://renegade-project.tech/en/faq) and [supported devices](https://renegade-project.tech/en/devices).

## Current status

- [x] Confirm target model: SM-G975F / `beyond2lte`
- [x] Identify existing Exynos 9820 UEFI implementation
- [x] Pin reviewed upstream commit in [UPSTREAM.lock.json](UPSTREAM.lock.json)
- [x] Add read-only source provenance checker
- [x] Document Android 16's relevance and limits
- [ ] Confirm upstream licensing before copying or adapting source
- [ ] Pin Mu-Silicium and every required submodule revision
- [ ] Reproduce a clean host-only build
- [ ] Record static validation and artifact hashes
- [ ] Independently validate hardware boot and OS handoff

See [upstream integration notes](docs/UPSTREAM_INTEGRATION.md), [model profile](docs/MODEL.md), [source audit](docs/SOURCE_AUDIT.md), and [porting status](docs/PORTING_STATUS.md).

## Safe scope

This repository currently contains documentation and read-only validation only. It does not contain a validated firmware image. It does not create partition tables, generate flash packages, or provide device-writing instructions. Do not treat a successful source check or host build as proof that firmware is safe or bootable on a handset.

## Verify a local upstream checkout

After obtaining the upstream source separately, run:

```sh
python3 scripts/verify_upstream.py /path/to/beyond2lte-uefi
```

This checks the remote URL, exact commit, clean working tree, and expected source files. It does not download, build, flash, or contact a device.
