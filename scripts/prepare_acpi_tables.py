#!/usr/bin/env python3
"""Compile and enable the pinned Exynos 9820 ACPI tables in a temporary Mu-Silicium build tree.

This is a host-build preparation step. It never accesses or modifies a handset.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ACPI_FREEFORM_GUID = "7E374E25-8E01-4FEE-87F2-390C23C606CD"
TABLES = {
    "APIC.aml": b"APIC",
    "DSDT_minimal.aml": b"DSDT",
    "FACP.aml": b"FACP",
    "GTDT.aml": b"GTDT",
    "PPTT.aml": b"PPTT",
}
COMMENTED_BLOCK = (
    f"#FILE FREEFORM = {ACPI_FREEFORM_GUID} {{\n"
    "#    SECTION RAW = S5E9820/APIC.aml\n"
    "#    SECTION RAW = S5E9820/DSDT_minimal.aml\n"
    "#    SECTION RAW = Common/SSDT.aml\n"
    "#    SECTION RAW = S5E9820/FACP.aml\n"
    "#    SECTION RAW = S5E9820/GTDT.aml\n"
    "#    SECTION RAW = S5E9820/PPTT.aml\n"
    '#    SECTION UI = "AcpiTables"\n'
    "#}\n"
)
ACTIVE_BLOCK = (
    f"FILE FREEFORM = {ACPI_FREEFORM_GUID} {{\n"
    "    SECTION RAW = S5E9820/APIC.aml\n"
    "    SECTION RAW = S5E9820/DSDT_minimal.aml\n"
    "    SECTION RAW = Common/SSDT.aml\n"
    "    SECTION RAW = S5E9820/FACP.aml\n"
    "    SECTION RAW = S5E9820/GTDT.aml\n"
    "    SECTION RAW = S5E9820/PPTT.aml\n"
    '    SECTION UI = "AcpiTables"\n'
    "}\n"
)


def run(command: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def validate_table(path: Path, signature: bytes) -> dict[str, object]:
    data = path.read_bytes()
    if len(data) < 36:
        raise RuntimeError(f"{path}: ACPI table is shorter than the 36-byte standard header")
    if data[:4] != signature:
        raise RuntimeError(
            f"{path}: expected signature {signature.decode()}, got {data[:4]!r}"
        )
    declared_length = int.from_bytes(data[4:8], "little")
    if declared_length != len(data):
        raise RuntimeError(
            f"{path}: header length {declared_length} does not match file length {len(data)}"
        )
    if sum(data) & 0xFF:
        raise RuntimeError(f"{path}: ACPI checksum is invalid")
    return {
        "file": path.name,
        "signature": signature.decode(),
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def install_apic_raw_table(source: Path, compiled: Path) -> dict[str, object]:
    """Use the pinned disassembly's embedded binary, not iasl's reconstructed header."""
    import re

    text = source.read_text(encoding="utf-8")
    match = re.search(r"Raw Table Data: Length (\d+) \(0x([0-9A-Fa-f]+)\)", text)
    if not match:
        raise RuntimeError(f"{source}: missing ACPICA Raw Table Data block")
    expected_length = int(match.group(1), 10)
    if expected_length != int(match.group(2), 16):
        raise RuntimeError(f"{source}: inconsistent raw-data length declaration")

    raw = bytearray()
    for line in text[match.end():].splitlines():
        row = re.match(r"\s*([0-9A-Fa-f]{4}):((?:\s+[0-9A-Fa-f]{2})+)\s+//", line)
        if not row:
            continue
        offset = int(row.group(1), 16)
        if offset != len(raw):
            raise RuntimeError(f"{source}: raw-data offset gap/overlap at 0x{offset:04X}")
        raw.extend(int(value, 16) for value in row.group(2).split())
    if len(raw) != expected_length:
        raise RuntimeError(
            f"{source}: extracted {len(raw)} raw bytes, expected {expected_length}"
        )
    if len(raw) < 36 or raw[:4] != b"APIC":
        raise RuntimeError(f"{source}: embedded raw data is not a complete APIC table")
    if int.from_bytes(raw[4:8], "little") != len(raw):
        raise RuntimeError(f"{source}: embedded APIC header length is invalid")
    if sum(raw) & 0xFF:
        raise RuntimeError(f"{source}: embedded APIC checksum is invalid")

    decoded = re.search(r'^\s*\[010h[^\n]*Oem Table ID\s*:\s*"([^"]+)"', text, re.MULTILINE)
    raw_oem = bytes(raw[16:24]).decode("ascii", errors="replace")
    decoded_oem = decoded.group(1) if decoded else None

    # ACPICA accepts the listing but reconstructs its decoded header fields.
    # Preserve the exact pinned binary represented by its Raw Table Data block.
    compiled.write_bytes(raw)
    if compiled.read_bytes() != bytes(raw):
        raise RuntimeError(f"{compiled}: failed to preserve embedded APIC raw bytes")
    return {
        "raw_table_installed": True,
        "raw_table_size": len(raw),
        "decoded_oem_table_id": decoded_oem,
        "raw_oem_table_id": raw_oem,
        "oem_table_id_mismatch": decoded_oem != raw_oem,
        "note": "APIC.aml is copied from the pinned disassembly raw-data block after iasl accepts the listing; reconstructed iasl header output is not used.",
    }


def enable_acpi_fdf(mu_root: Path) -> Path:
    include = mu_root / "Platforms/Samsung/beyond2ltePkg/Include/ACPI.inc"
    fdf = mu_root / "Platforms/Samsung/beyond2ltePkg/beyond2lte.fdf"
    if not include.is_file() or not fdf.is_file():
        raise RuntimeError("beyond2lte FDF or Include/ACPI.inc is missing from the temporary build tree")
    if "!include Include/ACPI.inc" not in fdf.read_text(encoding="utf-8"):
        raise RuntimeError("beyond2lte.fdf does not include Include/ACPI.inc")

    text = include.read_text(encoding="utf-8")
    if ACTIVE_BLOCK in text:
        pass
    elif COMMENTED_BLOCK in text:
        text = text.replace(COMMENTED_BLOCK, ACTIVE_BLOCK, 1)
        include.write_text(text, encoding="utf-8")
    else:
        raise RuntimeError(
            "ACPI.inc does not match the reviewed pinned table block; refusing a fuzzy edit"
        )
    if text.count(ACTIVE_BLOCK) != 1:
        raise RuntimeError("Expected exactly one active Exynos ACPI freeform block")
    return include


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream-root", type=Path, required=True)
    parser.add_argument("--mu-root", type=Path, required=True)
    args = parser.parse_args()

    upstream = args.upstream_root.resolve()
    mu_root = args.mu_root.resolve()
    source_soc = upstream / "silicium-acpi-overlay/SoCs/Samsung/S5E9820"
    target_acpi = mu_root / "Silicium-ACPI"
    target_soc = mu_root / "Silicium-ACPI/SoCs/Samsung/S5E9820"
    common_ssdt = target_acpi / "Common/SSDT.aml"
    pptt_generator = upstream / "tools_pptt_gen.py"

    if not source_soc.is_dir() or not target_soc.is_dir():
        raise RuntimeError("Pinned S5E9820 ACPI source or copied target directory is missing")
    if not common_ssdt.is_file():
        raise RuntimeError(f"Pinned Mu-Silicium ACPI submodule is missing {common_ssdt}")
    if not pptt_generator.is_file():
        raise RuntimeError(f"Pinned PPTT generator is missing: {pptt_generator}")

    iasl = "iasl"
    run([iasl, "-v"])
    run([sys.executable, str(pptt_generator), str(target_soc / "PPTT.aml")])

    required_sources = ("APIC.dsl", "DSDT_minimal.dsl", "FACP.dsl", "GTDT.dsl")
    for filename in required_sources:
        source = target_soc / filename
        if not source.is_file():
            raise RuntimeError(f"Required S5E9820 ACPI source is missing: {source}")
        run([iasl, "-ve", filename], cwd=target_soc)

    apic_audit = install_apic_raw_table(target_soc / "APIC.dsl", target_soc / "APIC.aml")
    manifest = []
    for filename, signature in TABLES.items():
        manifest.append(validate_table(target_soc / filename, signature))
    manifest[0].update(apic_audit)
    if apic_audit["oem_table_id_mismatch"]:
        print(
            "WARNING: APIC decoded OEM Table ID differs from its raw bytes: "
            f"{apic_audit['decoded_oem_table_id']!r} vs "
            f"{apic_audit['raw_oem_table_id']!r}",
            file=sys.stderr,
        )
    manifest.append(validate_table(common_ssdt, b"SSDT"))

    include = enable_acpi_fdf(mu_root)
    report_path = mu_root / "Build/acpi-build-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "target": "Samsung Galaxy S10+ SM-G975F / beyond2lte / Exynos 9820",
        "source_commit": "f122c7024c5eeef2c8c78dfd08c62708c9ef823d",
        "tables": manifest,
        "fdf_include": str(include.relative_to(mu_root)),
        "freeform_guid": ACPI_FREEFORM_GUID,
        "result": "HOST_ACPI_TABLES_COMPILED_AND_ENABLED",
        "limitations": [
            "Validates table headers, lengths, and checksums; not full Windows ACPI conformance.",
            "Does not prove the tables are accepted by firmware or Windows on the handset.",
            "Does not access, flash, repartition, or modify a physical device.",
        ],
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
