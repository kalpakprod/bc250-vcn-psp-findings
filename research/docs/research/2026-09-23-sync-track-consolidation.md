# Sync track consolidation: MCLK=FCLK=UCLK 1:1:1 on BIOS 5.00 CLV

Date: 2026-09-23. Scope: read-only repository mining; this file is the only new artifact.
Pinned base image: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA-256
`ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
Pinned ABL1 payload SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
Evidence classes: PROVEN-STATIC = byte-backed and reproduced in-repo; HYPOTHESIS = plausible,
join unproven; CLOSED-NEGATIVE = bounded negative with stated limits; NOT-TESTED = requires boot.

Standing rule preserved: no 1800/1800/1800 recipe is issued. Nothing below is a hardware claim.

## 1. Consolidated state (MECE: one row per question)

### 1a. Storage and serialization of the five clock fields

| #   | Question                                                                                                                                                                                                                                                     | Status                                                                     | Evidence pointer                                                                                                                           |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| S1  | Field identities and AmdSetup offsets: MemoryClockSpeed +0x316, UclkDiv1M0 +0x330, MemoryPstate +0x36D, FclkDpm +0x6A3, DfClockOverrideControl +0x703, DfClockOvrd +0x704 (u16); clv persisted values 0x24(1800 label), 0x01, 0xFF, 0x0F, 0x01, 0x058C(1420) | PROVEN-STATIC                                                              | docs/research/2026-09-20-clv-sync-configuration-domain-matrix.md, "Configuration-domain matrix" and "Final all-fields lifetime correction" |
| S2  | Serializer token ownership: +0x316→$INV 0x11ED, +0x330→0x1204, +0x36D→0x123C, +0x6A3→0x1331, +0x703→0x1373, +0x704→0x1374                                                                                                                                    | PROVEN-STATIC                                                              | same doc, final seven-field table; record-ownership correction 12/12 PASS                                                                  |
| S3  | UEFI consumers of the seven $INV field records: none found; every reference is one of seven byte-identical producer serializers (6 Fabric/NBIO PEIMs + CbsBasePei). 0 request/compare sites in 233 modules                                                   | PROVEN-STATIC (bounded: immediates/literals only)                          | docs/research/20260920-clv-inv-token-ownership.md, "PRODUCER_ONLY_IN_MODULE_SET"; two independent methods concur                           |
| S4  | Therefore the consumer, if any, is outside the UEFI module set (PSP/$PS1, ABL, SMU, host)                                                                                                                                                                    | HYPOTHESIS (direct consequence of S3, carriers unsearched for most tokens) | same doc, "Verdict and consequences"                                                                                                       |
| S5  | IFR enum labels (125..2000 MHz) are numerically inside DF override bounds 0..2000, but unit/domain equivalence is NOT established                                                                                                                            | PROVEN-STATIC (overlap only)                                               | docs/research/2026-09-20-clv-sync-configuration-domain-matrix.md, "Domain and training qualification"                                      |
| S6  | UclkDiv1M0 enum `Enabled=1` is not decoded as a divider ratio; no ratio arithmetic in serializer windows                                                                                                                                                     | PROVEN-STATIC                                                              | matrix, supplemental Uclk semantics 31/31 PASS                                                                                             |

### 1b. NVRAM / precedence (why stored values can be ignored)

| #   | Question                                                                                                                                                                         | Status                                                                                    | Evidence pointer                                                                                                           |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| N1  | Native variable read path: NvramPei BF8 executes natively; live AmdSetup reads work, defaults-only→NOT_FOUND; per-store parser preserves archived values (Tcl16 etc.)            | PROVEN-STATIC (host-native harness, not board)                                            | ledger "Native lookup execution"; evidence/firmware-audit/20260923-native-variable-harness/result.json                     |
| N2  | CbsBasePei acquisition: success preserves archived profile; 3 failure modes restore Auto/DF1000; serialized into $INV (1122 records)                                             | PROVEN-STATIC (native harness)                                                            | ledger "Native acquisition-to-$INV closed"; docs/research/2026-09-23-native-cbs-inv.md                                     |
| N3  | CMOS clock (72:96) can be read and accepted, then overwritten by APCB item7 lookup: APCB+0x482 (ROM 0xAB1482) enum 0x24→policy 1800 wins over valid CMOS in executed native path | PROVEN-STATIC (native execution with real APCB; runtime 7B000 copy is a model assumption) | docs/research/2026-09-23-cmos-apcb-precedence.md, "Observed native path" + 6-case run                                      |
| N4  | Runtime overlay producer: who copies/patches the runtime APCB at 7B000 and whether AmdSetup values ever reach APCB+0x482                                                         | OPEN / NOT-TESTED                                                                         | 2026-09-23-cmos-apcb-precedence.md "Decision and limits"; no report closes this                                            |
| N5  | Historical OC archives are not clean patch sources and their profiles did not apply (screenshot chronology shows Auto; UclkDiv1M0=0 i.e. 1:2 in the "low-latency" profile)       | CLOSED-NEGATIVE for using archives as recipes                                             | ledger "Chronology falsification", "Ultimate profile exact mapping"; docs/research/2026-09-23-profile-03-nonapplication.md |

### 1c. MCLK path (ABL1 item 0x17)

| #   | Question                                                                                                                                              | Status                                                             | Evidence pointer                                                                                  |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| M1  | Enum 0x24→policy integer 1800 (MHz-tagged strings), context flow to per-channel +0x20 policy writer, then ABL1 0x7E3A→0x0C60 service call item 0x17   | PROVEN-STATIC                                                      | docs/action-logs/2026-09-21-memory-clock-units-next.md, "Observed result": 38/38 PASS             |
| M2  | Item 0x17 dispatch: wrapper 0xC60→0xE50/0xFD8→literal table 0x6E224; entry (0x606FD, 0x17)→handler 0x95FC — CONDITIONAL on unproven load base 0x57100 | HYPOTHESIS (base unproven)                                         | docs/research/2026-09-23-mclk-item17-policy-path.md                                               |
| M3  | Handler 0x95FC semantics: reads u16 from channel+0x20, stores to outer+channel*4+0x278; 0x20 is fill length, not descriptor                           | PROVEN-STATIC (aligned disasm; no physical writer found in window) | same doc; earlier "descriptor" wording withdrawn                                                  |
| M4  | Table/load-base provenance for 0x95FC and any physical writer of +0x278                                                                               | OPEN                                                               | ledger "MCLK item17 boundary": "validate table/load-base provenance, not assert runtime dispatch" |
| M5  | "Multi-Die DRAM Speed Sync" string at 95FC gate: names a feature, NOT proven 1:1:1 enablement                                                         | CLOSED-NEGATIVE (as sync-enable-bit evidence)                      | docs/research/2026-09-23-abl-pll-service-boundary.md, "Why this changes the next work" section    |

### 1d. FCLK/UCLK path (PLL service boundary)

| #   | Question                                                                                                                                                                                                                               | Status                                                                                   | Evidence pointer                                                                               |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| P1  | ABL1 0x5E68 issues SVC#0x28 with strings `PSPSMC_MSG_SetupFclkPll` (selector 0x0E) and `PSPSMC_MSG_SetupUclkPll` (selector 0x0F)                                                                                                       | PROVEN-STATIC                                                                            | docs/research/2026-09-23-abl-pll-service-boundary.md, "Существенный результат"                 |
| P2  | UCLK service argument = input word >> 1 (LSR.W R8,R4,#1 at 0x5F30): 1800→900, 1750→875 (arithmetic, not measured MHz)                                                                                                                  | PROVEN-STATIC (executed in Unicorn, 9 cases)                                             | same doc, "UCLK: явное деление" + case table                                                   |
| P3  | FCLK service argument priority: provider lookup token 015F/0160 → else 1200 (or 250 if nested+0x790==6); clean APCB gate 0x015F=1 at ROM 0xAB1B99, value 0x0160=1420 at 0xAB1B9A → FCLK arg 1420                                       | PROVEN-STATIC (executed: real APCB bytes → service argument, 5 cases)                    | same doc, "Существенное продолжение: источник взят из настоящего APCB"                         |
| P4  | DfClockOvrd (+0x704, 1420) equals the APCB 0160 value, but AmdSetup→APCB producer link is NOT proven; equality is not a join                                                                                                           | HYPOTHESIS                                                                               | same doc: "совпадение1420 … не доказывает связь этих двух хранилищ"                            |
| P5  | Runtime cache (A04E/HEAP) population origin and load base 57100                                                                                                                                                                        | OPEN (cold-cache path executed from real APCB; cache-hit path only with synthetic cache) | same doc, "Native runtime-HEAP → PLL"                                                          |
| P6  | SVC#0x28 transport: plaintext PSP TrustedOS type2 dispatcher subtracts 51, caps at 80, returns 9 for selectors 28/2D — this TOS is NOT the early ABL service handler; matching early handler not found in available plaintext payloads | CLOSED-NEGATIVE (for type2 TOS); type1 payload unclassified (size 46592, hash 0bfbd84a…) | same doc, "Проверка доступного PSP-диспетчера" + "Граница раннего сервиса"                     |
| P7  | SMU candidate handlers for IDs 7/0E/0F: vector index 5 → 1E720 (state select), 1F218 (domain 0E), 1F2F0 (domain 0F/11); handlers reject when state+F6=FF, convert arg to float ×0.001. SVC28→queue link not proven                     | HYPOTHESIS (byte-checked decompile, not native execution)                                | same doc, "Более позднее переключение в ABL4" + "Очередь: устранена неоднозначность нумерации" |
| P8  | Early PLL path is `GnbSmuInitAblCAR` (initialization); steady-state after training / DF P-state switches (ABL4 SwitchToStartupDfPstate, SVC28 selector 7 arg 100) is a separate, unresolved actuation                                  | OPEN                                                                                     | same doc, "Ограничение, важное для1:1:1" + ABL4 section                                        |
| P9  | UclkDiv1M0 phase handlers in ABL1/3/4 ("Override UclkDiv1 M0..M3"): log-only on executed branches; 0 context writes, 0 actuator callbacks on 11 executed cases                                                                         | CLOSED-NEGATIVE (bounded to these handlers; whole field NOT declared inert)              | docs/research/2026-09-23-uclk-application.md                                                   |
| P10 | AmdSetup+330 / $INV 0x1204 → APCB token21 (+0x86F UclkDiv M0) join                                                                                                                                                                     | OPEN / NOT-TESTED                                                                        | same doc: "Связь AmdSetup+330 / INV1204 с APCB token21 всё ещё не установлена"                 |

### 1e. Voltage / acceptance (R2/R3/R6/R7)

| #                                                                                                                                                                                                                                                                                                                                                                               | Question                                                                                                                                      | Status                        | Evidence pointer                                                                  |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- | --------------------------------------------------------------------------------- |
| V1                                                                                                                                                                                                                                                                                                                                                                              | VDD control/value 1363/1364, GFX 1365/1366 tokens: producer-only in UEFI (see S3); +150 ≠ 1.15 V                                              | PROVEN-STATIC (producer-only) | docs/research/20260920-clv-inv-token-ownership.md                                 |
| V2                                                                                                                                                                                                                                                                                                                                                                              | SoC rail feedback topology: nine nets verified; no separate external programmable actuator listed; no proven firmware actuator for +VDDCR_SOC | OPEN (R2 unresolved)          | ledger "SoC feedback topology"; docs/research/2026-09-23-soc-feedback-topology.md |
| R6 hardware acceptance: NOT-TESTED (no boot ever exercised a sync candidate). R7 operator guide: draft; corrected so that "help FCLK>UCLK" is guidance, not enforcement, and 015F/0160 are ordered lookup alternatives (ledger "Clock reconciliation"). P2 above gives a concrete mechanism (UCLK arg = half of input) explaining why equal entries may not yield equal clocks. |

## 2. The fork — joins that unlock the recipe

Ranked by offline closability (evidence availability, closability without hardware):

**J1 — AmdSetup→runtime-APCB producer join (closable offline, highest value).**
Does any code path carry MemoryClockSpeed (+0x316/$INV 0x11ED, or any carrier) into the
runtime APCB that ABL1 reads at 7B000 (specifically +0x482 item7 and gate/value 0xB99/0xB9A)?
S3 says the UEFI $INV path is producer-only; N3 shows APCB wins over CMOS. If J1 closes
negative, then BIOS-only MCLK edits never reach the PLL arguments — which would itself close
the BIOS-only route for MCLK and redirect work to APCB-side construction. All ingredients
(real APCB, native harness, writer-watch method) already exist in
`evidence/firmware-audit/20260923-cmos-native-acceptance/` and `20260923-abl95fc-next/`.

**J2 — SVC#0x28 transport and unit semantics (partially offline).**
Which component implements the early SVC28 selectors 0E/0F/07, and what are the argument
units? P6 closed the type2 TOS; remaining offline carriers: the unclassified type1 PSP
payload (0x0BFBD84A…), ABL0→ABL1 internal service stubs, or an early PSP bootloader not yet
extracted. If the type1 payload is encrypted or absent, this join is NOT closable offline and
becomes the honest wall. P2 (halving) makes J2 decisive: without unit semantics, no equal
triple can be claimed.

**J3 — Final UCLK divider / steady-state actuation (least offline-closable).**
P9/P10: the named UclkDiv1M0 handlers are log-only, the token21 join is open, and P8 shows
the found PLL path is initialization-time only; steady-state after DF P-state switches is
unmapped. This join likely needs either J2's semantics or a boot observation; do not promise
it from statics.

## 3. Next executable action (single, offline, self-contained)

**Full-entry ABL1 writer census over the memory-clock policy word.** Extend the existing
Unicorn harness (`evidence/firmware-audit/20260923-cmos-native-acceptance/native_provider.py`,
model: real APCB at 7B000, hooks limited to logging 130C/112A0 and terminal SVC, assertions
retained) to start from the ABL1 entry rather than mid-function, and record every write to:
(a) any address inside the 0x2000-byte APCB image at 7B000, in particular +0x482, +0x86E..0x872,
+0xB99, +0xB9A; (b) context+0x2BC and nested+0x2C; (c) outer+channel*4+0x278. For each write,
log PC, value, and classify the producing path (CMOS-derived, APCB-native, AmdSetup-carrier,
other). Then diff the write sets between baseline APCB and an APCB with item7 modified.
Deliverable: `docs/research/2026-09-23-abl1-apcb-writer-census.md` + result.json. Exit
criteria: if no write source other than the known CMOS/APCB paths appears, J1 closes
CLOSED-NEGATIVE for the emulated window (AmdSetup never reaches the PLL arguments in native
ABL1 code), and the next step moves to J2's type1 payload; if an unknown writer appears, it is
the producer join. Reuse, do not rebuild: ABL1 SHA, harness hooks, and checksum scheme from the
two cited evidence directories. No ROM writes, no new candidates, no 1800/1800/1800.

## 4. Honest boundary: what statics cannot establish

- Whether any requested value becomes a physical frequency: all clock evidence is stored
  requests, serialized records, or service arguments; no board measurement exists (S1/S3, P1-P3).
- SVC28 handler semantics and argument units (J2): the plaintext corpus contains no matching
  early handler (P6); if the missing handler lives in the unclassified/encrypted type1 payload,
  no offline method can close this.
- Steady-state clocks after memory training and DF P-state transitions (P8): the proven PLL
  path is early init; later transitions may reprogram clocks from sources never touched here.
- Training acceptance of any specific MCLK/UCLK pair, GDDR6 rate conversion, and latency
  outcome: hardware-only by nature (R6 NOT-TESTED).
- Whether the physical board revision exposes a firmware-controllable +VDDCR_SOC actuator (V2).
- A boot can also contradict any PROVEN-STATIC row: load-base 0x57100 and the 7B000 runtime
  copy are explicit model assumptions (M2/N3/P5).
