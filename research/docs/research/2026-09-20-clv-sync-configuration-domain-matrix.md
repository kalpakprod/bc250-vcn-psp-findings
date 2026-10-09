# Exact-clv configuration-domain matrix: UI intersection versus actual semantics

> Audit 2026-09-27: the final all-fields lifetime correction at the end is the retained final map. Intermediate 0x1332/0x123D/0x1238 assignments are superseded history. The cited menu-result.json has 23 total options: Auto plus 22 frequency labels. Counts in old test output are preserved, not rerun results.

## Conclusion

The exact-clv HII package advertises 22 non-Auto Memory Clock Speed labels from `125MHz` through `2000MHz`. The separate DF Clock Override numeric question accepts a bounded value `0..2000`, and the UclkDiv1M0 question offers only `Auto=0xFF` or `Enabled=1`. Numerically, every advertised Memory Clock Speed label lies within the DF numeric bounds.

That is only an **advertised UI numeric intersection**. The IFR does not establish that the labels and DF values use the same physical clock unit, refer to the same domain, share a GDDR6 rate conversion, select a supported training point, or enable a synchronous crossing. UclkDiv1M0 `Enabled` is an enum value, not a decoded divider ratio. No safe frequency, voltage, or `1:1:1` profile is inferred.

The minimum offline semantic gate for a truthful experimental default profile remains open: obtain a byte-backed consumer/actuator map for all five clock fields, resolve units/rate conversion and UclkDiv1M0 semantics, establish the relation between Memory P-state/FCLK guidance and the actual training path, and combine that with explicit existing-NVRAM/default migration precedence. Live telemetry is not required for offline generation, but hardware acceptance and any applied/default claim remain separate gates.

## Pinned evidence and reproduction

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- ROM SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Exact menu evidence: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-df-init-route/menu-result.json`
- Matrix verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-sync-configuration-domain-matrix/configuration_domain_matrix.py`
- Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-sync-configuration-domain-matrix/configuration-domain-matrix.json`

Reproduction:

```text
python3 -B evidence/firmware-audit/20260920-clv-sync-configuration-domain-matrix/configuration_domain_matrix.py
```

Observed exit status: `0`; `23/23` checks passed. Machine result SHA-256: `56f5fc1e84d5eea4178d8256c041260457378c45c46954036093f67a30a783af`.

## Configuration-domain matrix

Persisted values are direct bytes at exact-clv `AmdSetup` body base `0x4CF`; they are stored requests, not applied hardware state. Internal enum codes are shown separately from human-readable MHz labels.

| Field / body offset             | Exact-clv IFR definition                                                                                                                                                                                                             | Persisted clv value                   | Advertised UI range/intersection                                                            | Actual frequency/domain/training meaning                                                                                     |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `MemoryClockSpeed +0x316`       | QID `0x20F`; enum; `Auto=0xFF`; 22 labels: `125,225,250,400,450,500,750,850,1000,1250,1330,1375,1500,1600,1650,1700,1750,1800,1850,1900,1950,2000MHz`; enum codes are `2,4,5,8,9,10,15,17,20,25,26,27,30,32,33,34,35,36,37,38,39,40` | Raw `24`, value `36`; label `1800MHz` | Every displayed label is within DF numeric bounds `0..2000`; this is numerical overlap only | **UNKNOWN/UNRUN.** No proven physical unit conversion, GDDR6 rate mapping, training range, or synchronous-crossing selection |
| `UclkDiv1M0 +0x330`             | QID `0x229`; `Auto=0xFF`, `Enabled=1`; help: “relative to FCLK”                                                                                                                                                                      | Raw `01`, value `1` (`Enabled`)       | No numeric ratio is advertised; cannot derive UCLK/MCLK relation                            | **UNKNOWN/UNRUN.** `Enabled` is not a decoded divider factor or synchronization proof                                        |
| `FclkDpm +0x6A3`                | QID `0x7045`; `Disabled=0`, `Enabled=1`, `Auto=15`; CALLBACK flag set                                                                                                                                                                | Raw `0F`, value `15` (`Auto`)         | No frequency value; callback-bearing control context only                                   | **UNKNOWN/UNRUN.** Callback/static serialization does not prove FCLK application or DPM behavior                             |
| `DfClockOverrideControl +0x703` | QID `0x37D`; `Auto=0xFF`, `Manual=1`                                                                                                                                                                                                 | Raw `01`, value `1` (`Manual`)        | Enables the separate numeric DF override request in the UI model                            | **UNKNOWN/UNRUN.** Control/value pairing is static; applied domain and training behavior are unresolved                      |
| `DfClockOvrd +0x704`            | QID `0x37E`; numeric question; bounds `[0,2000,0]`; no discrete option/default opcode                                                                                                                                                | Raw `8C05` LE, value `1420`           | Numeric interval overlaps every displayed Memory Clock Speed label                          | **UNKNOWN/UNRUN.** No unit equivalence, DF/FCLK identity, or training support is established                                 |

The DF help text says to ensure `FCLK > UCLK` and disable Memory P-state; that is UI guidance, not a measured constraint or proof that equal MCLK/UCLK/FCLK is valid. The exact question table gives `+0x704` QID `0x37E` no CALLBACK flag; only FCLK_DPM QID `0x7045` is callback-bearing.

## Domain and training qualification

Observed/static facts:

- Numeric UI overlap: `125..2000` labels are inside `[0,2000]`.
- Internal Memory Clock enum codes are not the displayed MHz numbers.
- UclkDiv1M0 has no numeric divider option beyond `Enabled`.
- No exact-clv menu bytes in this matrix identify a shared clock unit, GDDR6 edge/data-rate conversion, common PLL, synchronous-crossing bit, or training result.
- No hardware training, boot, clock measurement, voltage measurement, or live NVRAM action was performed.

Therefore “supported training/frequency/domain mapping” is **unknown**, not “all UI-overlapping combinations are supported.” Historical requested profiles and UI labels are not substituted for this missing evidence.

## Minimum offline semantic gate

Before describing a truthful experimental default profile, the project still needs one bounded static result that:

1. maps each of `+0x316`, `+0x330`, `+0x6A3`, `+0x703`, and `+0x704` to a concrete consumer/actuator or explicitly proves the value is discarded;
2. resolves units and rate conversion, including whether displayed Memory Clock Speed labels represent the same quantity as DF override values;
3. resolves UclkDiv1M0 semantics and identifies whether any control selects synchronous crossing rather than merely storing a request;
4. reconciles Memory P-state and `FCLK > UCLK` guidance with the actual training/configuration path; and
5. combines this map with existing-NVRAM, fallback, IFR, and migration precedence.

Live telemetry is not an offline prerequisite. It is required later for hardware acceptance of applied clocks, training, synchronization, performance, and stability. Until the offline gate closes, the only truthful label is an **advertised/requested UI profile with unresolved physical semantics**, not a supported frequency or `1:1:1` default.

## Acceptance status

- **PASS:** exact pinned ROM/menu identity, option lists, bounds, QIDs/flags, persisted bytes, and numerical-overlap calculation.
- **PASS:** explicit separation of enum codes, displayed labels, DF numeric bounds, and physical semantics.
- **OPEN:** consumer/actuator mapping, units/rate conversion, Uclk divider semantics, Memory-P-state/training relation, synchronous-crossing selection, and migration-aware profile semantics.
- **UNRUN:** firmware execution, live NVRAM, training, hardware clocks, voltage, performance, and stability.

## Supplemental Memory P-state mapping correction (2026-09-20)

The matrix was extended after review of the bounded exact-clv Memory P-state artifact. The prior `23/23` snapshot is superseded by the current `30/30 PASS` machine result, which includes a gating-control row:

| Gating control        | Exact static mapping                                                                                                                                                                            | Persisted clv value                  | Qualification                                                                                                                                        |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MemoryPstate +0x36D` | QID `0x25E`, form `0x7032` DRAM Power Options; options `Auto=0xFF`, `Enabled=1`, `Disabled=0`; flags `0x10`; no local conditions; package path `0x7000 -> 0x7008 -> 0x702E -> 0x7030 -> 0x7032` | Absolute ROM `0x83C` = `FF` (`Auto`) | `CbsBasePei` serializes the byte as `$INV` record `0x123D`; downstream consumer, training behavior, units, and synchronization effect remain unknown |

Supplemental evidence: `evidence/firmware-audit/20260920-clv-sync-stage2-memory-pstate/memory-pstate-result.json`, SHA-256 `237546fe5cc4edf44659dab93ce2ccd13ecbd817a6808ef18fa599b1da0b87c7`, `9864/9864 PASS`; evidence-directory manifest check `4/4 OK`; report SHA-256 `e018df53b222110702a94781684760db5174c12eb1e17cd51abbacb1284409c3`.

This strengthens the static configuration matrix but does not close the minimum offline semantic gate: token `0x123D` still lacks a proven DF override/training consumer, and the help phrase remains guidance rather than causal hardware evidence. No value `Disabled=0` is recommended or written.

## Adjacent serializer-token discrimination correction (2026-09-20)

A supplemental exact-byte discrimination result was reviewed and its evidence-directory manifest returned `4/4 OK`; `19/19` checks passed. Current result SHA-256 is `5f19242d614102ff92391753a3459ff7a57357adbc95c19cec8b05e7057f4eb9` and report SHA-256 is `43f37b835c3e352bdc09752baf172f6e0696d2d2674b63238656658822b87e92`.

The static distinctions are:

| Control          | body offset |        baseline | exact `$INV` record |
| ---------------- | ----------: | --------------: | ------------------: |
| `PhyPowerSaving` |     `0x368` | `0xFF` (`Auto`) |            `0x1238` |
| `MemoryPstate`   |     `0x36D` | `0xFF` (`Auto`) |            `0x123D` |
| `FclkDpm`        |     `0x6A3` | `0x0F` (`Auto`) |            `0x1332` |

The prior `+0x6A3 -> 0x1331` mapping in earlier bounded evidence is superseded for this exact CbsBasePei byte audit by `+0x6A3 -> 0x1332`; this is a token-identity correction only, not evidence of a consumer or applied clock. The historical ULTIMATE bytes disable all three controls (`+0x368=0`, `+0x36D=0`, `+0x6A3=0`), so that profile cannot isolate the Memory P-state effect.

The matrix now reports `38/38 PASS`, includes both `PhyPowerSaving` and `MemoryPstate` context rows, and records `FclkDpm` serializer record `0x1332`. Downstream consumers, training, units, and synchronization remain unknown; no value was changed or recommended.

## Cross-module token correction confirmation (2026-09-20)

A second raw-byte correction independently checks both `CbsBasePei` and `AmdNbioSmuV10Pei`: `Setup+0x6A2 -> $INV 0x1331`, while `Setup+0x6A3 (FCLK_DPM) -> $INV 0x1332`. Correction report SHA-256: `613d70da877a4439cd3504ef1d835bc39ff8844b92152de41d71882f4611efa5`; machine result SHA-256: `8b6828be6f26cf379f79ed6e5c88560c9ed8d934c35bff2011108999f5dc16a5`; `13/13 PASS`, manifest `4/4 OK`.

This supersedes the earlier `+0x6A3 -> 0x1331` identity in prior bounded evidence. It remains a serializer-token correction only; downstream consumption and clock semantics are unresolved.

## Decisive destination-pointer ownership correction (2026-09-20)

The previous `+0x6A3 -> 0x1332` correction is withdrawn. A contiguous instruction/dataflow trace paired each source load with the same destination record's `dest+3` value store and subsequent `dest += 4`:

- `+0x6A2 -> token 0x1330`;
- `+0x6A3 (FCLK_DPM) -> token 0x1331`;
- `+0x6A4 -> token 0x1332`.

The trace is duplicated in both exact modules. Own correction evidence: `evidence/firmware-audit/20260920-clv-sync-record-ownership-correction/record-ownership-result.json`, SHA-256 `cab9dd7e18defabe1459537fe870a520c24602f1641bd44af5e78ad3e2b2aaf3`, `12/12 PASS`. The own configuration matrix is now `39/39 PASS` and records FCLK_DPM token `0x1331`.

The earlier nearest-header/preceding-load pairing was a methodological error and remains preserved in prior artifacts. This correction identifies serializer ownership only; downstream consumer, units, training, physical clock and synchronization semantics remain unknown.

## Superseding ownership correction (2026-09-20)

The earlier `+0x6A3 -> 0x1332` statement is superseded by a destination-pointer trace. Current own matrix result is `39/39 PASS`, with FCLK_DPM token `0x1331`.

Evidence: `docs/research/2026-09-20-clv-sync-record-ownership-correction.md`, machine result SHA-256 `cab9dd7e18defabe1459537fe870a520c24602f1641bd44af5e78ad3e2b2aaf3`, `12/12 PASS`. Correct ownership: `+0x6A2 -> 0x1330`, `+0x6A3 -> 0x1331`, `+0x6A4 -> 0x1332`; both exact modules match. Prior nearest-header pairing remains historical and is not used in the current matrix.

## Final all-fields lifetime correction (2026-09-20)

The canonical all-fields lifetime artifact was independently verified: `29/29 PASS`, manifest `3/3 OK`. It corrects two prior wrong mappings:

- `MemoryPstate +0x36D -> $INV 0x123C` (not `0x123D`);
- `PhyPowerSaving +0x368 -> $INV 0x1237` (not `0x1238`).

Combined with the destination-pointer FCLK trace, the current seven-field static map is:

| Setup field                     |   Record | Width |
| ------------------------------- | -------: | ----: |
| `+0x316 MemoryClockSpeed`       | `0x11ED` |    u8 |
| `+0x330 UclkDiv1M0`             | `0x1204` |    u8 |
| `+0x368 PhyPowerSaving`         | `0x1237` |    u8 |
| `+0x36D MemoryPstate`           | `0x123C` |    u8 |
| `+0x6A3 FclkDpm`                | `0x1331` |    u8 |
| `+0x703 DfClockOverrideControl` | `0x1373` |    u8 |
| `+0x704 DfClockOvrd`            | `0x1374` |   u16 |

The supplemental Uclk semantics result (`31/31 PASS`, manifest `8/8 OK`) confirms no ratio arithmetic in the bounded `+0x330`/`+0x36D` serializer windows; it does not establish downstream ratio semantics. The own matrix is now `44/44 PASS`, with all seven fields sourced from exact lifetime/ownership evidence rather than historical token labels.
