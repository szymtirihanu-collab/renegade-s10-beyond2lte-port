# Hardware inventory

This inventory separates known public device facts from platform details that still need evidence.

| Component | Current information | Porting status |
|---|---|---|
| SoC | Samsung Exynos 9820 | Identity known; integration details incomplete |
| CPU | AArch64-capable Exynos M4 / Cortex-A75 / Cortex-A55 cluster | EDK2 initialization unknown |
| RAM | Device variants reported with 8 or 12 GB | Actual usable/reserved map unknown |
| Display | 3040 × 1440 AMOLED panel | Panel ID, controller and init sequence unknown |
| GPU | ARM Mali-G76 MP12 | No UEFI graphics driver |
| Storage | UFS 2.1 | Controller integration and safe access unknown |
| USB | USB-C device port | Controller/PHY setup unknown |
| Interrupts | ARM GIC family expected; exact integration unverified here | Register map and routing unknown |
| Timer | ARM architectural timer availability must be verified | EDK2 timer implementation unknown |
| UART | Board-specific debug access not established | Early console unknown |
| Power/clock | Samsung-specific power and clock domains | Initialization unknown |

## Required additions

For each component, add:

- Exact source URL and pinned source revision.
- Relevant source file paths and symbols.
- Whether the detail is vendor-documented, source-derived, or experimentally verified.
- Any variant dependency.
- A test that can validate the implementation without risking user data.

Do not add guessed physical addresses or register values.
