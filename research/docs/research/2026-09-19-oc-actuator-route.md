# Voltage Actuator Route: Hardware Actuation Chain, Conversion Formula, and Routing Gaps

## 1. Executive Summary & Verification Imperative

A prior exploratory note introduced an arithmetic transcription error asserting `0x01159E00 + 0x230 = 0x01159E30`.
Direct calculation from the verified firmware literals yields the correct addresses:

- **Base register**: `_DAT_000171a4` = `0x01159E00` (SMN aperture base)
- **Status / Polling register**: `0x01159E00 + 0x200` = `0x0115A000` (busy flag polled via `bbsi aX, 0x1f`)
- **Actuation / Command register**: `0x01159E00 + 0x230` = `0x0115A030`
- **Control / Mask registers**:
  - `0x01159E00 + 0x250` = `0x0115A050`
  - `0x01159E00 + 0x260` = `0x0115A060` (cleared via `& 0xfffffffe`)
  - `0x01159E00 + 0x270` = `0x0115A070` (`& 0xffffff3f`)
  - `0x01159E00 + 0x274` = `0x0115A074` (`& 0xffffff3f`)

Verification script `evidence/firmware-audit/20260919-oc-final-consumer-pass/actuator-verify.py` was executed to output `actuator-verification-recheck.json` without modifying existing evidence. All 280 `call8` targets, 393 `l32r` literals, and instruction sequences matched the raw SMU firmware (`robin_5`, SHA-256 `cae8617c...`) and CLV ROM body at `0x8FEF00` (SHA-256 `ea578104...`).

---

## 2. VID Conversion Formula & Floating-Point Parameters

The exact SMU voltage-to-VID conversion is implemented in helper `FUN_0001cb30` (`actuator-pass4.txt:2-40`) and mirrored in `FUN_0002b13c` (`actuator-pass6.txt:112-123`).

### Exact Conversion Parameters (SMU Firmware Literals)

- `_DAT_00017278` (`0x3fc66666`) = `1.55` V (IEEE-754 binary32: `1.5499999523162842` V; reference zero-point ceiling)
- `_DAT_0001727c` (`0x43200000`) = `160.0` (scale factor, corresponding to `1 / 0.00625` V step = 6.25 mV/step)
- `_DAT_00017280` (`0x3727c5ac`) = `9.999999747378752e-06` (`1e-5`, rounding epsilon)
- `_DAT_00017338` (`0xbbcccccd`) = `-0.00625` V (step decrement for reverse VID-to-voltage conversion: `V = VID * -0.00625 + 1.55`)

### Assembly & Semantic Implementation (`FUN_0001cb30`)

```c
int FUN_0001cb30(float volts) {
    if (volts >= 1.55f) {
        return 0; // Top rail clamp
    }
    float fVar = (1.55f - volts) * 160.0f + 1e-5f;
    return (uint32_t)utrunc(fVar);
}
```

_Note on binary32 truncation_: At exactly `1.100000` V, `(1.55f - 1.1f) * 160.0f + 1e-5f` produces `71.999992f`. The unsigned truncation instruction `utrunc.s` produces VID `71` (`0x47`), not ideal-real `72` (`0x48`). At `1.15` V, VID is `64` (`0x40`).

---

## 3. Actual Hardware Voltage Route vs Candidate Route

### Actual Hardware Route (SMU Coprocessor Internal Loop)

1. **Target Selection / Calculation**: Functions `FUN_0001d060`, `FUN_0002b13c`, `FUN_0002bb40`, and `FUN_0002be7c` calculate or receive target voltages.
2. **VID Translation**: Calculated `float` target voltage is converted via `FUN_0001cb30` or inlined formula into 8-bit VID.
3. **Actuator Dispatch**:
   - `FUN_0002bdec` shifts the VID left by 16 (`vid << 16`) and writes to SMN register `0x0115A030`:
     ```c
     *(uint32_t *)(0x0115A030) = (uint32_t)(uint8_t)vid << 16;
     while (*(uint32_t *)(0x0115A000) & 0x80000000) { memw(); }
     ```
   - `FUN_0002be40` writes `(vid << 16) | 1` to `0x0115A030` and polls `0x0115A000` bit 31.
   - `FUN_0002be18` reads default VID from literal `0x0001714c + 1` and writes `CONCAT12(vid, 0x20)` (`(vid << 16) | 0x20`) to `0x0115A030`.
4. **Hardware Bus**: Writes to `0x0115A030` drive the internal VR12/SVI2 telemetry controller interface to command external voltage regulators.

### Candidate Route (UEFI Setup / $INV Serialization Route)

- In UEFI PEI, CBS options (`Setup + 0x6E5`, `Setup + 0x6E6`) are serialized into `$INV` token `0x1364` (u32, flag 2) inside `CbsBasePei` / `AmdNbioSmuV10Pei`.
- Token `0x1364` is placed in a GUID-HOB (`NVTB`).
- Previous audits confirmed that DXE table scaling dispatch (`B000000A`) **does not** read or forward token `0x1364` to `PPTable + 0x400 / 0x404`.

---

## 4. Unknowns for SoC / INV 0x1364

1. **Missing Actuator Link**: No stock PEI or DXE consumer is found that translates `$INV` record `0x1364` into an SMU mailbox command or writes it directly to the SMN register aperture.
2. **Rail Identification**: While `0x0115A030` commands the SVI2 VR controller VID, the exact mapping between this internal SMU loop (handling VDDCR_VDD vs VDDCR_SOC) and the CBS Setup field `0x6E6` remains unresolved offline.
3. **Physical Rail Limits**: Hardware SVI2 telemetry ceiling, board VRM phase configuration, and physical rail limits cannot be determined from firmware binaries alone.
