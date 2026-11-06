# Samsung bootloader → BootShim → UEFI handoff audit

Reviewed: 2026-11-04  
Target: SM-G975F / beyond2lte / Exynos 9820  
Pinned device implementation: `orhunnx/beyond2lte-uefi` at `f122c7024c5eeef2c8c78dfd08c62708c9ef823d`  
Pinned Mu-Silicium reference: `Project-Silicium/Mu-Silicium` at `6b3d90b79e191e08171bfedd3980234a7e49d340`

## Executive finding

The source establishes a plausible *standard ARM64 Linux-kernel-style* handoff into BootShim, but does not establish the actual register/system-register state supplied by the exact SM-G975F S-Boot revision.

The BootShim preserves incoming `x0`, overwrites `x1` with the address of its payload, copies the configured UEFI FD to `0xC9000000`, and branches there. The Linux ARM64 boot protocol assigns the DTB physical address to `x0`, so this design is compatible with a DTB pointer being present in `x0` at BootShim entry. This is a protocol-based inference, not direct evidence of Samsung S-Boot behavior on this handset.

The original UEFI SEC entry path did not preserve or consume that pointer. The downstream branch now patches the pinned BootShim so that, immediately before branching to the UEFI FD, it computes `x0 = runtime_address(_Payload) + FD_SIZE`. In this package recipe `_Payload` begins at the first byte of the embedded FD and the appended DTB follows the FD immediately, so this explicitly passes the appended FDT address rather than relying on Samsung S-Boot's incoming `x0`. The SEC entry shim saves that value in callee-saved `x19`, passes it to `SecEntry()`, and checks after `MemoryPeim()` whether it is aligned and the minimum 40-byte FDT header span lies inside one declared DRAM descriptor. This is deliberately only a range check: it does not dereference or parse the FDT, establish that the loaded kernel region remains mapped for later DXE use, or make the DTB available to a DXE consumer.

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

No instruction in this shim writes `x0`. Thus `x0` is preserved from the Android bootloader's kernel-entry register state through the final branch to the UEFI FD. `x1` is not preserved; it is repurposed for the payload address. The downstream BootShim patch now explicitly computes the appended FDT address as `_Payload + FD_SIZE` and places it in `x0` immediately before the branch to the FD. The host source audit checks this exact transformation against the pinned BootShim source.

The current package audit independently verified the actual candidate's 112-byte shim prefix, 4 MiB FD copy range, embedded FD equality and appended FDT bounds. See `ARTIFACT_PACKAGE_AUDIT.md`.

### 2. ARM64 boot protocol comparison

The Linux ARM64 boot protocol specifies:

- `x0`: physical address of the DTB in RAM.
- `x1`, `x2`, `x3`: zero/reserved.
- CPU enters non-secure EL2 (recommended) or non-secure EL1.
- MMU is off.
- Interrupt masks and cache/coherency conditions must satisfy the protocol.

Under that protocol, BootShim's preservation of `x0` is useful: the incoming DTB pointer can survive the shim. The appended FDT handoff no longer depends on S-Boot placing a DTB in `x0`: BootShim overwrites `x0` with the address derived from its own runtime payload layout. This does not establish that the Android bootloader loaded the kernel at the configured address with the required execution state, or that the FDT memory remains accessible after SEC memory initialization.

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

## Additional upstream S-Boot evidence (static, revision-limited)

A later review of the device-specific upstream repository found additional evidence that was not included in the original handoff audit:

- Upstream `DEVIR.md` at the pinned device commit records static analysis of stock `G975FXXSGHWC1` and `G975FXXSGHWC2` S-Boot images.
- The HWC2 analysis identifies a wrapper around `f_load_hypervisor` and records the Samsung SMC call convention used by the stock U-H loader: `x0=0xC2000400`, `x1=0x87001000`, `x2=0x2000`, `x3=1`, `x4=0x87000000`, and `x5=0x100000`. These are arguments to the stock hypervisor-loading service, **not** the Android boot-image kernel-entry register contract and must not be copied into BootShim.
- The same analysis explicitly says its static call-graph scan does not prove whether the U-H wrapper is dispatched on the custom-BOOT path. A function and ABI can be identified without proving that this path invokes them.
- Upstream records a device-side UEFI `CurrentEL` observation for its own test configuration. That is useful corroboration that one S10+ configuration reached UEFI at EL1, but it is not a measurement of this project's handset or its reported bootloader build.

References (all pinned to `orhunnx/beyond2lte-uefi@f122c7024c5eeef2c8c78dfd08c62708c9ef823d`):

- `DEVIR.md`, sections “9820 S-Boot / uH research notes” and “HWC2 S-BOOT dispatch boundary”.
- `EL3_SEH_PLANI.md`, which documents the Exynos EL3 SMC interface as understood by that upstream project.
- `STOK_ACILIS.md`, the upstream stock boot/initcall analysis.

### Applicability to this project

The upstream binary evidence is revision-specific. Its examined builds (`G975FXXSGHWC1` / `G975FXXSGHWC2`) do not match the bootloader property previously supplied for this project's handset (`G975FXXUHHXJ1`). The property string alone also does not identify every relevant S-Boot component or prove that the currently executing boot chain matches either upstream sample.

Therefore:

1. The Samsung U-H SMC ABI is now documented as a known Exynos 9820 interface in the upstream sample; it is **not** evidence that the normal custom-BOOT handoff invokes that interface.
2. The upstream static analysis does not establish the entry values of `CurrentEL`, `SCR_EL3`, `SCTLR_ELx`, `HCR_EL2`, `SPSR_ELx`, `DAIF`, cache state, or translation-table state at this project's BootShim entry.
3. It does not prove image acceptance, signature policy, entry address, or memory reservations for the user's reported bootloader build.
4. No U-H/EL2 loading experiment, SMC invocation, partition access, or device write is justified by this evidence.

The correct status remains **partially characterized, not validated**. Closing the remaining gap requires a trustworthy analysis of the exact bootloader binaries for this handset and a read-only measurement at the existing handoff boundary. Until those are available, do not alter the SEC exception-level path or infer that a different EL/security state should be forced.

## Handoff matrix

| Property | Source finding | Exact S-Boot state |
|---|---|---|
| Entry image | Android boot-image kernel payload begins with ARM64 BootShim | Boot-image acceptance/signature policy unverified |
| Incoming `x0` | BootShim preserves it unchanged | Whether S-Boot sets it to the DTB address is inferred from ARM64 protocol, not measured |
| Incoming `x1` | Overwritten with payload address | Exact initial value immaterial to current shim |
| `x2`, `x3` | Not modified by BootShim | Initial values unverified |
| Exception level | SEC supports EL1 and EL2; fallback loops. Upstream reports EL1 in its own device test. | Exact EL/security state for this project's reported bootloader build remains unknown |
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

1. Whether the exact SM-G975F S-Boot build accepts this image and reaches BootShim. Upstream HWC1/HWC2 disassembly does not settle this for the reported UHHXJ1 build.
2. Which exception level and security state S-Boot uses for this image.
3. Whether the MMU is off and the cache, coherency, timer and interrupt state satisfy the firmware's assumptions.
4. Whether the memory map and reserved regions agree with the bootloader's live state.
5. Whether the bootloader's incoming `x0` is in fact the appended DTB pointer for this image.

## Engineering decision

The downstream branch now explicitly sets `x0` to the appended FDT address in BootShim, preserves it through SEC assembly, and checks its alignment and containment within one declared DRAM descriptor after memory initialization. It intentionally stops before dereferencing the value. A future FDT-header parser and DXE handoff must wait until the physical-to-virtual mapping and lifetime of the kernel payload memory are verified. The remaining bootloader questions concern image acceptance, entry EL/security state, and memory/cache/MMU setup—not the source of the DTB pointer.

For exact S-Boot facts, acceptable evidence would be a trustworthy Samsung bootloader implementation/specification for the target revision or read-only hardware diagnostics captured at the existing bootloader/firmware boundary by a qualified developer. The source-only repository cannot establish those runtime facts.

**Current status on `feature/sec-bootarg-fdt-validation`: BootShim explicitly passes the appended FDT address in x0; SEC preserves it and performs non-dereferencing DRAM range validation. The source transformation and host build must pass CI for each new commit. Exact handset bootloader entry state and image acceptance remain unknown; no phone boot is verified.**
