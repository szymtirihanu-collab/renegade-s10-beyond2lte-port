#!/usr/bin/env python3
"""Verify the pinned Mu-Silicium reference commit and its submodule gitlinks."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "UPSTREAM.lock.json").read_text(encoding="utf-8"))
PIN = LOCK["mu_silicium_reference_snapshot"]
API = "https://api.github.com"
REPO = PIN["repository"].removeprefix("https://github.com/").removesuffix(".git")


def get_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "beyond2lte-mu-snapshot-audit",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def main() -> int:
    try:
        metadata = get_json(f"{API}/repos/{REPO}")
        commit = get_json(f"{API}/repos/{REPO}/commits/{PIN['commit']}")
        tree_sha = commit["commit"]["tree"]["sha"]
        tree = get_json(f"{API}/repos/{REPO}/git/trees/{tree_sha}?recursive=1")
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: unable to verify Mu-Silicium snapshot: {exc}")
        return 1

    if commit.get("sha") != PIN["commit"]:
        print("ERROR: Mu-Silicium commit does not match UPSTREAM.lock.json")
        return 1
    if tree.get("truncated"):
        print("ERROR: Mu-Silicium tree response was truncated")
        return 1
    if (metadata.get("license") or {}).get("spdx_id") != "BSD-2-Clause":
        print("ERROR: Mu-Silicium repository license metadata changed; review manually")
        return 1

    actual = {
        entry["path"]: entry["sha"]
        for entry in tree.get("tree", [])
        if entry.get("mode") == "160000" or entry.get("type") == "commit"
    }
    expected = {
        item["path"]: item["commit"]
        for item in PIN["submodules"]
    }
    if actual != expected:
        print("ERROR: Mu-Silicium submodule gitlinks differ from the locked snapshot")
        for path in sorted(set(actual) | set(expected)):
            if actual.get(path) != expected.get(path):
                print(f"- {path}: expected {expected.get(path)}, got {actual.get(path)}")
        return 1

    print("MU-SILICIUM SNAPSHOT AUDIT: OK")
    print(f"Repository: {PIN['repository']}")
    print(f"Commit: {PIN['commit']}")
    print(f"License metadata: {metadata['license']['spdx_id']}")
    print(f"Submodule gitlinks verified: {len(expected)}")
    print("This is a reference snapshot, not a firmware build.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
