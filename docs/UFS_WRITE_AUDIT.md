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
3. The failing LUN and LBA have not been mapped conclusively to the EFI filesystem/partition in the downstream repository's independent evidence.
4. A reported `Media.ReadOnly = FALSE` is not proof that the underlying logical unit is writable.

## Prepared source correction

A minimal, non-bypass patch is committed at [`patches/0001-ufs-blockio-readonly-from-unit-descriptor.patch`](../patches/0001-ufs-blockio-readonly-from-unit-descriptor.patch). It changes the Block I/O `ReadOnly` capability to reflect the already-read Unit Descriptor field `bLUWriteProtect`. This prevents firmware from advertising a protected LU as writable; it does not defeat protection or make writes succeed. The patch is intentionally not integrated into a firmware image and is not yet compiled or hardware-tested.

## Safe engineering conclusion

- Do not add unconditional cache clean/invalidate calls as a supposed fix based on the earlier misdiagnosis.
- Do not retry writes to LBA 0 or alter UFS logical-unit write-protection settings.
- First resolve the read-only device-path mapping for the failing LUN (LUN number, GPT partition, and block range) using existing read-only enumeration output.
- Correct the driver's media capability reporting only after the exact UFS descriptor fields and the driver's LUN mapping are confirmed against the pinned upstream implementation.
- Keep UFS write testing separate from phone deployment. No device-write procedure is part of this repository audit.

## Status

| Item | Evidence | Result |
|---|---|---|
| Nonzero-LBA UFS write | Upstream DEBUG log, LUN 0, LBA 1,983,528 | Success |
| FAT directory metadata write | Same upstream DEBUG log | Success |
| LUN 2, LBA 0 write | Upstream DEBUG log, OCS 0x07 / response 0x01 | Target rejected |
| LUN 2 mapping to ESP/cache | Not conclusively established here | Open |
| LU write-protect descriptor handling | Upstream status says `bLUWriteProtect` is not reflected in `Media.ReadOnly` | Driver correctness issue identified; exact patch requires source-level confirmation |
| DMA cache coherency as root cause | Contradicted by successful writes and target-side rejection evidence | Not established |
