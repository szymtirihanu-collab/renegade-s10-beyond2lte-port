#!/usr/bin/env python3
"""Static audit for the BootShim appended-FDT x0 handoff."""
from __future__ import annotations

import sys
from pathlib import Path


def audit(root: Path) -> None:
    source = (root / "BootShim/BootShim.S").read_text(encoding="utf-8")
    expected = (
        "_Entry:\n"
        "  // The build appends the DTB immediately after the FD in _Payload.\n"
        "  // Compute its runtime physical address and pass it in ARM64 x0.\n"
        "  adr   x0, _Payload\n"
        "  ldr   x2, =FD_SIZE\n"
        "  add   x0, x0, x2\n"
        "  br    x5\n"
    )
    if source.count(expected) != 1:
        raise SystemExit("ERROR: BootShim does not compute and pass the appended FDT address in x0")
    if source.index("adr   x0, _Payload") > source.index("br    x5"):
        raise SystemExit("ERROR: FDT address is assigned after the branch")
    if "ldr   x6,  =FD_SIZE" not in source:
        raise SystemExit("ERROR: FD copy size and FDT offset no longer share FD_SIZE")
    print("BOOTSHIM FDT HANDOFF AUDIT: OK")
    print("x0 is computed as runtime _Payload + FD_SIZE immediately before branching to the FD.")
    print("This is the appended FDT address under the pinned FD-then-DTB package layout.")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} <Mu-Silicium-source-root>")
    audit(Path(sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
