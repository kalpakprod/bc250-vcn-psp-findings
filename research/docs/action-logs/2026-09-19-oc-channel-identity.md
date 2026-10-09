# Voltage channel identity: physical rail mapping, selector attribution, and SVI2 verification

## Intent — 2026-09-19T21:05:00+05:00

Actor: bounded code/RE agent. Offline BC250 voltage channel investigation following actuator route analysis.
Inputs asserted:

- CLV BIOS ROM SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8` (16,777,216 bytes)
- Robin SMU firmware SHA-256: `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37` (262,400 bytes)
- Match offset: `BC250_5.00_clv.bin` at `0x8FEF00` equals `smu_fw_robin_5` body.
  Target files:
- `docs/action-logs/2026-09-19-oc-channel-identity.md` (this log)
- `docs/research/2026-09-19-oc-channel-identity.md` (new research report)
- `evidence/firmware-audit/20260919-oc-final-consumer-pass/actuator-verify.py` (channel verification checks)

No candidate creation, flashing, builder modification, hardware access, or network calls.

## Investigation and Results — 2026-09-19T21:15:00+05:00

1. **Selector Mapping**:
   - `FUN_0002bdec`: commands `(VID << 16) | 0x00` to SMN `0x0115A030`. Actuates Selector 0 (tracks `_DAT_00017124 + 0x00` float, `+0x04` VID).
   - `FUN_0002be40`: commands `(VID << 16) | 0x01` to SMN `0x0115A030`. Actuates Selector 1 (tracks `_DAT_00017124 + 0x20` float, `+0x24` VID).
   - `FUN_0002be18`: commands `(VID << 16) | 0x20` to `0x0115A030` using default calibration from `_DAT_0001714c + 1`.

2. **Domain Attribution & G7 Corrections**:
   - Per-core CPU voltage does write VID directly to per-core apertures `*(iStack_64 + 0x10b0)` in `FUN_00020b04`, but having separate per-core VID apertures does **not** distinguish a shared CPU supply from SoC or uncore rails.
   - Attributing Selectors 0 and 1 to "package / uncore" rails based on Linux kernel driver `cyan_skillfish_ppt.c` labelling `Voltage[0]` = `VDDSOC` and `Voltage[1]` = `VDDGFX` was an overclaim: driver labels do not identify actuator selector 0/1 without a verified firmware producer-to-actuator mapping.
   - Setup `0x6E6` / token `0x1364` is `VddcrVddOffset`, not `VddcrSocOffset`. Assuming VDD = SoC was an unproven inference.

3. **SVI2 Verification**:
   - Searched `smu_fw_robin_5` for strings `SVI`, `SVI2`, `VR12`, `VR13`. Found 0 occurrences.
   - SVI2 terminology is an external architectural inference based on AMD APU VRM design (ISL69247/ISL95712), not an explicit firmware string.

4. **Missing Link & Scope of Consumer Search**:
   - No consumer in stock CLV PEI/DXE direct call-sites was located for CBS token `0x1364`. However, asserting "no stock 1364 consumer" was too broad, as earlier caller coverage did not exhaustively analyze indirect or dynamic dispatch.

5. **Outcome**:
   - Report written to `docs/research/2026-09-19-oc-channel-identity.md`.
   - Verification checks confirmed against ROM SHA-256 and SMU SHA-256.
