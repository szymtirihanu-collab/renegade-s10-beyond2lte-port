#!/usr/bin/env python3
"""Static audit of the built ARM64 firmware reset-vector and SEC TE image."""
from __future__ import annotations

import struct
import sys
from pathlib import Path

SEC_FILE_GUID = bytes.fromhex("03b5ff9a43e641418b9017e8588b1d35")
FV_SIGNATURE = b"_FVH"
EXPECTED_FD_BASE = 0xC9000000


def fail(message: str) -> int:
    print(f"FIRMWARE ENTRY AUDIT: FAIL: {message}")
    return 1


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} SILICIUM_UEFI.fd")
        return 2

    path = Path(sys.argv[1])
    data = path.read_bytes()
    if len(data) < 0x70:
        return fail("file is too small to contain an FV header")
    if data[0x28:0x2C] != FV_SIGNATURE:
        return fail("FV signature mismatch at expected reset-vector layout offset")

    fv_length = struct.unpack_from("<Q", data, 0x20)[0]
    header_length = struct.unpack_from("<H", data, 0x30)[0]
    if fv_length != len(data):
        return fail(f"FV length {fv_length:#x} does not match file size {len(data):#x}")
    if header_length < 0x38 or header_length > fv_length:
        return fail(f"invalid FV header length {header_length:#x}")

    # Decode the AArch64 unconditional B at the FD base.
    instruction = struct.unpack_from("<I", data, 0)[0]
    if instruction & 0xFC000000 != 0x14000000:
        return fail(f"first instruction {instruction:#010x} is not AArch64 B")
    imm26 = instruction & 0x03FFFFFF
    if imm26 & (1 << 25):
        imm26 -= 1 << 26
    reset_target = imm26 << 2

    # Find the SEC FFS file using the FILE_GUID in Sec.inf.
    sec_hits = []
    start = (header_length + 7) & ~7
    for offset in range(start, fv_length - 24 + 1, 8):
        if data[offset:offset + 16] != SEC_FILE_GUID:
            continue
        file_type = data[offset + 18]
        size = int.from_bytes(data[offset + 20:offset + 23], "little")
        header_size = 24
        if size == 0xFFFFFF:
            if offset + 32 > fv_length:
                continue
            size = struct.unpack_from("<I", data, offset + 24)[0]
            header_size = 32
        if file_type == 0x03 and size >= header_size and offset + size <= fv_length:
            sec_hits.append((offset, size))

    if len(sec_hits) != 1:
        return fail(f"expected one valid SEC FFS file, found {len(sec_hits)}")
    sec_offset, sec_size = sec_hits[0]
    sec_end = sec_offset + sec_size
    if not sec_offset <= reset_target < sec_end:
        return fail(f"reset target {reset_target:#x} is outside SEC FFS file {sec_offset:#x}..{sec_end:#x}")

    # Walk the SEC FFS file's top-level sections and locate its TE image.
    te_images = []
    section_offset = sec_offset + 24
    while section_offset + 4 <= sec_end:
        section_size = int.from_bytes(data[section_offset:section_offset + 3], "little")
        section_type = data[section_offset + 3]
        section_header_size = 4
        if section_size == 0xFFFFFF:
            if section_offset + 8 > sec_end:
                break
            section_size = struct.unpack_from("<I", data, section_offset + 4)[0]
            section_header_size = 8
        if section_size < section_header_size or section_offset + section_size > sec_end:
            break
        if section_type == 0x12:  # EFI_SECTION_TE
            te_offset = section_offset + section_header_size
            if te_offset + 40 <= section_offset + section_size and data[te_offset:te_offset + 2] == b"VZ":
                te_images.append(te_offset)
        section_offset = (section_offset + section_size + 3) & ~3

    if len(te_images) != 1:
        return fail(f"expected one SEC TE image, found {len(te_images)}")
    te_offset = te_images[0]
    machine = struct.unpack_from("<H", data, te_offset + 2)[0]
    entrypoint = struct.unpack_from("<I", data, te_offset + 8)[0]
    image_base = struct.unpack_from("<Q", data, te_offset + 16)[0]
    if machine != 0xAA64:
        return fail(f"SEC TE machine is {machine:#06x}, expected AArch64 0xAA64")
    if image_base != EXPECTED_FD_BASE:
        return fail(f"SEC TE image base {image_base:#x} != configured FD base {EXPECTED_FD_BASE:#x}")
    if entrypoint != reset_target:
        return fail(f"reset target {reset_target:#x} != SEC TE entrypoint {entrypoint:#x}")

    print("FIRMWARE ENTRY AUDIT: PASS")
    print(f"Firmware volume: {fv_length:#x} bytes; header length {header_length:#x}")
    print(f"Reset vector: AArch64 B {instruction:#010x} -> FD+{reset_target:#x}")
    print(f"SEC FFS file: offset {sec_offset:#x}, size {sec_size:#x}")
    print(f"SEC TE image: offset {te_offset:#x}, machine AArch64, image base {image_base:#x}")
    print(f"SEC TE entrypoint: {entrypoint:#x} (exact match)")
    print("Limit: format/linkage checks only; no proof of Samsung boot-chain acceptance,")
    print("       required processor state, recovery path, or hardware bootability.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
