# Exynos 9820 Windows UFS driver source audit

Review date: 2026-11-06

## Scope and provenance

The pinned upstream repository `orhunnx/beyond2lte-uefi` at
`f122c7024c5eeef2c8c78dfd08c62708c9ef823d` contains a Windows ARM64
StorPort miniport source tree under `windows/b2lufs/`. It is not present in
this integration repository and has not been independently built here.

The upstream tree includes a StorPort entry layer, UFS transport layer,
resource-binding code, an INF template, a Windows MSVC/WDK build reference,
and host-side resource tests. The build reference describes MSVC/WDK as the
toolchain for producing the ARM64 kernel driver. The current Linux UEFI
workflow does not build or validate a Windows `.sys` driver.

## What the upstream source claims

The upstream README describes a miniport intended to bind to ACPI compatible
ID `ACPI\\BYND9820`, claim six Exynos UFS-related MMIO resources, and expose
UFS user LUN 0 through StorPort. Its design assumes firmware has already
initialized the UFS PHY/link and leaves the controller active for Windows.
The described miniport does not independently perform the complete PHY
calibration and link-startup sequence.

The INF template matches `ACPI\\BYND9820`, which agrees with the pinned
DSDT's `_CID`. The README's opening description instead names
`ACPI\\SMSN9820\\0`; that is a documentation inconsistency worth
cleaning up before any driver integration.

These are statements made by upstream source documentation, not independently
reproduced behavior. Register values, resource ownership, DMA assumptions,
interrupt behavior, and firmware-to-Windows controller handoff still require
independent validation against the exact SM-G975F board and its boot state.

## Important data-safety finding

The upstream README explicitly describes normal SCSI WRITE operations being
passed through to the existing Android user-data LUN. It is therefore **not a
read-only diagnostic driver**. A mistaken or unexpected storage request could
change data on the phone's internal storage.

For that reason this repository does not copy, build, package, sign, or deploy
that driver. No driver or firmware test is to be treated as safe merely because
the source contains metadata/GPT inspection features. The current audit is
documentation and source review only.

## Licensing and integration status

At the reviewed upstream revision, GitHub reports no repository license
metadata and the root `LICENSE` path is absent. A prior project note records
that maintainer permission to use the implementation was reported, but the
exact written terms, scope, redistribution rights, and conditions are not
captured in this repository.

Until those terms are documented and independently reviewed, the driver source
must not be copied into this project or redistributed. Permission to inspect
public source is not the same as a clear license to publish derived binaries.

## Current blockers

| Area | Finding |
|---|---|
| Source availability | Upstream miniport source exists at the pinned revision |
| Independent driver build | Not performed by this project |
| WDK/MSVC environment | Required by upstream build reference; absent from current Linux UEFI CI |
| Firmware handoff | Driver assumes active UFSHCI/link state from UEFI; not proven on handset |
| ACPI binding | DSDT `_CID` and INF compatible ID agree; README device-path wording is inconsistent |
| Storage safety | Driver includes write-capable block I/O paths; not read-only |
| License | No declared upstream license; written permission terms need clarification |
| Windows boot | No verified Windows boot or usable storage path on the physical phone |

## Safe next work

1. Preserve the upstream source as an external reference; do not vendor it while
   licensing is unresolved.
2. Continue a static review of the ACPI resource description and compare each
   resource against the exact board device tree and firmware source.
3. Keep host-only UEFI builds separate from Windows driver validation.
4. Require a documented license and independent code review before considering
   any driver integration.
5. Keep all physical-device storage writes and firmware deployment outside this
   repository's current experimental workflow.

This audit does not establish that the driver works, that Windows can boot from
the S10+ internal storage, or that the phone is ready for deployment.
