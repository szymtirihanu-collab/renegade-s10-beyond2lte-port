#!/usr/bin/env python3
"""Run a generic AArch64 UEFI host baseline under QEMU.

This deliberately uses generic AAVMF on QEMU's generic 'virt' machine. It
never boots, writes, or modifies a physical device. Exynos firmware is
platform-specific and is not passed to QEMU's unrelated virt machine.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aavmf-code", type=Path, required=True,
                        help="Generic AArch64 AAVMF_CODE.fd")
    parser.add_argument("--qemu", default="qemu-system-aarch64")
    parser.add_argument("--seconds", type=int, default=8)
    parser.add_argument("--report", type=Path,
                        default=Path("qemu-uefi-diagnostic.json"))
    args = parser.parse_args()

    qemu = shutil.which(args.qemu)
    if not qemu:
        parser.error(f"QEMU executable not found: {args.qemu}")
    if not args.aavmf_code.is_file():
        parser.error(f"AAVMF firmware not found: {args.aavmf_code}")
    if not 3 <= args.seconds <= 60:
        parser.error("--seconds must be between 3 and 60")

    command = [
        qemu, "-machine", "virt", "-cpu", "cortex-a57", "-m", "1024",
        "-nodefaults", "-no-reboot", "-nographic",
        "-bios", str(args.aavmf_code.resolve()),
        "-serial", "stdio", "-monitor", "none",
    ]
    started = time.monotonic()
    try:
        result = subprocess.run(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=args.seconds, check=False,
        )
        output = result.stdout.decode("utf-8", "replace")
        outcome = "exited"
        return_code = result.returncode
    except subprocess.TimeoutExpired as exc:
        raw = exc.stdout or b""
        output = raw if isinstance(raw, str) else raw.decode("utf-8", "replace")
        outcome = "alive_until_timeout"
        return_code = None

    report = {
        "test": "generic_aarch64_uefi_qemu_baseline",
        "machine": "QEMU virt / cortex-a57 / 1 GiB",
        "firmware": str(args.aavmf_code.resolve()),
        "firmware_sha256": sha256(args.aavmf_code),
        "qemu": qemu,
        "duration_seconds": round(time.monotonic() - started, 2),
        "process_outcome": outcome,
        "process_return_code": return_code,
        "serial_output": output[-12000:],
        "result": "PASS_HOST_QEMU_BASELINE" if outcome == "alive_until_timeout" else "QEMU_EXITED",
        "limitations": [
            "Uses generic AAVMF, not the Exynos 9820 candidate firmware.",
            "Does not validate Samsung S-Boot acceptance or handset hardware.",
            "Does not validate Windows, UFS, USB, display, ACPI, or DTB handoff.",
            "No physical device is accessed or modified."
        ],
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items()
                      if key != "serial_output"}, indent=2))
    print(f"Report: {args.report}")
    return 0 if outcome == "alive_until_timeout" else 1


if __name__ == "__main__":
    raise SystemExit(main())
