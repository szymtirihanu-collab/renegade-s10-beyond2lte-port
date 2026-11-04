# Cloud CI and build boundary

Last reviewed: 2026-11-04

## What runs in GitHub Actions

The `.github/workflows/source-audit.yml` workflow uses GitHub's hosted Linux ARM64 runner. It performs four read-only checks:

1. Validates local documentation and relative links.
2. Verifies the pinned beyond2lte upstream repository metadata and recursive Git tree.
3. Fetches selected source files at the pinned beyond2lte commit and checks USB/DWC3/OTG/DisplayPort hardware-description markers against the board DSC/FDF component inventory.
4. Verifies the separate Mu-Silicium reference commit and all six submodule gitlinks recorded in `UPSTREAM.lock.json`.

The workflow does **not** execute upstream code, clone the firmware source tree, build firmware, create a flashable image, or communicate with a phone. It is a provenance and source-inventory check, not a firmware build.

## Why the firmware build is not enabled yet

The candidate beyond2lte upstream repository currently has no declared repository license and no root license file was found in the pinned tree. Public visibility does not itself grant permission to copy, adapt, or redistribute source. This project therefore keeps upstream implementation files out of this repository and does not automate their import.

The Mu-Silicium parent repository reports BSD-2-Clause, but some of its submodules return `NOASSERTION` or no detected license metadata. Also, the device-specific upstream build instructions do not pin the Mu-Silicium commit they used. A separate reference snapshot and its submodule gitlinks are recorded, but they are not claimed to be the tested build inputs. See [MU_SILICIUM_DEPENDENCIES.md](MU_SILICIUM_DEPENDENCIES.md).

Before enabling a build job, obtain a clear license or written permission for the beyond2lte overlay, confirm the actual Mu-Silicium revision used, and then:

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
