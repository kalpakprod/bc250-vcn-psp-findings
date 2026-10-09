# SMU Metrics Producer Trace: Backwards Provenance & State Mapping

## Intent — 2026-09-19T22:30:00+05:00

Actor: bounded code/RE agent. Offline SMU telemetry metrics producer investigation.
Goals:

1. Trace SMU metrics producer `Voltage[0]` and `Voltage[1]` backwards to their actual source addresses.
2. Compare source addresses against actuator state structure `_DAT_00017124` (`0x13474 + 0x00 / +0x20` and VID `+0x04 / +0x24`).
3. Assert exact ROM and SMU hashes.

Inputs asserted:

- CLV ROM SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8` (16,777,216 bytes)
- Robin-5 SMU body SHA-256: `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37` (offset `0x8FEF00`, 262,400 bytes)
- Driver interface reference: `smu11_driver_if_cyan_skillfish.h` / `cyan_skillfish_ppt.c`.

## Correction and Intent Log per Project G7 — 2026-09-19T23:00:00+05:00

Review of the voltage metrics producer report revealed reliance on an unidentified temporary decompile without pinning addresses `0x29E34`, `0x17F84`, `0x17F7C`, `0x109F4`, `0x10A08` directly to exact Robin-5 firmware in the source image.
All prior findings are marked PROVISIONAL pending this offline verification pass.
Withdraw unsupported claim that "periodic ADC poll populates" `0x109F4` / `0x10A08`; the writer is unidentified.
Correct float conversion instruction semantics: instructions use `utrunc.s` (unsigned truncation), not C-decompiler inferred signed `trunc`.

Intent:

1. Re-verify Robin-5 SMU body (`cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`) at CLV ROM offset `0x8FEF00` (`ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`).
2. Directly read literals `0x17F84` and `0x17F7C`, verify dereferencing.
3. Archive read-only Ghidra decompile/disassembly of `0x29E34` into new owned evidence directory `evidence/firmware-audit/20260919-metrics-producer-check/`.
4. Verify instruction bytes and `l32r` target mappings.
5. Establish metrics producer table voltage offsets and source addresses, rejecting any wrong-build mismatch.

## Results & Findings — 2026-09-19T22:45:00+05:00

1. **Producer Function Identification**:
   - In `robin_5`, table-6 export handler is `FUN_00029e34`.
   - Export buffer base `iVar13` = `0xcb68` (`iVar12 + 0x100`, where `iVar12 = _DAT_00017f88 = 0xca68`).
   - Total export length is 244 bytes (`0xf4`), matching `sizeof(SmuMetrics_t)`.

2. **Voltage[0] and Voltage[1] Source Addresses**:
   - Stride loop `uVar17` iterates across 2 domains using domain array base `_DAT_00017f84` = `0x107fc`.
   - Multiplier `fVar24 = *_DAT_00017f7c` = `1000.0f` at `0x16ee4`.
   - `Voltage[0]` (offset `0xcb68 + 0x50` = `0xcbb8`) reads float at `0x109f4` (`0x107fc + 0x1f8`).
   - `Voltage[1]` (offset `0xcb68 + 0x54` = `0xcbbc`) reads float at `0x10a08` (`0x10810 + 0x1f8`).
   - `Current[0]` reads float at `0x109f8`; `Current[1]` reads float at `0x10a0c`.
   - `Power[0]` reads float at `0x109fc`; `Power[1]` reads float at `0x10a10`.

3. **Instruction Byte & Conversion Semantics Verification**:
   - `0x29ecf`: `d12bb8` -> `l32r a13, 0x17f7c` (target `0x16ee4`, value `1000.0f`).
   - `0x29ede`: `d129b8` -> `l32r a13, 0x17f84` (target `0x107fc`).
   - `0x29eef`: `d30c7f` -> `lsi f13, a12, 0x1fc` (Domain Current source).
   - `0x29ef2`: `e30c7e` -> `lsi f14, a12, 0x1f8` (Domain Voltage source).
   - `0x29ef5`: `f30c80` -> `lsi f15, a12, 0x200` (Domain Power source).
   - `0x29f04`: `00ecea` -> `utrunc.s a14, f12, 0` (unsigned truncation from float to u32 for Power).
   - `0x29f07`: `00abea` -> `utrunc.s a10, f11, 0` (unsigned truncation from float to u32 for Voltage).
   - `0x29f0a`: `008aea` -> `utrunc.s a8, f10, 0` (unsigned truncation from float to u32 for Current).
   - Conversion is unsigned truncation (`utrunc.s`), correcting prior C pretty printer `trunc` inference.
   - The writer of `0x109f4` and `0x10a08` remains unidentified in static trace; the prior claim that "periodic ADC poll populates" these addresses is withdrawn per G7.

4. **Comparison with Actuator State Structure `_DAT_00017124` (`0x13474`)**:
   - Actuator state struct is at `0x13474`:
     - Domain 0: `+0x00` (float voltage), `+0x04` (VID)
     - Domain 1: `+0x20` (float voltage), `+0x24` (VID)
   - Telemetry source addresses `0x109f4` and `0x10a08` are physically distinct from `0x13474` (delta `0x2a80` / `0x2a8c` bytes).
   - Direct byte equivalence between producer telemetry sources and actuator target state is disproven.
