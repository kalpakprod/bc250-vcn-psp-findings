# PPTable Callback Side Effects & DF Isolation Analysis

## 1. Executive Summary

- **Target Callback**: `FUN_0001bc80` (Queue 0 Message 0x07 `TransferTableDram2Smu` handler in Robin-5 PMFW, CLV ROM offset `0x8FEF00`).
- **Callees Investigated**:
  1. `FUN_00021e8c`: Unconditionally invoked after PPTable copy and voltage float scaling.
  2. `FUN_0001e010`: Conditionally invoked if PPTable subtable flag `*(0x7EDC + 0x7E) != 0` (`0x7B5C + 0x3FE`).
- **Exact Side Effects & Written Registers**:
  - `FUN_00021e8c`:
    - Evaluates 8 CPU P-state ratio entries (P0..P7) from PPTable `0x7B5C + 0x04..0x13` (`CpuFid[0..7]`) and `0x7B5C + 0x14..0x1B` (`CpuDid[0..7]`) via `FUN_0001cbfc`, writing 8 floats to internal SRAM `0xF104..0xF123`.
    - Computes frequency `(CpuFid * 200) / CpuDid` MHz (P0=3200, P1=2550, P2=2325, P3=1960, P4=1820, P5=1600, P6=1271.4, P7=800 MHz).
    - Programs 8 SMN register pairs at `0x0115A820..0x0115A85C` (stride 8).
    - Writes control value `0x1FE` to register `0x01004220` via `FUN_000014fc(4, 4, 0x1fe)`.
    - Programs SMN register `0x0115A864` (`_DAT_00017148 + 0x264`).
    - Loops across active CPU cores (0..7) and writes `(bVar1 - 1 & 7) << 4` to per-core aperture `aperture + 0x10bc`.
    - These controls act strictly on CPU core clocks/ratios, not memory clocks (MCLK) or Data Fabric.
  - `FUN_0001e010` (Actuated by flag `+0x7E`):
    - Loops across active CPU cores (0..7) based on enable byte array `*(0x7AE0 + 0x28 + i)`.
    - Writes literal `1` to per-core aperture `aperture + 0x142c`.
    - Does **NOT modify table frequencies** or table entries in DF table `0xCF0C..0xCFD4`.
    - Acts as an **enable / trigger flag write** to CPU core control apertures.
- **DF Independence Determination**: Neither `FUN_00021e8c` nor `FUN_0001e010` accesses, references, or modifies the Data Fabric (DF) P-state table at `0xCF0C` or struct `0xCEE0`.

---

## 2. Baseline Hashes & Offsets

- **Host BIOS ROM**: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
  - SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
  - Size: 16,777,216 bytes
- **Robin-5 SMU Firmware**: `archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5`
  - SHA-256: `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`
  - Size: 262,400 bytes
  - ROM Offset: `0x8FEF00` (byte-for-byte identical to SMU binary).
- **Candidate Hashes**:
  - No new candidate binary was created in this offline audit pass.
  - Historical reference: `candidates/BC250_5.00_clv_VcnUnlock_W9_v001.bin` SHA-256 `3c50bc9a65194b75ca805e6ed31c5778369de1fe8eca4600f44e15fae3b40fc3`.

---

## 3. Detailed Callee Disassembly & Side Effects

### 3.1 Function `FUN_0001e010`: Flag +0x7E Actuator

Invoked conditionally from `FUN_0001bc80` at `0x1BCDA`:

```assembly
0001bcd5 c2027e    l8ui a12, a2, 0x7e      ; a2 = _DAT_00017120 = 0x7edc. Loads flag at 0x7edc + 0x7e = 0x7f5a
0001bcd8 8c1c      beqz.n a12, 0x0001bcdd  ; if 0, branch to retw.n
0001bcda 653302    call8 0x0001e010        ; if non-zero, invoke 0x1e010
```

Disassembly of `FUN_0001e010`:

```assembly
0001e010 364100    entry a1, 0x20
0001e013 4113e4    l32r a4, 0x00017060     ; a4 = literal at 0x17060 = 0x7ae0
0001e016 0c15      movi.n a5, 0x1          ; a5 = 1 (write payload)
0001e018 0c82      movi.n a2, 0x8          ; a2 = 8 (core loop count)
0001e01a 403420    mov a3, a4              ; a3 = 0x7ae0
0001e01d 76a212    loopgtz a2, 0x0001e033  ; 8-iteration loop
0001e020 820328    l8ui a8, a3, 0x28       ; a8 = *(0x7ae0 + 0x28 + i) (core active flag)
0001e023 98c4      l32i.n a9, a4, 0x30     ; a9 = *(0x7ae0 + 0x30 + i*4) (core aperture base)
0001e025 8c68      beqz.n a8, 0x0001e02f   ; if not active, skip write
0001e027 92d914    addmi a9, a9, 0x1400    ; a9 += 0x1400
0001e02a c02000    memw
0001e02d 59b9      s32i.n a5, a9, 0x2c     ; *(a9 + 0x2c) = 1 (aperture + 0x142c = 1)
0001e02f 4b44      addi.n a4, a4, 0x4      ; advance aperture pointer
0001e031 1b33      addi.n a3, a3, 0x1      ; advance flag pointer
0001e033 0c12      movi.n a2, 0x1
0001e035 1df0      retw.n
```

#### Core Apertures at `0x7AE0 + 0x30`

| Core Index | Active Flag Address | Aperture Base | Target Register (`+0x142c`) | Written Value |
| ---------- | ------------------- | ------------- | --------------------------- | ------------- |
| Core 0     | `0x00007B08`        | `0x01400000`  | `0x0140142C`                | `0x00000001`  |
| Core 1     | `0x00007B09`        | `0x01420000`  | `0x0142142C`                | `0x00000001`  |
| Core 2     | `0x00007B0A`        | `0x01440000`  | `0x0144142C`                | `0x00000001`  |
| Core 3     | `0x00007B0B`        | `0x01460000`  | `0x0146142C`                | `0x00000001`  |
| Core 4     | `0x00007B0C`        | `0x01800000`  | `0x0180142C`                | `0x00000001`  |
| Core 5     | `0x00007B0D`        | `0x01820000`  | `0x0182142C`                | `0x00000001`  |
| Core 6     | `0x00007B0E`        | `0x01840000`  | `0x0184142C`                | `0x00000001`  |
| Core 7     | `0x00007B0F`        | `0x01860000`  | `0x0186142C`                | `0x00000001`  |

**Finding**: Flag `+0x7E` controls a binary trigger write (`1`) to CPU core hardware registers at `aperture + 0x142c`. It does **not** change frequency entries in any table.

---

### 3.2 Function `FUN_00021e8c`: Unconditional Clock/Ratio Actuator

Invoked from `FUN_0001bc80` at `0x1BCD2`:

```assembly
0001bcd2 a51b06    call8 0x00021e8c
```

#### Key Operations:

1. **Ratio Loop (8 iterations, P0..P7)**:
   - Loop variable `a3` runs from `0x7B5C` to `0x7B64` (8 iterations).
   - Reads 16-bit word `uVar2 = *(0x7B5C + 0x04 + i*2)` (`CpuFid`) and 8-bit byte `bVar1 = *(0x7B5C + 0x14 + i)` (`CpuDid`).
   - Computes float `fVar9 = FUN_0001cbfc(uVar2 << 2, bVar1)` = `((uVar2 << 2) * 50000 / bVar1) * 1e-6` = `(uVar2 * 200) / bVar1` MHz.
   - P-state frequencies: P0=3200, P1=2550, P2=2325, P3=1960, P4=1820, P5=1600, P6=1271.4, P7=800 MHz.
   - Writes 8 floats to `pfVar16 = _DAT_0001778c + i` (`0xF104 + i*4`).
   - Writes `0x80000000` to SMN register `0x0115A824 + i*8` (covers `0x0115A824..0x0115A85C`).
   - Writes packed word `(uVar18 | (trunc(fVar19) * 0x400000) | 0x140000) & 0x3FFFFFFF | 0x40000000` to SMN register `0x0115A820 + i*8` (covers `0x0115A820..0x0115A858`).
2. **SMN Bridge Call**:
   - Calls `FUN_000014fc(4, 4, 0x1fe)`.
   - In `FUN_000014fc`, `param_1 = 4`, which computes `(((4 & 0x3ff) * 0x1000 + 0x9000220) & 0xfffff) + 0x1000000` = `0x01004220`.
   - Writes `0x000001FE` to SMN register `0x01004220`.
3. **Register `0x0115A864` Programming**:
   - Evaluates helper lookups via `FUN_0001cd80` and `FUN_000223b8`.
   - Stores packed word to `_DAT_00017148 + 0x264` (`0x0115A600 + 0x264 = 0x0115A864`).
4. **Per-Core Clock Control (`aperture + 0x10bc`)**:
   - Reads `bVar1 = *(0xF0D4 + 0x50)`.
   - For each active core, writes `(bVar1 - 1 & 7) << 4` to `aperture + 0x10bc` (`0x014010BC`, `0x014210BC`, etc.).

---

## 4. Synthesis: Actuator Aperture Map for CPU Cores

By cross-referencing `FUN_00020b04` (actuator-pass7.txt), `FUN_00021e8c`, and `FUN_0001e010`, the per-core aperture offsets are byte-proven:

| Register Offset     | Written By     | Value / Meaning                        | Classification               |
| ------------------- | -------------- | -------------------------------------- | ---------------------------- |
| `aperture + 0x10b0` | `FUN_00020b04` | VID code `((VID & 0xff) << 7) \| ...`  | Core VID / Voltage Code      |
| `aperture + 0x10bc` | `FUN_00021e8c` | `(bVar1 - 1 & 7) << 4`                 | Core Clock / Ratio Control   |
| `aperture + 0x142c` | `FUN_0001e010` | `1` (actuated by PPTable flag `+0x7E`) | Core Enable / Commit Trigger |

None of these apertures reside in the Data Fabric register space (`0x0001xxxx`, `0x0005xxxx`, `0x001Exxxx`).

---

## 5. Bounded Verifier & Instruction Assertions

Reproducible raw instruction checks verified via `scripts/verify_df_table_population.py`:

- `0x1BCD2` (`call8 0x00021e8c`): `a5 1b 06`
- `0x1BCD5` (`l8ui a12, a2, 0x7e`): `c2 02 7e`
- `0x1BCDA` (`call8 0x0001e010`): `65 33 02`
- `0x1E027` (`addmi a9, a9, 0x1400`): `92 d9 14`
- `0x1E02D` (`s32i.n a5, a9, 0x2c`): `59 b9`

Verifier stdout:

```
VERIFIER_RESULT: BOUNDED_STATIC_CHECKS_PASSED (static binary coverage only, does not prove runtime/indirect/DMA write isolation)
```

---

## 6. Limits & Authority

- **Static Coverage Only**: The analysis verifies static instructions and direct callees. It does not provide full runtime execution trace or prove that external hardware / coprocessors cannot alter firmware state.
- **No Flash Authorization**: These findings do not establish a working overclocking route or authorize flashing candidate images to hardware.
