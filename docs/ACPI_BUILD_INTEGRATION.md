# Exynos 9820 ACPI build integration

## Why this exists

The pinned beyond2lte source contains S5E9820 ACPI table sources and an
ACPI.inc firmware-volume include. The downstream host-build recipe
previously copied the ACPI source directory but did not compile the .dsl
tables or activate the freeform ACPI file in the platform FDF. A successful
UEFI compile therefore did not establish that the platform ACPI tables were
present in the candidate firmware.

## Host-build behavior

scripts/prepare_acpi_tables.py now runs inside the temporary
Mu-Silicium build workspace. It:

1. Uses the exact pinned beyond2lte upstream checkout.
2. Generates the S5E9820 PPTT with the upstream topology generator.
3. Compiles APIC, DSDT, FACP and GTDT sources with ACPICA iasl.
4. Requires the pinned Mu-Silicium Common/SSDT.aml.
5. Checks each table's signature, declared length and checksum.
6. Enables the reviewed AcpiTables freeform block in the temporary
   beyond2lte.fdf include.
7. Writes Build/acpi-build-report.json with the table hashes.

The repository source files and pinned upstream checkouts are not modified by
this preparation step; all generated AML and FDF edits stay in the disposable
host-build workspace.

## Tables included

| Table | Purpose |
|---|---|
| APIC / MADT | GIC and processor interrupt-controller descriptions |
| DSDT | Platform devices and resource descriptions |
| SSDT | Shared Silicium ACPI definitions |
| FACP / FADT | Fixed ACPI hardware description and PSCI conduit flags |
| GTDT | ARM generic timer description |
| PPTT | Exynos 9820 CPU topology |

## What this does not prove

- Header/checksum validation is not full ACPI specification validation.
- Successful firmware compilation does not prove Windows accepts every table.
- The ACPI UFS node describes resources and a device identity; it does not
  provide a Windows UFS driver.
- The custom BYND9820 UFS identity in the pinned DSDT expects a matching
  custom StorPort miniport. That driver is not built or distributed by this
  repository.
- No physical-device boot, Windows Setup, or Windows kernel stability is
  validated by this host-side step.

This is a necessary firmware-integration improvement, not a claim that the
Windows 11 port is complete or ready for handset deployment.
