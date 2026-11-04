#!/usr/bin/env python3
"""Read-only GitHub metadata audit for the pinned beyond2lte UEFI upstream.

This checks repository metadata and the Git tree only. It does not clone or
download source files, execute upstream scripts, build firmware, or access a
connected device.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "UPSTREAM.lock.json").read_text(encoding="utf-8"))
UPSTREAM = LOCK["uefi_upstream"]
REPOSITORY = UPSTREAM["repository"].removesuffix(".git").rstrip("/")
EXPECTED_COMMIT = UPSTREAM["commit"]
API = "https://api.github.com"


def get_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "beyond2lte-read-only-source-audit",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def main() -> int:
    owner_repo = REPOSITORY.removeprefix("https://github.com/")
    if "/" not in owner_repo:
        print(f"ERROR: unexpected GitHub repository URL: {REPOSITORY}")
        return 2

    try:
        repo = get_json(f"{API}/repos/{owner_repo}")
        commit = get_json(f"{API}/repos/{owner_repo}/commits/{EXPECTED_COMMIT}")
        tree_sha = commit["commit"]["tree"]["sha"]
        tree = get_json(
            f"{API}/repos/{owner_repo}/git/trees/{tree_sha}?recursive=1"
        )
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: upstream metadata request failed: {exc}")
        return 1

    if commit.get("sha") != EXPECTED_COMMIT:
        print("ERROR: GitHub returned a different commit than the locked revision")
        return 1
    if tree.get("truncated"):
        print("ERROR: upstream Git tree response was truncated")
        return 1

    entries = tree.get("tree", [])
    paths = [entry.get("path", "") for entry in entries]
    drivers = [
        path for path in paths
        if "/Drivers/" in path and path.lower().endswith((".c", ".h", ".inf"))
    ]
    usb_named = [
        path for path in paths
        if any(token in path.lower() for token in (
            "usb", "xhci", "ehci", "typec", "type-c", "displayport", "dwc3"
        ))
    ]
    license_paths = [
        path for path in paths
        if path.lower() in ("license", "license.md", "license.txt", "copying")
    ]
    license_declared = repo.get("license") is not None or bool(license_paths)
    permission_status = UPSTREAM.get("permission_status", "no maintainer permission recorded")

    print("UPSTREAM TREE AUDIT: OK")
    print(f"Repository: {REPOSITORY}")
    print(f"Locked commit: {EXPECTED_COMMIT}")
    print(f"Tree entries: {len(entries)}")
    print(f"Driver source/config files: {len(drivers)}")
    print("USB/Type-C/DisplayPort-named paths: " + (
        ", ".join(usb_named) if usb_named else "none found"
    ))
    print("License metadata: " + (
        "declared / license file present" if license_declared
        else "not declared in repository metadata or root tree"
    ))
    print(f"Permission record: {permission_status}")
    print("Scope: metadata and path inventory only; no source checkout or build.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
