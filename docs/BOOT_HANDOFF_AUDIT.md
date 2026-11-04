# Samsung bootloader → BootShim → UEFI handoff audit

Reviewed: 2026-11-04  
Target: SM-G975F / beyond2lte / Exynos 9820  
Pinned device implementation: `orhunnx/beyond2lte-uefi` at `f122c7024c5eeef2c8c78dfd08c62708c9ef823d`  
Pinned Mu-Silicium reference: `Project-Silicium/Mu-Silicium` at `6b3d90b79e191e08171bfedd3980234a7e49d340`

## Executive finding

The source establishes a plausible *standard ARM64 Linux-kernel-style* handoff into BootShim, but does not establish the actual register/system-register state supplied by the exact SM-G975F S-Boot revision.

The BootShim preserves incoming `x0`, overwrites `x1` with the address of its payload, copies the configured UEFI FD to `0xC9000000`, and branches there. The Linux ARM64 boot protocol assigns the DTB physical address to `x0`, so this design is compatible with a DTB pointer being present in `x0` at BootShim entry. This is a protocol-based inference, not direct evidence of Samsung S-Boot behavior on this handset.

The UEFI SEC entry path does not preserve or consume that pointer. It uses `x0` as scratch while detecting the exception level and later calculating the SEC stack. The Exynos 9820 platform assembly hook is a no-op, and `SecEntry()` / `SecMain()` accept no boot-argument parameter and do not parse an FDT. Consequently, the appended DTB is present in the Android boot image but is not consumed by a demonstrated UEFI path.

The SEC startup path accepts non-secure EL1 or EL2. Its EL3 path deliberately loops; there is no EL3-to-EL2 transition in this code. The exact entry EL on the user's handset remains unverified.

## Source trace

### 1. Android boot image and BootShim

Pinned source: `BootShim/BootShim.S`.

The relevant instructions are:

- `adr x1, _Payload`: place the payload address in `x1`.
- `b _Start`: enter the copy/dispatch code.
- `mov x4, x1`: retain the payload address in a temporary register.
- Load `FD_BASE` and `FD_SIZE`, copy exactly `FD_SIZE` bytes from payload to the configured FD base.
- `br x5`: branch to the FD base.

No instruction in this shim writes `x0`. Thus `x0` is preserved from the Android bootloader's kernel-entry register state through the final branch to the UEFI FD. `x1` is not preserved; it is repurposed for the payload address. The shim does not explicitly pass the appended FDT's address in a dedicated register or data structure.

The current package audit independently verified the actual candidate's 112-byte shim prefix, 4 MiB FD copy range, embedded FD equality and appended FDT bounds. See `ARTIFACT_PACKAGE_AUDIT.md`.

### 2. ARM64 boot protocol comparison

The Linux ARM64 boot protocol specifies:

- `x0`: physical address of the DTB in RAM.
- `x1`, `x2`, `x3`: zero/reserved.
- CPU enters non-secure EL2 (recommended) or non-secure EL1.
- MMU is off.
- Interrupt masks and cache/coherency conditions must satisfy the protocol.

Under that protocol, BootShim's preservation of `x0` is useful: the incoming DTB pointer can survive the shim. However, the exact Samsung S-Boot implementation, firmware revision, and its conformance to every ARM64 boot-protocol requirement have not been independently inspected. Do not promote the protocol comparison into a confirmed S-Boot fact.

Reference: Linux kernel documentation, “Booting AArch64 Linux”:
https://www.kernel.org/doc/html/latest/arch/arm64/booting.html

### 3. UEFI SEC entry and exception level

Pinned source: `Silicon/Silicium/SiliciumPkg/Sec/AArch64/ModuleEntryPoint.S`.

The entry sequence first calls `PlatformAssemblyInitialize()`. For Exynos 9820, the pinned implementation at `Silicon/Samsung/S5E9820Pkg/Library/PlatformSecLib/AArch64/PlatformHelper.S` is only `ret`; it does not save the incoming argument registers or alter the exception level.

The common entry then evaluates `CurrentEL` using the `EL1_OR_EL2` macro:

- EL1 path calls `SetupExceptionLevel1`.
- EL2 path calls `SetupExceptionLevel2`.
- The fallback path is a deliberate dead loop; this is not an EL3 transition implementation.

The entry code uses `x0` as a scratch register for the CurrentEL read and subsequent system-register configuration. It later overwrites `x0` with `PcdCPUCoresStackBase` and uses it to initialize the SEC stack. No copy of the incoming `x0` DTB address is made before those uses.

### 4. SEC C entry

Pinned source: `Silicon/Silicium/SiliciumPkg/Sec/Sec.c`.

- `SecEntry(VOID)` has no boot-argument parameter.
- `SecMain(VOID)` has no boot-argument parameter.
- SEC initializes cache/vector state, platform state, memory/HOBs and DXE loading.
- There is no FDT pointer argument or FDT parser in this SEC entry path.

The Exynos 9820 platform hook in `PlatformSec.c` only enables framebuffer writes through the configured DECON region. It does not import a DTB.

The platform FDF's embedded device-tree section and Device Tree DXE driver are commented out in the reviewed device overlay. Therefore, the current source does not demonstrate a later path that recovers the appended FDT.

## Handoff matrix

| Property | Source finding | Exact S-Boot state |
|---|---|---|
| Entry image | Android boot-image kernel payload begins with ARM64 BootShim | Boot-image acceptance/signature policy unverified |
| Incoming `x0` | BootShim preserves it unchanged | Whether S-Boot sets it to the DTB address is inferred from ARM64 protocol, not measured |
| Incoming `x1` | Overwritten with payload address | Exact initial value immaterial to current shim |
| `x2`, `x3` | Not modified by BootShim | Initial values unverified |
| Exception level | SEC supports EL1 and EL2; fallback loops | Actual EL1/EL2/EL3 unknown |
| Security state | SEC source assumes non-secure execution | Actual S-Boot security state unknown |
| MMU/cache state | SEC performs some cache operations; platform hook is no-op | Full entry contract and cache/coherency state unknown |
| Interrupt masks | No BootShim code establishes them | Exact DAIF state unknown |
| DTB use | Pointer can remain in `x0` through BootShim, then is clobbered by SEC entry | No DTB consumption path demonstrated |
| Memory ownership | FD/stack addresses are configured in the port | S-Boot reservations and conflicts not independently confirmed |

## What this proves and what it does not

**Proven by pinned source and package inspection:**

1. BootShim preserves `x0`, overwrites `x1`, copies the FD, and branches to the configured FD base.
2. The candidate's FD reset-vector branch resolves to the SEC TE entry point.
3. The Exynos 9820 platform assembly initialization hook is a no-op.
4. The common SEC entry has EL1 and EL2 paths and a non-returning fallback path.
5. The current SEC entry does not preserve or consume the incoming DTB pointer.
6. The appended FDT is not connected to a demonstrated DXE device-tree consumer.

**Not proven:**

1. Whether the exact SM-G975F S-Boot build accepts this image and reaches BootShim.
2. Which exception level and security state S-Boot uses for this image.
3. Whether the MMU is off and the cache, coherency, timer and interrupt state satisfy the firmware's assumptions.
4. Whether the memory map and reserved regions agree with the bootloader's live state.
5. Whether the bootloader's incoming `x0` is in fact the appended DTB pointer for this image.

## Engineering decision

Do not change the entry shim or add guessed register transitions based only on the generic ARM64 protocol. The next source-side improvement should be an explicit, reviewed boot-argument capture path that preserves the incoming DTB pointer before SEC startup reuses `x0`, followed by an FDT consumer that validates the pointer and memory range before parsing. That change must be designed against the actual EDK2 SEC interfaces and memory map; it must not assume that an unverified `x0` value is a valid FDT.

For exact S-Boot facts, acceptable evidence would be a trustworthy Samsung bootloader implementation/specification for the target revision or read-only hardware diagnostics captured at the existing bootloader/firmware boundary by a qualified developer. The source-only repository cannot establish those runtime facts.

**Current status: source-level handoff partially understood; exact handset bootloader handoff remains unknown; no phone boot is verified.**
