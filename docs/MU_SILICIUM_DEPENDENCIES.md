# Mu-Silicium dependency snapshot

Last reviewed: 2026-11-04

## Why this snapshot exists

The beyond2lte UEFI project describes itself as a Mu-Silicium overlay. Its build instructions clone Mu-Silicium recursively but do not pin a Mu-Silicium commit. A build from a moving `main` branch would therefore not be reproducible.

For planning only, this repository records the Mu-Silicium `main` snapshot observed on 2026-11-04:

- Commit: `6b3d90b79e191e08171bfedd3980234a7e49d340`
- Commit date: 2026-11-01
- Repository license metadata: BSD-2-Clause
- The exact gitlink commits for all six submodules are recorded in `UPSTREAM.lock.json`.

This is an **independent reference snapshot**, not proof that the beyond2lte maintainer used these revisions. Do not silently treat it as the tested dependency set.

## Submodule snapshot

| Path | Repository | Pinned commit |
|---|---|---|
| `Binaries` | Project-Silicium/Device-Binaries | `9f4dbfd7d61acdae69fd5bb48720ce7e53711e25` |
| `Common/Mu` | microsoft/mu_plus | `566cf5c8c2c8adf8e1a337ced1d147bc6246856f` |
| `Common/Mu_OEM_Sample` | microsoft/mu_oem_sample | `9292f9254adb94c5e5bb09a370b9662fcd66a953` |
| `Mu_Basecore` | microsoft/mu_basecore | `42d6d889f7c1f27e3226b44074b8a0ffe21cd988` |
| `Silicium-ACPI` | Project-Silicium/Silicium-ACPI | `f50bc115dccdea12e44efb550fd783d1daafc739` |
| OpenSSL submodule | openssl/openssl | `67b5686b4419b4cb8caa502711c41815f5279751` |

GitHub's repository metadata reports BSD-2-Clause for Mu-Silicium and Apache-2.0 for OpenSSL. Several other dependency repositories return `NOASSERTION` or no detected license metadata. That is not a legal conclusion; inspect the exact source-level license notices before reusing those components.

## Relevant Mu-Silicium USB modules

Search of the pinned Mu-Silicium tree shows generic EDK II USB bus and keyboard modules in other device configurations. Those platform configurations pair them with Qualcomm-specific xHCI components from the `Binaries` submodule.

That is not a ready-made Exynos DWC3 host-controller implementation. The generic bus/HID layer and the platform host-controller/PHY/role-control layer are separate requirements. Do not substitute Qualcomm binaries for Exynos hardware.

## Build gate

A cloud firmware build remains disabled until the beyond2lte overlay's license/permission is clarified and the actual dependency revisions used by its maintainer are confirmed. The reference snapshot is currently used only for immutable metadata checks.
