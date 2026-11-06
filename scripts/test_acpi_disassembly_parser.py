#!/usr/bin/env python3
"""Focused regression tests for the ACPICA APIC disassembly parser."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_acpi_tables import validate_apic_disassembly


def make_report(raw: bytes) -> str:
    rows = []
    for offset in range(0, len(raw), 16):
        chunk = raw[offset:offset + 16]
        rows.append(f"{offset:04X}: " + " ".join(f"{byte:02X}" for byte in chunk) + "  //")
    return (
        '[010h 0016 008h]                Oem Table ID : "S5E9820 "\n'
        f"Raw Table Data: Length {len(raw)} (0x{len(raw):X})\n"
        + "\n".join(rows)
        + "\n"
    )


def main() -> int:
    raw = bytearray(724)
    raw[0:4] = b"APIC"
    raw[4:8] = len(raw).to_bytes(4, "little")
    raw[16:24] = b"S5E9830 "
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source, compiled = root / "APIC.dsl", root / "APIC.aml"
        source.write_text(make_report(bytes(raw)), encoding="utf-8")
        compiled.write_bytes(raw)

        result = validate_apic_disassembly(source, compiled)
        assert result["raw_dump_matches_compiled_output"] is True
        assert result["decoded_oem_table_id"] == "S5E9820 "
        assert result["raw_oem_table_id"] == "S5E9830 "
        assert result["oem_table_id_mismatch"] is True

        compiled.write_bytes(bytes(raw[:-1]) + b"X")
        try:
            validate_apic_disassembly(source, compiled)
        except RuntimeError as error:
            assert "differs from the raw table" in str(error)
        else:
            raise AssertionError("modified AML was not rejected")

        report = make_report(bytes(raw)).replace("0000:", "0001:", 1)
        source.write_text(report, encoding="utf-8")
        compiled.write_bytes(raw)
        try:
            validate_apic_disassembly(source, compiled)
        except RuntimeError as error:
            assert "offset gap/overlap" in str(error)
        else:
            raise AssertionError("non-contiguous raw offsets were not rejected")

    print("APIC disassembly parser regression tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
