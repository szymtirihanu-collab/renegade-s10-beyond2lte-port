#!/usr/bin/env python3
"""Focused regression tests for the APIC raw-table extractor."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_acpi_tables import install_apic_raw_table


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
    raw[9] = (-sum(raw)) & 0xFF

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source, output = root / "APIC.dsl", root / "APIC.aml"
        source.write_text(make_report(bytes(raw)), encoding="utf-8")
        output.write_bytes(b"iasl reconstructed header")

        result = install_apic_raw_table(source, output)
        assert result["raw_table_installed"] is True
        assert result["raw_table_size"] == 724
        assert result["decoded_oem_table_id"] == "S5E9820 "
        assert result["raw_oem_table_id"] == "S5E9830 "
        assert result["oem_table_id_mismatch"] is True
        assert output.read_bytes() == bytes(raw)

        broken = make_report(bytes(raw)).replace("0000:", "0001:", 1)
        source.write_text(broken, encoding="utf-8")
        try:
            install_apic_raw_table(source, output)
        except RuntimeError as error:
            assert "offset gap/overlap" in str(error)
        else:
            raise AssertionError("non-contiguous raw offsets were not rejected")

        invalid = bytearray(raw)
        invalid[100] ^= 1
        source.write_text(make_report(bytes(invalid)), encoding="utf-8")
        try:
            install_apic_raw_table(source, output)
        except RuntimeError as error:
            assert "checksum is invalid" in str(error)
        else:
            raise AssertionError("invalid APIC checksum was not rejected")

    print("APIC raw-table extractor regression tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
