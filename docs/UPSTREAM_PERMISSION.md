# Upstream permission and provenance

Last updated: 2026-11-04

## Permission report

The downstream repository owner reports that the maintainer of
[orhunnx/beyond2lte-uefi](https://github.com/orhunnx/beyond2lte-uefi) has said
this project may use the beyond2lte implementation.

This is a record of the repository owner's report, not a copy of the maintainer's
message or a formal license grant. The upstream repository still has no
repository-level license declaration or root LICENSE file at the pinned commit.

## Current handling

- The upstream source remains pinned to commit
  `f122c7024c5eeef2c8c78dfd08c62708c9ef823d`.
- The source is fetched at build time into a temporary CI workspace.
- The source is not mirrored or vendored into this downstream repository.
- The host-build workflow does not publish source archives or compiled images.
- Attribution to the original project is retained in the repository documentation.

## Scope still to record

Before publishing adapted source or distributing firmware binaries, record the
maintainer's exact conditions, including whether modification, public
redistribution, binary redistribution, and required attribution are allowed.
Also review the individual licenses/notices of Mu-Silicium's recursive
dependencies; permission for the device overlay does not automatically grant
rights to third-party dependencies.

## Build dependency caveat

The candidate build uses the separately pinned Mu-Silicium snapshot in
`UPSTREAM.lock.json`. The beyond2lte maintainer's build instructions do not
identify the exact Mu-Silicium commit used for their reported working build.
Therefore a successful build against this snapshot is a **candidate host build**,
not a reproduction of the maintainer's exact build environment.
