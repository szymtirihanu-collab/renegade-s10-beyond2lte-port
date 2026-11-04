#!/usr/bin/env python3
"""Static audit of the Android boot-image wrapper and embedded UEFI payload."""
from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

ANDROID_MAGIC = b"ANDROID!"
FDT_MAGIC = 0xD00DFEED
EXPECTED_HEADER_VERSION = 1
EXPECTED_PAGE_SIZE = 2048
EXPECTED_KERNEL_ADDR = 0x10008000
EXPECTED_RAMDISK_ADDR = 0x11000000
EXPECTED_FD_BASE = 0xC9000000
EXPECTED_FD_SIZE = 0x400000
BOOTSHIM_SIZE = 112


def fail(message: str) -> int:
    print(f"ANDROID BOOT PACKAGE AUDIT: FAIL: {message}")
    return 1


def align(value: int, boundary: int) -> int:
    return (value + boundary - 1) & ~(boundary - 1)


def main() -> int:
    if len(sys.argv) != 3:
        print(f"Usage: {Path(sys.argv[0]).name} Mu-beyond2lte.img SILICIUM_UEFI.fd")
        return 2

    image_path, fd_path = map(Path, sys.argv[1:])
    image = image_path.read_bytes()
    fd = fd_path.read_bytes()

    if len(image) < EXPECTED_PAGE_SIZE or image[:8] != ANDROID_MAGIC:
        return fail("missing Android boot-image magic/header")
    if len(fd) != EXPECTED_FD_SIZE:
        return fail(f"FD size {len(fd):#x} != configured size {EXPECTED_FD_SIZE:#x}")

    # Android boot image v0 header fields, followed by the v1 extension.
    kernel_size, kernel_addr, ramdisk_size, ramdisk_addr, second_size, second_addr, tags_addr, page_size, header_version, os_version = struct.unpack_from("<10I", image, 8)
    if header_version != EXPECTED_HEADER_VERSION:
        return fail(f"header version {header_version} != expected v1")
    if page_size != EXPECTED_PAGE_SIZE:
        return fail(f"page size {page_size} != expected {EXPECTED_PAGE_SIZE}")
    if kernel_addr != EXPECTED_KERNEL_ADDR:
        return fail(f"kernel load address {kernel_addr:#x} != expected {EXPECTED_KERNEL_ADDR:#x}")
    if ramdisk_addr != EXPECTED_RAMDISK_ADDR:
        return fail(f"ramdisk load address {ramdisk_addr:#x} != expected {EXPECTED_RAMDISK_ADDR:#x}")
    if second_size != 0:
        return fail(f"unexpected second-stage payload size {second_size}")
    recovery_dtbo_size = struct.unpack_from("<I", image, 1632)[0]
    recovery_dtbo_offset = struct.unpack_from("<Q", image, 1636)[0]
    header_size = struct.unpack_from("<I", image, 1644)[0]
    if header_size != 1648:
        return fail(f"v1 header_size {header_size} != 1648")
    if recovery_dtbo_size or recovery_dtbo_offset:
        return fail("unexpected recovery-DTBO payload in v1 header")

    kernel_offset = page_size
    kernel_end = kernel_offset + kernel_size
    if kernel_size <= BOOTSHIM_SIZE + EXPECTED_FD_SIZE or kernel_end > len(image):
        return fail("kernel payload size/extent is invalid")
    ramdisk_offset = align(kernel_end, page_size)
    ramdisk_end = ramdisk_offset + ramdisk_size
    if ramdisk_end > len(image) or align(ramdisk_end, page_size) != len(image):
        return fail("ramdisk/file extent does not match Android page alignment")
    ramdisk = image[ramdisk_offset:ramdisk_end]
    if ramdisk != b"dummy":
        return fail(f"unexpected ramdisk payload {ramdisk!r}; expected 5-byte placeholder")

    payload = image[kernel_offset:kernel_end]
    # BootShim's ARM64 Image header and FD copy parameters.
    if payload[56:60] != b"ARM\x64":
        return fail("BootShim ARM64 Image magic is missing at payload offset 56")
    shim_fd_base, shim_fd_size = struct.unpack_from("<QQ", payload, 8)
    if shim_fd_base != EXPECTED_FD_BASE or shim_fd_size != EXPECTED_FD_SIZE:
        return fail(f"BootShim FD copy range is {shim_fd_base:#x}/{shim_fd_size:#x}, expected {EXPECTED_FD_BASE:#x}/{EXPECTED_FD_SIZE:#x}")

    embedded_fd_offset = BOOTSHIM_SIZE
    embedded_fd = payload[embedded_fd_offset:embedded_fd_offset + EXPECTED_FD_SIZE]
    if embedded_fd != fd:
        return fail("embedded FD bytes do not exactly match SILICIUM_UEFI.fd")

    fdt_offset = embedded_fd_offset + EXPECTED_FD_SIZE
    fdt = payload[fdt_offset:]
    if len(fdt) < 40:
        return fail("appended FDT is shorter than its header")
    fields = struct.unpack_from(">10I", fdt, 0)
    magic, total_size, off_struct, off_strings, off_mem_rsvmap, version, last_comp, boot_cpuid, size_strings, size_struct = fields
    if magic != FDT_MAGIC:
        return fail("appended FDT magic mismatch")
    if total_size != len(fdt):
        return fail(f"FDT totalsize {total_size} != appended FDT length {len(fdt)}")
    if version < 16 or last_comp > version:
        return fail(f"unsupported/inconsistent FDT version {version}/{last_comp}")
    if off_struct < 40 or off_struct + size_struct > total_size:
        return fail("FDT structure block is out of bounds")
    if off_strings < 40 or off_strings + size_strings > total_size:
        return fail("FDT strings block is out of bounds")
    if off_mem_rsvmap < 40 or off_mem_rsvmap % 8 or off_mem_rsvmap + 16 > total_size:
        return fail("FDT reservation map offset is invalid")
    # Reservation map is a sequence of 64-bit address/size pairs terminated by zero/zero.
    pos = off_mem_rsvmap
    while pos + 16 <= total_size:
        address, size = struct.unpack_from(">QQ", fdt, pos)
        pos += 16
        if address == 0 and size == 0:
            break
    else:
        return fail("FDT reservation map has no terminator")

    print("ANDROID BOOT PACKAGE AUDIT: PASS")
    print(f"Image: {len(image)} bytes; Android boot header v{header_version}; page {page_size}")
    print(f"Kernel payload: {kernel_size} bytes at {kernel_addr:#x}; BootShim {BOOTSHIM_SIZE} bytes")
    print(f"Embedded UEFI FD: {EXPECTED_FD_SIZE} bytes at payload+{embedded_fd_offset}; SHA256 {hashlib.sha256(fd).hexdigest()}")
    print(f"Appended FDT: {len(fdt)} bytes; version {version}; structure/string blocks in bounds")
    print("Ramdisk: 5-byte 'dummy' placeholder; not a usable initramfs")
    print("Limit: packaging/structure checks only; no proof Samsung accepts this image or passes the required CPU state.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
