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
    target_soc = target_acpi / "SoCs/Samsung/S5E9820"
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

    manifest = []
    for filename, signature in TABLES.items():
        manifest.append(validate_table(target_soc / filename, signature))
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
