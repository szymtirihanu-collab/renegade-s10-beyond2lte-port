#!/usr/bin/env python3
"""Static audit of the built ARM64 firmware reset-vector/SEC-file relationship.

This is a host-side format check only. It does not validate the Samsung boot
chain, TrustZone policy, processor state, or safe device recovery.
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

SEC_FILE_GUID = bytes.fromhex("03b5ff9a43e641418b9017e8588b1d35")
FV_SIGNATURE = b"_FVH"
FV_SIGNATURE_OFFSET = 0x28
FV_LENGTH_OFFSET = 0x20
FV_HEADER_LENGTH_OFFSET = 0x30


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

    if data[FV_SIGNATURE_OFFSET:FV_SIGNATURE_OFFSET + 4] != FV_SIGNATURE:
        return fail("FV signature is not at the expected reset-vector-compatible offset")

    fv_length = struct.unpack_from("<Q", data, FV_LENGTH_OFFSET)[0]
    header_length = struct.unpack_from("<H", data, FV_HEADER_LENGTH_OFFSET)[0]
    if fv_length != len(data):
        return fail(f"FV length {fv_length:#x} does not match file size {len(data):#x}")
    if header_length < 0x38 or header_length > fv_length:
        return fail(f"invalid FV header length {header_length:#x}")

    # The AArch64 reset-vector instruction at the FD base must be an
    # unconditional B (not BL). Its signed imm26 is measured in 4-byte words.
    instruction = struct.unpack_from("<I", data, 0)[0]
    if instruction & 0xFC000000 != 0x14000000:
        return fail(f"first instruction {instruction:#010x} is not AArch64 B")
    imm26 = instruction & 0x03FFFFFF
    if imm26 & (1 << 25):
        imm26 -= 1 << 26
    target = imm26 << 2

    # Locate the SEC FFS file by the FILE_GUID declared in Sec.inf. This checks
    # that the reset-vector destination is within that file's extent; it does
    # not prove the exact PE/COFF entrypoint or processor-state contract.
    hits = []
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
            hits.append((offset, size))

    if len(hits) != 1:
        return fail(f"expected one valid SEC FFS file, found {len(hits)}")

    sec_offset, sec_size = hits[0]
    if not sec_offset <= target < sec_offset + sec_size:
        return fail(
            f"reset-vector target {target:#x} is outside SEC file "
            f"{sec_offset:#x}..{sec_offset + sec_size:#x}"
        )

    print("FIRMWARE ENTRY AUDIT: PASS")
    print(f"File: {path}")
    print(f"Firmware volume: {fv_length:#x} bytes; header length {header_length:#x}")
    print(f"Reset-vector instruction: {instruction:#010x} (AArch64 B)")
    print(f"Reset-vector target offset: {target:#x}")
    print(f"SEC FFS file: offset {sec_offset:#x}, size {sec_size:#x}")
    print("Result: reset-vector branch target is inside the SEC FFS file.")
    print("Limit: this does not prove the exact SEC PE/COFF entrypoint, runtime state,")
    print("       Samsung boot-chain acceptance, or hardware bootability.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
