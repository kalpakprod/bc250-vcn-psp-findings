# SMU Clock Actuator Chain & Register Aperture Analysis

## Scope, Hashes & Provenance

- ROM Baseline: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
  - Size: 16,777,216 bytes (16 MiB)
  - SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Robin-5 SMU Firmware: `archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5`
  - Size: 262,400 bytes
  - SHA-256: `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`
  - Offset in ROM: `0x8FEF00` (byte-identical match asserted)
- Decompilation & Assembly Evidence: Byte-verified against Robin-5 (`cae8617c...`) across all instruction sequences in `verify-clock-handlers.py`.

## Queue 0 / Queue 3 Dispatch & Command Semantics

1. **Queue 0, ID `0x11` (offset `0x70F0`) -> Handler `0x0002EA74`**
   - Community Label: `PPSMC_MSG_QueryVddcrSocClock`.
   - Arguments: `arg >> 16` gives 0-based domain index (checked `<= 0x13`, 20 domains).
   - Execution: Reads software committed frequency float from `0x13EEC + 0x5C + index * 12` (`0x13F48 + index * 12`), converts via `utrunc.s a11, f0, 0x0`, writes return data via `0x00000fe4`. Returns status `1`. If domain ID is `0x13` or `0x14`, returns `0xFFFFFFFF`.
   - Semantic Proof: Reads an internal software state float. Does NOT sample hardware PLL counters, physical clock lines, or external registers.
2. **Queue 0, ID `0x13` (offset `0x7100`) -> Handler `0x0001E988`**
   - Community Label: `PPSMC_MSG_QueryDfPstate`.
   - Execution: Ignores argument. Reads struct `0xCEE0`: byte `+0x0D` (current P-state index) and byte `+0xF7` (P-state upper bound). Computes `(byte[0xF7] - byte[0x0D]) - 1`.
   - Semantic Proof: Returns an integer P-state count/index delta, NOT a frequency in MHz.
3. **Queue 0, ID `0x1A` (offset `0x7138`) -> Handler `0x0002B634`**
   - Controls GFX DFLL divider (`DfllGfxDiv`). Distinct from memory/fabric/UCLK dividers.
4. **Queue 3, ID `0x1D` (offset `0x7550`) -> Handler `0x0002EA08`**
   - Dynamic per-domain clock request.
   - Arguments: `arg >> 16` gives 1-based domain index `index` (`1..20`). Rejects `index == 0` or `index > 20`. Frequency value is `arg & 0xFFFF`.

## Clock State Struct `0x13EEC` Dataflow

- `0x13EF0` (`+0x04`): Current P-state index integer.
- `0x13EF4` (`+0x08`): Array of 20 domain ID integers:
  - `[0]=0x0D, [1..8]=0x00..0x07 (CPU Cores 0..7), [9]=0x0A, [10]=0x18, [11]=0x13, [12]=0x14, [13]=0x15, [14]=0x16, [15]=0x17, [16]=0x0B, [17]=0x08, [18]=0x09, [19]=0x0C`.
- `0x13F48` (`+0x5C`): Array of 20 **software committed frequency floats** (stride 12 bytes). Read by handler `0x2EA74`.
- `0x14038` (`+0x14C`): Array of 20 **target/requested frequency floats** (stride 12 bytes).

## Writers & Target Indexing Verification

1. **Writer 2 (`FUN_0002ea08`, Dynamic Request)**:
   - Index: 1-based (`1..20`).
   - Domain ID lookup: `0x13EEC + 4 + index * 4` = `0x13EF0 + index * 4`. For index `1..20`, this resolves to `0x13EF4..0x13F40` (the 20 domain IDs).
   - Target float write: `0x13EEC + 0x140 + index * 12` = `0x1402C + index * 12`.
     - For index `1`: `0x1402C + 12 = 0x14038` (entry 0).
     - For index `20`: `0x1402C + 240 = 0x1411C` (entry 19).
   - Provenance: `0x1402C` is mathematically the **prebiased base** (`0x14038 - 12`) to allow direct indexing by 1-based index `1..20`. Calls actuator `FUN_0002e788`.
2. **Writer 1 (`FUN_0002e9dc`, P-state Bulk Loader)**:
   - Inputs: P-state index in register `a2`.
   - Arithmetic: `base = 0x7B5C + pstate * 100`. Loops 20 iterations (`a3 = 20`).
   - Load: `l32i a8, a2, 0x48`, then `addi.n a2, a2, 4`. Converts uint32 to float, stores to `0x14038 + i * 12`.
   - Read window: Iteration 0 reads offset `0x48` (72 decimal). Iteration 19 reads offset `0x48 + 19 * 4 = 0x94` (148 decimal). Total read span is 80 bytes (offsets 72 to 152 relative to `0x7B5C + pstate * 100`).
   - Structural Analysis: Reading 80 bytes starting at offset 72 within a 100-byte row stride extends 52 bytes into the next 100-byte boundary. However, whether this represents a firmware bug, a structure-of-arrays layout, or a prebiased table base in uninitialized RAM is preserved as an open technical uncertainty; it cannot be asserted as an unconditional defect without runtime buffer population evidence.

## Actuator Chain & Hardware Register Apertures

Actuator loop `FUN_0002e788`:

- Iterates 20 domains. Compares requested target float `0x14038 + i * 12` with committed float `0x13F48 + i * 12`.
- When modified:
  - Calls `FUN_00023994(domain_id)` if target == 0.
  - Calls `FUN_00023ab0`, `FUN_00023ac4`, `FUN_00023c78`, and `FUN_00023890(domain_id, step)` for target frequency updates.
  - Commits target float to `0x13F48 + i * 12` (**software committed state**).
- Actuator helper `FUN_00023890`:
  - Dereferences domain configuration record at `domain_id * 0x1C + 0xF728` and `domain_id * 0x1C + 0xF568 + 0x254`.
  - For Domain `0x13` (`CLK_GROUP_5`), manipulates gate register `_DAT_000178CC + 0x214` = `0x01D80414` (clearing bits 3 and 4 with mask `0xFFFFFFE7`, polling `0x01D80418` bits `0x18`).
  - Writes program value to SMN register via `FUN_000235c8(ivar4, param_2)`.
  - Polls status register `((ivar4 + 0x24) & 0xFFFFF) + 0x1100000` bit 16 until set.
- Aperture Primitive `FUN_000235c8`:
  - If `0x5AFFF < ivar4 <= 0x5B7FF`: IPC call `FUN_0001b514` to second SMU core.
  - Otherwise: Direct SMN store to `(ivar4 & 0xFFFFF) + 0x1100000`.

### Exact Hardware Register Mapping (20 Domains)

| Domain Index (1-based) | Domain ID | Classification | PLL Group (`+0x80`) | SMN Program Reg | SMN Poll Reg | Notes                     |
| :--------------------- | :-------- | :------------- | :------------------ | :-------------- | :----------- | :------------------------ |
| 1                      | `0x0D`    | CLK_GROUP_1    | `0x01`              | `0x0115B9D4`    | `0x0115B9F8` | Group 1 Clock             |
| 2                      | `0x00`    | CPU_CORE_0     | `0x00`              | `0x0115B114`    | `0x0115B138` | Core 0 Clock              |
| 3                      | `0x01`    | CPU_CORE_1     | `0x00`              | `0x0115B13C`    | `0x0115B160` | Core 1 Clock              |
| 4                      | `0x02`    | CPU_CORE_2     | `0x00`              | `0x0115B164`    | `0x0115B188` | Core 2 Clock              |
| 5                      | `0x03`    | CPU_CORE_3     | `0x00`              | `0x0115B18C`    | `0x0115B1B0` | Core 3 Clock              |
| 6                      | `0x04`    | CPU_CORE_4     | `0x00`              | `0x0115B1B4`    | `0x0115B1D8` | Core 4 Clock              |
| 7                      | `0x05`    | CPU_CORE_5     | `0x00`              | `0x0115B1DC`    | `0x0115B200` | Core 5 Clock              |
| 8                      | `0x06`    | CPU_CORE_6     | `0x00`              | `0x0115B204`    | `0x0115B228` | Core 6 Clock              |
| 9                      | `0x07`    | CPU_CORE_7     | `0x00`              | `0x0115B22C`    | `0x0115B250` | Core 7 Clock              |
| 10                     | `0x0A`    | CLK_GROUP_1    | `0x01`              | `0x0115B95C`    | `0x0115B980` | Group 1 Clock             |
| 11                     | `0x18`    | CLK_GROUP_6    | `0x06`              | `0x0116D150`    | `0x0116D174` | Group 6 Clock             |
| 12                     | `0x13`    | CLK_GROUP_5    | `0x05`              | `0x0116C900`    | `0x0116C924` | Group 5 (Gate 0x01D80414) |
| 13                     | `0x14`    | CLK_GROUP_5    | `0x05`              | `0x0116C928`    | `0x0116C94C` | Group 5 Clock             |
| 14                     | `0x15`    | CLK_GROUP_5    | `0x05`              | `0x0116C950`    | `0x0116C974` | Group 5 Clock             |
| 15                     | `0x16`    | CLK_GROUP_6    | `0x06`              | `0x0116D100`    | `0x0116D124` | Group 6 Clock             |
| 16                     | `0x17`    | CLK_GROUP_6    | `0x06`              | `0x0116D128`    | `0x0116D14C` | Group 6 Clock             |
| 17                     | `0x0B`    | CLK_GROUP_1    | `0x01`              | `0x0115B984`    | `0x0115B9A8` | Group 1 Clock             |
| 18                     | `0x08`    | CLK_GROUP_1    | `0x01`              | `0x0115B90C`    | `0x0115B930` | Group 1 Clock             |
| 19                     | `0x09`    | CLK_GROUP_1    | `0x01`              | `0x0115B934`    | `0x0115B958` | Group 1 Clock             |
| 20                     | `0x0C`    | CLK_GROUP_1    | `0x01`              | `0x0115B9AC`    | `0x0115B9D0` | Group 1 Clock             |

## Discriminative Verdict & Coverage Limits

1. **UCLK / UMC / DF Clock Isolation & Bounds**:
   - The observed actuator chain (`FUN_0002e788` -> `FUN_00023890` -> `FUN_000235c8`) touches SMN registers in apertures `0x0115Bxxx`, `0x0116Cxxx`, `0x0116Dxxx`, and `0x01D80414`.
   - Zero Data Fabric (DF) registers (`0x0001xxxx`, `0x0005xxxx`, `0x001Exxxx`) or Unified Memory Controller (UMC) UCLK divisor registers are observed in this specific register set.
   - Root Review Correction: The absence of DF/UMC known register ranges in this set cannot prove UCLK is not controlled (the clock generator/PLL architecture may use another aperture or indirect mechanism). UCLK mapping/control unestablished; observed address set only. No claim of physical clock synchronization.
2. **Helper Findings & Verifier Scope**:
   - Actuator helpers `FUN_00023890`, `FUN_000235c8`, `FUN_00023994`, `FUN_00023ab0`, `FUN_00023ac4`, and `FUN_00023c78` are documented via static disassembly and decompilation archived durably under `evidence/firmware-audit/20260919-oc-clock-provenance/ghidra-helpers-decompiles.txt`.
   - The deterministic verifier `verify-clock-handlers.py` tests raw instruction byte matching and literal loads for the primary dispatch and handlers, but does not exhaustively model all helper routing branches; helper findings are static disassembly only.
3. **Software Committed State vs Physical Hardware Telemetry**:
   - Mailbox `0x11` returns the value committed by `FUN_0002e788` into memory array `0x13F48`. It is a software committed state value, NOT a physical hardware PLL counter reading or frequency measurement.
   - Mailbox `0x13` returns an internal P-state counter difference, NOT a frequency in MHz.
   - Mailbox `0x1A` is restricted to GFX DFLL dividers (`DfllGfxDiv`) and has no relationship to UCLK/MCLK.
4. **Verification Scope**:
   - Analyzed offline against immutable binary baselines. Hardware response, actual PLL lock, and physical silicon frequency verification remain unrun and unverified.
