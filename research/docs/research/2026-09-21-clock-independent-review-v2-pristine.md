Current: this v2 copy adds the newly verified memory-clock/APOB/ABL boundary. It supersedes only the earlier recommendation to trace a presumed `$INV 0x11ED -> ABL1/APOB` chain: the three observed paths below are distinct and no join is proven. The original `2026-09-21-clock-independent-review.md` is preserved unchanged.

# Independent clock evidence review

## Decision

**NO-GO for any claim that the pinned CLV request produced physical `MCLK=UCLK=FCLK=1:1:1`, applied 1800 MHz, or established a safe operating point.** Preserve the exact CLV request as an observed/static baseline only. The next offline action is to trace one byte-backed consumer/source edge for `$INV 0x11ED` (Memory Clock Speed) into the ABL1/APOB/SMU-side object, or stop at the first unresolved boundary; do not create another equal-number profile or repeat a generic immediate-token census.

The direct UEFI scans and provider/HOB checks are useful bounded negatives. They do **not** prove that a token has no consumer, that its data reaches ABL1/APOB/SMU, or that it actuates a clock.

## Bound target and reopened artifacts

Target: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8` (reopened; unchanged).

| Artifact                                                                                                           | Reopened result                                                                                                                      | SHA-256                                                            | Evidence class                        |
| ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------------------------- |
| `evidence/firmware-audit/20260920-clv-sync-frequency-unit-discrimination/frequency-unit-result.json`               | `11/11 PASS`; driver FCLK/MCLK/UCLK exports alias `MemclkFrequency`; SMU `0x11` is committed software state; `0x13` is a state/count | `6027fd54d8803fbd2a8b22f09c098ec5e9174ddbb143fd2b41f68a5575f7fb0c` | observed-bytes + static + host-tested |
| `evidence/firmware-audit/20260921-clock-discriminating-test/uclk-consumer-trace.json`                              | `22/22 PASS`; `AmdSetup+0x330` is copied as byte into `$INV 0x1204`; adapter is not a clock writer                                   | `bb9ed4ea7b21f9f86f4d2e757fb940a77ce545464da900a26815fdf007796910` | observed-bytes + static               |
| `evidence/firmware-audit/20260921-luna-token1204-provider-object-boundary/token1204-provider-boundary-result.json` | `45/45 PASS`; `0x25D3` uses `SIDT`/`[IDTR.Base-4]`, `0x266F` calls `[ECX+0x34]`; no `0x1204` in this bounded provider edge           | `b20a743af0c18d547d77aaaca08ba515518fa496aa690a3320939c7f0d9eae53` | observed-bytes + static               |
| `evidence/firmware-audit/20260921-df-consumer/df-consumer-result.json`                                             | `9/9 PASS`; serializers for `0x1373/0x1374`; zero selected direct-query patterns in extracted UEFI corpus                            | `7da3381cc8c203024f7bc7817053a47c6c9af39012455bba2c7ae1f0aa2c7f24` | observed-bytes + static, bounded      |
| `evidence/firmware-audit/20260921-clock-observability-next/clock-observability-source-result.json`                 | `12/12 PASS`; ATOM API is a boot/PLL-frequency candidate, not bound to exact CLV physical readback                                   | `504e67618d0bf6ece9ca0c5fc543e12c38f1a0f5cfae1d9f652431be40322fff` | observed-bytes + static               |
| `evidence/firmware-audit/20260921-pstate-precedence-next/pstate-precedence-result.json`                            | `47/47 PASS`; ABL1 branch/writeback shape at `0x9644..0x989A`; stack-slot meanings and Setup joins unknown                           | `76cf4c684d5e4caaf8a40372b2b5ac71bb851fd2f8c101742efdc3ec72ad87a9` | observed-bytes + static               |
| `evidence/firmware-audit/20260921-native-clock-menu-next/direct-ifr-check-result.json`                             | `25/25 PASS`; six writable VarStore questions, local refs, donor bytes, `SetVariable` call bytes                                     | `0d6182635f9a7463e75537d9671753502f446696f78081a860af156abf4fcb15` | observed-bytes + static               |

Fresh manifest checks passed for the clock discriminator (`13` entries), provider result (`4` entries), DF result (`5` entries), pstate result (`16` entries), native-menu evidence (`14` entries), and observability result (`5` entries) when run from the path each manifest declares. The pstate result also preserves the failed formatting-only attempt under `attempt1/`; the final disassembly/verifier run is the `47/47 PASS` result.

## What is actually proven

### F1 — CLV 1800 is a stored request, not a measured clock

Exact HII/static bytes establish `AmdSetup+0x316 = 0x24`, and the exact CLV IFR option labels byte `0x24` as `1800MHz`. The native-menu result also maps:

- `+0x330 = 0x01` (`UclkDiv1M0 = Enabled`),
- `+0x36D = 0xFF` (`Memory P-state = Auto`),
- `+0x6A3 = 0x0F` (`FCLK_DPM = Auto`),
- `+0x703 = 0x01` (DF override control Manual),
- `+0x704 = 1420` (`8C 05` LE).

These are stored bytes in the pinned donor and static menu definitions. They do not prove current board NVRAM, training, applied rate, physical clock, or synchronization. The latest preserved W11 snapshot is a separate saved image and does not substitute for a fresh current readback.

### F2 — The first UCLK path is byte-preserving

The exact `CbsBasePei` body (SHA-256 `6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77`) loads `AmdSetup+0x330` at RVA `0x9CE4`, writes it unchanged to the record value at `0x9CEA`, and emits record `0x1204`. The callback path `0x36C0 -> 0x36F0` builds an `$INV` buffer; the bounded dispatcher window has no ratio arithmetic or direct clock-register write. The synthetic `00/01/7F` model demonstrates copy preservation in this exact static sequence only. It does **not** decode `Enabled=1` as `/1`, and it does not identify the eventual consumer.

The provider-object report establishes only that the selected `AmdFabricAriPei 0x266F -> 0x25D3 -> [ECX+0x34]` edge is generic PEI/HOB infrastructure and contains no token `0x1204` or clock operand. Its negative result does not show that the record cannot be consumed by another path.

### F3 — DF fields have serializer evidence, not an actuator

`AmdFabricAriPei` exact bytes serialize `0x1373` from `AmdSetup+0x703` (`RVA 0x11C66`, u8) and `0x1374` from `AmdSetup+0x704` (`RVA 0x11C98`, u16 LE), with the CBS registration descriptor at module offset `0x16A78`. The selected corpus scan finds no direct immediate-query patterns for these IDs in the 233 extracted UEFI modules. That is a bounded static absence for the tested encodings; it is not a final-reader or actuator map.

### F4 — ABL1 has a static override shape, but no Setup-field join

Fresh exact ABL1 bytes show branch tests on unknown stack slots `[SP+0x164]` and `[SP+0x174]`. One route gathers channel `+0x20` words, substitutes `0x7D1` for zero entries, reduces to a minimum, then writes context `+0x2BC` and all channel `+0x20`; another route invokes opaque helpers; a `<=1` route avoids the bounded all-channel writeback. The report explicitly leaves slot producers, helper semantics, `$INV`/APOB/APCB/AmdSetup joins, units, and runtime priority unresolved. This is useful precedence evidence, not proof of memory-clock application or synchronization.

### F5 — No independent physical-clock route survived review

The retained driver aliases FCLK/MCLK/UCLK to one `MemclkFrequency` source. The SMU queries tested return software committed state or a P-state count. The new ATOM candidate delegates to an untraced command table and stores boot values; exact CLV has no standard `55AA`/`+0x48` ATOM header binding this route. No domain-mapped MCLK/UCLK/FCLK counters, divider/crossing status, common unit conversion, or read-only target-board path is established.

## Adversarial correction to the integration claim

The prior integration sentence “zero direct reader queries exist across the UEFI corpus; downstream consumption terminates into the ABL1/APOB/SMU handoff” is too strong and is corrected here to:

> **Bounded result:** the selected extracted UEFI corpus contains zero occurrences of the tested direct-immediate query patterns for `0x1373`/`0x1374`; the serializer records are therefore not shown to have a direct reader in those encodings. The downstream consumer, if any, and the path from the NVTB/`$INV` buffer into ABL1/APOB/SMU remain unresolved.

The verifier itself hard-codes only three byte patterns per ID (`push`, `mov ecx`, `mov edi`) and scans extracted `.pe`, `.te`, and `body.bin` files. It does not exclude computed IDs, table-indexed readers, callback/registration paths, HOB/DMA transfer, pointer-based parsing, decompressed/closed payload consumers outside the selected extract, or runtime behavior. Therefore its `PASS` is an integrity/result-of-predicate status, not proof of consumer absence. The same discipline applies to the UCLK provider/HOB negative: no token in one generic edge does not prove no elsewhere.

A related phrasing correction applies to the clock-team registry and DF report: “handoff terminates into ABL1/APOB/SMU” is an unresolved destination hypothesis, not an observed dataflow edge. No report should call this handoff established without a byte-backed pointer/descriptor/source join.

## Claim matrix / G9 status

| Claim                                          | Status                             | Evidence and missing check                                                             |
| ---------------------------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------- |
| Exact CLV donor identity and size              | **PASS (observed-bytes)**          | Hash/size above; reopened directly.                                                    |
| `0x24` is the exact CLV `1800MHz` HII option   | **PASS (observed-bytes + static)** | Native-menu `25/25`; no physical-rate claim.                                           |
| `UclkDiv1M0=1` means `/1` or sync              | **FAIL as stated**                 | Byte-preserving serializer + enum label only; divider/crossing semantics absent.       |
| `0x1204`/`0x1373`/`0x1374` have no consumer    | **UNPROVEN**                       | Direct-immediate scans are bounded; computed/indirect/HOB/DMA/closed paths unsearched. |
| Serialized clock records reach ABL1/APOB/SMU   | **UNPROVEN**                       | No pointer/descriptor/source join; retain as a hypothesis.                             |
| ABL1 branch affects native Setup clock fields  | **UNPROVEN**                       | Stack-slot producers and field joins not recovered.                                    |
| FCLK/MCLK/UCLK physical values are independent | **FAIL as host-metric claim**      | Driver alias and software-state query evidence falsify independence of those sources.  |
| Physical `MCLK=UCLK=FCLK=1:1:1`                | **UNRUN / unsupported**            | No independent domain-mapped measurement or crossing/divider readback.                 |
| 1800 MHz applied/trained/stable on target      | **UNRUN**                          | No current board capture, training trace, or independent rate measurement.             |
| SoC `1.15 V` safe/applied                      | **FAIL / unsupported**             | No board-mapped field/unit/rail readback or safety rating; outside this clock review.  |
| Candidate/hardware acceptance/rollback         | **UNRUN**                          | No candidate or board action occurred in this review.                                  |

## Contradictions and limits retained

1. Exact DF help text requires `FCLK > UCLK` and Memory P-state disabled, which conflicts with treating equal numeric targets as a proven `1:1:1` profile. The `UclkDiv1M0` label “Enabled” does not resolve this.
2. The native forms are statically writable and `SetVariable`-wired, but `0x7007` and `0x7009` have no package-local incoming `REF`; live AMITSE/external registration and browser invocation remain untested.
3. The ABL1 “minimum/writeback” result uses internal channel words and opaque stack-slot gates; it does not establish that `0x7D1` or any stored menu number is MHz.
4. The exact CLV ATOM header negative rejects only the standard header binding for the candidate API; it does not prove no undocumented/computed clock route exists.
5. Worker report/action histories contain earlier failed/renamed verifier attempts and path variants; final machine results/manifests listed above are the authoritative re-opened artifacts. A worker `PASS` is not hardware acceptance.

## Recommendation

1. **Do not flash, apply voltage, or label any equal-number profile synchronized.** Preserve `AmdSetup+0x316=0x24` as the static CLV context.
2. **Next executable offline step:** follow the exact ABL1 caller of `0x95FC` and recover the producer of one of `[SP+0x164]`, `[SP+0x174]`, or `context+0x3C4/+0x74`, while independently searching for the serialized Memory Clock token `0x11ED`/its typed record. Acceptance is one byte-backed source/descriptor join with unit/ordering classification; a negative stops at that first unresolved caller boundary. Do not repeat the completed direct serializer scans.
3. **Only after that boundary is resolved**, map `MemoryClockSpeed`, `UclkDiv1M0`, Memory P-state, FCLK_DPM, and DF override to one actual UMC/DF divider/training/crossing path. Then, separately, design a read-only board test requiring exact board/image/NVRAM identity, recovery/readback, independent physical clock observation, training/error screening, and rollback.

## Completion checks

- `PASS`: exact target re-opened; seven result JSONs and their source reports inspected; byte-backed findings and bounded negatives reproduced from actual files; at least one integration assumption challenged and corrected; no firmware/hardware/network write.
- `PASS`: owned action log records intent before this report and an evidence ledger with hashes is available in the report and log.
- `INCONCLUSIVE/UNRUN`: final closed consumer path, unit/rate mapping, physical clocks, sync crossing, training, voltage, performance, board acceptance, and rollback.

Owned artifacts:

- Report: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-clock-independent-review.md`
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-21-clock-independent-review.md`

## Follow-up correction: memory policy and APOB/ABL handoff remain separate

### Accepted for any project guide or status summary

1. **Native CLV setting (observed/static):** exact donor `AmdSetup+0x316=0x24`, whose exact CLV IFR option label is `1800MHz`. The two selected PEI serializers preserve that byte into `$INV 0x11ED`. This is a stored request / static label, not an applied physical MCLK measurement.
2. **ABL1 policy mapping (observed/static, separate namespace):** exact ABL1 APCB/CBS getter uses token `7` at timepoint `2` with selector `0x0F` / group `0x1707`; a separate TBB path maps enum `0x24` to integer `0x708` (1800). Nearby ABL strings label memory-clock policy values in MHz. This supports an MHz-named policy integer, not proof that token `7` is native `$INV 0x11ED`, that the `AmdSetup` byte feeds it, or that the integer is a physical/GDDR6 transfer rate.
3. **APOB/PPI chain (observed/static, separate path):** `AmdMemAm4Pei` issues service pointer `0x09E3B14C`, message `0x61`, argument `0xFF`; its PPI descriptor and `AmdMemoryHobInfoPeim` `LocatePpi` use the same GUID `e54e6e84-020b-4081-8156-37e9c62c1ed6`. The consumer reads PPI fields `+0x28/+0x2C/+0x30/+0x31/+0x40` and calls `InstallPeiMemory`. This is a static interface join; it does not show PPI invocation, field provenance, or linkage to `$INV 0x11ED`.

### Disallowed conclusions

- Do **not** state that the full native menu -> `$INV 0x11ED` -> APOB/PPI -> ABL1 policy chain is proven. The reports explicitly identify the first missing boundary as the input population for the APOB service/PPI; ABL1's token-7 provider namespace remains separate.
- Do **not** equate ABL1 token `7`, raw APCB CBSG byte value `7`, native `$INV` token `0x11ED`, and menu enum `0x24` without a byte-backed source/descriptor/dataflow join. Matching `0x24` and the integer `1800` is numeric agreement only.
- Do **not** claim `AmdMemoryHobInfoPeim` consumes `0x11ED`, that `InstallPeiMemory` confirms the selected memory rate/training, or that ABL1 service item `0x17` is a clock actuator. Those edges are not established here.
- Do **not** infer physical MCLK=1800 MHz, GDDR6 data/edge-rate, UCLK/FCLK equality, synchronization, stable performance, or hardware acceptance.

### Decisive source-byte check: corrected APOB pointer

I independently reopened the exact extracted `AmdMemAm4Pei` body from the pinned CLV census. Module SHA-256 is `1ef4e7b944672a9a48b6fcb16c4d35cb6d23bb8306429dc3eb10ee1d0c7bb5f8`, image base `0x09E39E20`. At module RVA `0x08A0` (section-translated raw offset `0x0708`), bytes are `68 4C B1 E3 09`; x86 `push imm32` little-endian decodes to `0x09E3B14C`. Verified source fact: service-pointer-immediate=0x09E3B14C; the report/result spelling is correct. Root's `0x9E3B14` drops the final `C` and is not the observed immediate.

The same source window shows a constant service setup: the full pointer is pushed, followed by fixed `0xFF`/`0x61` arguments at RVA `0x08CA/0x08CF`, then a call to `0x0CD9` at RVA `0x08D1`. This byte check corrects the pointer and confirms the bounded call-site constants; it does not resolve the opaque gateway or exclude an indirect/populated-input path upstream.

### Correction to next-step wording

The previous memo's generic “trace `$INV 0x11ED` into ABL1/APOB” wording is too eager if read as though the bridge already exists. The concrete next offline test is to trace the provider/data source behind `AmdMemAm4Pei`'s exact `0x09E3B14C / 0x61 / 0xFF` request and the matching PPI field population, looking for a byte-backed `$INV 0x11ED` input. Stop at that gateway/PPI producer boundary if no edge is recovered. Keep ABL1 token `7` as an independent path until its producer is separately joined. No guide was edited by this reviewer.

### Claim status

`PASS (static)`: exact CLV menu label/request byte; `$INV 0x11ED` serializer; ABL1 token-7 enum-to-policy map; APOB PPI GUID/interface join; pointer immediate `0x09E3B14C`.
`UNPROVEN`: `$INV 0x11ED` -> APOB service/PPI fields; native Setup -> ABL1 token 7; ABL1/service item -> PLL/training/SMU actuator.
`UNRUN`: PPI/APOB/ABL1/SMU execution, physical clock/readback, training, performance, hardware acceptance and rollback.

Evidence hashes reopened for this correction: memory report `4e318813e16035216aa48303d292422ca43d113ee91807fc97b8a61ee0ced33b`; APOB report `f8c8d1610ae89a933b3060b3917ec57a2b1f69d7c6fd4f3620baec2de6f991db`; APOB machine result `36abcbcb636b330457c00ab59e74a17b8ae5976c774b80f9c29f3912918da2a6`; exact service-pointer source module `1ef4e7b944672a9a48b6fcb16c4d35cb6d23bb8306429dc3eb10ee1d0c7bb5f8`; exact ROM `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
