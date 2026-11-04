# Candidate artifact packaging audit

Reviewed: 2026-11-04  
Candidate commit: `7546e37dae5f1010fba4617e2bd087febaca4b46`  
Build run: [Candidate beyond2lte host build #8](https://github.com/szymtirihanu-collab/renegade-s10-beyond2lte-port/actions/runs/41860771504)

## Scope

This is a static inspection of the CI-produced files and the pinned upstream packaging source. It is not a device test, a bootloader compatibility result, or permission to install the image.

## Artifact integrity

The uploaded ZIP was downloaded and inspected. Its SHA-256 is:

```
3deed8554ab5eb8601d9331191bf00642ce6886c2656eb1a869436b7d28bf585
```

It contains:

| File | Size | SHA-256 |
|---|---:|---|
| `SILICIUM_UEFI.fd` | 4,194,304 bytes | `6b01ceb07f339896b0172dafb398ad1b3b02ce6cac411085a06fc84efdba55f8` |
| `Mu-beyond2lte.img` | 4,575,232 bytes | `d6a6659c81918ea5de8e471167d519b2ae02b53fb3d283ff0230879487737c76` |

The firmware file has a 4 MiB UEFI Firmware Volume header with the `_FVH` signature and a declared volume length of 4 MiB. This verifies basic container structure only; it does not validate every PE/COFF image, relocation, entry point, or runtime dependency.

## Android boot-image container: expected packaging confirmed

The pinned Mu-Silicium `build_uefi.py` and beyond2lte TOML configuration explain the observed image:

- `boot_shim.requires_kernel_header = true`
- UEFI FD base: `0xC9000000`
- UEFI FD size: `0x00400000`
- `boot_image_kernel.kernel_compression = "none"`
- `boot_image_kernel.append_dtb = true`
- Android boot-image header version: `1`

The build script prepends the 112-byte BootShim binary to the 4 MiB FD, appends the device tree to that combined kernel payload, and passes the resulting file to the Android `mkbootimg.py` script. Therefore, the `ANDROID!` magic is the expected outer container, not evidence that the firmware itself is an Android kernel.

The extracted image matches that recipe:

- Android header version: 1
- Kernel payload: 4,570,494 bytes
- Kernel load address: `0x10008000`
- Ramdisk payload: 5 bytes, the literal placeholder `dummy`
- BootShim prefix: 112 bytes
- UEFI FD begins at kernel-payload offset 112 and is 4 MiB
- FDT begins at kernel-payload offset 4,194,416
- FDT declared size: 376,078 bytes
- FDT ends exactly at the end of the kernel payload

The 5-byte ramdisk is a placeholder supplied to the image builder. It is not a usable initramfs and is not intended to be one for this UEFI payload.

## BootShim and memory layout cross-check

The pinned BootShim assembly copies exactly `FD_SIZE` bytes from its payload to `FD_BASE`, then branches to `FD_BASE`. The current beyond2lte overlay sets:

- UEFI FD: `0xC9000000..0xC9400000`
- UEFI stack: `0xC9400000..0xC9440000`

The current overlay's memory map and DSC stack PCD agree with the 4 MiB FD configuration and keep the stack immediately after, not inside, the firmware volume. An older non-overlay copy of the platform memory map still contains a 2 MiB FD entry and a stack at `0xC9200000`; that stale copy must not be substituted for the active overlay.

## Remaining blockers

1. **Exact-device boot entry remains unverified.** The build guide describes packaging, but does not prove that the exact SM-G975F firmware/S-Boot revision will accept and transfer control to this image. The required execution state, trust policy, and entry register contract have not been independently established.
2. **BootShim handoff contract needs review.** Its assembly copies the FD and branches to its base. The precise register state, exception level, cache/MMU state, and any DTB handoff expected by the SEC entry point must be documented from the exact platform code and authoritative boot-chain evidence.
3. **The appended FDT is not currently integrated as an active UEFI device-tree protocol in the FDF.** The platform FDF's Device Tree driver and embedded DTB section are commented out. Do not assume DXE consumes the appended FDT merely because it is present in the Android image.
4. **Firmware-volume contents still need independent structural validation.** The FV header and file size were checked, but all embedded FFS/PE32 modules, machine types, relocations, and entry points have not yet been exhaustively enumerated.
5. **No device-side recovery path has been independently verified for this user's exact firmware state.** No hardware test should be inferred from the successful host build.

## Current decision

**Do not boot or install this candidate on the handset yet.** The outer packaging is now understood and the FD/stack layout in the active overlay is internally consistent. The next work is source-level verification of the BootShim-to-SEC handoff, firmware-volume contents, and exact-device boot-entry evidence. USB OTG and DisplayPort remain later milestones; the first eventual hardware milestone should remain the existing internal framebuffer only.
