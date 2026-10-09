# Clock Handler Provenance & Semantic Dataflow Analysis

## Scope, Hashes & Baseline Inputs

- ROM: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`, 16,777,216 bytes)
- Robin-5 SMU: `archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5` (offset `0x8FEF00`, SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`, 262,400 bytes)
- Project Integrity: Binary correspondence asserted byte-for-byte; SMU body matches ROM offset `0x8FEF00`. Analysis conducted via read-only Ghidra headless script `OcConsumerRead.java` and verified with deterministic Python script `verify-clock-handlers.py`.

## Queue 0 Dispatch Table Structure & Message Semantics

Queue 0 entry dispatch table is located at `0x7068` (vector at `0x7A94` points to `0x706C`). Each entry is 8 bytes (`+0x0`: gate flags, `+0x4`: handler PC).

- **ID `0x11`** (offset `0x70F0`): Flags `0x00000000`, Handler `0x0002EA74`.
  - Community label: `PPSMC_MSG_QueryVddcrSocClock`.
  - Byte execution trace: Handler retrieves argument from mailbox (`func_0x00000ffc`), extracts domain index `uVar3 = (arg >> 16)`. Checks bounds `uVar3 <= 0x13` (20 domains).
  - Reads domain ID at `0x13EEC + 8 + uVar3 * 4` (`0x13EF4 + uVar3 * 4`). If domain ID is `0x13` or `0x14`, returns `0xFFFFFFFF`.
  - Otherwise, reads **float** from internal clock state array at `0x13EEC + 0x5C + uVar3 * 12` (`0x13F48 + uVar3 * 12`).
  - Converts float via `utrunc.s a11, f0, 0x0` (unsigned truncation), writes return data via `func_0x00000fe4` and returns status `1` (`func_0x00000fa8`).
  - **Semantic proof**: Handler reads an **internal firmware software committed state float** representing the programmed clock frequency for the indexed domain. It does **NOT** read an external hardware frequency counter, PLL lock counter, physical clock measurement register, or live operating MHz.

- **ID `0x13`** (offset `0x7100`): Flags `0x00000000`, Handler `0x0001E988`.
  - Community label: `PPSMC_MSG_QueryDfPstate`.
  - Byte execution trace: Handler ignores input argument. Loads literal `_DAT_000171ec` (`0xCEE0`).
  - Reads byte at `0xCEE0 + 0x0D` (offset `0xCEED`, current P-state index).
  - Reads byte at `0xCEE0 + 0xF7` (offset `0xCFD7`, P-state count / upper limit).
  - Computes: `result = (byte[0xCFD7] - byte[0xCEED]) - 1`.
  - Writes integer result via `func_0x00000fe4` and returns status `1` (`func_0x00000fa8`).
  - **Semantic proof**: Handler returns a **state count / index difference** (remaining available P-states or index delta), **NOT** a frequency in MHz or clock measurement.

- **ID `0x1A`** (offset `0x7138`): Flags `0x00000006`, Handler `0x0002B634`.
  - Controls GFX DFLL divider (`DfllGfxDiv`). Confirmed distinct from UCLK/MCLK/FCLK dividers; no semantic link to memory or fabric clock sync.

## Clock State Struct `0x13EEC` Dataflow & Producers

The structure at `0x13EEC` is the central clock management entity:

1. `0x13EF0` (`+0x04`): Current DPM / P-state index.
2. `0x13EF4` (`+0x08`): Array of 20 domain ID integers:
   - `[0] = 0x0D, [1] = 0x00, [2] = 0x01, [3] = 0x02, [4] = 0x03, [5] = 0x04, [6] = 0x05, [7] = 0x06`
   - `[8] = 0x07, [9] = 0x0A, [10] = 0x18, [11] = 0x13, [12] = 0x14, [13] = 0x15, [14] = 0x16, [15] = 0x17`
   - `[16] = 0x0B, [17] = 0x08, [18] = 0x09, [19] = 0x0C`
3. `0x13F48` (`+0x5C`): Array of 20 **software committed clock frequency floats** (stride 12 bytes). Read by handler `0x2EA74`.
4. `0x14038` (`+0x14C`): Array of 20 **target / requested clock frequency floats** (stride 12 bytes).
5. **Producer / Writer 1 (`FUN_0002e9dc`)**:
   - Takes P-state index, looks up table at `0x7B5C` (`0x7B5C + index * 100 + 0x48`), converts 20 uint values to float, and stores them into target array `0x14038`. Total read span is 80 bytes across offsets 72..152; structural relation to row stride preserved as open uncertainty without runtime buffer evidence.
6. **Producer / Writer 2 (`FUN_0002ea08`)**:
   - Takes clock domain index (`1..20`) and frequency request (`arg & 0xFFFF`), updates specific target float in `0x14038` via prebiased base `0x1402C` (`0x1402C + index * 12`), and calls `FUN_0002e788`.
7. **Actuator / Copier (`FUN_0002e788`)**:
   - Compares target floats (`0x14038`) with committed floats (`0x13F48`). For modified entries, calls frequency program helpers (`FUN_00023994`, `FUN_00023ab0`, `FUN_00023ac4`, `FUN_00023c78`, `FUN_00023890`) and commits target float into `0x13F48`.

## Conclusion & Discriminative Verdict

- `PPSMC_MSG_QueryVddcrSocClock` (0x11 / 0x2EA74) returns the **internal software committed frequency state float** of the requested domain, not a physical hardware measurement or operating clock.
- `PPSMC_MSG_QueryDfPstate` (0x13 / 0x1E988) returns an **internal P-state delta / count**, not a clock frequency.
- Neither mailbox query provides an independent physical clock measurement or proves clock synchronization.
