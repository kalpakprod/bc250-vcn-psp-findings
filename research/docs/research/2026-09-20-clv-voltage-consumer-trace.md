# CLV Voltage Consumer Trace ($INV/NVTB) — Whole-Image Audit

> Correction 2026-09-23: voltage token labels and universal inertness claims below are superseded by [the byte-backed correction](2026-09-23-clv-voltage-token-correction.md). `0x1363/0x1364` are VDD control/value. GFX control/value are `0x1365/0x1366`. The scan does not exclude computed or indirect consumers. Historical text retained for provenance.

Date: 2026-09-20  
Evidence Class: `observed-bytes` + `static-analysis`  
Target: CLV donor ROM `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`  
SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8` (16,777,216 bytes)

---

## 1. Executive Summary

A whole-image forensic audit was conducted across the entire 16 MB CLV donor ROM (`BC250_5.00_clv.bin`) to determine whether AMD CBS tokens **0x1364** (`VDDCR_GFX_OFFSET`, mapped from `AmdSetup+0x6EA/+0x6EB`) and **0x1363** (`VDDCR_VDD_OFFSET`, mapped from `AmdSetup+0x6E5/+0x6E6`) are consumed anywhere in the firmware, either within UEFI PE/TE modules or within non-UEFI PSP/SMU/ABL carriers.

### Key Findings:

1. **Zero `$INV`/`NVTB` Markers in Non-UEFI Carriers**:
   - The literal markers `$INV` (`24 49 4E 56`) and `NVTB` (`4E 56 54 42`) occur 8 times and 1 time respectively in the raw ROM.
   - All 9 occurrences reside strictly in the **non-PSP** (UEFI FV) region, attributed to PEI modules (`AmdFabricAriPei`, `AmdNbioBaseARIPei`, `AmdNbioGfxARIPei`, `AmdNbioPcieARIPei`, `AmdNbioSmuV10Pei`, `AmdSocBl5AriPei`, `CbsBasePei`).
   - Across all 19 PSP directory entries (raw and zlib-decompressed, including PSP Bootloader, SMU Offchip Firmware, and ABL1–ABL4), **zero** `$INV` or `NVTB` markers exist.

2. **Zero Consumers in UEFI Modules**:
   - The 20260919 census (233 extracted executable modules) and `scan_inv_consumers.py` confirmed that only two modules contain inlined `$INV`/`NVTB` table readers:
     - `AmdFabricAriPei` (PEI 32-bit, RVA `0x1D3C`)
     - `AmdCcxVhAriDxe` (DXE 64-bit, RVA `0x5AC4`)
   - Neither reader is ever called with token ID `0x1363` or `0x1364`. There are **0 callers** querying these voltage offset tokens anywhere in the 233-module corpus.

3. **Analysis of Incidental Byte Matches in PSP Carriers**:
   - Little-endian matches for `0x1363` (`63 13`) and `0x1364` (`64 13`) in PSP payloads were analyzed in context:
     - **SMU_OFFCHIP_FW**: Occurrences at `0x901B0C` (`63 10 ... 63 11 ... 63 13 ... 63 14 ...`) and `0x91A6D9` (`64 11 ... 64 12 ... 64 13 ...`) are sequential byte patterns / instruction encodings, not little-endian 16-bit CBS token identifiers.
     - **PSP_BOOTLOADER / DRIVER_ENTRIES / ABL**: Matches are unaligned or embedded in encrypted/compressed/data regions without any token table structure.
   - No hit is preceded by a `0xFFFF` table terminator, and zero `(0x1363, 0x1364)` pairs occur within 8 bytes anywhere in the ROM.

4. **Definitive Conclusion on Voltage Tokens**:
   - CBS tokens `0x1363` and `0x1364` are **producers-only / inert Setup options**.
   - They are written to NVRAM by `CbsBasePei` (RVA `0xE3C4/0xE3F6`) and `AmdSocBl5AriPei` (RVA `0x10184/0x101B6`) when configured in `AmdSetup`, but are **never read or actuated by any firmware component**.
   - The historical recipe claiming `AmdSetup+0x6EA=80` controls or offsets GPU/SoC voltage on BC-250 is an inert placebo with zero hardware or firmware consumer.

---

## 2. Evidence and Measurements

### 2.1 Machine Scans

- **Non-UEFI Scanner**: `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/scan_non_uefi_inv.py`
  - Exit code: `0`
  - Machine result: `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/non-uefi-inv-scan.json` (SHA-256: `4d1f4da3f13839236189a3d58a0ec404b3cba7f97f613aaddbfb85ac2823aec1`)
  - Stdout: `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/non-uefi-inv-scan.stdout`
  - Stderr: `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/non-uefi-inv-scan.stderr` (0 bytes)
- **UEFI Inlined Reader Scanner**: `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/scan_inv_consumers.py`
  - Exit code: `0`
  - Machine result: `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/inv-consumer-scan.json` (SHA-256: `2e5bf0a5f25d1ede73e134c22830ffbd9c37b50fcf7cdc70d60bc317ab8965b3`)

### 2.2 Marker Distribution

| Marker                | Total Hits | Non-PSP Region | PSP Directory Entries (Raw) | PSP Payloads (Decompressed) |
| --------------------- | ---------- | -------------- | --------------------------- | --------------------------- |
| `$INV` (`0x564E4924`) | 8          | 8              | 0                           | 0                           |
| `NVTB` (`0x4254564E`) | 1          | 1              | 0                           | 0                           |

All hits reside in the UEFI PEI volume. No non-UEFI component contains `$INV` or `NVTB` table infrastructure.

### 2.3 Token ID Distribution

| Token ID | Meaning            | Raw ROM Hits | Non-PSP Hits | PSP Raw Hits | Decompressed PSP Hits | Active Consumers |
| -------- | ------------------ | ------------ | ------------ | ------------ | --------------------- | ---------------- |
| `0x1363` | `VDDCR_VDD_OFFSET` | 46           | 36           | 10           | 7                     | **0**            |
| `0x1364` | `VDDCR_GFX_OFFSET` | 39           | 33           | 6            | 5                     | **0**            |

All raw/decompressed PSP hits were inspected; none represent token queries or record table entries.

---

## 3. Verdict and Impact

- **Verdict**: `CONFIRMED_INERT_SETUP_OPTION`
- **Impact on Overclocking / Tuning**:
  - `AmdSetup+0x6EA=80` does NOT adjust voltage.
  - No software or firmware mechanism exists via CBS `$INV` tokens to adjust VDDCR_VDD or VDDCR_GFX on BC-250.
  - Any observed voltage changes in historical community experiments were either measurement artifacts or resulted from physical hardware modifications (e.g. feedback resistor mods reported in AyuGram chat ID 772341–772344), not firmware configuration.
