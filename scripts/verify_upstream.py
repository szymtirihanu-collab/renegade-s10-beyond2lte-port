#!/usr/bin/env python3
"""Verify a separately obtained beyond2lte-uefi checkout against our source pin.

This is a read-only, host-side provenance check. It does not fetch, build, flash,
or communicate with a device.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "UPSTREAM.lock.json").read_text(encoding="utf-8"))
UPSTREAM = LOCK["uefi_upstream"]
EXPECTED_URL = UPSTREAM["repository"]
EXPECTED_COMMIT = UPSTREAM["commit"]
REQUIRED_FILES = (
    "README.md",
    "BUILD.md",
    "HARDWARE.md",
    "beyond2ltePkg/beyond2lte.dsc",
    "mu-silicium-overlay/Platforms/Samsung/beyond2ltePkg/DeviceBuild.py",
)


def git(path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(path), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/verify_upstream.py /path/to/beyond2lte-uefi")
        return 2

    checkout = Path(sys.argv[1]).expanduser().resolve()
    if not (checkout / ".git").exists():
        print(f"ERROR: not a Git checkout: {checkout}")
        return 1

    try:
        origin = git(checkout, "remote", "get-url", "origin")
        commit = git(checkout, "rev-parse", "HEAD")
        dirty = git(checkout, "status", "--porcelain")
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"ERROR: unable to inspect Git checkout: {exc}")
        return 1

    errors: list[str] = []
    normalized_origin = origin.removesuffix(".git").rstrip("/")
    normalized_expected = EXPECTED_URL.removesuffix(".git").rstrip("/")
    if normalized_origin != normalized_expected:
        errors.append(f"origin mismatch: expected {EXPECTED_URL}, got {origin}")
    if commit != EXPECTED_COMMIT:
        errors.append(f"commit mismatch: expected {EXPECTED_COMMIT}, got {commit}")
    if dirty:
        errors.append("working tree is modified; verify a clean source snapshot")

    for relative in REQUIRED_FILES:
        if not (checkout / relative).is_file():
            errors.append(f"missing expected file: {relative}")

    if errors:
        print("UPSTREAM CHECK: FAILED")
        print("\n".join(f"- {item}" for item in errors))
        return 1

    print("UPSTREAM CHECK: OK")
    print(f"Repository: {origin}")
    print(f"Commit: {commit}")
    print(f"Required source files: {len(REQUIRED_FILES)} present")
    print("No build or device operation was performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
