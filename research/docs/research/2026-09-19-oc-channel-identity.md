# Voltage Channel Identity: Selector Mapping, Domain Attribution, and SVI2 Truth

## 1. Executive Summary & Core Verdict

The offline investigation of SMU firmware `robin_5` (SHA-256 `cae8617c...`, CLV ROM offset `0x8FEF00`) and UEFI CBS configuration resolves the exact dataflow and hardware domains of the `0x0115A030` actuator port:

1. **Selector Disambiguation**:
   - Actuator helper `FUN_0002bdec` commands **Selector 0** via `(VID << 16) | 0x00` to SMN register `0x0115A030`. It tracks state struct `_DAT_00017124` offset `+0x00` (float volts) and offset `+0x04` (VID code).
   - Actuator helper `FUN_0002be40` commands **Selector 1** via `(VID << 16) | 0x01` to SMN register `0x0115A030`. It tracks state struct `_DAT_00017124` offset `+0x20` (float volts) and offset `+0x24` (VID code).
   - Actuator helper `FUN_0002be18` commands `(VID << 16) | 0x20` to `0x0115A030`, setting initial/default calibration from literal `_DAT_0001714c + 1`.

2. **Domain Attribution & Scope Boundary (G7 Correction)**:
   - **Per-Core CPU VID Path**: Function `FUN_00020b04` iterates over all 8 CPU cores (`iVar15 = 0..7`). For each core, it translates target voltage via `FUN_0001cb30` and writes the resulting VID directly to per-core SMN apertures at `*(iStack_64 + 0x10b0)` and `*(iVar8 + 0x10)`. However, having separate per-core VID apertures does **not** distinguish a shared CPU supply from SoC or uncore rails.
   - **Selectors 0 and 1 (Actuator 0x0115A030 vs Driver Labels)**:
     - Linux kernel driver `cyan_skillfish_ppt.c` maps telemetry fields:
       - `Voltage[0]` = `METRICS_VOLTAGE_VDDSOC`
       - `Voltage[1]` = `METRICS_VOLTAGE_VDDGFX`
     - Cross-referencing SMU Q3 mailbox API (`api_q3.py`):
       - `q3_0x0f_set_cpu_gpu_vid` accepts `kind=0` vs `kind=1`.
       - `q3_0x30_return_cpu_vid_float_or` accepts `selector=0` vs `selector=1`.
     - **G7 Correction**: Driver labels `Voltage[0]=VDDSOC` / `Voltage[1]=VDDGFX` do **not** identify actuator selector 0 or 1 without a verified firmware producer-to-actuator mapping. Calling selectors 0/1 "package / uncore rails" based on driver labels is an overclaim.
     - **DO NOT ASSUME VDD = SoC**: UEFI CBS Setup exposes:
       - `AmdSetup+0x6E5` (`VddcrVddOffsetControl`, u8) and `+0x6E6` (`VddcrVddOffset`, u32) -> Token `0x1364`
       - `AmdSetup+0x6EA` (`VddcrGfxOffsetControl`, u8) and `+0x6EB` (`VddcrGfxOffset`, u32)
         In AMD AGESA terminology, `VddcrVdd` refers to the main core/SoC supply, while `VddcrGfx` refers to the graphics rail. CBS token `0x1364` is strictly `VddcrVddOffset`, NOT `VddcrSocOffset`.

3. **Status of SVI2 "Proof"**:
   - **Textual Evidence in Firmware**: The exact strings `"SVI"`, `"SVI2"`, `"VR12"`, `"VR13"` **do not exist** anywhere in the raw SMU firmware binary `robin_5`. Their usage in prior notes is an **architectural inference** derived from known AMD SMU v11 / APU hardware architecture (which communicates with external VRMs like ISL69247 / ISL95712 via the SVI2 bus), not an explicit literal from the binary.

4. **Missing Hardware Link & Scope of Consumer Search**:
   - The link between UEFI CBS token `0x1364` (`Setup+0x6E6`) and the SMU internal state struct `_DAT_00017124` is absent in static direct call-sites of stock PEI and DXE.
   - Asserting "no stock 1364 consumer" was too broad: direct static call-site coverage in current readers is bounded, but indirect, dynamic, or computed dispatch coverage is not exhaustive across all modules.
   - Safe discriminating next step: trace SMU mailbox command reception for message `0x0F` / `0x4D` / `0x49` or boardview tracing of ISL69247/ISL95712 SVI2 telemetry lines to physically map channel 0 and channel 1 to board inductors.

---

## 2. Detailed Dataflow to 0x0115A030

### Actuation Port Semantics (`0x0115A030`)

Base register: `_DAT_000171a4` = `0x01159E00`.

- Command register: `0x01159E00 + 0x230` = `0x0115A030`.
- Status/Poll register: `0x01159E00 + 0x200` = `0x0115A000` (bit 31 polled via `bbsi aX, 0x1f`).

```
          Target Voltage (f32 Volts)
                     │
                     ▼
          FUN_0001cb30 (or inlined)
          VID = (1.55f - V) * 160.0f + 1e-5f
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
    FUN_0002be7c            FUN_0002bf1c
    (Selector 0)            (Selector 1)
         │                       │
         ▼                       ▼
    FUN_0002bdec            FUN_0002be40
    Writes to 0x0115A030:   Writes to 0x0115A030:
    (VID << 16) | 0x00      (VID << 16) | 0x01
         │                       │
         └───────────┬───────────┘
                     ▼
             SMN 0x0115A030
      (Hardware VR Telemetry Bus)
```

### State Structure `_DAT_00017124` (SRAM Base `0x13474`)

- `+0x00`: `float` Current Voltage for Domain 0
- `+0x04`: `uint8_t` Current VID for Domain 0 (Selector 0)
- `+0x05`: `uint8_t` Target VID for Domain 0
- `+0x06`: `uint8_t` Lock/Busy flag for Domain 0
- `+0x20`: `float` Current Voltage for Domain 1
- `+0x24`: `uint8_t` Current VID for Domain 1 (Selector 1)
- `+0x25`: `uint8_t` Target VID for Domain 1
- `+0x26`: `uint8_t` Lock/Busy flag for Domain 1

---

## 3. Proven Facts vs Inferences

| Item                         | Firmware / Byte Status                                                           | Classification                                                      |
| ---------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Formula `(1.55 - V) * 160`   | Byte-proven (`FUN_0001cb30`, literals `0x17278`, `0x1727c`, `0x17280`)           | **Observed Fact**                                                   |
| Register `0x0115A030`        | Byte-proven (`_DAT_000171a4 + 0x230`)                                            | **Observed Fact**                                                   |
| Low byte `0x00` (Selector 0) | Byte-proven (`FUN_0002bdec`: `uStack_30 = VID << 16; *(0x0115A030) = uStack_30`) | **Observed Fact**                                                   |
| Low byte `0x01` (Selector 1) | Byte-proven (`FUN_0002be40`: `*(0x0115A030) = uStack_30 \| 1`)                   | **Observed Fact**                                                   |
| Low byte `0x20` (Calib)      | Byte-proven (`FUN_0002be18`: `CONCAT12(vid, 0x20)`)                              | **Observed Fact**                                                   |
| Per-Core CPU VID             | Byte-proven (`FUN_00020b04`: 8-iteration loop writing `*(iStack_64 + 0x10b0)`)   | **Observed Fact** (does not establish package vs SoC rail identity) |
| Wording `"SVI2"`             | **0 matches** in `robin_5`                                                       | **Inference from board architecture**                               |
| Driver Voltage[0]=VDDSOC     | Driver header label only (`cyan_skillfish_ppt.c`)                                | **Unproven mapping to actuator selector 0**                         |
| Setup `0x6E6` = SoC          | **False/Unproven** (`0x6E6` is `VddcrVddOffset`, CBS token `0x1364`)             | **Disproven Assumption**                                            |
| Token `0x1364` -> SMU        | **Unconnected** in direct static call-sites                                      | **Observed Fact** (indirect dispatch unexhausted)                   |

---

## 4. Next Safe Discriminating Step

1. **Board Physical Mapping**: Use high-resolution board photography and continuity probing from ISL69247 / ISL95712 PWM output pins to determine which physical VRM phases feed the Zen2 CPU cores versus the SoC/uncore versus the GFX rail.
2. **Mailbox Dispatch Audit**: Analyze the SMU queue message handler dispatch table around `0x15200` to locate how messages `0x0F` (set VID) and `0x49`/`0x4A` (VID offset) manipulate `_DAT_00017124`.
