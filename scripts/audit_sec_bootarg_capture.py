#!/usr/bin/env python3
"""Static audit for the guarded ARM64 SEC x0 capture change."""
from __future__ import annotations

import sys
from pathlib import Path


def audit_tree(root: Path) -> None:
    asm = (root / "Silicon/Silicium/SiliciumPkg/Sec/AArch64/ModuleEntryPoint.S").read_text(encoding="utf-8")
    sec = (root / "Silicon/Silicium/SiliciumPkg/Sec/Sec.c").read_text(encoding="utf-8")
    inf = (root / "Silicon/Silicium/SiliciumPkg/Sec/Sec.inf").read_text(encoding="utf-8")

    save = asm.find("mov   x19, x0")
    platform_call = asm.find("bl    ASM_PFX (PlatformAssemblyInitialize)")
    if save < 0 or platform_call < 0 or save > platform_call:
        raise SystemExit("ERROR: incoming x0 is not saved before the first platform call")

    target = asm.find("ldr   x16, =ASM_PFX (SecEntry)")
    restore = asm.find("mov   x0, x19", target)
    call = asm.find("blr   x16", target)
    if min(target, restore, call) < 0 or not (target < restore < call):
        raise SystemExit("ERROR: captured x0 is not passed to SecEntry using a separate call-target register")

    if "SecEntry (IN UINTN BootArgument0)" not in sec or "SecMain (IN UINTN BootArgument0)" not in sec:
        raise SystemExit("ERROR: SEC C entry does not accept the captured argument")
    if "MemoryMapLib" not in inf or '#include <Library/MemoryMapLib.h>' not in sec:
        raise SystemExit("ERROR: SEC does not declare the platform memory-map library dependency")

    validator_start = sec.find("IsBootArgument0InKnownDram (")
    validator_end = sec.find("\nSTATIC\nVOID\nPrintFirmwareVersion", validator_start)
    if validator_start < 0 or validator_end < 0:
        raise SystemExit("ERROR: bounded DRAM-pointer validator is missing")
    validator = sec[validator_start:validator_end]
    for required in (
        "GetMemoryMap (&Regions, &RegionCount)",
        "EFI_RESOURCE_SYSTEM_MEMORY",
        "EFI_RESOURCE_MEMORY_RESERVED",
        "(Address & 7) != 0",
        "Address <= (RegionBase + RegionLength - 40)",
    ):
        if required not in validator:
            raise SystemExit(f"ERROR: validator is missing required bound check: {required}")
    if "((CONST UINT8 *)Address)" in validator or "*(CONST UINT" in validator:
        raise SystemExit("ERROR: validator must not dereference the untrusted boot argument")

    if "IsBootArgument0InKnownDram (BootArgument0)" not in sec:
        raise SystemExit("ERROR: SEC does not run the bounded pointer check after memory initialization")
    if "DTB identity remains unverified" not in sec or "not dereferencing" not in sec:
        raise SystemExit("ERROR: SEC diagnostics overstate the meaning of the pointer check")

    print("SEC BOOT-ARGUMENT CAPTURE AUDIT: OK")
    print("Incoming x0 saved in callee-saved x19 before platform calls.")
    print("Captured value passed to SecEntry without clobbering the call target.")
    print("Pointer checked against platform DRAM descriptors after MemoryPeim.")
    print("No untrusted pointer dereference or FDT parsing is performed.")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} <Mu-Silicium-source-root>")
    audit_tree(Path(sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
