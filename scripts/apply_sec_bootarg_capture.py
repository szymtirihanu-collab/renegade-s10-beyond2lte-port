#!/usr/bin/env python3
"""Apply the reviewed SEC boot-argument capture change to a temporary Mu-Silicium tree."""
from __future__ import annotations

import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"ERROR: expected one {label} insertion point, found {count}")
    return text.replace(old, new, 1)


def apply(root: Path) -> None:
    sec_root = root / "Silicon/Silicium/SiliciumPkg/Sec"
    asm_path = sec_root / "AArch64/ModuleEntryPoint.S"
    sec_path = sec_root / "Sec.c"
    inf_path = sec_root / "Sec.inf"

    asm = asm_path.read_text(encoding="utf-8")
    if "mov   x19, x0" in asm:
        raise SystemExit("ERROR: SEC x0 capture appears to be already applied")
    asm = replace_once(
        asm,
        "  // Do Platform Specific Initialization\n"
        "  bl    ASM_PFX (PlatformAssemblyInitialize)\n",
        "  // Do Platform Specific Initialization\n"
        "  // Preserve the incoming ARM64 x0 argument before platform setup.\n"
        "  // x19 is callee-saved by AAPCS64 and survives the calls below.\n"
        "  // Its meaning remains opaque until SEC validates its DRAM range.\n"
        "  mov   x19, x0\n"
        "  bl    ASM_PFX (PlatformAssemblyInitialize)\n",
        "assembly entry capture",
    )
    asm = replace_once(
        asm,
        "  // Set Jump Location\n"
        "  ldr   x0, =ASM_PFX (SecEntry)\n\n"
        "  // Clear Frame Pointer\n"
        "  mov   x29, xzr\n\n"
        "  // Jump to C Code\n"
        "  blr   x0\n",
        "  // Set Jump Location\n"
        "  ldr   x16, =ASM_PFX (SecEntry)\n\n"
        "  // Clear Frame Pointer\n"
        "  mov   x29, xzr\n\n"
        "  // Pass captured incoming x0 as the first C argument.\n"
        "  mov   x0, x19\n\n"
        "  // Jump to C Code; x16 holds the call target.\n"
        "  blr   x16\n",
        "assembly SEC call",
    )
    asm_path.write_text(asm, encoding="utf-8")

    sec = sec_path.read_text(encoding="utf-8")
    if "IsBootArgument0InKnownDram" in sec:
        raise SystemExit("ERROR: SEC pointer validator appears to be already applied")
    sec = replace_once(
        sec,
        "#include <Library/MemoryMapHelperLib.h>\n",
        "#include <Library/MemoryMapHelperLib.h>\n"
        "#include <Library/MemoryMapLib.h>\n",
        "SEC memory-map include",
    )
    helper = """
//
// The initial x0 value is opaque until checked against the platform's
// reviewed physical-memory descriptors. Do not dereference it.
//
STATIC
BOOLEAN
IsBootArgument0InKnownDram (
  IN UINTN  Address
  )
{
  EFI_MEMORY_REGION_DESCRIPTOR  *Regions;
  UINT8                         RegionCount;
  UINT8                         Index;
  UINTN                         RegionBase;
  UINTN                         RegionLength;

  // A candidate FDT address is 8-byte aligned and the header is at least
  // 40 bytes. This proves only DRAM containment, not that x0 is a DTB.
  if ((Address == 0) || ((Address & 7) != 0) || (Address > MAX_UINTN - 40)) {
    return FALSE;
  }

  GetMemoryMap (&Regions, &RegionCount);
  if ((Regions == NULL) || (RegionCount == 0)) {
    return FALSE;
  }

  for (Index = 0; Index < RegionCount; Index++) {
    if ((Regions[Index].ResourceType != EFI_RESOURCE_SYSTEM_MEMORY) &&
        (Regions[Index].ResourceType != EFI_RESOURCE_MEMORY_RESERVED))
    {
      continue;
    }

    if ((Regions[Index].Address > MAX_UINTN) ||
        (Regions[Index].Length > MAX_UINTN))
    {
      continue;
    }

    RegionBase   = (UINTN)Regions[Index].Address;
    RegionLength = (UINTN)Regions[Index].Length;
    if ((RegionLength < 40) || (RegionBase > MAX_UINTN - RegionLength)) {
      continue;
    }

    if ((Address >= RegionBase) &&
        (Address <= (RegionBase + RegionLength - 40)))
    {
      return TRUE;
    }
  }

  return FALSE;
}

"""
    sec = replace_once(sec, '#include "Sec.h"\n', '#include "Sec.h"\n' + helper, "SEC range validator")
    sec = replace_once(sec, "SecMain (VOID)", "SecMain (IN UINTN BootArgument0)", "SecMain parameter")
    sec = replace_once(
        sec,
        "  // Initialize Memory\n"
        "  Status = InitializeMemory ();\n"
        "  if (EFI_ERROR (Status)) {\n"
        "    return;\n"
        "  }\n\n"
        "  // Build CPU HOB\n",
        "  // Initialize Memory\n"
        "  Status = InitializeMemory ();\n"
        "  if (EFI_ERROR (Status)) {\n"
        "    return;\n"
        "  }\n\n"
        "  // MemoryPeim has established the platform memory descriptors. Check\n"
        "  // only containment; do not dereference or parse this untrusted value.\n"
        "  if (IsBootArgument0InKnownDram (BootArgument0)) {\n"
        "    DEBUG ((EFI_D_INFO, \"SEC: incoming x0=0x%lx is inside a known DRAM region; DTB identity remains unverified.\\n\", (UINT64)BootArgument0));\n"
        "  } else {\n"
        "    DEBUG ((EFI_D_WARN, \"SEC: incoming x0=0x%lx is not a validated DRAM pointer; not dereferencing.\\n\", (UINT64)BootArgument0));\n"
        "  }\n\n"
        "  // Build CPU HOB\n",
        "post-MemoryPeim pointer check",
    )
    sec = replace_once(sec, "SecEntry (VOID)", "SecEntry (IN UINTN BootArgument0)", "SecEntry parameter")
    sec = replace_once(sec, "  SecMain ();", "  SecMain (BootArgument0);", "SecMain argument forwarding")
    sec_path.write_text(sec, encoding="utf-8")

    inf = inf_path.read_text(encoding="utf-8")
    inf = replace_once(inf, "  MemoryMapHelperLib\n", "  MemoryMapHelperLib\n  MemoryMapLib\n", "SEC library dependency")
    inf_path.write_text(inf, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} <Mu-Silicium-source-root>")
    apply(Path(sys.argv[1]))
    print("Applied guarded SEC x0 capture and non-dereferencing DRAM range check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
