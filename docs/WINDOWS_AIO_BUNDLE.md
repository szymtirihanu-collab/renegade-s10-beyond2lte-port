# beyond2lte Windows 11 ARM64 AIO bundle

The all-in-one host packager is `scripts/build_windows11_beyond2lte_aio.py`.
It uses the existing `scripts/make_windows_arm64_media.py` media builder,
then wraps the FAT32 setup filesystem in a GPT disk image with one EFI System
Partition. It also copies the source ISO and the separately-built
`Mu-beyond2lte.img` launcher into one output directory.

## Inputs

Default ISO:

```
~/Windows11_Client_arm64_en-us_26300_9457.iso
```

Required UEFI launcher: the `Mu-beyond2lte.img` artifact produced by the
pinned beyond2lte host build. The AIO script checks its Android boot-image
magic, but this check does not prove bootloader acceptance.

## openSUSE dependencies

Install Python 3, xorriso, mtools, and wimlib (needed if the ISO contains an
oversized install.wim):

```sh
sudo zypper install python3 xorriso mtools wimlib
```

## Build

From the repository root:

```sh
python3 scripts/build_windows11_beyond2lte_aio.py \
  --iso "$HOME/Windows11_Client_arm64_en-us_26300_9457.iso" \
  --uefi-image "$HOME/Mu-beyond2lte.img" \
  --output "$HOME/beyond2lte-windows11-aio"
```

The default ESP size is 16 GiB. Increase it with `--size-gib` if the
extracted installation media requires more space. Use `--force` only when
you intentionally want the existing output directory replaced.

## Output

- `<source ISO filename>`: copied Windows ARM64 source ISO.
- `Mu-beyond2lte.img`: candidate Samsung/Exynos UEFI launcher.
- `windows11-arm64-gpt-disk.img`: GPT disk image with one FAT32 EFI System
  Partition containing the Windows ARM64 setup files.
- `windows11-arm64-esp-fat32.img`: the standalone FAT32 filesystem image.
- `bundle-report.json`: hashes, GPT layout, validation, and limitations.
- `README.txt`: package scope.

The GPT disk image is installation media, not an internal UFS partition map.
The Android boot-image launcher and Windows setup disk are separate files;
the current UEFI source must still discover and boot the setup media correctly.

## Safety and validation boundary

This script is deliberately host-only. It does not call adb, fastboot,
heimdall, Odin, dd, or any phone-writing utility. It does not unlock the
bootloader, modify partitions, reboot the handset, or start installation.

The current project has a successful host build and a static reset-vector /
SEC entry-point audit, but no independent hardware boot. The exact
SM-G975F bootloader handoff and recovery path remain unverified. The upstream
port reports Windows Boot Manager progress but also an early Windows reset.
No Exynos Windows driver set or corrected ACPI platform description is
included by this packager.

A successful AIO build therefore means only that the Windows ARM64 setup
media and candidate UEFI launcher have been assembled and structurally
checked. It is not evidence that the phone can boot Windows Setup or install
Windows.

## Immediate QEMU media test (not a handset test)

Install the AArch64 QEMU system emulator and an AArch64 EDK2/AAVMF UEFI
firmware package from openSUSE. Package names vary by repository; locate the
firmware files with:

```sh
find /usr/share -type f \( -iname '*aarch64*code*.fd' -o -iname '*aarch64*vars*.fd' -o -iname 'AAVMF_CODE.fd' -o -iname 'AAVMF_VARS.fd' \) 2>/dev/null
```

After building the AIO bundle, run:

```sh
bash scripts/test_windows_arm64_qemu.sh "$HOME/beyond2lte-windows11-aio/windows11-arm64-gpt-disk.img"
```

If firmware files are stored elsewhere, set `UEFI_CODE` and `UEFI_VARS`
to their exact paths. This launches a generic QEMU ARM virtual machine. It
tests whether the generated Windows ARM64 setup media starts under generic
UEFI; it does not run the Samsung-specific `Mu-beyond2lte.img` and does not
validate the Exynos handset boot chain.
