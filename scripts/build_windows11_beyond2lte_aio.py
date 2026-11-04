#!/usr/bin/env python3
"""Build a GPT-partitioned Windows 11 ARM64 media bundle for beyond2lte.

This is a host-side packager only. It does not flash, repartition, unlock,
reboot, or otherwise write to a phone. The generated GPT image is Windows
installation media, not a complete internal UFS layout or a proven phone image.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import struct
import subprocess
import sys
import tempfile
import uuid
import zlib
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_ISO = "~/Windows11_Client_arm64_en-us_26300_9457.iso"
SECTOR = 512
ESP_START_LBA = 2048
GPT_ENTRIES = 128
GPT_ENTRY_SIZE = 128
ESP_TYPE_GUID = uuid.UUID("C12A7328-F81F-11D2-BA4B-00A0C93EC93B")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(args: list[str], capture: bool = False) -> str:
    try:
        p = subprocess.run(args, check=True, text=True,
                           stdout=subprocess.PIPE if capture else None,
                           stderr=subprocess.STDOUT if capture else None)
        return p.stdout or ""
    except FileNotFoundError as e:
        raise RuntimeError(f"Required program not found: {args[0]}") from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command failed ({e.returncode}): {' '.join(args)}\n{e.stdout or ''}") from e


def make_gpt_disk(fat_image: Path, disk_image: Path) -> dict:
    size = fat_image.stat().st_size
    if size % SECTOR:
        raise RuntimeError("FAT image size is not sector-aligned")
    part_sectors = size // SECTOR
    total_sectors = ESP_START_LBA + part_sectors + 34
    last_lba = total_sectors - 1
    first_usable = 34
    last_usable = total_sectors - 34
    part_first = ESP_START_LBA
    part_last = part_first + part_sectors - 1
    if part_last > last_usable:
        raise RuntimeError("ESP would overlap backup GPT metadata")

    entries = bytearray(GPT_ENTRIES * GPT_ENTRY_SIZE)
    unique = uuid.uuid4()
    entry = struct.pack(
        "<16s16sQQQ72s",
        ESP_TYPE_GUID.bytes_le, unique.bytes_le, part_first, part_last,
        0, b"\0" * 72
    )
    entries[:GPT_ENTRY_SIZE] = entry
    entries_crc = zlib.crc32(entries) & 0xffffffff
    disk_guid = uuid.uuid4()

    def header(current: int, backup: int, entries_lba: int) -> bytes:
        raw = struct.pack(
            "<8sIIIIQQQQ16sQIII",
            b"EFI PART", 0x00010000, 92, 0, 0,
            current, backup, first_usable, last_usable,
            disk_guid.bytes_le, entries_lba, GPT_ENTRIES,
            GPT_ENTRY_SIZE, entries_crc
        )
        crc = zlib.crc32(raw) & 0xffffffff
        return raw[:16] + struct.pack("<I", crc) + raw[20:] + b"\0" * (SECTOR - len(raw))

    disk_image.parent.mkdir(parents=True, exist_ok=True)
    with disk_image.open("wb") as f:
        f.truncate(total_sectors * SECTOR)
    with disk_image.open("r+b") as f:
        # Protective MBR.
        mbr = bytearray(SECTOR)
        mbr[446:462] = struct.pack(
            "<B3sB3sII", 0, b"\0\0\0", 0xEE, b"\xff\xff\xff",
            1, min(total_sectors - 1, 0xffffffff)
        )
        mbr[510:512] = b"\x55\xaa"
        f.seek(0); f.write(mbr)
        # Primary GPT.
        f.seek(SECTOR); f.write(header(1, last_lba, 2))
        f.seek(2 * SECTOR); f.write(entries)
        # ESP payload.
        f.seek(part_first * SECTOR)
        with fat_image.open("rb") as src:
            shutil.copyfileobj(src, f, 8 * 1024 * 1024)
        # Backup GPT entries and header.
        backup_entries_lba = total_sectors - 33
        f.seek(backup_entries_lba * SECTOR); f.write(entries)
        f.seek(last_lba * SECTOR)
        f.write(header(last_lba, 1, backup_entries_lba))

    return {
        "partition_table": "GPT",
        "partition": "EFI System Partition",
        "partition_type_guid": str(ESP_TYPE_GUID),
        "partition_start_lba": part_first,
        "partition_end_lba": part_last,
        "partition_bytes": size,
        "disk_bytes": total_sectors * SECTOR,
        "disk_guid": str(disk_guid),
        "esp_unique_guid": str(unique),
        "disk_sha256": sha256(disk_image),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default=DEFAULT_ISO)
    ap.add_argument("--uefi-image", required=True,
                    help="Existing Mu-beyond2lte.img from the pinned host build")
    ap.add_argument("--output", default="./beyond2lte-windows11-aio")
    ap.add_argument("--size-gib", type=int, default=16,
                    help="FAT32 ESP size; increase if the ISO contents need more space")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    iso = Path(args.iso).expanduser().resolve()
    uefi = Path(args.uefi_image).expanduser().resolve()
    out = Path(args.output).expanduser().resolve()
    if not iso.is_file():
        raise RuntimeError(f"Windows ISO not found: {iso}")
    if not uefi.is_file():
        raise RuntimeError(f"UEFI image not found: {uefi}")
    if args.size_gib < 8 or args.size_gib > 512:
        raise RuntimeError("--size-gib must be between 8 and 512 GiB")
    if out.exists() and not args.force:
        raise RuntimeError(f"Output exists: {out}; choose another path or use --force")

    with uefi.open("rb") as f:
        if f.read(8) != b"ANDROID!":
            raise RuntimeError("UEFI launcher is not the expected Android boot-image container (ANDROID! magic)")
    run(["xorriso", "-version"], capture=True)
    run(["mformat", "-V"], capture=True)
    run(["mcopy", "-V"], capture=True)
    run(["mdir", "-V"], capture=True)

    script_dir = Path(__file__).resolve().parent
    media_builder = script_dir / "make_windows_arm64_media.py"
    if not media_builder.is_file():
        raise RuntimeError(f"Missing media builder: {media_builder}")

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    with tempfile.TemporaryDirectory(prefix="beyond2lte-aio-") as td:
        temp_out = Path(td) / "media"
        print("[1/5] Building and validating Windows ARM64 FAT32 setup media")
        run([
            sys.executable, str(media_builder),
            "--iso", str(iso),
            "--output", str(temp_out),
            "--size-gib", str(args.size_gib),
            "--uefi-image", str(uefi),
        ])
        fat = temp_out / "windows11-arm64-esp.img"
        if not fat.is_file():
            raise RuntimeError("Media builder did not produce its FAT32 image")

        print("[2/5] Creating GPT disk image with an EFI System Partition")
        disk = out / "windows11-arm64-gpt-disk.img"
        gpt = make_gpt_disk(fat, disk)

        print("[3/5] Copying source ISO and device UEFI launcher")
        shutil.copy2(iso, out / iso.name)
        shutil.copy2(uefi, out / "Mu-beyond2lte.img")
        # Preserve the FAT-only image for independent inspection.
        shutil.copy2(fat, out / "windows11-arm64-esp-fat32.img")

    print("[4/5] Verifying GPT signatures and expected ARM64 boot path")
    with disk.open("rb") as f:
        mbr = f.read(SECTOR)
        f.seek(SECTOR)
        primary = f.read(SECTOR)
        f.seek(gpt["partition_start_lba"] * SECTOR)
        boot_sector = f.read(SECTOR)
        f.seek(gpt["partition_end_lba"] * SECTOR)
        _ = f.read(SECTOR)
    if mbr[510:512] != b"\x55\xaa" or primary[:8] != b"EFI PART":
        raise RuntimeError("GPT/MBR signature verification failed")
    if boot_sector[510:512] != b"\x55\xaa":
        raise RuntimeError("ESP boot-sector signature missing")
    # Recheck the actual Windows EFI loader in the FAT image via mtools.
    run(["mdir", "-i", f"{disk}@@{gpt['partition_start_lba'] * SECTOR}", "::/EFI/BOOT"])
    run(["mdir", "-i", f"{disk}@@{gpt['partition_start_lba'] * SECTOR}", "::/SOURCES"])

    print("[5/5] Writing bundle manifest")
    files = {}
    for p in sorted(out.iterdir()):
        if p.is_file():
            files[p.name] = {"size": p.stat().st_size, "sha256": sha256(p)}
    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "target": "Samsung Galaxy S10+ SM-G975F / beyond2lte / Exynos 9820",
        "source_iso": {"name": iso.name, "size": iso.stat().st_size, "sha256": sha256(iso)},
        "uefi_launcher": {"name": "Mu-beyond2lte.img", "size": uefi.stat().st_size, "sha256": sha256(uefi)},
        "windows_media_disk": {"name": disk.name, **gpt},
        "files": files,
        "validation": [
            "Windows ARM64 setup media was checked by make_windows_arm64_media.py",
            "GPT primary header and protective MBR signatures checked",
            "ESP FAT32 boot and sources directories checked with mtools",
            "The ISO's ARM64 EFI loader was checked by the media builder",
        ],
        "not_validated": [
            "Samsung bootloader acceptance or exact entry register state",
            "Whether this UEFI build discovers this GPT image as a UFS disk",
            "Whether Windows Boot Manager or Windows Setup runs on this handset",
            "Exynos Windows drivers, ACPI resource descriptions, and early kernel reset",
            "Any physical-device boot or installation",
        ],
        "safety": "Host-side packaging only. No device is accessed and no phone storage is written."
    }
    (out / "bundle-report.json").write_text(json.dumps(report, indent=2) + "\n")
    (out / "README.txt").write_text(
        "beyond2lte Windows 11 ARM64 AIO bundle\n"
        "======================================\n\n"
        "This directory contains the source ISO, the existing UEFI launcher,\n"
        "a GPT disk image with one FAT32 EFI System Partition, and SHA-256\n"
        "validation metadata.\n\n"
        "This is not a complete internal-phone disk layout. The GPT image is\n"
        "Windows installation media. The UEFI launcher is a separate Android\n"
        "boot-image container. No flashing or phone-storage writes are done.\n\n"
        "Read bundle-report.json before any further device-specific work.\n"
    )
    print(f"SUCCESS: bundle created at {out}")
    print(f"GPT media image: {disk}")
    print("No phone was accessed or modified. This does not prove handset bootability.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
