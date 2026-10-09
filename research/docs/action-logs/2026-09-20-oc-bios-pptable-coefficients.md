# Action Log: BIOS Producer & SMU Actuator Trace for PPTable Coefficients — 2026-09-20

## Summary

Offline analysis traced the exact BIOS producer and SMU consumer chain for PPTable coefficients ingested at Robin-5 SMU `0x21E8C`.

## Actions Taken

1. Re-verified CLV ROM SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`, Robin-5 SMU `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`, and extracted `AmdNbioSmuV10Dxe` `b158f039f48db05e352b965a62c8e983a395a4858791c93c73f727285c9ac8d8`.
2. Traced PPTable constructor in `AmdNbioSmuV10Dxe` at RVA `0x17DC`:
   - Allocates `0x49C` bytes.
   - Copies static template from RVA `0x5D20`:
     - Words at `+0x04..+0x13`: `[128, 102, 93, 98, 91, 96, 89, 96]` (`CpuFid` for P0..P7).
     - Bytes at `+0x14..+0x1B`: `[8, 8, 8, 10, 10, 12, 14, 24]` (`CpuDid` for P0..P7).
   - Debug logging at RVA `0x1CE5`/`0x1CEA` labels these fields: `PSTATES[%d] - CpuFid = 0x%02x, CpuDid = 0x%02x` (format string RVA `0x6AD8`).
   - Fields originate as hardcoded constants in the DXE template; no direct PCD/Setup writes occur to these offsets in static code.
3. Verified SMU validation and consumer math:
   - `0x1BD20` validates `0x50 <= CpuFid <= 0xA0` and `8 <= CpuDid <= 0x30`.
   - `0x21E8C` executes an 8-iteration loop (a3: `0x7B5C..0x7B64`) calling `0x1CBFC(CpuFid << 2, CpuDid)`.
   - Exact conversion formula: `ratio = ((CpuFid << 2) * 50000 / CpuDid) * 1e-6` = `(CpuFid * 200) / CpuDid` MHz.
   - Values: P0=3200, P1=2550, P2=2325, P3=1960, P4=1820, P5=1600, P6=1271.4, P7=800 MHz.
   - SMN register programming: writes pairs to `0x0115A820..0x0115A85C`, `0x1FE` to `0x01004220`, updates `0x0115A864`, and writes `(bVar1 - 1 & 7) << 4` to active core apertures `aperture + 0x10BC`.
4. Domain classification: These fields are confirmed CPU core P-state frequency ratios. They do not affect MCLK, UCLK, or Data Fabric clocks.
5. DF clock override token 1374:
   - Token `0x1374` is serialized in `AmdFabricAriPei` (RVA `0x11C98`) from Setup `+0x704`.
   - Bounded caller audit of all 233 executable modules confirmed no direct static consumer for `0x1374` in either generic reader (`1D3C` or `5AC4`).
6. Delivered audit artifact `evidence/firmware-audit/20260920-oc-pptable-coefficients/pptable-coefficients-audit.json` and research doc `docs/research/oc-bios-pptable-coefficients.md`.
