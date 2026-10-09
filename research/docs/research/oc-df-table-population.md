# SMU DF P-State Table (0xCF0C / 0xCEE0) Population & Host Influence Audit

## 1. Overview & Core Finding

- **Core Determination**: The Data Fabric (DF) P-state table at SRAM `0xCF0C` (`0xCF0C..0xCFD4`, stride 40 bytes, 5 P-state rows) contains **hardcoded static firmware default data** embedded directly in the Robin-5 PMFW binary image (`smu_fw_robin_5`, SHA-256 `cae8617c572613b6...`) at image file offset `0x0CF0C`, mapping to SRAM `0xCF0C` when loaded at CLV ROM (`BC250_5.00_clv.bin`, SHA-256 `ea5781049160ab...`) offset `0x8FEF00`.
- **Scope of Coverage & Negative Scan Limits**: Static disassembly and literal reference tracking across the 49 literal references to `0xCEE0` establish that no direct literal instruction in this observed set writes new frequency or divider values into table `0xCF0C`. **However**, static defaults do not prove immutability, and direct-reference scans do not rule out indirect, computed dispatch, or DMA writes into this region.
- **Host / PPTable Influence**: Host PPTable transfers (Queue 0 Message 0x07 `TransferTableDram2Smu`, handled by callback `FUN_0001bc80`) copy data into PPTable buffer `0x7B5C` and actuate VDD/GFX voltage margin floats at `0x13474`. Callback `0x1BC80` further calls `FUN_00021e8c()` and conditionally calls `FUN_0001e010()` if byte `*(0x7EDC + 0x7E) != 0` (full PPTable offset `+0x3FE`). While these routines do not write into table entries `0xCF0C..0xCFD4`, they write to SMN clock/hardware registers and per-core apertures (see `docs/research/oc-pptable-df-side-effects.md`).
- **No-Host / Immutability Overclaim Withdrawal**: Prior assertions that host/BIOS "cannot influence frequencies" or that "signed PMFW patching is necessary" are withdrawn as unproven. The absence of direct writes to `0xCF0C` shows only that the default table entries are not directly overwritten by this specific transfer; it does not prove complete absence of host influence or physical frequency changes through downstream side effects.

---

## 2. Pinned Firmware & Image Offsets

- **Host ROM**: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
  - SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- **SMU Binary**: `archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5`
  - SHA-256: `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`
  - ROM Offset: `0x8FEF00` (length 262,400 bytes, byte-for-byte identical).
- **Table SRAM Location**: `0x0000CF0C` (ROM file offset `0x8FEF00 + 0x0CF0C = 0x90BE0C`).

---

## 3. Static Table Content & Decoded Frequencies

The table spans `0xCF0C..0xCFD4` (200 bytes = 5 rows × 40 bytes):

| P-State | Table SRAM Offset | Raw Bytes (first 24 bytes)                                                | Rate A Float (+0x04) | Rate B Float (+0x10) | Rate C Float (+0x14) |
| ------- | ----------------- | ------------------------------------------------------------------------- | -------------------- | -------------------- | -------------------- |
| **0**   | `0x0000CF0C`      | `1e 30 00 00 00 00 7a 43 24 40 00 60 00 00 00 00 00 00 61 43 00 00 e1 42` | **250.0 MHz**        | **225.0 MHz**        | **112.5 MHz**        |
| **1**   | `0x0000CF34`      | `1e 30 00 00 00 00 7a 43 24 40 00 60 00 00 00 00 00 00 61 43 00 00 e1 42` | **250.0 MHz**        | **225.0 MHz**        | **112.5 MHz**        |
| **2**   | `0x0000CF5C`      | `1e 10 00 00 00 80 3b 44 22 20 00 60 00 00 00 00 00 80 d4 43 00 80 d4 42` | **750.0 MHz**        | **425.0 MHz**        | **106.25 MHz**       |
| **3**   | `0x0000CF84`      | `27 0d 00 00 00 00 96 44 23 10 00 60 00 00 00 00 00 c0 5a 44 00 c0 da 42` | **1200.0 MHz**       | **875.0 MHz**        | **109.375 MHz**      |
| **4**   | `0x0000CFAC`      | `1e 48 00 00 00 00 16 43 1e 50 00 50 00 00 00 00 00 00 fa 42 00 00 fa 42` | **150.0 MHz**        | **125.0 MHz**        | **125.0 MHz**        |

_Note on Rate Labels_: Rate A (+0x04), Rate B (+0x10), and Rate C (+0x14) correspond to Domain Descriptors 0x0E, 0x0F/0x11, and 0x10/0x12 respectively. While commonly associated with FCLK, UCLK, and SOCCLK in driver code, physical rail/clock domain identities and DDR4/GDDR6 rate equivalence are inferred architectural conventions, not established physical facts.

---

## 4. Header, Index Vectors & Initialization Logic (`0xCEE0`, `FUN_0001e038`)

The enclosing data structure starts at `0x0000CEE0` (referenced via literal `_DAT_000171ec`):

- `0xCEE0..0xCF0B` (44 bytes, `0x2C` bytes): Initialized to `0x00` in static binary. Contains runtime pointers and state tracking.
- `0xCF80..0xCF83` (`0xCEE0 + 0xA0`): Initial static index array: `[0x03, 0x02, 0x01, 0x00]`.
- `0xCFD0..0xCFD3` (`0xCEE0 + 0xF0`): Secondary static index array: `[0x00, 0xFF, 0xFF, 0xFF]`.

### Function `FUN_0001e038` (DF Init Handler)

Called from Queue 5 Msg 0x09 (`FUN_0001c3b0` at `0x1c3cf`):

1. Records `param_1` into `*(0xCEE0 + 0x11)` and `param_2` into `*(0xCEE0 + 0x12)`.
2. Reads hardware configuration `FUN_0002e4c4()` (reads `*(DAT_000170b0 + 4)` at `0x15774 + 4` = `8`).
3. Because `8 != 7`, it takes the standard branch:
   - Loops 4 times over index array at `0xCEE0 + 0xA0` (`0xCF80`), reading entries `[3, 2, 1, 0]`.
   - Computes row address: `row_ptr = 0xCEE0 + 0x2C + (index * 40) = 0xCF0C + index * 40`.
   - Writes row pointers into `0xCEE0 + 0x1C + (loop * 4)`:
     - Pointer 0 (`0xCEFC`) -> `0x0000CF84` (P-State 3: 1200 / 875 MHz)
     - Pointer 1 (`0xCF00`) -> `0x0000CF5C` (P-State 2: 750 / 425 MHz)
     - Pointer 2 (`0xCF04`) -> `0x0000CF34` (P-State 1: 250 / 225 MHz)
     - Pointer 3 (`0xCF08`) -> `0x0000CF0C` (P-State 0: 250 / 225 MHz)
   - Writes sequential P-state index (0, 1, 2, 3) to `*(row_ptr + 3)`.
   - Writes active P-state count `4` to `*(0xCEE0 + 0xF7)`.
   - Invokes `FUN_0001ef18()` to configure SMN fabric registers from row pointers.
   - Sets valid flag `*(0xCEE0 + 0x0C) = 1` and clears `*(0xCEE0 + 0x104) = 0`.

---

## 5. Trace of Direct Literal Writers & Scope Limits

### Struct 0xCEE0 Literal Trace

Literals referencing `0xCEE0` (`_DAT_000171ec`) appear in 49 `l32r` instructions across SMU firmware.

- Runtime writers to `0xCEE0` in this direct set are restricted to header fields:
  - `+0x0C`: Initialized flag (`FUN_0001e038`)
  - `+0x0D`: Current P-state index (`FUN_0001e448`)
  - `+0x11, +0x12`: Configuration parameters (`FUN_0001e038`)
  - `+0x13`: Enable gate byte (`FUN_0001e0b8`, `FUN_0001e0e8`)
  - `+0x1C..0x28`: 4 row pointers (`FUN_0001e038`)
  - `+0xF6`: P-state tracking index (`FUN_0001e6b0`)
  - `+0xF7`: P-state count bound (`FUN_0001e038`)
  - `+0x104, +0x108, +0x10C, +0x110`: Telemetry/timer state (`FUN_0001e0b8`)
- **Direct Table Range `0xCF0C..0xCFD4`**: No instruction in the 49 literal references writes to offsets `0x2C..0xF5` of struct `0xCEE0` other than the row-index byte write `*(row_ptr + 3) = loop_idx` during init.
- **Coverage Boundary**: This bounded scan confirms static defaults and direct literal references only; it does not prove the impossibility of indirect pointer stores, DMA engine writes, or external writes.

### PPTable Callback Callees (`FUN_0001bc80`)

- `FUN_0001bc80` receives host buffer pointer `param_1`, copies 0x49C bytes into temporary buffer `0x7FF8` (`_DAT_00017118`).
- Calls validator `FUN_0001bd20(0x7FF8)`.
- On validation success, copies 0x49C bytes to operational PPTable buffer `0x7B5C` (`_DAT_0001711c`).
- Computes voltage scaling into actuator struct `0x13474 + 0x14` and `+0x30`.
- Calls `FUN_00021e8c()` unconditionally.
- Calls `FUN_0001e010()` conditionally if byte `*(0x7EDC + 0x7E) != 0` (full PPTable offset `+0x3FE`).
- Detailed analysis of `0x21E8C` and `0x1E010` is presented in `docs/research/oc-pptable-df-side-effects.md`.

---

## 6. Upstream Driver Correlation & Physical Classification

- In `archives/imported/recon-evidence/legacy-tmp-bc250-recon/cyan_skillfish_ppt.c`:
  - `METRICS_CURR_UCLK` is read to report both `SMU_UCLK` and `SMU_FCLK` via sysfs `pp_dpm_fclk` and `pp_dpm_mclk`.
- Driver and community labels:
  - Rate A 1200 MHz and Rate B 875 MHz represent maximum DF P-state (P0 in driver / P3 in SMU internal table).
  - The prior DDR4/GDDR6 rate equivalence is withdrawn: the stored float alone establishes neither memory clock nor transfer-rate conversion.
  - **Inference Label**: These identities (FCLK/UCLK/SOCCLK) and memory rate relationships are inferred architectural conventions. They are not byte-proven physical facts.

---

## 7. Conclusions & Scope Boundaries

1. **Static Defaults**: The table at `0xCF0C` in the binary contains default values (250/225, 250/225, 750/425, 1200/875, 150/125 MHz).
2. **Direct Reference Isolation**: Direct static literal references to `0xCEE0` do not write new frequencies into `0xCF0C`.
3. **No Immutability Proof**: Static defaults and absence of direct writes do not prove that frequencies cannot be altered via indirect mechanisms, DMA, or downstream side effects.
4. **Build vs Flash**: The user requests an offline BIOS candidate; current evidence is insufficient for the requested synchronized profile. Flash approval and recovery verification remain separate gates.
