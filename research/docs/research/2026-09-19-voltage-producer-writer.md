# Voltage Producer Writer Trace & Telemetry Provenance

## Scope, Hashes & Baseline Inputs

- ROM: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`, 16,777,216 bytes)
- Robin-5 SMU: `archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5` (offset `0x8FEF00`, SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`, 262,400 bytes)
- G7 Project Integrity Correction: ROM and SMU binary hashes remain strictly unmodified. Prior claim that Ghidra project was unchanged contradicted workspace index metadata writes; analysis was isolated in temporary/read-only environment. Model identity is uncertified; documentation correction not independent release review.
- Logical Correction on Telemetry Provenance: Unequal addresses disprove direct pointer aliasing, but do NOT disprove an actuator->telemetry copy path. Negative literal-reference scan covers only the literal-loading path, NOT all stores/indirect/DMA writes, and does NOT establish an external hardware writer. Verified producer reads 0x109f4/0x10a08, not direct alias 0x13474; source writer and copied provenance remain unknown.

## Table Base & Producer Loop Verification (`FUN_00029e34`)

- Table Base Literal `_DAT_00017f88` = `0xca68`.
- Instruction `0x29e46` (`addmi a2, a4, 0x100`) sets export buffer base `iVar13 = 0xcb68` (244 bytes exported via `FUN_0003ab90`).
- Loop `0x29ee1-0x29f16` (2 iterations, stride `0x14` / 20 bytes):
  - Domain 0 (`a9=0`): float source `0x107fc + 0x1f8` = `0x109f4` -> exported to `0xcb68 + 0x50` = `0xcbb8` (`Voltage[0]`).
  - Domain 1 (`a9=1`): float source `0x107fc + 0x14 + 0x1f8` = `0x10a08` -> exported to `0xcb68 + 4 + 0x50` = `0xcbbc` (`Voltage[1]`).
  - Current[0/1] at sources `0x109f8`/`0x10a0c` -> offsets `+0x58`/`+0x5c` (`0xcbc0`/`0xcbc4`).
  - Power[0/1] at sources `0x109fc`/`0x10a10` -> offsets `+0x60`/`+0x64` (`0xcbc8`/`0xcbcc`).
  - Conversion: unsigned truncation `utrunc.s` after `1000.0f` multiplier (`0x16ee4`).
  - Exact loop bytes verified: `76ab3120f9a01bb990c9a0d0cca0d30c7fe30c7ef30c8000cf2a00be2a00ad2ab0907400ecea00abea008aeaa26f14826f16e26f18`.

## Actuator State Struct `0x13474` vs Telemetry Sources

- Actuator struct `_DAT_00017124` (`0x13474`):
  - Domain 0: float target voltage at `0x13474 + 0x00`, VID byte at `+0x04`.
  - Domain 1: float target voltage at `0x13474 + 0x20`, VID byte at `+0x24`.
- Producer does **not** read actuator struct `0x13474`: address delta is `0x2a80` (Domain 0) and `0x2a8c` (Domain 1). Verified producer reads 0x109f4/0x10a08, not direct alias 0x13474; however, unequal addresses do not disprove an actuator->telemetry copy path.
- Pointer Table `0x15380` explicitly lists both: actuator struct `0x13474` at `0x15394`, Domain 0 telemetry `0x109f4` at `0x15398`, Domain 1 telemetry `0x10a08` at `0x153a8`.

## Writer Provenance: Bounded Negative Scan

- Scope of negative scan: only literal-reference paths (`l32r` loading base literal `0x17f84` = `0x107fc`), NOT all stores/indirect/DMA writes across firmware or external hardware blocks.
- Literal `0x17f84` is only loaded by `FUN_00029b90` (`0x29c2d`) and `FUN_00029e34` (`0x29ede`), both read paths.
- Conclusion: Verified producer reads `0x109f4`/`0x10a08`, not direct alias `0x13474`. Direct literal-reference write instructions were not found in this bounded scan, but this does NOT establish an external hardware writer. Source writer and copied provenance remain unknown.
- Remaining gap: Writer provenance is unresolved; exact physical power rail identity (e.g. SoC vs GFX vs VDDCR) cannot be asserted without physical schematic/trace routing or board-level measurement.
