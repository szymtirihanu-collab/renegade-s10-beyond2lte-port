# Cloud CI and build boundary

Last reviewed: 2026-11-04

## What runs in GitHub Actions

The `.github/workflows/source-audit.yml` workflow uses GitHub's hosted Linux ARM64 runner. It validates local documentation and queries GitHub's public API for metadata and the recursive Git tree at the exact upstream commit pinned in `UPSTREAM.lock.json`.

It does **not** clone upstream source, execute upstream scripts, build firmware, create a flashable image, or communicate with a phone. It is a provenance and source-inventory check, not a firmware build.

## Why the firmware build is not enabled yet

The candidate upstream repository currently has no declared repository license and no root license file was found in the pinned tree. Public visibility does not itself grant permission to copy, adapt, or redistribute source. This project therefore keeps upstream implementation files out of this repository and does not automate their import.

Before enabling a build job, obtain a clear license or written permission from the upstream maintainer, then:

1. Record the approved license/permission and scope.
2. Pin Mu-Silicium and every recursive submodule to immutable commit IDs.
3. Record toolchain and Python dependency versions.
4. Review build scripts and generated inputs before executing them.
5. Add a host-only build job that stores checksums and logs, not device-installation packages.

## ARM64 runner

GitHub provides hosted Linux ARM64 runner labels such as `ubuntu-24.04-arm`. This lets CI perform native AArch64 host-side checks without the user's openSUSE computer. Runner availability and usage are controlled by GitHub; see [GitHub's hosted runner documentation](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

## Evidence labels

- **CI metadata audit:** pinned GitHub repository and tree were queried successfully.
- **Host build:** only after a licensed, pinned source build completes in CI.
- **Device validation:** only after direct observation on the SM-G975F.

A green metadata-audit workflow must never be described as a successful firmware build.
