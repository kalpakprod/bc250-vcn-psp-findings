# PPTable Coefficients: BIOS Producer & SMU Actuator Chain Analysis

## Executive Summary

This document establishes the end-to-end trace from BIOS PEI/DXE producers through SMU validation, parsing, ratio scaling, and final hardware SMN register programming for the PPTable coefficients consumed by Robin-5 SMU function `0x21E8C`.

1. **BIOS Producer**:
   - Module: `AmdNbioSmuV10Dxe` (PE32 SHA-256 `b158f039f48db05e352b965a62c8e983a395a4858791c93c73f727285c9ac8d8`).
   - Construction: Function RVA `0x17DC` allocates `0x49C` bytes for the PPTable and initializes it by copying from compiled constant template at RVA `0x5D20` (raw `0x5D20`).
   - Fields:
     - `PPTable + 0x04..+0x13` (8 `uint16_t` values): `[128, 102, 93, 98, 91, 96, 89, 96]` = `CpuFid` for P0..P7.
     - `PPTable + 0x14..+0x1B` (8 `uint8_t` values): `[8, 8, 8, 10, 10, 12, 14, 24]` = `CpuDid` for P0..P7.
   - Debug Log: RVA `0x1CE5`/`0x1CEA` formats `PSTATES[%d] - CpuFid = 0x%02x, CpuDid = 0x%02x` using format string at RVA `0x6AD8`.
   - Source: Hardcoded BIOS DXE driver template constants; no AmdSetup or PCD overrides write these exact fields in static trace. Hook `0xB000000A` called at RVA `0x1C60` dispatches to protocol `0ecad4a0-75e9-46d7-a3a6-81fe173f2eca`.

2. **SMU Validator & Ingestion**:
   - SMU Binary: Robin-5 PMFW SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37` (CLV ROM `ea578104...` offset `0x8FEF00`).
   - Ingestion: Callback `0x1BC80` receives PPTable at staging buffer `0x7FF8`.
   - Validator: `FUN_0001bd20` validates each of the 8 entries:
     - `0x50 <= CpuFid <= 0xA0` (all template values `[128, 102, 93, 98, 91, 96, 89, 96]` are in range `[80, 160]`).
     - `8 <= CpuDid <= 0x30` (all template values `[8, 8, 8, 10, 10, 12, 14, 24]` are in range `[8, 48]`).
   - Committed: `0x1CC7C` copies `0x49C` bytes from `0x7FF8` to committed table base `0x7B5C`.

3. **Ratio Conversion & Actuator**:
   - Actuator Function: `FUN_00021e8c`.
   - Loop: Runs 8 iterations (`a3` increments from `0x7B5C` to `0x7B64`, comparing with `a9`).
   - Helper: `FUN_0001cbfc(CpuFid << 2, CpuDid)` computes:
     `ratio_ghz = ((CpuFid << 2) * 50000 / CpuDid) * 1e-6` = `(CpuFid * 200) / CpuDid` MHz.
     - P0: (128 * 200) / 8 = 3200 MHz
     - P1: (102 * 200) / 8 = 2550 MHz
     - P2: (93 * 200) / 8 = 2325 MHz
     - P3: (98 * 200) / 10 = 1960 MHz
     - P4: (91 * 200) / 10 = 1820 MHz
     - P5: (96 * 200) / 12 = 1600 MHz
     - P6: (89 * 200) / 14 = 1271.4 MHz
     - P7: (96 * 200) / 24 = 800 MHz
   - Hardware Writes:
     - Stores 8 floats to internal SRAM `0xF104..0xF123`.
     - Programs 8 SMN register pairs `0x0115A820 + 8*i` (low) and `0x0115A824 + 8*i` (high), covering `0x0115A820..0x0115A85C`.
     - Writes `0x000001FE` to SMN register `0x01004220` via `FUN_000014fc(4, 4, 0x1fe)`.
     - Programs SMN register `0x0115A864`.
     - Loops over active CPU cores (0..7) and writes `(bVar1 - 1 & 7) << 4` to CPU core clock register `aperture + 0x10bc`.

4. **Domain Discrimination**:
   - These coefficients are strictly CPU core clock/ratio controls (Zen2 `CpuFid`/`CpuDid`).
   - They do NOT affect Data Fabric clock (FCLK) or Memory clock (MCLK/UCLK).
   - Direct DF table modification is falsified.

5. **BIOS DF-Clock Override Token 1374**:
   - Token `0x1374` is serialized in `AmdFabricAriPei` (`c5b99650a442`) at RVA `0x11C98` from AmdSetup offset `0x704` (`DfClockOvrd`).
   - Static audit of all 233 executable UEFI bodies confirms only two generic `$INV` readers: `AmdFabricAriPei` (`1D3C`) and `AmdCcxVhAriDxe` (`5AC4`).
   - Direct callers only request tokens `10FF`/`1104` and `1000`/`1001`.
   - Bounded static analysis confirms no direct stock caller requests token `0x1374`. Any host fabric-program routine or override mechanism remains an open unknown.
