#!/usr/bin/env python3
"""Build a FAT32 Windows ARM64 installation-media filesystem image.

Host-side packaging only. This script never writes to a phone, changes
partitions, installs Windows, or proves the handset boot path.
"""
from __future__ import annotations
import argparse, hashlib, json, math, shutil, struct, subprocess, sys, tempfile
from pathlib import Path
from datetime import datetime, timezone

GIB = 1024 ** 3
FAT32_MAX_FILE = 4 * 1024**3 - 1
DEFAULT_ISO = "~/Windows11_Client_arm64_en-us_26300_9457.iso"

def run(args, capture=False):
    try:
        return subprocess.run(args, check=True, text=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.STDOUT if capture else None)
    except FileNotFoundError as e:
        raise RuntimeError(f"Required command not found: {args[0]}") from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command failed ({e.returncode}): {' '.join(args)}\n{e.stdout or ''}") from e

def require_tools():
    missing = [x for x in ("xorriso", "mformat", "mcopy", "mdir") if not shutil.which(x)]
    if missing:
        raise RuntimeError("Missing tools: " + ", ".join(missing) +
            ". Install xorriso and mtools on openSUSE.")

def pe_machine(path):
    with path.open("rb") as f:
        if f.read(2) != b"MZ": raise RuntimeError(f"Not a PE executable: {path}")
        f.seek(0x3c); raw = f.read(4)
        if len(raw) != 4: raise RuntimeError(f"Truncated DOS header: {path}")
        f.seek(struct.unpack("<I", raw)[0])
        if f.read(4) != b"PE\0\0": raise RuntimeError(f"Missing PE signature: {path}")
        raw = f.read(2)
        if len(raw) != 2: raise RuntimeError(f"Truncated PE header: {path}")
        return struct.unpack("<H", raw)[0]

def find_ci(root, rel):
    cur = root
    for part in Path(rel).parts:
        if not cur.is_dir(): return None
        matches = [p for p in cur.iterdir() if p.name.casefold() == part.casefold()]
        if not matches: return None
        cur = matches[0]
    return cur

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b""): h.update(b)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default=DEFAULT_ISO)
    ap.add_argument("--source-dir", help="Mounted Windows ISO directory (e.g. /mnt/winiso); copied into staging before processing")
    ap.add_argument("--output", default="./beyond2lte-windows11-media")
    ap.add_argument("--size-gib", type=int, default=16)
    ap.add_argument("--uefi-image", help="Optional existing Mu-beyond2lte.img to copy beside the ESP")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    iso, out = Path(a.iso).expanduser().resolve(), Path(a.output).expanduser().resolve()
    source_dir = Path(a.source_dir).expanduser().resolve() if a.source_dir else None
    if not iso.is_file(): raise RuntimeError(f"ISO not found: {iso}")
    if source_dir and not source_dir.is_dir(): raise RuntimeError(f"Source directory not found: {source_dir}")
    if not 8 <= a.size_gib <= 512: raise RuntimeError("--size-gib must be 8..512")
    if out.exists() and not a.force: raise RuntimeError(f"Output exists: {out}; choose another path or use --force")
    if a.uefi_image and not Path(a.uefi_image).expanduser().is_file():
        raise RuntimeError(f"UEFI image not found: {a.uefi_image}")
    require_tools()
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="beyond2lte-media-") as td:
        stage = Path(td) / "iso"; stage.mkdir()
        if source_dir:
            print(f"[1/6] Copying mounted Windows media from {source_dir} into staging")
            shutil.copytree(source_dir, stage, dirs_exist_ok=True)
        else:
            print("[1/6] Extracting ISO")
            run(["xorriso", "-osirrox", "on", "-indev", str(iso), "-extract", "/", str(stage)])
        # ISO9660/UDF mounts are read-only, and copytree preserves their
        # read-only mode bits. Normalize the private staging tree so wimlib
        # can create split SWM files and mtools can read every directory.
        for node in (stage, *stage.rglob("*")):
            mode = node.stat().st_mode
            node.chmod(mode | (0o700 if node.is_dir() else 0o200))
        boot = find_ci(stage, "EFI/BOOT/BOOTAA64.EFI")
        if not boot: raise RuntimeError("ISO lacks EFI/BOOT/BOOTAA64.EFI; not ARM64 UEFI installation media")
        machine = pe_machine(boot)
        if machine != 0xAA64: raise RuntimeError(f"EFI loader is not AArch64 (PE machine 0x{machine:04x})")
        if not find_ci(stage, "sources/boot.wim"): raise RuntimeError("ISO lacks sources/boot.wim")
        iw, esd = find_ci(stage, "sources/install.wim"), find_ci(stage, "sources/install.esd")
        if not iw and not esd: raise RuntimeError("ISO lacks sources/install.wim or install.esd")
        print("[2/6] Checking FAT32 limits")
        for p in list(stage.rglob("*")):
            if not p.is_file() or p.stat().st_size <= FAT32_MAX_FILE: continue
            if iw and p == iw:
                print("      Splitting install.wim into FAT32-compatible SWM files")
                # Read-only ISO mounts expose files without write permission;
                # copytree preserves those mode bits. wimlib needs a writable
                # staging directory to create install.swm beside install.wim.
                p.chmod(p.stat().st_mode | 0o200)
                p.parent.chmod(p.parent.stat().st_mode | 0o200)
                run(["wimlib-imagex", "split", str(p), str(p.with_name("install.swm")), "3800"])
                p.unlink()
            elif esd and p == esd:
                raise RuntimeError("install.esd is over 4 GiB; this tool cannot split ESD files. Use media with install.wim or a smaller ESD.")
            else: raise RuntimeError(f"File exceeds FAT32 4 GiB limit: {p.relative_to(stage)}")
        total = sum(p.stat().st_size for p in stage.rglob("*") if p.is_file())
        needed = math.ceil((total * 1.15 + 512 * 1024**2) / GIB)
        if a.size_gib < needed: raise RuntimeError(f"Need about {needed} GiB; rerun with --size-gib {needed}")
        print("[3/6] Creating FAT32 filesystem image")
        if out.exists(): shutil.rmtree(out)
        out.mkdir(parents=True)
        esp = out / "windows11-arm64-esp.img"
        with esp.open("wb") as f: f.truncate(a.size_gib * GIB)
        run(["mformat", "-i", str(esp), "-F", "-v", "WIN11ARM64", "::"])
        print("[4/6] Copying Windows setup files")
        run(["mcopy", "-s", "-i", str(esp), *map(str, sorted(stage.iterdir())), "::/"])
        print("[5/6] Verifying copied boot files")
        listing = run(["mdir", "-b", "-i", str(esp), "::/EFI/BOOT"], capture=True).stdout
        entries = {Path(line.strip()).name.casefold() for line in listing.splitlines() if line.strip()}
        if "bootaa64.efi" not in entries:
            raise RuntimeError("BOOTAA64.EFI missing after copy; EFI/BOOT entries reported by mtools: " + repr(listing))
        run(["mdir", "-i", str(esp), "::/SOURCES"], capture=True)
        fwcopy = None
        if a.uefi_image:
            fwcopy = out / "Mu-beyond2lte.img"
            shutil.copy2(Path(a.uefi_image).expanduser().resolve(), fwcopy)
        print("[6/6] Writing hashes and report")
        split = find_ci(stage, "sources/install.swm") is not None
        report = {
          "created_utc": datetime.now(timezone.utc).isoformat(),
          "target": "Samsung Galaxy S10+ SM-G975F / beyond2lte / Exynos 9820",
          "source_iso": str(iso), "source_iso_size": iso.stat().st_size, "source_iso_sha256": digest(iso),
          "efi_loader": f"EFI/BOOT/{boot.name}", "efi_machine": "AArch64 (0xAA64)",
          "boot_image": "sources/boot.wim",
          "install_payload": "split install*.swm" if split else ("sources/install.wim" if iw and iw.exists() else "sources/install.esd"),
          "esp_image": esp.name, "esp_size": esp.stat().st_size, "esp_sha256": digest(esp),
          "optional_uefi_image_copy": fwcopy.name if fwcopy else None,
          "limitations": [
            "This is a FAT32 Windows ARM64 installation-media filesystem image, not a handset disk layout.",
            "No phone partitions are created, modified, or written.",
            "The exact SM-G975F bootloader acceptance and handoff remain unverified.",
            "The existing port reports an early Windows reset; packaging does not fix it.",
            "No Exynos Windows drivers or corrected ACPI tables are injected.",
            "Media validation does not prove Windows Setup or Windows will boot on the handset."
          ]}
        (out / "media-report.json").write_text(json.dumps(report, indent=2) + "\n")
        (out / "README.txt").write_text(
          "Windows 11 ARM64 media package for beyond2lte research\n"
          "=====================================================\n\n"
          "windows11-arm64-esp.img contains Windows ARM64 setup files on FAT32.\n"
          "It is not a phone flash image or a standalone boot chain.\n"
          "Mu-beyond2lte.img is included only if --uefi-image was supplied.\n"
          "Read media-report.json. This tool performs no device-writing operation.\n")
    print(f"DONE: {out}\nESP: {out / 'windows11-arm64-esp.img'}")
    print("This package is not proof of a bootable or installable SM-G975F port.")
    return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr); raise SystemExit(2)
