# SMU clock entrypoint continuation — source and unit boundary

## Conclusion

**PASS (observed-bytes + static-analysis; hardware unrun).** The exact CLV SMU payload exposes two request-to-consumer data sources:

- Queue ID `3`, message `0x1D`: mailbox low16 request -> `ufloat.s` -> dynamic target array -> shared clock actuator.
- Raw Queue ID `4`, message `0x07`: mailbox P-state selector -> static DF table row -> DF actuator helpers.

The first path has no encoded MHz conversion or divider selector in the checked request window. The second path encodes a P-state selector and fixed-point/DID arithmetic that reproduces stored numeric rates, but does not encode a proven physical MCLK/UCLK/FCLK identity or synchronous-crossing selector. The native CLV `AmdSetup+0x316=0x24` (`1800MHz` label) remains an unmodified stored request and is not joined to either mailbox input.

## Bound target and baseline

- Donor: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- SMU body: `archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5`, 262,400 bytes, SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`, byte-identical at ROM `0x8FEF00`.
- Preserved request: ROM offset `0x7E5` (`AmdSetup+0x316`) = `0x24`, IFR-labelled `1800MHz`.
- Existing report used as context: `docs/research/2026-09-21-smu-clock-entrypoints-next.md`; no prior queue-map census or telemetry alias scan was repeated.

## Candidate A — Queue 3 message `0x1D`

### Source and consumer edge

Exact instruction dataflow:

```text
Queue ID 3 / msg 0x1D @ dispatch 0x7550
  -> FUN_0002EA08
     arg[31:16] = 1-based dynamic-domain index
     arg[15:0]  = unsigned request, converted directly with ufloat.s
     target[0x1402C + index*12] = float(request)
  -> FUN_0002E788
  -> FUN_00023890
  -> FUN_000235C8 (SMN program/poll path)
```

The checked `FUN_0002EA08` window contains no multiplication, fixed-point conversion, MHz constant, or divider arithmetic. Therefore the exact encoded unit of the low16 value is **not identified**; it is only proven to be an unsigned integer converted directly to a float target.

### Bulk target source

The same target array has a separate static source in `FUN_0002E9DC`:

```text
PPTable base literal 0x7B5C + pstate*100 + 0x48
  -> 20 uint32 values -> ufloat.s
  -> target array 0x14038 + i*12
```

This source is distinct from the direct Queue 3 mailbox request. The byte-backed edge stops at the committed PPTable base; a complete runtime/provider edge from native `AmdSetup` or ABL1/APOB into this target source is not established here. The shared actuator later commits target floats to the internal software state array; that committed state must not be treated as physical clock telemetry.

The dynamic domain map contains IDs `0x13..0x18` in Group-5/Group-6-associated entries with observed program apertures `0x0116C900`, `0x0116C928`, `0x0116C950`, `0x0116D100`, `0x0116D128`, and `0x0116D150`. These addresses are static destination calculations only; no physical MCLK/UCLK/FCLK or VCN identity is assigned.

## Candidate B — raw Queue ID 4 message `0x07`

### Selector and static table source

The raw dispatch entry is `0x79E8`, with handler pointer at `0x79EC` equal to `FUN_0001E720`. Older project wording and the helper name `_q5_0x07` use a one-based “Queue 5” label; the local API queue integer and raw table are Queue ID `4`.

```text
raw Queue ID 4 / msg 0x07
  -> FUN_0001E720
     high byte mode must be 0x01 in the checked branch
     low byte selects P-state index, bounded by byte 0xCEE0+0xF7
  -> FUN_0001E448
     static row base 0xCF0C, stride 0x28
  -> FUN_00023B7C / FUN_00023BA8 / FUN_00023BF4
  -> FUN_00023F18 and SMN program helpers
```

For row `0xCF84` (P-state 3), observed floats are:

- row `+0x04`: `1200.0`
- row `+0x10`: `875.0`
- row `+0x14`: `109.375`
- row `+0x18`: `1750.0`

The static helper arithmetic uses a fixed-point VCO multiplier and AMD DFS DID decoding. Applying that arithmetic to row bytes reproduces `1200.0`, `875.0`, and `109.375`. This establishes a numeric encoding/dataflow, not the external unit label or physical domain identity. The `+0x18` value is not joined by this path to the native CLV `1800` request or to a proven memory-clock actuator.

Actuator argument edges are byte-backed:

- `0x23B7C`: domain `0x0E`, Group 2, program register `0x0115C0FC`, `row[2], row[0], row[1]`.
- `0x23BA8`: domains `0x0F`/`0x11`, Groups 3/4, program registers `0x0115C8FC`/`0x0116C0FC`, `row[10], row[8], row[9]`.
- `0x23BF4`: domains `0x10`/`0x12`, Groups 3/4, program registers `0x0115C924`/`0x0116C124`, `row[12], row[8], row[11]`.

Source strings/community labels may call these DF/FCLK/UCLK/SOCCLK-like domains, but the exact CLV payload does not provide a physical MCLK/UCLK/FCLK selector or synchronous-crossing bit in this path.

## What remains unresolved

The first unresolved boundary is the caller/provider that supplies Queue 3 `0x1D` and Queue ID 4 `0x07` arguments and joins them to native `AmdSetup`, ABL1, or APOB state. Specifically unproven:

- whether Queue 3 low16 values are MHz, another frequency unit, or a firmware-internal target scale;
- whether Queue 3 Group-5/6 destinations are MCLK, UCLK, FCLK, VCN, or another clock domain;
- whether Queue ID 4 table outputs correspond to physical FCLK/UCLK/MCLK and any GDDR6 conversion;
- UCLK divider/synchronous-crossing selector and training semantics;
- runtime invocation, PLL lock, physical frequency, stability, or hardware acceptance.

No board/register/NVRAM/network/ROM/candidate operation occurred.

## Reproduction and evidence

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260921-smu-clock-entrypoints-continuation/trace_clock_sources.py
```

Final literal stdout:

```json
{
  "checks": 25,
  "preserved_clv_request": {
    "AmdSetup_offset": "0x316",
    "byte": "0x24",
    "label": "1800MHz",
    "rom_offset": "0x7E5"
  },
  "pstate3": {
    "row": "0xCF84",
    "stored_plus_0x04": 1200.0,
    "stored_plus_0x10": 875.0,
    "stored_plus_0x14": 109.375,
    "stored_plus_0x18": 1750.0
  },
  "status": "PASS"
}
```

Exit status: `0`; stderr empty. Machine result: `source-consumer-result.json`, SHA-256 `08a30b4bc9f7153ff81f532ebf5203d355f27840c3aca59e58a51797b50f7b63`. Verifier SHA-256 `540e8be034cdbdc8a42f63d504c2a3d4c42e7ad4feabd9e8ad9bdfec59afe233`. Output SHA-256 `beb6f5a6356f6bd0f845fc3cf2adef0ba8f3f3506622c824c758bab65c38c66b`; stderr SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; exit capture SHA-256 `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`.

Two verifier corrections are preserved in the action log: malformed instruction-window hex, then wrong arithmetic input width. Neither changed source/input bytes.

Artifacts:

- Report: `docs/research/2026-09-21-smu-clock-entrypoints-continuation.md`
- Action log: `docs/action-logs/2026-09-21-smu-clock-entrypoints-continuation.md`
- Evidence directory: `evidence/firmware-audit/20260921-smu-clock-entrypoints-continuation/`
- Manifest: `SHA256SUMS.final`; all listed files must return `OK` on readback.

Evidence class: `observed-bytes` + `static-analysis`; hardware verification: **unrun**.
