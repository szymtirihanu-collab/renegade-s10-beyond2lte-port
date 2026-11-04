#!/usr/bin/env python3
"""Read-only content checks for the pinned upstream's USB and display evidence.

Fetches a few text sources at an immutable Git commit and checks for known
hardware-description and firmware-component markers. It never executes upstream
code, builds firmware, or communicates with a device.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "UPSTREAM.lock.json").read_text(encoding="utf-8"))
UPSTREAM = LOCK["uefi_upstream"]
REPOSITORY = UPSTREAM["repository"].removeprefix("https://github.com/").removesuffix(".git")
COMMIT = UPSTREAM["commit"]
RAW_BASE = f"https://raw.githubusercontent.com/{REPOSITORY}/{COMMIT}/"


def fetch_text(path: str) -> str:
    request = urllib.request.Request(
        RAW_BASE + path,
        headers={"User-Agent": "beyond2lte-read-only-io-audit"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def require(source: str, marker: str, label: str) -> None:
    if marker not in source:
        raise ValueError(f"missing expected source marker: {label}")


def main() -> int:
    try:
        base_dts = fetch_text("dtb-analiz/exynos9820-base.dts")
        revision_dts = fetch_text("dtb-analiz/beyond2lte-rev17.dts")
        dsc = fetch_text("beyond2ltePkg/beyond2lte.dsc")
        fdf = fetch_text("beyond2ltePkg/beyond2lte.fdf")
    except (urllib.error.URLError, TimeoutError, UnicodeDecodeError) as exc:
        print(f"ERROR: unable to fetch pinned source text: {exc}")
        return 1

    checks = [
        (base_dts, 'compatible = "samsung,exynos-dwusb";', "Exynos USB controller node"),
        (base_dts, 'compatible = "synopsys,dwc3";', "Synopsys DWC3 controller node"),
        (base_dts, 'phy-names = "usb2-phy\\0usb3-phy";', "USB2/USB3 PHY bindings"),
        (base_dts, 'compatible = "samsung,exynos-displayport";', "Exynos DisplayPort node"),
        (revision_dts, 'dr_mode = "otg";', "board overlay OTG role"),
        (revision_dts, "dp,sbu_sw_sel", "DisplayPort SBU mux property"),
        (revision_dts, "dp,usb_con_sel", "USB/DP connector mux property"),
    ]

    try:
        for source, marker, label in checks:
            require(source, marker, label)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    driver_pattern = re.compile(
        r"(?im)^\s*INF\s+[^#\n]*(?:usb|xhci|dwc3|displayport|dpdxe)[^#\n]*\.inf"
    )
    dsc_driver_entries = driver_pattern.findall(dsc)
    fdf_driver_entries = driver_pattern.findall(fdf)
    if dsc_driver_entries or fdf_driver_entries:
        print("NOTE: USB/display-related INF entries are present; review them manually.")
        for item in dsc_driver_entries + fdf_driver_entries:
            print(item.strip())
    else:
        print("UEFI component inventory: no USB/xHCI/DWC3/DisplayPort INF entries in board DSC/FDF.")

    print("USB hardware description: Exynos DWC3 + USB2/USB3 PHY markers found.")
    print("USB role description: board overlay declares OTG mode.")
    print("External display description: Exynos DisplayPort node and connector mux markers found.")
    print("Important: DTB declarations are not UEFI drivers and do not prove working I/O.")
    print("Scope: read-only source text checks; no upstream code execution or device operation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
