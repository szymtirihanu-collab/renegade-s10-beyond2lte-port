# Exynos 9820 ACPI static review

Reviewed: 2026-11-06  
Source: orhunnx/beyond2lte-uefi at f122c7024c5eeef2c8c78dfd08c62708c9ef823d

This is a source-only review of the pinned ACPI inputs. It does not modify or build firmware and does not validate behavior on a handset.

## Findings

### APIC/MADT OEM Table ID mismatch

The APIC source's decoded header fields identify the OEM Table ID as S5E9820 , but the same disassembly's raw table bytes at offsets 0x10–0x17 encode S5E9830 . The raw bytes are what the compiled table actually contains; the decoded symbolic header and raw dump therefore disagree. The ACPI build script currently checks only signature, length, and checksum, so it will not detect this semantic/header inconsistency.

Do not silently change the table ID based on this review alone. Confirm the intended platform identity against the source generator and other pinned S5E9820 tables, then add a deterministic validation against the generated AML bytes.

### CPU topology is explicitly single-core in this table set

The MADT contains eight Generic Interrupt Controller CPU interface (GICC) entries with processor UIDs 0–7. Only UID 0 has the Enabled flag set; UIDs 1–7 are disabled. The minimal DSDT also describes CPU0–CPU7, but _STA returns 0x0F only for CPU0 and zero for CPU1–CPU7.

This is consistent internally as a single-core bring-up configuration. It is not an eight-core Windows topology. It must not be described as full Exynos 9820 SMP support.

### GIC address cross-check is incomplete

The MADT GIC Distributor base is 0x10101000, which matches the corresponding register address found in the reviewed device-tree data. That single match does not validate the complete GIC programming model, interrupt assignments, CPU interface/redistributor layout, timer interrupts, PSCI, or secondary CPU startup.

### APIC input is a disassembly listing, not compilable ASL

The pinned upstream tree contains `APIC.dsl`, but inspection shows it is an ACPICA disassembler report: it begins with the disassembly banner, contains decoded table fields and a `Raw Table Data` hexadecimal dump, and has no `DefinitionBlock` or ASL table-construction statements. The pinned tree does not contain a sibling `APIC.aml` binary. The raw hexadecimal dump is inside the report text; it is not an ASL definition that `iasl` can compile into the original table.

The integration script currently invokes `iasl -ve APIC.dsl` and then expects `APIC.aml` to exist. That generation assumption is not supported by the checked-in input format. The APIC path must be reconciled against actual clean-build logs and corrected to use a verified binary source or a deterministic, independently validated reconstruction of the raw table bytes. Do not accept a stale generated APIC.aml or a successful command exit as proof that the intended MADT was embedded.

## Required follow-up before any Windows-compatibility claim

- Resolve and automatically test the APIC OEM Table ID against the intended Exynos 9820 identity.
- Keep the current single-core limitation explicit until all CPU interface entries, DSDT processor objects, interrupt topology, and CPU bring-up behavior are validated together.
- Run a full ACPI/AML semantic validation pass; header/checksum validation alone is insufficient.
- Validate tables in a suitable isolated firmware/OS test environment before making compatibility claims.

## Scope and safety

No firmware image is generated here. No physical device is accessed, modified, or tested. This review is not a deployment or handset-test recommendation.
