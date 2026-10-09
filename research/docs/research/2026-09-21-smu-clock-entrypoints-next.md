# SMU clock entrypoint map — exact plain-CLV static checkpoint

## Conclusion

**PASS (observed-bytes + static-analysis; hardware unrun).** Two request-oriented SMU entrypoints are byte-backed in the exact plain CLV/Robin-5 payload, and they are distinct from the previously excluded Queue-0 query/telemetry aliases:

1. **Dynamic per-domain request:** mailbox Queue ID `3`, message `0x1D`, dispatch entry `0x7550` -> `FUN_0002EA08` -> `FUN_0002E788` -> `FUN_00023890` -> `FUN_000235C8`. It accepts a packed domain index/request, writes a target float, and reaches the SMN program/poll primitive.
2. **DF P-state request:** raw dispatch table Queue ID `4`, message `0x07`, entry `0x79E8` (handler pointer `0x79EC`) -> `FUN_0001E720` -> `FUN_0001E448` -> `FUN_00023B7C`/`FUN_00023BA8`/`FUN_00023BF4` -> `FUN_00023EF8`/`FUN_00023F18`. It selects a static DF P-state row and programs domains `0x0E`, `0x0F`, `0x10`, `0x11`, and `0x12` through observed SMN register apertures.

These are **candidate request/actuator paths**, not proof that a request is MCLK, UCLK, FCLK, or a physical fabric clock on BC-250. Numeric units and domain identity remain partly unresolved. The exact CLV memory request is preserved unchanged: `AmdSetup+0x316` at ROM `0x7E5` is `0x24` (IFR label `1800MHz`), which is stored-request metadata, not a measured clock.

## Inputs and provenance

| Input                                                                                                                             | Role                      | SHA-256                                                            |
| --------------------------------------------------------------------------------------------------------------------------------- | ------------------------- | ------------------------------------------------------------------ |
| `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (16,777,216 B)                                                              | exact plain CLV donor     | `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8` |
| `archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5` (262,400 B)       | exact Robin-5 SMU body    | `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37` |
| `archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/tables/raw_messages__smu_fw_robin_5.txt` | local raw dispatch labels | `9e85df600ba0e8158a4e1cc2fe39cf570b8def300c030fac23a28805076796ce` |
| `archives/imported/smu-host-library/legacy-tmp-bc250-bc250-smu/bc250_smu/api.py`                                                  | mailbox queue IDs         | `584b135de0796e2b1e5d593b316457f18b5e5120bb3f8b5307acb551c2721185` |

The SMU body is byte-identical to CLV ROM offset `0x8FEF00`. The preserved baseline check reads `rom[0x7E5] == 0x24`; no ROM, NVRAM, candidate, register, board, network, or installation action occurred.

## Candidate A — Queue 3 message `0x1D`

### Entry and argument format

- Dispatch entry `0x7550` has handler `0x0002EA08` and flags `0x6`.
- `FUN_0002EA08` extracts `arg >> 16` as a **1-based domain-array index** and `arg & 0xFFFF` as an unsigned request value.
- The low halfword is converted directly with `ufloat.s`; no multiplier, MHz conversion, or divider arithmetic appears in the checked window.
- The target float is stored at `0x1402C + index*12`, which maps to target-array entries `0x14038..0x1411C` for indices `1..20`.
- The handler calls `FUN_0002E788` and returns status through the SMU response helpers.

### Caller/callee and observed apertures

`FUN_0002E788` compares target floats (`0x14038 + i*12`) with committed software floats (`0x13F48 + i*12`) and dispatches changed entries to `FUN_00023994`, `FUN_00023AB0`, `FUN_00023AC4`, `FUN_00023C78`, and `FUN_00023890`. `FUN_00023890` calls `FUN_000235C8`, which has a direct SMN-store path and a second-core IPC branch for its address interval. The observed dynamic domain array is:

```text
0x0D, 0x00..0x07, 0x0A, 0x18, 0x13, 0x14, 0x15, 0x16, 0x17, 0x0B, 0x08, 0x09, 0x0C
```

The group/domain table yields candidate Group-5/Group-6 program apertures:

```text
Domain 0x13 -> 0x0116C900    Domain 0x14 -> 0x0116C928
Domain 0x15 -> 0x0116C950    Domain 0x16 -> 0x0116D100
Domain 0x17 -> 0x0116D128    Domain 0x18 -> 0x0116D150
```

These are observed SMN destination calculations, not physical MCLK/UCLK/FCLK or VCN identity. The code does not join this mailbox argument to `AmdSetup+0x316`, `+0x330`, `+0x6A3`, `+0x703`, or `+0x704`.

## Candidate B — DF P-state request

### Queue-label correction and entry

The byte-backed local raw map places the entry at **Queue ID `4`**, message `0x07`, table offset `0x79E8`, with handler pointer at `0x79EC` equal to `0x0001E720`. The local API defines queue IDs `0..4`; its legacy `Queue4Mixin._q5_0x07` name and older project reports use a one-based “Queue 5” spelling for this same route. Queue ID `5` is not configured by the local API. This is a queue-label correction only; the handler and static result are unchanged.

### Argument, table, and actuator

`FUN_0001E720` validates a P-state selector against the runtime bound byte at `0xCEE0+0xF7`; the accepted branch uses low byte as the P-state index and requires the checked high-byte mode value `0x01`. It calls `FUN_0001E448`, which reads a row from the static table `0xCF0C` (five rows, 40-byte stride) and calls three actuator helpers:

- `FUN_00023B7C`: domain `0x0E`, Group 2, program register `0x0115C0FC`, arguments `row[2], row[0], row[1]`.
- `FUN_00023BA8`: domains `0x0F`/`0x11`, Groups 3/4, program registers `0x0115C8FC`/`0x0116C0FC`, arguments `row[10], row[8], row[9]`.
- `FUN_00023BF4`: domains `0x10`/`0x12`, Groups 3/4, program registers `0x0115C924`/`0x0116C124`, arguments `row[12], row[8], row[11]`.

The checked rate helpers decode the row fields as fixed-point VCO/DID arithmetic. For row `0xCF84` (P-state 3), the reproduced stored/computed numeric values are `1200.0`, `875.0`, and `109.375`; the row also contains `1750.0` at `+0x18`, but this field is not joined here to the CLV `1800` Setup request or to a physical memory clock. Existing source labels commonly associate these domains with DF/FCLK/UCLK/SOCCLK, but this task preserves that as an architectural inference, not a proven board mapping. No direct `AmdSetup` or ABL1/APOB provider edge reaches this request in the tested SMU payload.

## Explicit exclusions

The following were not treated as memory/fabric request entrypoints:

- Queue 0 `0x11` -> `0x2EA74`: reads the internal committed software float at `0x13F48 + index*12`; it is not a hardware counter.
- Queue 0 `0x13` -> `0x1E988`: returns a DF P-state index/count delta from `0xCEE0`; it is not a frequency.
- Queue 0 `0x1A` -> `0x2B634`: GFX DFLL divider path, not a memory/fabric divider.

This avoids repeating `$INV` producer scans and avoids promoting telemetry aliases to clock evidence.

## One bounded test and literal result

Existing exact verifiers were reused, copied only to the unique evidence directory, and retargeted solely for output isolation:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260921-smu-clock-entrypoints-next/verify-clock-handlers.py
PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260921-smu-clock-entrypoints-next/verify-fabric-domains.py
```

The first command returned exit `0` and literal stdout:

```text
PASS: Clock handlers and actuator chain verification complete. Written to evidence/firmware-audit/20260921-smu-clock-entrypoints-next/clock-handlers-verification.json
```

The second returned exit `0` and literal stdout:

```text
PASS: all fabric domain assertions passed. Verification written to evidence/firmware-audit/20260921-smu-clock-entrypoints-next/fabric-domains-verification.json
```

Combined capture: `source-check.stdout` SHA-256 `1e51127a837a45408538854459f04fbf336c99e3aac4e649eea008a83f5b2b44`; `source-check.stderr` is empty, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; `source-check.exit` records `0` and `0`, SHA-256 `52f96c26a39ed25108a6db43d6e11c6051eba8a498a5baab1891adfa7ac7c262`.

Machine result hashes:

- `clock-handlers-verification.json`: `eb8f41d575ef1e931b96240054bad4271c03a90055dd311ae463a3b2b5363ffa`
- `fabric-domains-verification.json`: `eedaaeaf70cf130352107760defadcef9c3005566de5254bedb980a2c3dad7d6`
- `clock-entrypoints-summary.json`: `4427add2890006487b397516111709ba6f74f56764eecd3498a6150eddae98e0`
- `queue-map-correction.txt`: `ec8a452452eb72c264f84869a72487682d11883c537681a600ae2eedee91e441`
- `SHA256SUMS.final`: `345d48c51222c34ee4622217da558f179df5bcf5f58e1ba779252237e5d79507`

## First unresolved boundary

The first missing edge is the provider/caller that supplies Queue 3 `0x1D` or Queue ID 4 `0x07` requests and joins the native CLV `AmdSetup` bytes / ABL1/APOB records to those SMU arguments. The tested payload does not establish:

- physical MCLK, UCLK, FCLK, or VCN identity of any domain/group;
- MHz versus another firmware unit for the Queue 3 low halfword;
- GDDR6 rate conversion, UCLK divider, or synchronous-crossing selector;
- invocation on the BC-250 board, PLL lock, training, applied frequency, stability, or latency;
- hardware acceptance or any relationship between the preserved `1800MHz` stored request and the static P-state table.

The next offline discriminator is the missing provider/caller join, not another Queue-0 alias scan or another literal `$INV` producer census. Hardware work remains outside this result.

## Artifacts and rollback

- Report: `docs/research/2026-09-21-smu-clock-entrypoints-next.md`
- Action log: `docs/action-logs/2026-09-21-smu-clock-entrypoints-next.md`
- Evidence directory: `evidence/firmware-audit/20260921-smu-clock-entrypoints-next/`
- Evidence manifest: `SHA256SUMS.final` (all listed files `OK` on readback).
- Rollback: remove only the report and this unique evidence directory if invalidated; preserve donor, source, original verifiers, and other project artifacts. No firmware or hardware rollback was needed because no write occurred.

Evidence class: `observed-bytes` + `static-analysis`; hardware verification: **unrun**.
