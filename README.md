# Renegade S10+ / beyond2lte port

**Status: research scaffold only — not bootable, not flashable, and not an official Renegade Project port.**

This repository investigates whether a Renegade-style EDK2 UEFI environment can be brought up on the **Samsung Galaxy S10+ Exynos variant (beyond2lte)**.

## Confirmed target

| Property | Target |
|---|---|
| Device | Samsung Galaxy S10+ |
| Exact model supplied by owner | **SM-G975F** |
| Codename | `beyond2lte` |
| SoC | Samsung Exynos 9820 |
| CPU architecture | AArch64 |
| Display | 3040 × 1440 |
| GPU | ARM Mali-G76 MP12 |
| Android kernel baseline | Samsung Exynos 9820 vendor kernel, 4.14 |

The target is the international Exynos SM-G975F. The Korean SM-G975N uses the related codename `beyond2lteks` and is not the target. See [MODEL.md](docs/MODEL.md) for the model-specific scope and remaining unknowns.

## Important architecture difference

Renegade Project's published EDK2 firmware targets Qualcomm Snapdragon platforms. Its documented Qualcomm boot chain and device packages cannot be reused as if this phone were a Snapdragon device. The S10+ uses Samsung's Exynos platform and Samsung boot firmware. A real port needs independently established platform initialization, boot hand-off, memory map, interrupt controller, timer, storage, display and USB support.

This repository therefore starts with platform research and a validation plan. A model-specific Project Silicium-based UEFI candidate has now been identified; see [EXISTING_UEFI_PORT_REVIEW.md](docs/EXISTING_UEFI_PORT_REVIEW.md) and [SOURCE_AUDIT.md](docs/SOURCE_AUDIT.md). The next step is to audit and reproduce that source, not to invent a second board package. This repository does **not** contain a fabricated device tree, guessed register addresses, patched boot images, or a supposedly working firmware binary.

## Current state

- [x] Target identity and architecture documented
- [x] Exact target model supplied: SM-G975F
- [x] Renegade/Qualcomm versus Samsung/Exynos differences documented
- [ ] Confirm handset's bootloader state and firmware revision
- [ ] Collect and document trustworthy Exynos 9820 hardware references
- [ ] Establish a reproducible EDK2 build environment
- [ ] Identify a supported and auditable boot hand-off path
- [ ] Implement platform description and early serial/debug output
- [ ] Bring up memory, timer, interrupt controller and console
- [ ] Add storage, display and USB drivers
- [ ] Validate boot on hardware with recovery and rollback procedures

See [MODEL.md](docs/MODEL.md), [EXISTING_UEFI_PORT_REVIEW.md](docs/EXISTING_UEFI_PORT_REVIEW.md), [SOURCE_AUDIT.md](docs/SOURCE_AUDIT.md), [PORTING_STATUS.md](docs/PORTING_STATUS.md), [ARCHITECTURE.md](docs/ARCHITECTURE.md), and [REFERENCES.md](docs/REFERENCES.md).

## Safety and device integrity

Do not flash anything from this repository. There are no validated images. Samsung boot-chain behavior is not interchangeable with Qualcomm EDL/ABL workflows, and an incorrect image or partition operation can make a phone unusable or erase its data. Development must begin with source review and non-destructive research; any future device testing requires verified model-specific procedures, backups, and a recovery plan.

## Scope

The initial target is an **EDK2/UEFI feasibility port**, following the general idea of Renegade Project. Booting Windows ARM64 is a separate later milestone and is not implied by a UEFI build. Native Linux support is also a separate operating-system integration task.

## License

No Renegade Project or EDK2 source code is copied into this repository at this stage. Licensing for future imported or adapted components must be reviewed file-by-file before inclusion.
