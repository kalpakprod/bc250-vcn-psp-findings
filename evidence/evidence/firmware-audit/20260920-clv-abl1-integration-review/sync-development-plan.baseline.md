# Plain clv BIOS default synchronization development plan

## Scope and planning anchor
2026-09-20. Deliver a reproducible BIOS 5.00 clv candidate that requests and, upon separate hardware acceptance, actually applies MCLK=UCLK=FCLK by default, reducing memory latency. Exact frequency is not yet selected. Do not substitute equal displayed values for synchronization. Base SHA256: ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8. CPU, timings, VCN, core count and graphics remain unchanged initially. SoC 1.15 V is the operator ceiling, not a validated safe rating; no automatic voltage increase or physical modification.

## Evidence and corrected priority
Source: /home/OWNER/Downloads/AyuGram Desktop/ChatExport_2026-09-20. All 208 message texts reviewed; retain technical message IDs only. This is historical participant evidence, not a fresh target-board experiment.
- IDs771986,772010–772015: initial report of little/no DF effect and failed higher settings.
- IDs772088–772109: profiles01/03 reportedly booted without the expected latency improvement. Photo7 shows 141.7 ns and 66611 MB/s read. Boot is not proof of synchronization; CPU-X output is not independent clock validation.
- Photo9 (ID772115) shows UMC Common Options / I Accept / Memory Clock Speed Auto. It establishes historical menu access on that photographed firmware, not exact-clv identity or successful setting application.
- ID772183: reported DF/memory operating ranges did not overlap as expected; lowering memory also prevented initialization. Treat training feasibility as a first-class constraint.
- IDs772237–772239 supersede the blanket historical assertion that DF control has no effect: 1400 reportedly stable, 1500 initializes but fails OS boot, performance falls at900 and rises at1400. These are requested settings, not independently measured clocks.
- IDs772341–772344: physical feedback modification and reported SoC above1.2 V associated with requested DF1800. Photo16 shows131.4 ns and77619 MB/s read. Neither proves1:1:1; this hardware configuration violates the current project's voltage ceiling and must not be copied as a recipe.
- IDs772050/772014 contain unverified clock/domain and expected-performance claims; do not adopt their numeric mapping or promise desktop latency.
- Five BIN attachments checked against clv. Duplicate dfg_idx08_down_20_ckfix files are identical; only3 bytes differ atAB1014/AB112E/AB116A. Three SYNC-named images differ by3018–3020 bytes and require structural attribution, not name-based reuse. Exact hashes/ranges: chat-attachment-audit.json.
- ZIP README explicitly labels DFG token semantics unknown and checksum unverified. Its recommendation to infer training semantics from a failed boot is insufficient. RAR contents and16 remaining photographs not inspected; full archive audit is phase1.

## Connected logic and existing tools
Reuse scripts/build_clv_oc_candidate.py, scripts/nvar_audit.py, tests/test_clv_oc_builder.py; current builder supports only a stored df1400 request. Reuse exact menu-verify.py, e1_ifr_dump.py and existing233-module census. Native Setup fields316/330/6A3/703/704 and tokens11ED/1204/1331/1373/1374 are starting points. Native UI says FCLK>UCLK and Memory P-state disabled; UclkDiv1M0 is described relative to FCLK. Resolve these semantics, not assume desktop DDR behavior. Existing Ghidra projects and coefficient traces are references; no new generic PSP/mailbox search.

## Use cases
U1 fresh default initialization; U2 Load Optimized Defaults; U3 normal saved-settings boot; U4 cold boot and warm restart; U5 recovery to pristine clv after failure. Existing user NVRAM must not silently defeat or be destructively overwritten by the default profile. Design explicit precedence/migration behavior.

## Implementation checklist and gates
### 1. Reconcile historical candidates (offline)
[x] Inventory ZIP/RAR members without executing contents; identify all ROM baselines by hash, compare archived and loose duplicates.
[x] Parse differences into NVRAM, defaults, APCB, executable and checksum regions using existing tools. Explain every change in profiles01/02/03 and later revisions.
[x] Correlate message IDs, photo evidence and exact binary identity; retain ambiguous flash-to-file associations.
Deliverable: candidate comparison table and changed-region report. Exit: know what previous failed attempts actually changed. Do not rebuild them unchanged.

### 2. Resolve native actuation and frequency definitions (offline)
[ ] Trace fields316/330/6A3/703/704 through existing serializers to the consuming divider/clock/training configuration; investigate gating, override precedence and discarded values.
[ ] Establish MCLK/UCLK/FCLK units and GDDR6 clock/rate conversions, and whether equal frequency also selects a synchronous crossing mode.
[ ] Identify Memory P-state control and reconcile FCLK>UCLK guidance with UclkDiv1M0. Distinguish forbidden combinations, conditional modes and generic help text.
[ ] Use existing Cutter/Ghidra disassembly for bounded consumer branches; preserve exact instruction/byte tests. Design read-only hardware observations in parallel, but do not require their execution before offline development.
Deliverable: field -> consumer -> register/coefficient -> domain/units matrix, accepted ranges and remaining unknowns. Exit: a defensible candidate configuration, not just equal UI labels.

### 3. Select minimal route and defaults (offline)
Decision A: native controls reach the correct actuator: patch the authoritative defaults and necessary menu access only.
Decision B: native values are overwritten/ignored: patch the specific initialization/override path, before training if required; do not insert a late DXE write into a pre-training dependency.
Decision C: a proven protection boundary prevents the required operation: document the boundary and review alternatives before any exploit design. Missing consumers do not establish this case.
[ ] Locate defaults initializer, IFR defaults, persistent NVRAM precedence and fallback. Test fresh store, existing store and Load Defaults independently.
[ ] Select frequency only after phase2 range intersection. Keep voltage, CPU and timings unchanged initially. If no supported intersection exists under constraints, report it rather than silently exceed1.15 V or substitute1:2.
Deliverable: exact patch specification with offsets/symbols, units, single hypothesis, failure path and rollback.

### 4. Build reversible candidate (offline)
[ ] Extend existing builder rather than fork a new framework. Pin source hash; reject wrong input, overlapping outputs and unsupported combinations.
[ ] Produce MODIFIED_FILE, reconstructing DIFF_FILE, VERIFICATION.txt and executable self-contained ROLLBACK.sh.
[ ] Same-input baseline/candidate/rollback inspection; restored hash must equal pristine clv. Preserve originals and signed regions unless separately justified/reviewed.
[ ] Validate FV/FFS/APCB/NVRAM structures and relevant checksums, expected changes only, default-selection paths and malformed inputs. Use emulation where applicable, without claiming board-clock emulation.
[ ] Independent review of actual patch/evidence/failure path before hardware candidate approval.
Deliverable: hash-pinned experimental ROM plus complete reproducible transaction. Label offline-verified, not hardware-accepted.

### 5. Separate hardware acceptance
Prerequisites: exact board/memory identity, full verified recovery dump and recovery method, approval for exact candidate/target, recorded procedure and stop conditions. No assumption that historical modified board equals current target.
Matrix: stock control; minimal native/default candidate; only if justified a targeted consumer-path candidate. One causal configuration change per comparison, all unrelated settings fixed. Do not add voltage and timings to rescue an ambiguous clock result.
[ ] Verify programmed readback; test cold boot, warm restart and Load Defaults, at least3 repetitions each.
[ ] Independently identify actual clock/divider state; aliased Linux FCLK/UCLK metrics, cached requests and QueryDfPstate do not suffice. Distinguish frequencies from true synchronous mode.
[ ] Compare latency and throughput with same OS, benchmark/version, CPU configuration, thermal conditions and workload; alternate stock/candidate, at least5 runs each, report medians and spread.
Proposed performance gate: median latency reduction >=5% and greater than baseline variation; flag throughput regression >5%. Thresholds are project criteria, not promised outcomes. Synchronization and performance acceptance are separate.
[ ] Predefined memory/CPU/mixed-load suite (minimum1h each as initial screening), zero detected errors, resets or artifacts; any failure stops escalation and triggers recorded recovery. This screening is not a lifetime stability guarantee.
Stop on no POST, training loop, OS failure, errors, unexpected voltage or limit violation. Do not try higher clocks/voltage automatically.

### 6. Release decision
Publish only with explicit approval. Final package includes exact source/output identities, build command, full diff, checks, reviewed limits, recovery image/procedure and hardware ledger. If only offline gates pass, deliver an experimental candidate explicitly lacking hardware acceptance. If synchronization cannot be independently established, do not label the image1:1:1 even if latency improves.

## Phase-2 checkpoint — PARTIAL, not complete (2026-09-20)

The current offline evidence narrows the route but does not satisfy the phase-2 exit condition or authorize a candidate:

- **Persisted request bytes (observed, not clocks):** on pinned clv, `AmdSetup` body base `0x4CF` contains `+0x316=0x24` (`36`, IFR label `1800MHz`), `+0x330=0x01` (`Enabled`), `+0x6A3=0x0F` (`Auto`), `+0x703=0x01` (`Manual`), and `+0x704=0x058C` (`1420`).
- **Missing-variable fallback (static):** `CbsSetupDxe`/`CbsBasePei` helpers write `0xFF`, `0xFF`, `0x0F`, `0xFF`, and `0x03E8` (`1000`) at those offsets when their read-failure paths are taken. This does not describe a successful existing-variable path.
- **Declared exact-clv IFR defaults (static):** enumerated questions declare `Auto` defaults `0xFF`, `0xFF`, `0x0F`, `0xFF` for `+0x316`, `+0x330`, `+0x6A3`, `+0x703`. Numeric `+0x704` has bounds `0..2000` and no option/default opcode in the retained package. The later callback audit statically maps action `EFI_BROWSER_ACTION_DEFAULT_STANDARD (0x1000)` at `CbsSetupDxe` RVA `0x950` to helper `0x2FE4`, which writes `+0x704=1000`; this is only a code-path finding. In the checked ABI window, `Action` is in `RDX`, `QuestionId` in `R8W`; actions `3`/`4` return early, action `2` takes the retrieve path, and action `0x1000` reaches `0x2FE4` without a visible `QuestionId` equality gate. The `+0x704` IFR question itself has no CALLBACK flag. Callback invocation, browser dispatch, and live NVRAM readback remain unrun.
- **Serializer/consumer boundary (static + host-tested):** the fields serialize to `$INV` tokens `0x11ED`, `0x1204`, `0x1331`, `0x1373`, `0x1374` with one-byte/one-byte/one-byte/one-byte/two-byte encodings. The exact `AmdFabricAriPei` generic-reader call inventory requests only `0x10FF` and `0x1104`, not `0x1204`. Complete containing-function recovery for `AmdNbioGfxARIPei` (`0x4E20..0x12FA3`) and `AmdNbioSmuV10Pei` (`0x5770..0x138F3`) finds only two size-helper calls per builder and zero direct calls after the token body; each wrapper calls its builder and returns immediately. Exact module data also contains wildcard/event `0xFFFFFFFF/0xFFFFFFFE` callback descriptors whose provider pointers resolve to those wrappers. This establishes a static registration candidate, not an installed/invoked dispatcher: the actual indirect caller remains unresolved. Indirect/computed/callback-table/HOB/DMA/runtime paths and the final actuator remain open.
- **Builder qualification:** the existing builder is a `df1400` stored-value request only; it changes `+0x704` (`1420 -> 1400`, virtual byte `0xBD3`) and leaves MCLK/UCLK/FCLK fields and defaults untouched. It is not a synchronization candidate and cannot establish `Load Defaults`, migration precedence, physical clock application, training, or `MCLK=UCLK=FCLK`.
- **Configuration-domain matrix (static):** exact-clv UI labels advertise Memory Clock Speed `125..2000MHz`, while DF Clock Override accepts numeric `0..2000`; all displayed Memory labels fall inside that numeric interval. This is only numerical UI overlap: enum codes differ from labels, UclkDiv1M0 `Enabled` has no decoded ratio, and no shared unit/domain, training range, or synchronous-crossing selection is established. The current seven-field cursor-lifetime map is `+0x316->0x11ED`, `+0x330->0x1204`, `+0x368->0x1237`, `+0x36D->0x123C`, `+0x6A3->0x1331`, `+0x703->0x1373`, `+0x704->0x1374`; prior adjacent-ID mappings are superseded. Their downstream consumers/training semantics remain unresolved. The minimum offline semantic gate remains the byte-backed field-to-consumer/actuator and unit/rate map, including Memory-P-state/training relation and migration-aware precedence; live telemetry remains a hardware gate.
- **Frequency/unit discrimination (static + host-tested):** retained `cyan_skillfish_ppt.c` maps FCLK/MCLK/UCLK exports through `MemclkFrequency`, while Robin-5 clock queries return internal committed state or a P-state count. This demonstrates software aliasing/state, not independent physical clocks, GDDR6 rate conversion, or synchronous crossing. The smallest offline check passed `11/11`; the field/token-to-consumer/unit/rate gate remains open.

These findings are recorded as **PARTIAL** only. Keep all phase-2 and phase-3 checklist boxes unchecked until the remaining gates below are met; do not label any image `1:1:1` from equal labels or stored requests.

### Concrete remaining acceptance gates before phase-2 completion or hardware candidate approval

1. **Offline default-semantics gate (does not block offline candidate development):** retain the exact static separation between existing-variable precedence, missing-variable fallback, IFR-declared defaults, and the clv callback-bearing `FCLK_DPM` standard-default side effect path. The current callback result is static source evidence only; upstream EDK II browser references identify dispatch semantics, not execution of this exact firmware. **Hardware-acceptance subgate:** before hardware acceptance or release, execute `Load Optimized Defaults`/reset and obtain post-reset NVRAM readback for all five fields, including numeric `+0x704`.
2. **Consumer/requester gate (still open after bounded direct and registration candidates):** complete selected builders/wrappers show no direct post-token/post-builder call, and wildcard/event descriptor data statically points to each wrapper, but the installed/invoked registration dispatcher and any computed/HOB/DMA/runtime requester of token `0x1204` remain unresolved; generic reader reachability, descriptor presence, and direct-call negatives are insufficient.
3. **Semantic actuator gate:** map each field/token to the actual divider/clock/training consumer, units, valid shared range, Memory-P-state interaction, and synchronous-crossing selection. A one-byte raw copy or two-byte token width is not a domain or frequency proof.
4. **Offline candidate gate:** after the static consumer/semantic work and explicit default unknowns are recorded, choose one supported frequency intersection and specify migration/invalidation precedence for existing `AmdSetup`; the live/default readback subgate is not a prerequisite for generating an offline experimental artifact, but its unrun status must remain explicit. Keep voltage, CPU, timings, and unrelated fields unchanged; then build the required reversible four-role transaction and obtain independent review. Hardware approval remains gated separately by gate 1's live readback and gate 5.
5. **Hardware gate:** separately verify recovery, exact board/memory identity, programmed readback, cold/warm/Load-Defaults behavior, independent clock/divider observation, performance, and error-free screening. No flash or release approval follows from this offline checkpoint.

Research role paths reopened for this checkpoint:
- `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-sync-stage2-independent-baseline-review.md`
- `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-sync-stage2-defaults.md`
- `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-sync-stage2-consumer.md`
- `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-sync-stage2-consumer-followup.md`
- `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-sync-stage2-function-boundary.md`
- `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-sync-stage2-wrapper-dispatch.md`
- `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-sync-configuration-domain-matrix.md`
- `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-sync-stage2-memory-pstate.md`
- `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-sync-stage2-memory-pstate-discrimination.md`
- `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-sync-stage2-token-matrix.md`
- `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-sync-frequency-unit-discrimination.md`
- `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-sync-extraction-coverage.md`
- `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-sync-stage2-record-lifetime-all-fields.md`
- `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-sync-stage2-uclk-semantics.md`

## Open questions
Blocking candidate semantics: meaning of UclkDiv1M0; genuine MCLK/UCLK/FCLK mapping; valid shared frequency/training range; authoritative defaults/override path; synchronous-crossing selection.
Blocking hardware acceptance only: exact current target, physical modifications, voltage measurement/rail identity, recovery readiness and independent clock observation.
Non-blocking offline work: unavailable live board telemetry, historical archive-to-flash ambiguity (retain uncertainty).

## Decision log
D1 Prioritize native actuation/default precedence, not menu existence alone or an exploit-first approach.
D2 Historical late DF performance report corrects the initial no-effect report; no fresh hardware proof is inferred.
D3 No promised frequency, latency or safe voltage from chat/model text. Physical voltage modification is outside scope.
D4 Next executable work: phase1 structural reconciliation of the three attached SYNC ROMs and their archived revisions against pinned clv, then carry only unexplained relevant differences into phase2.
D5 This turn creates a plan, not a firmware candidate. BASELINE ROM unchanged; MODIFIED/ROLLBACK firmware behavior unrun.
D6 Phase-2 is **PARTIAL**, not complete. A stored-request-only build is insufficient because the existing `AmdSetup` variable wins on the successful `GetVariable` path, four IFR defaults are only declared static values, numeric `+0x704` requires the callback/helper distinction, and the bounded consumer traces have not reached a proven divider/clock/training actuator. Offline candidate development may proceed only as explicitly experimental static work once the offline consumer/semantic gates are met; live/default readback is not a prerequisite for generating that artifact. Hardware acceptance/release still requires the live/default-path readback, token-`0x1204` requester classification, semantic actuator/domain mapping, migration-aware candidate specification and independent review, then separate hardware acceptance. No stored request may be labelled `1:1:1` or hardware-applied.

## Final current checkpoint integration — still PARTIAL (2026-09-20)

Independent checkpoint integration reopened the pinned clv (`ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`) and the current phase-2 evidence. Owned inventory/review: `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-psp-abl-provenance.md` (SHA-256 `2b8cb2c85de39b57264e58e34aab7764b1295a96353e7ace77dd092df8559456`); machine inventory `evidence/firmware-audit/20260920-clv-psp-abl-provenance/clv-psp-abl-inventory.json` (`7fab47054f8548c2bf5812ddc1ee649ec42a22184b4107fef75e210649c29f94`); independent checkpoint result `evidence/firmware-audit/20260920-clv-psp-abl-provenance/stage2-checkpoint-review-result.json` (`32dbcc6353ff0b07c87942558736b3a789d8a259e332f1fa9a6bee06cfd813a1`); action log `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-psp-abl-provenance.md`.

Exact PSP/ABL boundary is now inventory-backed: five bootloader payloads `ABL0..ABL4` (PSP types `0x30..0x34`) at `0x99F700`, `0x99FD00`, `0x9ABE00`, `0x9AFF00`, and `0x9BA200`; all are `22.4.6.0`, compressed 32-bit ARM/Thumb payloads, and each exactly matches the preserved Robin-5 container of the same ID. ABL1/ABL3/ABL4 historical decompilation is version-label aligned, but source-text-to-binary identity remains UNPROVEN. The 233 executable PE32/TE census does not cover these non-x86 PSP/ABL payloads.

The following four current role paths were reopened with their evidence manifests:
- `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-sync-stage2-cbs-ppi-lifecycle.md`
- `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-sync-stage2-memclk-consumer.md`
- `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-sync-stage2-cbs-dispatch-selection.md`
- `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-sync-stage2-cbs-caller-chain.md`

Qualified findings: CBS PPI/Notify registration and wildcard/event callback dispatch are static ownership only; `AmdMemAm4Pei` uses `EFI_PEI_SERVICES**` (`ESI -> [ESI]` service table), calls `AllocatePool`/`InstallPpi`, and has no bounded `InstallPeiMemory` call, so this is a PPI/data handoff and not a training proof. The Fabric chain proves local pointer identity from the second `0x3710` buffer argument to the `0x1DFC` first-reader use; the initial request is a NULL-buffer size pass, and `HOB+0x28` is not promoted. The final contiguous serializer map retains FCLK `+0x6A3 -> 0x1331`; stale `0x1332` wording is superseded.

Phase 2 remains **PARTIAL**. Consumer/requester, AGESA/PSP/APOB training actuator, runtime invocation, units, physical clocks, synchronization, candidate, and hardware acceptance remain unresolved/unrun. No plan gate is marked complete by this integration.

## Config-source provenance boundary — APCB versus `$INV` versus APOB/PPI (2026-09-20)

Fresh exact-clv parser execution and a 32-check byte audit establish a bounded source/interface distinction. Evidence report: `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-apcb-abl-apob-interface.md` (SHA-256 `0c5337d9c3e4559079b502ee69ce2a9e3041a0cee62693401ea558d9b98fe81a`); machine result `evidence/firmware-audit/20260920-clv-apcb-abl-apob-interface/apcb-abl-apob-interface-result.json` (SHA-256 `73ea48688e988222a6046f5f1a38cc98b33a029566a4c37d69a04dcdd3efd42f`); action log `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-apcb-abl-apob-interface.md`.

- APCB is an observed flash input: `0xAB1000`, size `2972`, checksum `0xC0`, DFG words `0x001FFF00` at `+0x130/+0x16C`. BHD type `0x61` APOB entry is size `0`; type `0x63` APOB NV copy is 8192 B at `0xAB3000`.
- Persisted `AmdSetup+0x316` is serialized by `CbsBasePei` into `$INV` token `0x11ED` (`0x9837/0x9857/0x985D`).
- `AmdMemAm4Pei` requests a service using `0x9E3B14C`, message `0x61`, argument `0xFF`, then validates returned `APOB`, `$PSP`, and `$BHD` headers. `AmdMemoryHobInfoPeim` obtains a PPI, reads fields `+0x28/+0x2C/+0x30/+0x31/+0x40`, and calls `InstallPeiMemory` at `0x299`.
- No direct `Setup+0x316` or `$INV 0x11ED` read appears in the bounded memory-HOB consumer. This is a qualified provenance boundary relevant to persisted settings being ignored, not proof that `$INV` cannot feed APOB indirectly.

Phase 2 remains **PARTIAL**. APCB-to-APOB merge, PPI identity/provider, runtime precedence, memory-training actuator, clocks, synchronization, and hardware acceptance remain unresolved/unrun. Worker review retained: defaults report establishes static `GetVariable` precedence; exact ABL memory report falsifies direct historical source-address anchors; CCX reader report is a CPU-MS​​R branch and not a memory/DF consumer.

## Final Fabric reader/HOB slot review — bounded direct branch only (2026-09-20)

Independent review report: `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-fabric-reader-review.md` (SHA-256 `ae693a85ffa0522f203951dc8e6c5e80a83d3f239d8a074ef2f2cbb90694d`); machine result `evidence/firmware-audit/20260920-clv-fabric-reader-review/fabric-hob-review-result.json` (SHA-256 `afa0188902717bb14aaa7278e4ad083174e2c69300dd9cb12f714b3525587aa0`; `32/32 PASS`).

The exact Fabric reader returns values into caller stack slots: token `0x10FF` is consumed by handler `0x1E8F` through `[esp+0x10]/[esp+0x14]`, token `0x1104` by `0x1F6D` through `[esp+0x8]/[esp+0xC]`; IDS events map `0x20000003 -> 0x1E8F` and `0x20000004 -> 0x1F6D`. No direct `WRMSR`, `in`, or `out` occurs in these complete slices. Transitive AGESA/IDS helper MMIO effects remain unknown; corrected targets `0x1331/0x1204/0x123C` are not consumed here.

`AmdMemoryHobInfoPeim` slot provenance is corrected/reopened: `0x269 ESI=EAX`, `0x26B EAX=[ESI]`, `0x299 call [EAX+0x44]`; the existing PEI services layout identifies `+0x44` as `InstallPeiMemory`. This confirms the PPI/APOB-to-permanent-memory output edge and does not identify training semantics. Phase 2 remains **PARTIAL**.

## Exact ABL1 memory-policy function review — structural match, caller still open (2026-09-20)

Independent review: `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl-memory-review.md` (SHA-256 `6c81802a3e6e4b0e52588642501534df02972862a67a1863277bd4dac20b4ea1`); machine result `evidence/firmware-audit/20260920-clv-abl-memory-review/abl1-memory-review-result.json` (SHA-256 `e06dba13765d30d1040f2fb6bfeec65120ef6d7aed3152683c587936c811fd23`; `20/20 PASS`).

Exact ABL1 payload hash `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a` independently decodes as Thumb-2 at `0x95FC`. Raw/dataflow checks show per-channel speed input `[r0+0x20]`, table store `+0x278`, channel count `[r4+0x3C4]+0x74`, lower-value reduction into `[r4+0x2BC]`, and selected halfword writeback to `[r0+0x20]`. This structurally corroborates a memory-speed policy/training function.

Boundary: no edge from `AmdSetup+0x316`/`$INV 0x11ED` to the ABL context, no unit/MHz conversion, UclkDiv1M0/FCLK relation, or synchronization proof. Caller/provider population, execution, training, physical clocks, and hardware acceptance remain unresolved. Phase 2 remains **PARTIAL**.

## ABL1 exact address/base and function-boundary correction (2026-09-20)

Independent continuation of the ABL1 review: `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl-memory-review.md` (current SHA-256 `42fa15939c387bab92a9f87dbe941dbba9480248ebd5e677ae521707d08ed3ac`); result `evidence/firmware-audit/20260920-clv-abl-memory-review/abl1-memory-review-result.json` (current SHA-256 `6006c96b182611609ed6998b5a3109d30f1cdb34342e3dfedbbf44b1fbed0eae`; `26/26 PASS`).

The exact ABL1 header records `load_address=0`, decompressed length `0x171A0`, and an ARM entry trampoline at payload `0x0` whose literal `0x0005E02D` is outside the decompressed payload. Thus `0x95FC` is retained as an exact payload-relative address, while physical/runtime relocation remains unknown. Independent Thumb decoding extends the function code from `0x95FC` through `0x98AB`: branch `0x9744 -> 0x984E`, continuation/backedge `0x98AA -> 0x978E`, and raw `AGESA MEM` string data begins at `0x98AC`. Observed register contract is `R0 -> [R0]` context (`R4`), caller-supplied `R5` outer structure, and per-channel row pointer `R1=R4+(index<<2)`.

This corrects the bounded worker window without promoting a physical address, caller/provider, memory domain, unit, synchronization, or hardware result. Phase 2 remains **PARTIAL**.

## ABL1 payload-relative entry and loop semantics qualification (2026-09-20)

Independent bounded report: `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl-address-loop-review.md` (SHA-256 `dcb541247c31a642c5d160058448be2dd20fd18f0a8d95f254ace5a17a8f5ea5`); machine result `evidence/firmware-audit/20260920-clv-abl-address-loop-review/abl1-address-loop-result.json` (SHA-256 `04a1086be29f6297461d90ecaa9865d5d74747371ccd2860510967dc94e87227`; `25/25 PASS`).

The exact ABL1 header records `load_address=0`, `rom_size=0xC020`, and decompressed length `0x171A0`; the ARM entry literal `0x0005E02D` lies outside the payload, so no physical runtime base is inferred. The matched function begins at payload `0x95FC`, continues through `0x98AB`, and reaches data at `0x98AC`. Its first loop is bounded by `[R5+0x4B]`, invokes `[R5+0x52C](../../../../references/DEPENDENCIES.md#unavailable-local-inputs)`, reads `[R5+0x0C]+0x20`, and writes `R4+(index<<2)+0x278`; later loops use `[[R4+0x3C4]+0x74`. Channel/MEMCLK/P-state strings are nomenclature context only; exact channel/P-state/domain semantics remain unresolved. Phase 2 remains **PARTIAL**.

## Exact ABL1 aggregate consumer/classifier qualification (2026-09-20)

Independent review report: `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl1-aggregate-review.md` (SHA-256 `63174c7232351044af528205893537b2b60cb8963ae6164d9317101257afab2e`); machine result `evidence/firmware-audit/20260920-clv-abl1-aggregate-review/abl1-aggregate-review-result.json` (SHA-256 `a0f69ced2b24295b109562278c1717ae256c4dfaa7007e3ac828032d92ac6973`; `14/14 PASS`).

Exact ABL1 downstream provenance is byte-backed: `0x75CC r0->r6`, `0x7E3E r0=[r6]`, `0x7E40 r6=[r0+0x2BC]`, selector `r0=[sp+0x20]` at `0x7E44`, aggregate `r1=r6` at `0x7E52`, then `BL 0x751C`. Classifier `0x751C` loops exactly 8 halfword entries from an external table pointer literal `0x0006DB04`; match/no-match converge, and the output is class `7` iff selector `r0==6`, else class `0`. The table pointer lies outside the exact payload, so values are unavailable and no index-range/error meaning is inferred.

This is a control-classifier consumer of aggregate `+0x2BC`, not a clock/unit/divider proof. Phase 2 remains **PARTIAL**.

## ABL1 relocation coherence — candidate `0x60000` falsified (2026-09-20)

Independent report: `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl-relocation-coherence.md` (SHA-256 `5d85b1cc75bac84573a0e0fff7ba80d21b721305cb0e096297138d86f8e347b3`); result `evidence/firmware-audit/20260920-clv-abl-relocation-coherence/abl1-relocation-coherence-result.json` (SHA-256 `1f9b84eba2a9b44d959eec7e52217ba800aca873f602cf31a1d273325b78ecfe`; `15/15 PASS`).

Three bounded anchors were checked: classifier literal `0x6DB04`, PC-relative string `0x8188 -> 0x820C`, and callable callback literal `0x67ABD` stored at `[r0+0x52C]`. Candidate base `0x60000` maps `0x6DB04 -> payload 0xDB04` (structured 8-halfword data) but maps callable `0x67ABD -> payload 0x7ABD` ASCII data (`lock Speed...`), falsifying it as a universal runtime base. Keep ABL addresses payload-relative; loader/runtime relocation remains unresolved. Phase 2 remains **PARTIAL**.

## ABL1 producer/callback conditional base `0x57100` review (2026-09-20)

Independent review: `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl-producer-base-review.md` (SHA-256 `120ac10f4a7b53895e8c71acc69be005e091ca53292b168a5d39163a3243402c`); machine result `evidence/firmware-audit/20260920-clv-abl-producer-base-review/abl1-producer-base-review-result.json` (SHA-256 `ecb7953571d3b008e76798718d216362bf819a4b0ffcb3dc52da58e23e2c483b`; `28/28 PASS`).

Four independent absolute pointer anchors map under conditional base `0x57100` to local Thumb code, including callback slot `+0x52C -> 0x109BC`. Producer path `0x7548 -> 0x75CC -> 0x7E00/0x7E30` writes the same per-channel `+0x20` field. Classifier literal `0x6DB04` maps conditionally to payload `0x16A04`; raw halfwords are `0x06D6,0x0532,0x0532,0x0352,0x00E1,0,0,0x00E1`.

This is static address coherence only; loader/runtime base, units, physical domain, clock, training, synchronization, and hardware acceptance remain unresolved. Phase 2 remains **PARTIAL**.

## Offline non-aliased clock evidence route — hardware counter prototype only (2026-09-20)

Independent route report: `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-independent-clock-counter-route.md` (SHA-256 `3dfa7e53ba044f9a9eae7104f3f94c37b4fc8a8f96618d00514250c0fef9bd3e`); machine result `evidence/firmware-audit/20260920-clv-independent-clock-counter-route/clock-counter-route-result.json` (SHA-256 `6eaa6a027118cc88a47d909bfcce39841eac29870561c8c05a82f3da3f43dda0`; `23/23 PASS`); action log `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-independent-clock-counter-route.md`.

Existing register headers prove a non-aliased hardware-counter mechanism for `GFXCLK/REFCLK`: counters `0x4C30..0x4C33`, control `0x4C34`, status `0x4C35`, separate run/reset/sample controls and independent valid bits. This is a route prototype only; the retained map does not bind it to exact CLV MCLK/UCLK/FCLK and no UMC/DF/UCLK counter/status mapping was recovered. A truthful synchronous-crossing mechanism still requires domain-specific counter pairs, a common reference, calibration, and a dedicated crossing/divider status selector. Software aliases and SMU committed-state queries remain insufficient. Phase 2 remains **PARTIAL**; no live/hardware result or MMIO write occurred.

## Exact-CLV counter applicability gate — static gap, Phase 2 remains PARTIAL (2026-09-20)

The external GFXCLK/REFCLK counter prototype was checked against the pinned CLV image, not adopted as an exact-board MCLK/UCLK/FCLK route. Evidence report: `docs/research/20260920-clv-independent-clock-counter-route.md`; exact applicability result: `evidence/firmware-audit/20260920-clv-independent-clock-counter-route/clock-counter-applicability-result.json`; verifier: `evidence/firmware-audit/20260920-clv-independent-clock-counter-route/clock_counter_applicability_verify.py`.

- Pinned CLV ROM SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Exact PSP type-0x08 PMFW: container `0x8FEE00`, size `0x40200`; extracted body `0x40100`, SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`.
- Direct little-endian scan of body literals `0x4C30..0x4C35`: no hits; retained SMU source has no direct `RLC_CLK_COUNT_GFXCLK` use.
- Machine result: `23/23 PASS`.

This is a bounded static applicability gap, not proof of absence of computed/indirect access and not a hardware result. No UMC/DF/UCLK counter/status mapping, synchronous-crossing selector, live read, MMIO write, or physical clock identity was established. Phase 2 remains **PARTIAL**; do not relabel GFXCLK as FCLK or infer MCLK=UCLK=FCLK.

## ABL1-to-IFR enum comparison — correlation with invalid/default gaps (2026-09-20)

Independent comparison: `docs/research/20260920-clv-abl1-ifr-enum-compare.md`; result `evidence/firmware-audit/20260920-clv-abl1-ifr-enum-compare/abl1-ifr-enum-compare-result.json`; verifier `evidence/firmware-audit/20260920-clv-abl1-ifr-enum-compare/abl1_ifr_enum_compare.py`; status `21/21 PASS`.

Exact ABL1 selector dispatch recognizes 20 codes and produces numeric values that match the numeric portions of all 20 corresponding exact CLV IFR `Memory Clock Speed` labels. However, exact IFR options `0x26=1900MHz`, `0x27=1950MHz`, and default `0xFF=Auto` are not accepted by the ABL TBB and take its invalid diagnostic path at `0x232A`. The result is therefore a strong bounded table correlation, not a proof of shared token namespace, units, runtime precedence, training, or physical clock semantics. Direct token `7` to `AmdSetup+0x316`/`$INV 0x11ED` remains unresolved; Phase 2 stays **PARTIAL**.

## ABL1 reader precedence clarification — remains PARTIAL (2026-09-20)

Append-only correction from exact reader bytes: the ABL1 descriptor arrays are ordered, but are not generic “try every key until any successful value” lists. Reader `0x1FB4` advances on helper status `R0=0`; for the earlier element, a nonzero helper status advances only when its returned byte is exactly `1`. A different returned byte is terminal failure (`R0=0` at `0x209A`). The final element is the typed value query; its width-specific sentinel checks also fail terminally without another index increment. Thus `[0x20,0x21..0x24]` and `[0x015F,0x0160]` encode a first gate/status position followed by a final typed-value position, with a not-found path that may skip the gate and query the final item. No semantic field name is assigned to those IDs.

Independent verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-fallback-status-xhigh/abl1_reader_fallback_status_verify.py` (`64/64 PASS`). Exact source remains observed bytes/static analysis only. The Fclk context consumer path stores a local default `0x4B0` into `context+0x78` and later compares that field against `0x3E8/0x4B0`; no unit or mapping to descriptor IDs `0x015F/0x0160` is demonstrated. The Fclk type-byte pointer local at `SP+0x0C` has no explicit initialization in the bounded handler before the reader call, so type-2 execution for that caller remains unproven. No physical clock, synchronization, candidate, or hardware acceptance result follows. Phase 2 stays **PARTIAL**; no plan gate or checkbox is promoted.

Open question, not a completion gate outcome: do context+0x78 comparisons against `0x3E8/0x4B0` consume values from Fclk token `0x015F/0x0160` in the same numeric/unit space, or is there a conversion/override boundary? Exact static bytes do not join them; do not equate IDs with thresholds or assign MHz.
