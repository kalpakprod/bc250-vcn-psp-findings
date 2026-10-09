# OC Fabric Domain Identification and SMU Rate Encoding Analysis

## Executive Summary & G7 Correction

- **G7 Correction**: Previous audits hardcoded DF/UCLK identities and assumed 1:1:1 synchronization without hardware or firmware telemetry proof. Prior claims that 1750 MHz memory implies 1750 MHz FCLK/UCLK were unbacked. The promised research report was absent and is established here with reproducible byte evidence.
- **Scope & Model Limits**: Offline firmware analysis on pinned SMU Robin-5 (`cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`) matching BC250 CLV ROM (`ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`) at offset `0x8FEF00`. No ROM modification, candidate generation, or board flash.
- **Classification Rule**: Exact byte structures and firmware logic are classified as `observed/static`. Physical clock line mappings and real-world rail behaviors remain unproven.

## SMU Helper 0x2360C: Rate Encoding Function

Disassembly and decompilation of `0x2360C` using read-only headless Ghidra analysis (`OcConsumerRead.java`):

```c
float FUN_0002360c(uint param_1) {
  return (float)(param_1 & 0x1ff) / 1.0 + ((float)(param_1 >> 0x10) / 1.0) * _DAT_00017460;
}
```

### Bitfield & Type Specification

- **Literal `0x17460`**: IEEE-754 single precision float `0x37800000` = `2^-16` = `1.52587890625e-05` (`1.0 / 65536.0`).
- **Bitfield Layout (`uint32_t`)**:
  - `Bits [8:0]` (9 bits): Unsigned integer multiplier (`param_1 & 0x1FF`), range 0..511.
  - `Bits [15:9]` (7 bits): Ignored / unmapped by mask and shift operations.
  - `Bits [31:16]` (16 bits): Unsigned fractional part (`param_1 >> 16`), scaled by `1 / 65536.0`.
- **Representation**: Unsigned fixed-point U9.16.
- **Companion Helper `0x23654`**: Implements three-way fixed-point comparison `(param_1 >> 16) + (param_1 & 0x1FF) * 0x10000` against `param_2`.

### Arithmetic Probe & Boundary Verification

- `0x00000000` -> `0.0`
- `0x000001FF` -> `511.0`
- `0x00010000` -> `1 / 65536.0` (`~0.00001526`)
- `0x80000000` -> `0.5`
- `0xFFFF01FF` -> `511.99998474121094`
- `0x0000FE00` (ignored bits `[15:9]` set) -> `0.0`

## SMU Helper 0x1CAD8: AMD DFS Divider Decoding

Called by `0x23F18` to translate 8-bit post-divider / DID codes to floating-point divisors:

- Scaling literal `0x17270` = `0.25f` (`1/4`).
- Clamp literal `0x17274` = `128.0f`.
- Formula:
  - If `code <= 0x40` (64): `divisor = code * 0.25`
  - If `code <= 0x60` (96): `divisor = (code * 2 - 64) * 0.25 = (code - 32) * 0.5`
  - If `code <= 0x7E` (126): `divisor = (code * 4 - 256) * 0.25 = code - 64.0`
  - If `code >= 0x7F`: `divisor = 128.0`

## Provenance Chain: 1E720 -> 1E448 -> Actuators -> 23F18

The DF P-state dispatch path flows:

1. **Queue 5 Message 0x07 (`0x1E720`)**: SetDfPstate handler validates requested P-state against bound `*(0xCEE0 + 0xF7)` and invokes `0x1E448`.
2. **Applier `0x1E448`**: Reads row pointer `*(0xCEE0 + 0x1C + pstate * 4)` pointing into table `0xCF0C` (stride 40 bytes).
3. **Actuator Calls**:
   - `0x23B7C(row[2], row[0], row[1])`:
     - Writes `row[0]` to Clock Group 2 (offset `0xF5F8 + 0x00`).
     - Invokes `0x23EF8(Group 2)`, which evaluates `0x2360C(row[0]) * Group[2].word4` (`0.1f`), yielding VCO frequency in GHz.
     - Writes `row[1]` to Domain Descriptor 0x0E (offset `+0x02`).
     - Invokes `0x23F18(Domain 0x0E)`, computing `VCO / DFS_DID(row[1])`.
   - `0x23BA8(row[10], row[8], row[9])`:
     - Targets Clock Groups 3 & 4 and Domain Descriptors 0x0F and 0x11.
     - Multiplier VCO is `0x2360C(row[8]) * 0.1f`. Divisor is `DFS_DID(row[9])`.
   - `0x23BF4(row[12], row[8], row[11])`:
     - Targets Clock Groups 3 & 4 and Domain Descriptors 0x10 and 0x12.
     - Multiplier VCO is `0x2360C(row[8]) * 0.1f`. Divisor is `DFS_DID(row[11])`.

## Reproduction: Encoded Rates vs Stored P-state Rates

Evaluating the decoded formulas on the 5 P-states at `0xCF0C`:

| P-state | Domain 0x0E (row[0], row[1]) | VCO (GHz) | DID   | Computed Rate | Stored Float at +0x04 | Domain 0x0F/0x11 (row[8], row[9]) | Computed Rate | Stored Float at +0x10 | Domain 0x10/0x12 (row[8], row[11]) | Computed Rate | Stored Float at +0x14 |
| ------- | ---------------------------- | --------- | ----- | ------------- | --------------------- | --------------------------------- | ------------- | --------------------- | ---------------------------------- | ------------- | --------------------- |
| 0       | 30, 48                       | 3.00      | 12.00 | 250.0 MHz     | 250.0 MHz             | 36, 64                            | 225.0 MHz     | 225.0 MHz             | 36, 96                             | 112.5 MHz     | 112.5 MHz             |
| 1       | 30, 48                       | 3.00      | 12.00 | 250.0 MHz     | 250.0 MHz             | 36, 64                            | 225.0 MHz     | 225.0 MHz             | 36, 96                             | 112.5 MHz     | 112.5 MHz             |
| 2       | 30, 16                       | 3.00      | 4.00  | 750.0 MHz     | 750.0 MHz             | 34, 32                            | 425.0 MHz     | 425.0 MHz             | 34, 96                             | 106.25 MHz    | 106.25 MHz            |
| 3       | 39, 13                       | 3.90      | 3.25  | 1200.0 MHz    | 1200.0 MHz            | 35, 16                            | 875.0 MHz     | 875.0 MHz             | 35, 96                             | 109.375 MHz   | 109.375 MHz           |
| 4       | 30, 72                       | 3.00      | 20.00 | 150.0 MHz     | 150.0 MHz             | 30, 80                            | 125.0 MHz     | 125.0 MHz             | 30, 80                             | 125.0 MHz     | 125.0 MHz             |

Every computed rate exactly reproduces the IEEE-754 floats stored in the table.

## Remaining Technical Gaps & Limits

1. **DF P-State Table Population (Determined 2026-09-19)**:
   - As documented in `docs/research/oc-df-table-population.md`, table `0xCF0C` is **static ROM data**, not populated by host PPTable or mailboxes.
   - P-state 3 rates remain hardcoded in SMU binary to FCLK 1200 MHz, UCLK 875 MHz, SOCCLK 109.375 MHz.
2. **Physical Meaning of Clock Domains**:
   - While Domain 0x0E matches the frequency commonly associated with FCLK, and 0x0F/0x11 matches UCLK, firmware structures only expose group IDs and register offsets.
   - Physical routing from SMN apertures to hardware fabric dividers is unverified without oscilloscope/JTAG or vendor schematics.
3. **No 1:1 Patch Justified**:
   - Forcing P-state 3 rate to 1750 MHz without knowing fabric PLL bounds, lock stability, or voltage dependency risks non-boot or brick.
   - No 1750 MHz patch is authorized.
