#!/usr/bin/env python3
"""Apply and audit the BootShim FDT handoff against the pinned Mu-Silicium source."""
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
SOURCE = "BootShim/BootShim.S"


def main() -> int:
    url = f'https://raw.githubusercontent.com/{REPO}/{PIN["commit"]}/{SOURCE}'
    request = urllib.request.Request(url, headers={"User-Agent": "beyond2lte-bootshim-fdt-audit"})
    with urllib.request.urlopen(request, timeout=30) as response:
        source = response.read().decode("utf-8")
    with tempfile.TemporaryDirectory(prefix="beyond2lte-bootshim-fdt-") as temp:
        root = Path(temp)
        target = root / SOURCE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
        subprocess.run([sys.executable, str(ROOT / "scripts/apply_bootshim_fdt_handoff.py"), str(root)], check=True)
        subprocess.run([sys.executable, str(ROOT / "scripts/audit_bootshim_fdt_handoff.py"), str(root)], check=True)
    print(f"BootShim transformation and audit passed for {REPO}@{PIN['commit']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
