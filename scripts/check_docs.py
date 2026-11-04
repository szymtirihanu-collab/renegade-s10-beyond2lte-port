#!/usr/bin/env python3
"""Check that relative Markdown links in project documentation resolve."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")
errors = []

for md in ROOT.rglob("*.md"):
    if ".git" in md.parts:
        continue
    text = md.read_text(encoding="utf-8")
    for target in LINK_RE.findall(text):
        target = target.strip().split("#", 1)[0]
        if not target or "://" in target or target.startswith(("mailto:", "#")):
            continue
        candidate = (md.parent / target).resolve()
        if not candidate.exists():
            errors.append(f"{md.relative_to(ROOT)}: missing link target {target}")

if errors:
    print("\n".join(errors))
    sys.exit(1)

required = [
    "README.md",
    "docs/PORTING_STATUS.md",
    "docs/ARCHITECTURE.md",
    "docs/REFERENCES.md",
    "docs/VALIDATION.md",
    "docs/BOOT_FLOW.md",
    "docs/HARDWARE_INVENTORY.md",
]
missing = [p for p in required if not (ROOT / p).is_file()]
if missing:
    print("Missing required project documents: " + ", ".join(missing))
    sys.exit(1)

print("Documentation structure and relative links: OK")
