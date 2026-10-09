# Voltage Producer Writer Trace & Verification Log

## Intent & G7 Correction — 2026-09-19T23:45:00+05:00

Actor: bounded code/RE agent.
G7 Correction on Project Integrity & Metadata Writes:

- Prior assertion that Ghidra project was strictly "unchanged" contradicted workspace index/metadata writes (`OCConsumer.rep` project metadata tracking).
- Formal distinction preserved: source ROM binary (`BC250_5.00_clv.bin`, SHA-256 `ea578104...`) and extracted SMU firmware body (`smu_fw_robin_5`, SHA-256 `cae8617c...`) remain byte-identical and unmodified (ROM hashes unchanged). Headless Ghidra execution performed in disposable/isolated workspace (`/tmp/gh_disposable/`) or with `-readOnly -noanalysis` to preserve original workspace files.
- Model default identity unconfirmed; documentation correction not independent release review.
- Telemetry Provenance Correction: Unequal addresses do not disprove an actuator->telemetry copy. Negative literal scan covers only literal references, NOT all stores/indirect/DMA writes, and does NOT establish an external hardware writer. Verified producer reads 0x109f4/0x10a08, not direct alias 0x13474; source writer and copied provenance remain unknown.

Goals:

1. Verify exact byte loop in `FUN_00029e34` (2 iterations, stride `0x14`), literal `0x17f88` (`0xca68`), and derive actual exported table buffer base `0xcb68` (`0xca68 + 0x100`).
2. Trace writer of float telemetry sources `0x107fc + 0x1f8` (`0x109f4`) and `0x107fc + 0x14 + 0x1f8` (`0x10a08`).
3. Determine whether producer reads actuator command state struct `_DAT_00017124` (`0x13474 + 0x00 / +0x20`) or hardware measurement telemetry.
4. Establish code-backed writer relation or explicit bounded negative result.

## Results & Verifier Findings

1. **Table Base & Loop Arithmetic (`FUN_00029e34`)**:
   - Instruction `0x29e3d`: `l32r a4, 0x17f88` -> `a4 = 0xca68`.
   - Instruction `0x29e46`: `addmi a2, a4, 0x100` -> `a2 = 0xcb68` (Table export buffer base).
   - Loop `0x29ee1-0x29f16` runs 2 iterations (`a9` = 0, 1) with stride `0x14` (`20` bytes):
     - Iteration 0: reads float `0x107fc + 0x1f8` = `0x109f4`, stores u32 (`utrunc.s`) at `0xcb68 + 0x50` = `0xcbb8` (`Voltage[0]`).
     - Iteration 1: reads float `0x107fc + 0x14 + 0x1f8` = `0x10a08`, stores u32 (`utrunc.s`) at `0xcb68 + 4 + 0x50` = `0xcbbc` (`Voltage[1]`).
   - Bytes match exact binary: `76ab3120f9a01bb990c9a0d0cca0d30c7fe30c7ef30c8000cf2a00be2a00ad2ab0907400ecea00abea008aeaa26f14826f16e26f18`.

2. **Actuator Struct (`0x13474`) vs Telemetry Source (`0x109f4` / `0x10a08`)**:
   - Actuator state struct is at `0x13474`:
     - Domain 0: `+0x00` (float target voltage), `+0x04` (VID)
     - Domain 1: `+0x20` (float target voltage), `+0x24` (VID)
   - Telemetry sources `0x109f4` and `0x10a08` are physically separated by `0x2a80` and `0x2a8c` bytes. Verified producer reads 0x109f4/0x10a08, not direct alias 0x13474; unequal addresses do not disprove an actuator->telemetry copy path.

3. **Master Pointer Table `0x15380`**:
   - Static literal table `0x15380` explicitly collocates:
     - `0x15394`: `0x00013474` (actuator state struct base)
     - `0x15398`: `0x000109f4` (Domain 0 Voltage telemetry source)
     - `0x1539c`: `0x000109f8` (Domain 0 Current telemetry source)
     - `0x153a0`: `0x000109fc` (Domain 0 Power telemetry source)
     - `0x153a8`: `0x00010a08` (Domain 1 Voltage telemetry source)
     - `0x153ac`: `0x00010a0c` (Domain 1 Current telemetry source)
     - `0x153b0`: `0x00010a10` (Domain 1 Power telemetry source)

4. **Writer Provenance (Bounded Negative Scan)**:
   - Scope of negative scan covers only literal-reference paths (`l32r` loading `0x17f84` = `0x107fc`), NOT all stores/indirect/DMA writes across firmware or external hardware blocks.
   - Code references loading `0x17f84` (`0x107fc`): `0x29c2d` (`FUN_00029b90`) and `0x29ede` (`FUN_00029e34`), both read consumers.
   - Conclusion: Verified producer reads `0x109f4`/`0x10a08`, not direct alias `0x13474`. Direct literal-reference write instructions were not found in this bounded scan, but this does NOT establish an external hardware writer. Source writer and copied provenance remain unknown.
