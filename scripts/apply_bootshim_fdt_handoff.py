#!/usr/bin/env python3
"""Pass the appended device FDT address to SEC in ARM64 x0."""
from __future__ import annotations

import sys
from pathlib import Path


def apply(root: Path) -> None:
    path = root / "BootShim/BootShim.S"
    source = path.read_text(encoding="utf-8")
    marker = "  // Pass the appended FDT physical address in x0 to the UEFI entry.\n"
    if marker in source:
        raise SystemExit("ERROR: BootShim FDT handoff patch is already applied")
    needle = "_Entry:\n  br    x5\n"
    replacement = (
        "_Entry:\n"
        "  // The build appends the DTB immediately after the FD in _Payload.\n"
        "  // Compute its runtime physical address and pass it in ARM64 x0.\n"
        "  adr   x0, _Payload\n"
        "  ldr   x2, =FD_SIZE\n"
        "  add   x0, x0, x2\n"
        "  br    x5\n"
    )
    if source.count(needle) != 1:
        raise SystemExit(f"ERROR: expected one BootShim entry point, found {source.count(needle)}")
    if "ldr   x6,  =FD_SIZE" not in source or "_Payload:" not in source:
        raise SystemExit("ERROR: pinned BootShim layout no longer matches the reviewed FD+DTB recipe")
    path.write_text(source.replace(needle, replacement, 1), encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} <Mu-Silicium-source-root>")
    apply(Path(sys.argv[1]))
    print("Applied BootShim handoff: x0 = runtime address of appended FDT.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
