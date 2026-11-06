# UFS miniport source review

Review target: `orhunnx/beyond2lte-uefi` commit
`f122c7024c5eeef2c8c78dfd08c62708c9ef823d`.

## Findings

The upstream tree contains a Windows ARM64 StorPort miniport source set:
`b2lufs_storport.c`, `b2lufs_transport.c`, `b2lufs_resources.c`,
headers, an INF template, a PowerShell build script, and a WDK build
reference. The build reference requires a Windows MSVC/WDK environment;
the Linux UEFI host workflow does not build this driver.

The INF template binds to `ACPI\\BYND9820`, matching the compatible ID
documented by the pinned minimal DSDT. The README's introductory paragraph
instead names `ACPI\\SMSN9820\\0`, while later sections and the build
reference use `ACPI\\BYND9820`. This is an upstream documentation
inconsistency; the actual INF/DSDT pair is the relevant match.

The implementation is a physical StorPort miniport, not a generic inbox
driver. It expects the UFS controller and link to have been initialized by
firmware, maps six MMIO resource windows, and uses StorPort-managed common
DMA memory. Its design is therefore tightly coupled to the firmware's
controller state and resource description.

The source explicitly supports normal SCSI READ and WRITE operations to the
existing Android user-data LUN 0. It is not a read-only diagnostic driver.
Its own README describes writes and other mutating SCSI commands. A host-side
compile would not prove that the controller handoff, DMA, interrupts, or
storage behavior is correct on the actual handset.

## Licensing and validation

At the pinned revision, the upstream repository does not declare a repository
license. No source has been copied into this project. The reported permission
to use the upstream implementation needs documented terms covering
modification and redistribution before vendoring or publishing a derivative.

No independent WDK build, driver signing, Windows Setup test, or physical
device test has been performed by this project.

## Current decision

Do not integrate or package this miniport at this stage. First resolve
licensing, review the complete driver and its firmware assumptions, and
establish an isolated validation strategy that cannot write to the phone's
existing data. This repository's current workflow remains host-side firmware
and source review only.

This review does not establish that Windows can boot from the handset's UFS
storage.
