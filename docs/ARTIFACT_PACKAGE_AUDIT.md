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

## Additional reset-vector inspection (2026-11-04)

The 4 MiB FD was inspected at byte level after the initial audit:

- The FV header begins at FD offset 0; its `_FVH` signature is at offset `0x28`, with a declared length of `0x400000` and header length `0x48`.
- The first AArch64 instruction is `0x140020ec`, an unconditional `B` instruction. Its signed immediate resolves to FD-relative offset `0x83b0`.
- The SEC FFS file GUID from `Sec.inf` is present at offset `0x48`. Its FFS type is `EFI_FV_FILETYPE_SECURITY_CORE` (`0x03`) and its declared extent is `0x48..0xb000`.
- The SEC FFS file contains a TE image section at offset `0x158`. Its TE signature is `VZ`, machine is AArch64 (`0xAA64`), image base is `0xC9000000`, and `AddressOfEntryPoint` is `0x83b0`.
- The reset-vector branch destination and SEC TE `AddressOfEntryPoint` are an **exact match**: `FD_BASE + 0x83b0`.

A host-side check was added as `scripts/audit_firmware_entry.py`. It passed against the downloaded candidate FD. It verifies the reset-vector branch target equals the AArch64 SEC TE entry point and that the TE image base equals the configured FD base. The host-build workflow now runs this check before uploading artifacts.

**Interpretation:** this resolves the narrow concern that branching to FD base would immediately execute the FV header. The FD begins with an AArch64 reset-vector branch, and its destination is inside the SEC FFS file. This establishes the reset-vector-to-SEC-TE entry-point linkage in the built FD. It does **not** prove that the required processor state is valid or that Samsung's boot chain will accept the image.

## SEC processor-state contract found in source

The pinned Mu-Silicium startup assembly and Exynos 9820 platform helper were also traced:

- `PlatformAssemblyInitialize()` in `S5E9820Pkg/Library/PlatformSecLib/AArch64/PlatformHelper.S` is a no-op (`ret`).
- `ModuleEntryPoint.S` then evaluates `CurrentEL` through `EL1_OR_EL2`.
- The macro explicitly selects EL1 (`CurrentEL=0x4`) or EL2 (`CurrentEL=0x8`). For EL3 (`CurrentEL=0xC`), it takes its deliberate infinite-loop path; it does not transition from EL3 to EL2.
- The SEC startup code subsequently configures EL1/EL2 state and initializes the configured stack.

Therefore, the current handoff has a concrete prerequisite: **the Android/Samsung boot chain must enter the BootShim/SEC path in non-secure EL1 or EL2, not EL3.** The source alone does not establish which level the user's exact bootloader uses.

The appended DTB is also not demonstrated to reach DXE: the current SEC entry assembly uses `x0` as a scratch register while checking `CurrentEL`, and later reuses it for stack setup. The FDF's embedded-DTB file and `DtPlatformDxe` remain commented out. Treat the appended DTB as present in the image but not consumed by the current UEFI platform until a separate handoff/protocol path is proven.

## Remaining blockers

1. **Exact-device boot entry remains unverified.** The build guide describes packaging, but does not prove that the exact SM-G975F firmware/S-Boot revision will accept and transfer control to this image. The required execution state, trust policy, and entry register contract have not been independently established.
2. **BootShim-to-SEC processor-state contract needs device-side confirmation.** Source review shows SEC only supports entry at EL1 or EL2; EL3 leads to a deliberate dead loop. The exact SM-G975F bootloader's entry level and cache/MMU/register state remain unverified.
3. **The appended FDT is not currently consumed by a demonstrated UEFI path.** SEC startup clobbers x0, and the platform FDF's Device Tree driver and embedded-DTB section are commented out. Do not assume DXE consumes the appended FDT merely because it is present in the Android image.
4. **Firmware-volume contents still need independent structural validation.** The FV header and file size were checked, but all embedded FFS/PE32 modules, machine types, relocations, and entry points have not yet been exhaustively enumerated.
5. **No device-side recovery path has been independently verified for this user's exact firmware state.** No hardware test should be inferred from the successful host build.

## Current decision

**Do not boot or install this candidate on the handset yet.** The outer packaging is understood, the FD/stack layout in the active overlay is internally consistent, and the FD reset vector has been checked against the exact SEC TE entry point. The next work is confirming the bootloader's EL1/EL2 entry state, completing firmware-volume validation, and establishing exact-device boot-entry and recovery evidence. USB OTG and DisplayPort remain later milestones; the first eventual hardware milestone should remain the existing internal framebuffer only.
