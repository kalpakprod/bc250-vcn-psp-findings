# Voltage Metrics Producer Trace: Backwards Provenance & State Mapping [PROVISIONAL — under recheck]

> **G7 Notice**: Claims in this report were flagged for reliance on unpinned decompile and unverified writer claims. Findings are marked PROVISIONAL and re-evaluated per G7. The claim that "periodic ADC poll populates" `0x109F4`/`0x10A08` is withdrawn as unsupported. Conversion semantics are `utrunc.s` (unsigned truncation), not signed. Fresh verification is archived under `evidence/firmware-audit/20260919-metrics-producer-check/`.

## 1. Scope, Asserted Inputs & Hashes

Scope: Trace SMU metrics producer `Voltage[0]` and `Voltage[1]` backwards to their actual firmware source addresses in SRAM, and compare them against actuator state struct `_DAT_00017124` (`0x13474 + 0x00 / +0x20` and VID `+0x04 / +0x24`).

- Asserted ROM: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
  - Size: 16,777,216 bytes
  - SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Asserted SMU Body: `archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5`
  - Body offset in CLV ROM: `0x8FEF00` (length 262,400 bytes)
  - SHA-256: `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`
  - Memory mapping convention: 1:1 file offset == SRAM address (byte-proven in `scripts/repro_smu_globals.py`).
- Driver reference: `cyan_skillfish_ppt.c` and public `smu11_driver_if_cyan_skillfish.h` (Linux v6.8, `MP1_DRIVER_IF_VERSION=8`).

---

## 2. Telemetry Export Producer (`FUN_00029e34`)

In `robin_5` (CLV PMFW), the table-6 (SMU Metrics) producer is `FUN_00029e34` (offset `0x29e34`, corresponding to `0x29aec` in earlier `robin_3` builds).

### Metrics Buffer Layout & Base Literals

- `_DAT_00017f88` = `0xca68` (internal state/metrics wrapper base `iVar12`)
- Exported `SmuMetrics_t` buffer base `iVar13` = `iVar12 + 0x100` = `0xcb68`
- Total export size: 244 bytes (`0xf4`), matching `sizeof(SmuMetrics_t)` upstream (2 × 116 byte Current/Average blocks + 12 byte trailer).

### Backwards Trace of Voltage[0] and Voltage[1]

In `FUN_00029e34` (disassembly verified in `evidence/firmware-audit/20260919-metrics-producer-check/metrics-producer-29e34.txt`):

- Multiplier: `fVar24 = *_DAT_00017f7c` (`0x16ee4`) = `1000.0f` (`0x447a0000`).
- Telemetry domain array base: `_DAT_00017f84` = `0x107fc`.
- Stride per domain: `0x14` bytes.
- Float to integer conversion: Instruction at `0x29f07` is `utrunc.s a10, f11, 0`, which performs unsigned truncation of the single-precision float to 32-bit unsigned integer (not signed `trunc`).

The loop iterates `uVar17` over `[0, 1]`:

```
Iteration 0 (Domain 0):
  iVar21 = iVar13 (0xcb68)
  iVar19 = 0x107fc
  Voltage[0]: *(uint *)(iVar21 + 0x50) = utrunc.s(*(float *)(iVar19 + 0x1f8) * 1000.0f)
              -> *(uint *)(0xcbb8)      <- utrunc.s(*(float *)(0x109f4) * 1000.0f)
  Current[0]: *(uint *)(iVar21 + 0x58) = utrunc.s(*(float *)(iVar19 + 0x1fc) * 1000.0f)
              -> *(uint *)(0xcbc0)      <- utrunc.s(*(float *)(0x109f8) * 1000.0f)
  Power[0]:   *(uint *)(iVar21 + 0x60) = utrunc.s(*(float *)(iVar19 + 0x200) * 1000.0f)
              -> *(uint *)(0xcbc8)      <- utrunc.s(*(float *)(0x109fc) * 1000.0f)

Iteration 1 (Domain 1):
  iVar21 = iVar13 + 4 (0xcb6c)
  iVar19 = 0x107fc + 0x14 = 0x10810
  Voltage[1]: *(uint *)(iVar21 + 0x50) = utrunc.s(*(float *)(iVar19 + 0x1f8) * 1000.0f)
              -> *(uint *)(0xcbbc)      <- utrunc.s(*(float *)(0x10a08) * 1000.0f)
  Current[1]: *(uint *)(iVar21 + 0x58) = utrunc.s(*(float *)(iVar19 + 0x1fc) * 1000.0f)
              -> *(uint *)(0xcbc4)      <- utrunc.s(*(float *)(0x10a0c) * 1000.0f)
  Power[1]:   *(uint *)(iVar21 + 0x60) = utrunc.s(*(float *)(iVar19 + 0x200) * 1000.0f)
              -> *(uint *)(0xcbcc)      <- utrunc.s(*(float *)(0x10a10) * 1000.0f)
```

Quiesced runtime verification:

- Snapshot `evidence/runtime/20260913-quiesced-metrics-table6-244B.bin`:
  - `0x50` (u32): `1275` (1275 mV, Domain 0)
  - `0x54` (u32): `912` (912 mV, Domain 1)

---

## 3. Comparison with Actuator State Structure `0x13474`

Actuator helpers `FUN_0002bdec` and `FUN_0002be40` interface with SMN register `0x0115A030` using state structure `_DAT_00017124` (SRAM base `0x13474`):

- `0x13474 + 0x00`: `float` Domain 0 target/current voltage
- `0x13474 + 0x04`: `uint8_t` Domain 0 VID (commanded via `(VID << 16) | 0x00`)
- `0x13474 + 0x20`: `float` Domain 1 target/current voltage
- `0x13474 + 0x24`: `uint8_t` Domain 1 VID (commanded via `(VID << 16) | 0x01`)

### Comparison Matrix

| Metric Field | SmuMetrics Offset  | Producer Source Address | Actuator State Struct Address                       | Direct Byte Equivalence             |
| ------------ | ------------------ | ----------------------- | --------------------------------------------------- | ----------------------------------- |
| `Voltage[0]` | `+0x50` (`0xcbb8`) | `0x109f4` (float)       | `0x13474` (`+0x00` float) / `0x13478` (`+0x04` VID) | **DISPROVEN** (Delta: 0x2a80 bytes) |
| `Voltage[1]` | `+0x54` (`0xcbbc`) | `0x10a08` (float)       | `0x13494` (`+0x20` float) / `0x13498` (`+0x24` VID) | **DISPROVEN** (Delta: 0x2a8c bytes) |

Producer source addresses `0x109f4` and `0x10a08` reside in the array read by the metrics producer (base `0x107fc`), populated by routines whose writer is unidentified in current static trace (the prior claim that a periodic ADC poll routine populates these buffers is withdrawn as unsupported), **not** from the actuator command state structure `0x13474`.

---

## 4. Conclusion & Status

1. Telemetry `Voltage[0]` and `Voltage[1]` are produced by reading float values at `0x109f4` and `0x10a08` and multiplying by 1000.0f.
2. They do **not** directly read `_DAT_00017124` (`0x13474 + 0x00 / +0x20`) or VID code `+0x04 / +0x24`.
3. Inferring actuator selector identity or physical rail identity directly from `Voltage[0]` or `Voltage[1]` driver labels is invalid at the byte level without tracing the internal calibration/feedback link between `0x107fc` telemetry buffers and `0x13474` actuator targets.

## Document audit clarification — 2026-09-27

The producer reads and scales these values. This does not establish that they
are independent physical measurements: the source writer, copied provenance
and rail identity remain unresolved. See 2026-09-19-voltage-producer-writer.md.
