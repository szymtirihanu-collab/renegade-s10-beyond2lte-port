# Validation plan

No device tests have been performed yet.

## Source and build validation

- Pin EDK2 and all submodule revisions.
- Record compiler, assembler, linker, Python and build-tool versions.
- Build from a clean checkout in CI.
- Run formatting and static checks on project-owned source.
- Preserve full build logs as CI artifacts.
- Do not publish a firmware artifact until the platform package and build are independently reviewed.

## Platform validation evidence

For each future test, record:

- Exact handset model and board/variant.
- Firmware version and relevant boot configuration.
- Source commit and build identifier.
- Test objective and expected result.
- Full serial/debug log where available.
- Observed result, known limitations and recovery outcome.

## Bring-up order

1. Confirm entry-point assumptions from authoritative evidence.
2. Validate basic AArch64 build and EDK2 package integration on a host.
3. Validate platform hand-off and memory description in a controlled test setup.
4. Establish early console and exception reporting.
5. Validate timer and interrupt-controller integration.
6. Enumerate and validate storage, USB and display independently.
7. Test OS loader hand-off only after UEFI core stability.

## Release criteria

A release must clearly distinguish source-only, build-tested, emulator-tested and physical-device-tested status. A build artifact must never be described as device-compatible solely because it compiles.
