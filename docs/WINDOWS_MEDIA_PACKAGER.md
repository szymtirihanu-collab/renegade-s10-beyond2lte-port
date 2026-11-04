# Windows 11 ARM64 media packager

The script `scripts/make_windows_arm64_media.py` extracts a Windows ARM64 ISO,
checks that its EFI boot application is AArch64, splits an oversized
`install.wim` into FAT32-compatible SWM parts, and creates a FAT32 filesystem
image containing the installation media.

## Default ISO

`~/Windows11_Client_arm64_en-us_26300_9457.iso`

## Requirements

Python 3, `xorriso`, and `mtools`. If the ISO has an `install.wim` larger
than 4 GiB, `wimlib-imagex` is also required.

## Run

```sh
python3 scripts/make_windows_arm64_media.py
```

Or pass the ISO explicitly:

```sh
python3 scripts/make_windows_arm64_media.py \
  --iso "$HOME/Windows11_Client_arm64_en-us_26300_9457.iso" \
  --output ./beyond2lte-windows11-media
```

An existing candidate UEFI image can optionally be copied into the output
folder with `--uefi-image /path/to/Mu-beyond2lte.img`.

Outputs:
- `windows11-arm64-esp.img`: FAT32 filesystem image containing Windows setup.
- `media-report.json`: source and output SHA-256 hashes and validation notes.
- `README.txt`: package scope.
- `Mu-beyond2lte.img`: optional copy if `--uefi-image` was supplied.

The tool refuses to overwrite an existing output folder unless `--force` is
specified. It never writes to a phone or modifies any disk or partition.

## Important limitation

This prepares Windows installation media, not a complete, proven handset boot
chain. The UEFI launcher and Windows ESP are separate artifacts. Exact
SM-G975F bootloader acceptance and handoff are not verified. The current
upstream port reports an early Windows reset. No Exynos-specific Windows
drivers or corrected ACPI tables are injected.

Microsoft notes that ARM64 installation media may require device-manufacturer
drivers: [Windows 11 Arm ISO overview](https://learn.microsoft.com/en-us/windows/arm/iso)
and [Windows on Arm manufacturing guidance](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/arm64-device-manufacturing?view=windows-11).

A successful media audit does not establish that Windows Setup or the installed
OS will boot on the Galaxy S10+.
