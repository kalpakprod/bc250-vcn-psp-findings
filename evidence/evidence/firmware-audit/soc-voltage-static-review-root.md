# Root static review: BC-250 VDDCR_VDD / SoC-voltage semantics

## Scope

This review analyzes the current BC-250 `AmdSetup+0x6E5/+0x6E6` fields and their possible memory/SMU relationship. It is read-only static/source analysis. It does not choose a voltage, build a SoC-voltage image, execute a programmer, write a register, or claim boot/runtime behavior.

Review date: 2026-09-11T09:38:07.064307+00:00

## Exact baseline

- Fresh reads: `evidence/programmer/reads/20260911/read-a.bin` and `read-b.bin`; both 16 MiB, byte-identical, SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- Fresh NVAR parse: `evidence/programmer/reads/20260911/firmware-audit/read-a-nvar-primary.json`; SHA-256 `d3e769533368d0fcbfad476e6c2b75f510d1b4f80d356c4b8ff72bdfd3673b65`.
- Current AmdSetup record: relative `0x4BB`, body begins at `0x4CF`, body length `0x8B5`, body SHA-256 `6f266c3c78a544d73eae5cea465756dd73e343fe16e2725d2300d08ba176d055`.
- IFR map: `evidence/firmware-audit/amdsetup-ifr-field-map.json`; SHA-256 `ff657447e9070b18773d149bca6e82bbd7c36295172561e5e2a425a6fecab2b7`.

## Observed bytes and IFR structure

| Field | Location | Type | Current value | Direct static evidence |
|---|---:|---|---:|---|
| `VddcrVddOffsetControl` | `AmdSetup+0x6E5` / flash `0xBB4` | `u8` | `0` | IFR options `Auto=0`, `Manual=1` |
| `VddcrVddOffset` | `AmdSetup+0x6E6` / flash `0xBB5` | `u32` | `0` | IFR numeric type `0x2`, range `0..0xFFFFFFFF` |
| `VddcrGfxOffsetControl` | `AmdSetup+0x6EA` | `u8` | `0` | IFR options `Auto=0`, `Manual=1` |
| `VddcrGfxOffset` | `AmdSetup+0x6EB` | `u32` | `0` | IFR numeric type `0x2`, range `0..0xFFFFFFFF` |

The exact flash offsets are body offset plus the AmdSetup-relative offsets. The `+0x6E5` control and `+0x6E6` value are a pair. A nonzero value must not be interpreted without its control byte. The direct fresh parse reproduces the same values and three known tail NVAR name warnings.

The IFR field map also identifies, statically:

- `FCLK_DPM` at `+0x6A3`: `Disabled=0`, `Enabled=1`, `Auto=0x0F`; this is a feature switch, not a frequency.
- DF override control/value at `+0x703/+0x704`: `Auto=0xFF`/`Manual=1`, numeric range `0..2000` for the value.
- `MemoryClockSpeed` at `+0x316`: enumerated values include `0x23=1750MHz`.

Evidence: `evidence/firmware-audit/amdsetup-ifr-field-map.json` and the fresh NVAR report above. Evidence class: `observed-bytes` + `static-analysis`.

## Static consumer evidence

The current extracted modules and Rizin scan provide leads but not a complete consumer trace:

- `AmdNbioGfxARIPei` (TE, 87,048 bytes, SHA-256 `63413be2ac290e584bbbeeba5eb573a94b66b9624c4e0ecbea145ded655245b8`) contains literal references to the Setup offsets `0x316`, `0x6A3`, `0x6E6`, and `0x704`, plus DF window/control constants.
- `AmdNbioPcieARIPei` (TE, 108,776 bytes, SHA-256 `62b1398c4ba9b5a03ea533306cd8200257fac323c8fa688caa057667a5871312`) contains the same classes of literal references.
- `AmdNbioBaseARIPei` (TE, 105,264 bytes, SHA-256 `51d96c1e5a5e2c39f04fb962b0b5be686dea0a05eecbde829a4595fe3356884f`) contains Setup-offset and DF-window literals.
- `CbsBasePei` (TE, 81,520 bytes, SHA-256 `6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77`) contains Setup-offset and DF-window literals.
- `CbsSetupDxe` (PE32, 264,160 bytes, SHA-256 `9fae1341693fe1b89e6f070f8740c94228f5161cca701ac31425bc5d438533b3`) contains Setup-offset constants and the DFG wildcard constant.
- `AmdNbioSmuV10Dxe` (PE32, 33,024 bytes, SHA-256 `546a0689e607a3a87b8c437c7fe7191e55757f56b35792fb8d84f539844b500e`) contains Q2 mailbox address literals (`CMD=0x03B10528`, `RSP=0x03B10564`, `ARG=0x03B10998`) and DF window references.
- `AmdNbioSmuV10Pei` (TE, 90,672 bytes, SHA-256 `905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80`) and `AmdMemAm4Pei` (TE, 5,192 bytes, SHA-256 `1ef4e7b944672a9a48b6fcb16c4d35cb6d23bb8306429dc3eb10ee1d0c7bb5f8`) are present, but the targeted literal scan does not by itself identify a VDD field consumer.

Source: `evidence/firmware-audit/rizin/vcn-apcb-static-constant-scan.json` SHA-256 `066bf18889edef6df8f8daad91721101b62e0f92da863e2168f0ee8868c1fef9`; module-triage `evidence/firmware-audit/rizin/module-triage.json` SHA-256 `6b43307c93b02b7bfd35b69a31900bda16e941088a2e0481a924a906824ac120`. Evidence class: `static-analysis`.

A scalar constant hit is not proof of an instruction reading or writing the field. TE modules also carry a Rizin endian metadata caveat. Exact function/caller context remains incomplete because the native MCP session covered `Bc250CoreUnlockDxe`, while GUI-controlled MCP sessions for other modules were unavailable.

## Host-source and PMFW context

- Imported `cyan_skillfish_ppt.c` (SHA-256 `9259ad3ff6f660fe97ca7ea68f9b7e5f5d185982f0d3341180bd880442f030f1`) exposes current metric values: `Current.Voltage[0]`/`[1]` for VDD SOC/GFX and clock members for GFX/SOC/UCLK/FCLK. The source comments and sysfs paths use mV/MHz for those **metrics**. It does not decode the AmdSetup NVRAM offset field. In this source, UCLK and FCLK are both assigned from `MemclkFrequency`, so it is not sufficient to prove independent clocks.
- Imported `smu_v11_8_pmfw.h` (SHA-256 `8893329478e28c2f36b0298b2aeb0fc4b5902a77e76e82db57e2884fe0a82966`) defines PMFW feature bits such as `FCLK_DPM=5`, `SOC_DPM=13`, `UMC_THROTTLE=23`, and `DF_THROTTLE=24`. It does not map `AmdSetup+0x6E6` to a physical unit or message.
- Historical `feature_callbacks_2026-08-25.txt` (SHA-256 `fab4157a57a1d73ae35402d1d35c06adc7bf64a509c108a2eb32f63cc5e499d4`) is a callback map, not proof of current PMFW state.

Evidence class: `static-analysis` / `historical-report` for the imported context.

## Contradictory historical claims

`import/from-windows/Users/kukuruza/bc250-bios/docs/CPU_MEMORY_OVERCLOCK_ANALYSIS.md` (SHA-256 `050041933ac0efe95399f2e81555b75b275fb3687b8a044772ec9effd4b755ea`) and `build_oc_profiles.py` (SHA-256 `af5f59a283a5a0c450cbe2e2f0610f8e30bce8b12811ec5d8de7de9d16997ccd`) describe the offset as `u8/i8` and label historical values `+35`, `+80`, and `+100` mV. The current IFR evidence says the value is a `u32` with a separate control byte. The historical comments therefore cannot establish encoding, sign, physical units, safe range, or actual applied rail voltage.

The same historical material reports FCLK/UCLK behavior and memory-training outcomes, while imported runtime logs contain different clock contexts and VCN ring timeouts. These reports are retained as historical leads only. No historical voltage value is selected or recommended.

## Results

| Question | Status | Evidence |
|---|---|---|
| Locate control/value fields | PASS | Fresh NVAR + IFR map |
| Establish value width | PASS: IFR `u32` | IFR map + fresh bytes |
| Establish Auto/Manual control | PASS: static IFR options | IFR map |
| Prove physical unit/sign/encoding | INCONCLUSIVE | Historical mV comments conflict with u32 map; no consumer trace |
| Prove SMU/PMFW consumer | INCONCLUSIVE | Literal mailbox/DF references only |
| Prove memory-training dependency | UNRUN/INCONCLUSIVE | No current boot/training test or complete source trace |
| Prove live rail response | UNRUN | Board is not running in this session |
| Choose SoC-voltage value | NO-GO | No value may be guessed |

## Next discriminating read-only test

1. Reconcile `CbsSetupDxe`, `CbsBasePei`, `AmdNbioBaseARIPei`, and `AmdNbioSmuV10Dxe` instruction/caller context in Cutter/Rizin to identify the path from HII/NVAR buffer to the SMU table/message. Do not use mutation tools.
2. After disconnecting the programmer/clip and restoring the board to stock power, capture a fresh stock boot with the exact kernel/driver/PMFW versions and read-only `gpu_metrics`, `pp_dpm_socclk`, `pp_dpm_mclk`, `pp_dpm_fclk`, thermal, throttle, and memory-training logs. Do not infer NVRAM offset units from telemetry alone.
3. Only if both static consumer mapping and controlled stock telemetry establish the encoding should a separate SoC candidate be considered.

## Safety decision

No SoC-voltage candidate is built. The two existing candidates intentionally do not change `AmdSetup+0x6E5/+0x6E6`. This review does not authorize flash, register writes, JTAG writes, or any hardware mutation.


## Separate runtime SMU API context

Imported `bc250_smu` source exposes several distinct runtime voltage protocols:

- `api_q3.py` SHA-256 `30464310e6c4f6146322dd0136255e7f6069c2c397509296e92519e0f0cd8c90` documents q3 `0x36/0x37` current voltage queries in mV, q3 `0x49/0x4A` small VID-offset steps, q3 `0x4D/0x4E` float offsets, and q3 `0x42` SoC DPM clock query.
- `codec.py` SHA-256 `bb747622598b92ff43f10583ef93803bda4d6ae59b2480e74fc2abf6751db116` converts mV to a VID code and packs large offsets as an IEEE float.
- `api_q2.py` SHA-256 `a5da57c58230e4be02204efb8791ff49082fe7d4b78890d838c47439c0ee8f8d` documents feature-mask and droop-calibration paths with mV arguments.

These files are static imported host-tool context and contain write-capable methods; they were not executed. Their multiple encodings show why a BIOS `u32` field cannot be assumed to be mV or a VID code. None maps `AmdSetup+0x6E6` to a specific runtime message. The no-guessed-voltage decision is unchanged.


## Encoding ambiguity demonstration

Host-side reproduction artifact: `evidence/firmware-audit/soc-voltage-encoding-comparison.json`, SHA-256 `3576ead3e78ab343cd93727046f2de44e135fb4a4d67024228fee114061823c5`. It compares the historical offset-mV comments with the imported VID/mV and IEEE-float conversion formulas without executing any write-capable API. The same raw values `0x23`, `0x50`, and `0x64` have materially different hypothetical meanings under these interpretations. This is not a value recommendation; it strengthens the no-go decision.


## Correction: imported `bc250_smu` queries are not read-only

Static inspection of `bc250_smu/api.py` (SHA-256 `584b135de0796e2b1e5d593b316457f18b5e5120bb3f8b5307acb551c2721185`) and `transport.py` (SHA-256 `4ec3ba8cc13ff4af8ab2e2e525edd145bb23ffe3c59098231ada36f45b6685a6`) shows `O_RDWR` PCI config access, an index write to `0xB8` in `read_smu_reg`, and mailbox command/argument writes in `send_message`. Query-shaped methods therefore cannot be run under the read-only hardware gate. This is a tool-safety correction, not evidence that any current rail value was applied.


## Direct `AmdNbioSmuV10Dxe` mailbox context

Bundled Rizin report `evidence/firmware-audit/rizin/AmdNbioSmuV10Dxe.mailbox-context.txt` (SHA-256 `c81b065ee241d336efa5354b38aa44668f3041d3162254152e2563eaf8a4e76c`) shows direct code context where Q2 response `0x03B10564`, argument `0x03B10998`, and command `0x03B10528` are passed through an SMU service helper. This proves a static mailbox path exists in the module, but no data flow from `AmdSetup+0x6E6` to that path is identified. It therefore does not change the SoC-voltage no-go.


## Direct NBIO PEI DF path

`AmdNbioGfxARIPei` forced-little-endian Rizin report `evidence/firmware-audit/rizin/AmdNbioGfxARIPei.df-window-context.txt` (SHA-256 `95ce1c7917dd12789e6af168dbbdfa046d0003ec653116e3f276da6ea74b8c68`) shows generic DF indirect read/write/read-modify-write helpers using `0x405C`/`0x4098`. The path is write-capable and no data flow from `AmdSetup+0x6E6` is proven; it does not justify a voltage value.


## Direct `CbsBasePei` Setup-default context

Forced-little-endian TE Rizin report `evidence/firmware-audit/rizin/CbsBasePei-setup-defaults-context.txt` (SHA-256 `04f27d70a345d06a66dfae3f0af07185f5c742dd1049acd4057d167b9f53db2e`) shows the large `fcn.000004C0` initializer writing `MemoryClockSpeed/UclkDiv1M0=0xFF`, `FclkDpm=0x0F`, `VDDCR_VDD control=0` and value `0`, `DF control=0xFF` and value `0x3E8`, plus power/current defaults into a setup-like structure. This corroborates field layout and default bytes, but it is not a proof that the NVAR is read or that the fields reach SMU/training.
