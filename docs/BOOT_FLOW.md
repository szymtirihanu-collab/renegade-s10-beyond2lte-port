# Boot-flow investigation

## Known boundary

The published Renegade examples are built around Qualcomm device firmware. The Galaxy S10+ target is an Exynos 9820 Samsung device. Therefore, Qualcomm-specific assumptions such as Snapdragon EDL/ABL workflows must not be copied into this project.

## Questions that must be answered from evidence

- What exact boot stages and signed-image policy apply to the target model and firmware revision?
- What boot modes are available on the exact regional model?
- Is there a documented, supported way to execute a third-party payload?
- What execution state and exception level would the payload receive?
- Which memory regions are reserved by earlier firmware stages?
- Which device-tree or other hardware-description data is passed to the next stage?
- What rollback and recovery mechanism is available if a test image fails?

## Evidence standard

Answers must cite primary documentation, audited source code, or reproducible non-destructive observations from the exact target. A boot flow inferred from a Qualcomm device, another Samsung generation, or an unrelated Exynos board is not sufficient.

## Current conclusion

**Boot entry is an unresolved blocker.** This repository intentionally does not provide partition-writing commands, boot image repacking, or a test payload until a legitimate and model-specific execution path has been established.
