#!/usr/bin/env python3
"""Apply and statically audit the SEC x0 capture change against pinned sources."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "UPSTREAM.lock.json").read_text(encoding="utf-8"))
PIN = LOCK["mu_silicium_reference_snapshot"]
REPO = PIN["repository"].removeprefix("https://github.com/").removesuffix(".git")
APPLIER = ROOT / "scripts/apply_sec_bootarg_capture.py"
AUDITOR = ROOT / "scripts/audit_sec_bootarg_capture.py"
SOURCES = (
    "Silicon/Silicium/SiliciumPkg/Sec/AArch64/ModuleEntryPoint.S",
    "Silicon/Silicium/SiliciumPkg/Sec/Sec.c",
    "Silicon/Silicium/SiliciumPkg/Sec/Sec.inf",
)


def fetch(path: str) -> str:
    url = f'https://raw.githubusercontent.com/{REPO}/{PIN["commit"]}/{path}'
    request = urllib.request.Request(url, headers={"User-Agent": "beyond2lte-sec-bootarg-audit"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="beyond2lte-sec-bootarg-") as temp:
        root = Path(temp)
        for relative in SOURCES:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(fetch(relative), encoding="utf-8")
        subprocess.run([sys.executable, str(APPLIER), str(root)], check=True)
        subprocess.run([sys.executable, str(AUDITOR), str(root)], check=True)
    print(f"Source transformation and audit passed for {REPO}@{PIN['commit']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
