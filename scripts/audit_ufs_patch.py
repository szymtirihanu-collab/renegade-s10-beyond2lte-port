#!/usr/bin/env python3
"""Validate that the reviewed UFS LU write-protect patch applies to its pinned source."""
from __future__ import annotations

import json
import subprocess
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / 'UPSTREAM.lock.json').read_text(encoding='utf-8'))
PIN = LOCK['mu_silicium_reference_snapshot']
REPO = PIN['repository'].removeprefix('https://github.com/').removesuffix('.git')
SOURCE = 'Silicon/Samsung/SamsungPkg/Drivers/UfsDxe/UfsDxe.c'
HEADER = 'Silicon/Samsung/SamsungPkg/Include/Library/UfsHostBridge.h'
PATCH = ROOT / 'patches/0001-ufs-blockio-readonly-from-unit-descriptor.patch'

def fetch(path: str) -> str:
    url = f'https://raw.githubusercontent.com/{REPO}/{PIN["commit"]}/{path}'
    request = urllib.request.Request(url, headers={'User-Agent': 'beyond2lte-ufs-patch-audit'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode('utf-8')

def main() -> int:
    source = fetch(SOURCE)
    header = fetch(HEADER)
    if 'struct UfsUnitDesc' not in header or 'UINT8 bLUWriteProtect;' not in header:
        raise SystemExit('ERROR: pinned UFS Unit Descriptor does not expose bLUWriteProtect')
    if 'Dev->Media.ReadOnly = FALSE;' not in source:
        raise SystemExit('ERROR: expected upstream ReadOnly assignment changed; review patch manually')
    if 'Dev->Media.ReadOnly = (Ufs->UnitDesc[Lun].bLUWriteProtect != 0);' in source:
        raise SystemExit('ERROR: pinned source already contains the patch; refresh the patch')

    with tempfile.TemporaryDirectory(prefix='beyond2lte-ufs-patch-') as temp:
        root = Path(temp)
        target = root / SOURCE
        target.parent.mkdir(parents=True)
        target.write_text(source, encoding='utf-8')
        subprocess.run(['git', 'init', '-q', str(root)], check=True)
        subprocess.run(['git', '-C', str(root), 'add', SOURCE], check=True)
        subprocess.run(['git', '-C', str(root), '-c', 'user.name=Audit', '-c',
                        'user.email=audit@example.invalid', 'commit', '-qm', 'baseline'], check=True)
        subprocess.run(['git', '-C', str(root), 'apply', '--check', str(PATCH)], check=True)
        subprocess.run(['git', '-C', str(root), 'apply', str(PATCH)], check=True)
        patched = target.read_text(encoding='utf-8')
        expected = 'Dev->Media.ReadOnly = (Ufs->UnitDesc[Lun].bLUWriteProtect != 0);'
        if patched.count(expected) != 1:
            raise SystemExit('ERROR: patch output does not contain exactly one expected ReadOnly assignment')
        diff = subprocess.check_output(['git', '-C', str(root), 'diff', '--numstat', '--', SOURCE], text=True).strip()
        if diff != '2\t1\t' + SOURCE:
            raise SystemExit(f'ERROR: unexpected UFS patch scope: {diff!r}')

    print('UFS PATCH AUDIT: OK')
    print(f'Source pin: {REPO}@{PIN["commit"]}')
    print('Descriptor field: bLUWriteProtect present')
    print('Patch: applies cleanly and changes only BlockIo.Media.ReadOnly reporting')
    print('No storage write operation is performed by this audit.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
