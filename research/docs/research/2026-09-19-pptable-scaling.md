# Exact clv PPTable scaling: voltage-margin fields, not a clock/power conversion

## Result and limits

**PARTIAL semantic chain, with concrete upstream and downstream boundaries.** The callback's subtable offsets `+0x80/+0x84` are **incoming full PPTable offsets `+0x400/+0x404`**, not full-table `+0x80/+0x84`. Exact DXE debug strings identify them as `VddcrVddVoltageMargin` and `VddcrGfxVoltageMargin`. Signed integer-to-float conversion and multiplication by approximately `0.001f` are proven. These are voltage-margin-labelled fields, not evidence of SoC voltage, an absolute voltage setpoint, an electrical limit, or a clock/power conversion.

Adjacent PPTable offsets `+0x04..+0x13` (`CpuFid[0..7]`) and `+0x14..+0x1B` (`CpuDid[0..7]`) are populated by `AmdNbioSmuV10Dxe` from compiled template RVA `0x5D20` and consumed by SMU callback callee `0x21E8C` via ratio converter `0x1CBFC`. These control CPU core clock P-states (P0..P7: 3200, 2550, 2325, 1960, 1820, 1600, 1271.4, 800 MHz) and program SMN registers `0x0115A820..0x0115A85C` and per-core apertures `aperture + 0x10BC`. They do not control memory clocks (MCLK) or Data Fabric clocks.

The DXE initializes both fields to zero from its compiled template. Its visible PCD getter stores target other offsets. A subsequent IDS hook receives the entire PPTable; the local hook list is empty, and the fallback is a protocol dispatch. **No Setup/PCD setter for these exact fields has been established.** State `+0x14` has identified additive consumers; `+0x30` has an identified alternate writer but no proven reader in this bounded pass. No hardware behavior or safety claim follows.

## Identity and provenance

| Input                                                                                                           |    Bytes | SHA-256                                                            |
| --------------------------------------------------------------------------------------------------------------- | -------: | ------------------------------------------------------------------ |
| `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`                                                           | 16777216 | `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8` |
| `archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5` |   262400 | `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37` |
| `20260919-clock-trace/modules/0000_AmdNbioSmuV10Dxe_pe32.bin`                                                   |    33632 | `b158f039f48db05e352b965a62c8e983a395a4858791c93c73f727285c9ac8d8` |

Module paths in this report are under `evidence/firmware-audit/` unless otherwise qualified. Existing `20260919-clock-trace/trace.json:36` records DXE extraction provenance. The requested `20260919-oc-final-consumer-pass/extract.py:10` pins clv and reuses `firmware_audit.Extractor` for UEFI modules; **it does not itself extract/map the raw SMU body**. This pass additionally proves every SMU body byte equals ROM `[0x8FEF00,0x93F000)` and loaded Ghidra memory at base zero. Thus the adopted body-file-offset = SRAM-address convention is reconciled with the exact ROM, not inferred from a filename. No extractor was rerun or changed.

## Exact little-endian literals

| Body offset / SRAM | Bytes      | u32          | IEEE-754 f32 interpretation |
| ------------------ | ---------- | ------------ | --------------------------- |
| `0x170AC`          | `6f12833a` | `0x3A83126F` | `0.0010000000474974513`     |
| `0x17118`          | `f87f0000` | `0x00007FF8` | `4.5906537691281007e-41`    |
| `0x1711C`          | `5c7b0000` | `0x00007B5C` | `4.4253005503377723e-41`    |
| `0x17120`          | `dc7e0000` | `0x00007EDC` | `4.550856892741276e-41`     |
| `0x17124`          | `74340100` | `0x00013474` | `1.1065213193694486e-40`    |

Only `0x170AC` is used as a float here; the remaining float interpretations are requested bit reinterpretations, **not semantic values**.

## Pointer and transfer chain

Existing `smu-table-callback.txt:43-68` and `smu-table-apply.txt:365-456` establish:

1. Callback `0x1BC80` invokes transfer wrapper `0x3ABDC(descriptor,0x7FF8,0x49C)`, then validator `0x1BD20(0x7FF8)`. The transfer wrapper constructs a descriptor and invokes `0x397C8/0x019EC`; it is not ordinary C `memcpy`. Transport completion/physical execution are not validated by offline analysis.
2. On validation success, `0x1CC7C(0x7FF8,0x7B5C,0x49C)` copies source to destination: `l32i a8,a2,0; s32i a8,a3,0`, repeated `0x127` words. The staging and committed ranges are adjacent (`0x7B5C+0x49C=0x7FF8`), not aliases of each other.
3. `0x7EDC=0x7B5C+0x380`. Therefore reads `0x7EDC+0x80=0x7F5C` and `+0x84=0x7F60` are committed PPTable `+0x400/+0x404`, copied from staging `0x83F8/0x83FC`.
4. Instructions `0x1BCB7..0x1BCCF` implement:

   ```text
   *(float*)0x13488 = float32(int32(PPTable[0x400])) * float32(0x3A83126F)
   *(float*)0x134A4 = float32(int32(PPTable[0x404])) * float32(0x3A83126F)
   ```

   Xtensa `float.s`, not `ufloat.s`, determines signed conversion. The decompiler's `/1.0` is not an extra scaling operation in the instruction stream.

This proves the local input-field alias through the committed incoming-table copy, conditional on the existing transport callback path. It does not establish that a particular Setup value was supplied.

## Exact DXE writers and upstream boundary

In `0000_AmdNbioSmuV10Dxe_pe32.asm:1423-1440`, function `0x17DC` allocates `0x49C`, zeroes it, then copies `0x49C` bytes from template RVA `0x5D20` at call `0x191F`. PE section mapping confirms the inspected RVAs equal raw offsets for this module. Template `0x6120/0x6124` (PPTable `+0x400/+0x404`) contains `00000000` for both.

The same function logs `PPTable+0x400` at `0x25A7` with string RVA `0x72A0`, `VddcrVddVoltageMargin = 0x%x`; it logs `+0x404` at `0x25C9` with RVA `0x72C0`, `VddcrGfxVoltageMargin = 0x%x`. These are exact code-to-string associations, not inference from the float factor.

The PCD getter block after template copy visibly writes other fields (for example tokens `0x46/0x44/0x47` to `+0x42C/+0x430/+0x434`). It does **not** justify assigning those tokens to the two margins. The direct full-table `+0x400/+0x404` references found in this module's retained listing are the debug loads, not PCD stores.

A concrete potential mutator is `0x1C54..0x1C60`: pass the PPTable in `r8` to `0x4E58`, hook ID `0xB000000A`. `0x4E58` consults local table pointer at `0x5CE0`, whose value is `0x5CB0`; its first ID is `0xFFFFFFFF`, the terminator. Fallback `0x5870` locates protocol GUID **`0ecad4a0-75e9-46d7-a3a6-81fe173f2eca`** and calls method zero at `0x58D4`, with hook ID in `r8d` and a descriptor `{0, PPTable pointer}` in `rdx`. Provider implementation is the **next exact missing upstream link**. Resolve that provider's hook `0xB000000A` handler and inspect its writes to `+0x400/+0x404`, then identify any PCD token/Setup source there. Do not return to the serializer or substitute the Setup voltage-field label for this missing edge.

## Downstream: separate 0x21E8C from the scaled-margin readers

`smu-table-apply.txt:150-207` shows `0x21E8C` reads committed PPTable `+4+2*i` and `+0x14+i` for eight entries, not the scaled output fields. Its helper `0x1CBFC` takes **two** arguments: integer quotient `u32(param1*50000)/param2`, converted unsigned to float and multiplied by bits `0x358637BD` (approximately `1e-6`). At `0x21EA4` the divisor is loaded into `a11` from table `+0x14+i`; the first argument is table u16 `<<2`. The old decompile displaying only one argument is incomplete; assembly supplies the missing divisor.

It stores floats starting at `0xF104`, and forms register-write addresses `0x01000000 + 0x5A824 + 8*i` and `0x01000000 + 0x5A820 + 8*i`. Its later `0x1CD80` calls extract bitfields, and `0x223B8` selects an index by comparing the ratio against floats at `0xF0D4+0x30`, count at `+0x50`. **That `+0x30` is a different structure (`0xF104`), not scaled output `0x134A4`.** These ratio/table-programming operations must not be described as consuming the two voltage margins merely because they follow the callback.

Proven scaled-output use:

- `0x25660`: `l32r a8,0x17124` at `0x256B2`, `lsi f11,a8,0x14` at `0x256C4`. It adds this margin to a polynomial/other state terms, then stores derived maxima at base `0x10F84 +0x30C/+0x308`. Evidence: `scaling-consumers.txt:843-888,921-927`. This is an additive software-model input, not a proven rail write.
- `0x207C8`: reads the same `state+0x14`, adds `state+0x0C` and a selected value, writes derived state `+0x250` and another structure's `+0x1DC`, then calls `0x30070`. Evidence: `scaling-consumers-followup.txt:244-253`. Follow **`0x30070` and those exact destinations** to close its eventual actuator relationship.
- `0x28184` and `0x281D4` overwrite `state+0x14/+0x30` from a checked message argument (`scaling-consumers.txt:1448-1561`). They are **alternate writers**, not readers. The PPTable value need not remain the live value after such a handler runs.
- No reader of **`0x134A4`** was established. A lookalike `lsi ...,+0x14` at `0x2607A` uses a base loaded from literal `0x17BA8`, not `0x17124`; it is not evidence for this margin.

Next exact downstream boundary: reader of absolute state address `0x134A4` (including base-plus-interior-pointer aliases), and destination/actuator use after `0x207C8 -> 0x30070`. The bounded literal-pool `[0x17000,0x18000)` and code `[0x1B000,0x2B000)` scan is **not exhaustive whole-program xref coverage**. Initial function-entry heuristic missed `0x207C8` because its frame encoding is `364101`; the separate follow-up correctly decodes it. The original lead/output is preserved, not silently replaced.

## Verification, preserved outputs, reproduction

All evidence below is under `evidence/firmware-audit/20260919-oc-final-consumer-pass/`:

| Artifact                         | SHA-256                                                            |
| -------------------------------- | ------------------------------------------------------------------ |
| `scaling-literals.json`          | `db4b193b0040f9da6a7f782c67147408292da7412064460fefcd1e7afb8a65f2` |
| `scaling-consumers.txt`          | `d76ef379cb6ed1e2a8bb896e074ff7ae594004f34e37173c285146a4f06c1e45` |
| `scaling-consumers-followup.txt` | `07b0c0d471a0904037317b7e97d1aacc80e2374555643f8aa741a7c8e39c8d22` |
| `scaling-verification.json`      | `bc22555e775e699ccd96764ccb21ec26ab815249df3749b37d3eba6d6ef8dcdd` |

`scaling-SHA256SUMS` covers new scripts, outputs and Ghidra logs. Verification passed **2084 SMU instruction-byte comparisons** (57 callback + 209 apply + 1512 first output + 306 follow-up), plus **251 selected DXE listing lines** against the exact body. Ghidra 12.1.3/OpenJDK 21.0.12.1 reused the existing OCConsumer project and unchanged script; `-readOnly -noanalysis` discards any in-memory function creation. No full autoanalysis, new import, ROM/candidate/builder change, hardware/network operation, or key inspection was performed. Whole-image hashes necessarily read firmware bytes; no security-material fields were decoded/reported.

From repository root (choose fresh output names for reruns to preserve evidence):

```sh
E=evidence/firmware-audit/20260919-oc-final-consumer-pass
S=archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5
# Recorded producers; these overwrite only their own scaling outputs if rerun:
python3 "$E/scaling-audit.py"
python3 "$E/scaling-verify.py"
sha256sum -c "$E/scaling-SHA256SUMS"
# Fresh reproduction of the focused consumer/helper decompiles:
/home/OWNER/tools/ghidra_12.1.3_PUBLIC/support/analyzeHeadless \
  "$E/project" OCConsumer -process smu_fw_robin_5 -noanalysis -readOnly \
  -scriptPath "$E" -postScript OcConsumerRead.java "$S" "$E/scaling-repro.txt" \
  0x25660 0x207c8 0x28184 0x281d4 0x223b8 0x1cbfc 0x1cd80 \
  -log "$E/scaling-repro.log" -scriptlog "$E/scaling-repro-script.log"
```

Procedural limitation: exposed tools had no worker-dispatch/model-selection facility; requested **OpenAI Codex high delegation was not performed**. Local offline analysis is not represented as an independent delegated review. The memory service also returned `AI_NoSuchToolError`; repository memory was used. Project build/lint/test were not applicable to this documentation/offline-evidence pass; the two Python producers and instruction assertions ran successfully. Hardware execution, installed-image equivalence, protocol provider resolution and physical rail units remain unverified.

## Wording correction

Replace any earlier unconditional “voltage scaling proves SoC voltage” interpretation with **“signed PPTable VDD/GFX voltage-margin-labelled integers are scaled into additive float state; Setup provenance and physical actuator encoding remain unresolved.”** There is no basis to relabel these exact fields clock or power merely from a generic `0.001` scale. Conversely, the adjacent `0x21E8C` ratio/clock-like table path is not proof of voltage-margin consumption. Historical reports and raw evidence were preserved rather than rewritten.
