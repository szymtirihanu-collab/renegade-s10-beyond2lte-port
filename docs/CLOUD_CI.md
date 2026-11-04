# Cloud CI and build boundary

Last reviewed: 2026-11-04

## What runs in GitHub Actions

The `.github/workflows/source-audit.yml` workflow uses GitHub's hosted Linux ARM64 runner. It performs four read-only checks:

1. Validates local documentation and relative links.
2. Verifies the pinned beyond2lte upstream repository metadata and recursive Git tree.
3. Fetches selected source files at the pinned beyond2lte commit and checks USB/DWC3/OTG/DisplayPort hardware-description markers against the board DSC/FDF component inventory.
4. Verifies the separate Mu-Silicium reference commit and all six submodule gitlinks recorded in `UPSTREAM.lock.json`.

The workflow does **not** execute upstream code, clone the firmware source tree, build firmware, create a flashable image, or communicate with a phone. It is a provenance and source-inventory check, not a firmware build.

## Candidate host build

The maintainer's permission to use the beyond2lte implementation has been reported by the downstream repository owner and recorded in [UPSTREAM_PERMISSION.md](UPSTREAM_PERMISSION.md). The repository still has no declared SPDX license; the permission report is not treated as a public redistribution license. Source is fetched transiently at build time, not mirrored into this repository.

A manual-only workflow, `.github/workflows/host-build.yml`, now performs a candidate RELEASE build on `ubuntu-24.04-arm`. It checks out the exact beyond2lte commit and the pinned Mu-Silicium snapshot with recursive submodules, applies the upstream overlay in a temporary runner directory, and invokes the project's documented build entry point. It does not upload the generated image, publish source, flash a device, or access a handset.

**Important:** the Mu-Silicium snapshot is a reproducibility candidate, not yet confirmed as the exact revision used by the beyond2lte maintainer. A green build would validate this candidate combination only.

## Permission and dependency boundaries

The beyond2lte upstream repository has no declared repository license and no root license file was found in the pinned tree. The owner reports that the maintainer has permitted use of the implementation. This permission report is recorded separately; exact conditions for redistribution of source and binaries still need to be documented. The workflow uses the source transiently and does not mirror it.

The Mu-Silicium parent repository reports BSD-2-Clause, but some of its submodules return `NOASSERTION` or no detected license metadata. Also, the device-specific upstream build instructions do not pin the Mu-Silicium commit they used. A separate reference snapshot and its submodule gitlinks are recorded, but they are not claimed to be the tested build inputs. See [MU_SILICIUM_DEPENDENCIES.md](MU_SILICIUM_DEPENDENCIES.md).

Before distributing adapted source or firmware binaries, document the exact permission conditions, confirm the actual Mu-Silicium revision used, and review dependency notices. The candidate build is already enabled as a manual, non-publishing CI job.

1. Record the approved license/permission and scope.
2. Review dependency licenses and pin every recursive submodule to immutable commit IDs.
3. Record toolchain and Python dependency versions.
4. Review build scripts and generated inputs before executing them.
5. Add a host-only build job that stores checksums and logs, not device-installation packages.

## ARM64 runner

GitHub provides hosted Linux ARM64 runner labels such as `ubuntu-24.04-arm`. This lets CI perform native AArch64 host-side checks without the user's openSUSE computer. Runner availability and usage are controlled by GitHub; see [GitHub's hosted runner documentation](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

## Evidence labels

- **CI source audit:** pinned GitHub repositories, git trees, and selected source markers were checked successfully.
- **Host build:** only after a licensed, pinned source build completes in CI.
- **Device validation:** only after direct observation on the SM-G975F.

A green source-audit workflow must never be described as a successful firmware build.
