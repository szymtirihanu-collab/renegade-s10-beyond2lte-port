#!/usr/bin/env python3
"""Verify the SEC boot-argument patch applies to the pinned Mu-Silicium sources."""
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
PATCH = ROOT / "patches/0002-sec-capture-bootarg-and-bound-x0.patch"
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
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "add", *SOURCES], check=True)
        subprocess.run(
            ["git", "-C", str(root), "-c", "user.name=Audit", "-c",
             "user.email=audit@example.invalid", "commit", "-qm", "baseline"],
            check=True,
        )
        subprocess.run(["git", "-C", str(root), "apply", "--check", str(PATCH)], check=True)
        subprocess.run(["git", "-C", str(root), "apply", str(PATCH)], check=True)
        subprocess.run([sys.executable, str(AUDITOR), str(root)], check=True)
    print(f"Patch applies cleanly to {REPO}@{PIN['commit']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
