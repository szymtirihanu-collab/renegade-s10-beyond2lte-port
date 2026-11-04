#!/usr/bin/env python3
"""Run a QEMU AArch64 UEFI *host baseline* and audit a candidate package.

This deliberately boots generic AAVMF on QEMU's generic 'virt' machine. It
never boots, writes, or modifies a physical device. The Exynos firmware is
platform-specific and is not passed to QEMU's unrelated virt machine.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--aavmf-code", type=Path, required=True,
                   help="Generic AArch64 AAVMF_CODE.fd for the QEMU baseline")
    p.add_argument("--qemu", default="qemu-system-aarch64")
    p.add_argument("--seconds", type=int, default=8,
                   help="How long to keep the generic UEFI VM alive (default: 8)")
    p.add_argument("--report", type=Path, default=Path("qemu-uefi-diagnostic.json"))
    args = p.parse_args()

    qemu = shutil.which(args.qemu)
    if not qemu:
        p.error(f"QEMU executable not found: {args.qemu}")
    if not args.aavmf_code.is_file():
        p.error(f"AAVMF firmware not found: {args.aavmf_code}")
    if args.seconds < 3 or args.seconds > 60:
        p.error("--seconds must be between 3 and 60")

    with tempfile.TemporaryDirectory(prefix="beyond2lte-qemu-") as td:
        vars_path = Path(td) / "AAVMF_VARS.fd"
        # A writable variable store is kept in a temporary directory and
        # discarded after the test.
        vars_path.write_bytes(bytes(args.aavmf_code.stat().st_size))
        cmd = [
            qemu, "-machine", "virt", "-cpu", "cortex-a57", "-m", "1024",
            "-nodefaults", "-no-reboot", "-nographic",
            "-drive", f"if=pflash,format=raw,readonly=on,file={args.aavmf_code}",
            "-drive", f"if=pflash,format=raw,file={vars_path}",
            "-serial", "stdio", "-monitor", "none",
        ]
        started = time.monotonic()
        try:
            proc = subprocess.run(
                cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, timeout=args.seconds, check=False,
            )
            output = proc.stdout.decode("utf-8", "replace")
            outcome = "exited"
            return_code = proc.returncode
        except subprocess.TimeoutExpired as exc:
            raw = exc.stdout or b""
            if isinstance(raw, str):
                output = raw
            else:
                output = raw.decode("utf-8", "replace")
            outcome = "alive_until_timeout"
            return_code = None
        elapsed = round(time.monotonic() - started, 2)

    report = {
        "test": "generic_aarch64_uefi_qemu_baseline",
        "machine": "QEMU virt / cortex-a57 / 1 GiB",
        "firmware": str(args.aavmf_code.resolve()),
        "firmware_sha256": sha256(args.aavmf_code),
        "qemu": qemu,
        "duration_seconds": elapsed,
        "process_outcome": outcome,
        "process_return_code": return_code,
        "serial_output": output[-12000:],
        "result": "PASS_HOST_QEMU_BASELINE" if outcome == "alive_until_timeout" else "QEMU_EXITED",
        "limitations": [
            "This uses generic AAVMF, not the Exynos 9820 candidate firmware.",
            "A QEMU virt boot does not validate Samsung S-Boot acceptance or handset hardware.",
            "This test does not validate Windows, UFS, USB, display, ACPI, or device-tree handoff.",
            "No physical device is accessed or modified."
        ],
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "serial_output"}, indent=2))
    print(f"Report: {args.report}")
    return 0 if outcome == "alive_until_timeout" else 1


if __name__ == "__main__":
    raise SystemExit(main())
