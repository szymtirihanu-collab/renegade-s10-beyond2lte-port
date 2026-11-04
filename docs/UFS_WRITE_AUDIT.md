# UFS write-path audit (SM-G975F / Exynos 9820)

Last reviewed: 2026-11-04

## Verdict

**Do not apply a blanket DMA-cache patch.** The pinned upstream device project's instrumented DEBUG run records successful UFS WRITE_10 and FAT metadata writes for nonzero LBAs. A separate Windows-triggered write to **LUN 2, LBA 0** is rejected by the target. This is not evidence of a general UFS DMA-coherency failure.

Evidence is in the pinned upstream source at `orhunnx/beyond2lte-uefi`, commit `f122c7024c5eeef2c8c78dfd08c62708c9ef823d`:

- `STATUS.md`, section “Düzeltme: UFS yazma ÇALIŞIYOR...” records `WriteBlocks LUN=0 LBA=1983528`, `ro=0`, and `WriteBlocks sonuc = Success`, followed by FAT directory-entry creation.
- The same status records a later failure on `LUN=2 LBA=0`: `OCS=0x07`, `response=0x01`, and `WRITE_10 ... Device Error`.
- The upstream notes explain that `Media.ReadOnly` is currently forced to FALSE and does not reflect the LU's `bLUWriteProtect` attribute.

## Interpretation

1. UFS command submission and the data-write path are demonstrated to work for at least one nonzero LBA.
2. The failing request reaches the device and is rejected with a target response. That points away from a general cache-maintenance failure.
3. The pinned upstream status later resolves the mapping: `map -r` found GPT partitions on LUN 0 and LUN 3, while LUN 2 had no partition. LUN 2 is a Samsung boot logical unit protected by the device; `bootmgfw` attempts a write at LBA 0, receives the expected rejection, and continues booting.
4. Therefore the LUN 2 / LBA 0 rejection is not evidence that the Windows ESP or ordinary user-data LU is failing. It is an expected protected-boot-LU response.
5. A reported `Media.ReadOnly = FALSE` is still incorrect capability reporting and should reflect the Unit Descriptor.

## Prepared source correction

A minimal, non-bypass patch is committed at [`patches/0001-ufs-blockio-readonly-from-unit-descriptor.patch`](../patches/0001-ufs-blockio-readonly-from-unit-descriptor.patch). It changes the Block I/O `ReadOnly` capability to reflect the already-read Unit Descriptor field `bLUWriteProtect`. This prevents firmware from advertising a protected LU as writable; it does not defeat protection or make writes succeed. The host-build script now applies this patch to its temporary Mu-Silicium build tree, and the host-build workflow is configured to run when the patch or build script changes. Compilation is pending the current CI run; no firmware has been deployed to a phone.

## Safe engineering conclusion

- Do not add unconditional cache clean/invalidate calls as a supposed fix based on the earlier misdiagnosis.
- Do not retry writes to LBA 0 or alter UFS logical-unit write-protection settings.
- Treat LUN 2 as the protected Samsung boot LU, not as the Windows ESP or user-data volume. Do not try to make it writable.
- Keep the Block I/O `ReadOnly` capability synchronized with the already-read Unit Descriptor field.
- Keep UFS write testing separate from phone deployment. No device-write procedure is part of this repository audit.

## Status

| Item | Evidence | Result |
|---|---|---|
| Nonzero-LBA UFS write | Upstream DEBUG log, LUN 0, LBA 1,983,528 | Success |
| FAT directory metadata write | Same upstream DEBUG log | Success |
| LUN 2, LBA 0 write | Upstream DEBUG log, OCS 0x07 / response 0x01 | Target rejected |
| LUN 2 mapping | Upstream `map -r`: GPT partitions on LUN 0 and 3; LUN 2 has no partition and is a protected boot LU | Resolved; expected rejection |
| LU write-protect descriptor handling | Pinned Mu-Silicium source exposes `bLUWriteProtect`; original driver hardcodes `ReadOnly = FALSE` | Patch prepared and wired into host build; CI compile pending |
| DMA cache coherency as root cause | Ordinary nonzero-LBA writes and FAT metadata writes succeed; LUN 2 rejection is expected protection | Not indicated by current evidence |
