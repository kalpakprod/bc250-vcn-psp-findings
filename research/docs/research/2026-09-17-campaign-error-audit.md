# Recursive error audit: 4700S-base campaign and why no goal has landed yet

Date: 2026-09-17. Actor: root. Evidence class per entry: observed-bytes,
static-analysis, or operator-statement (recorded in logs). Scope: the
2026-09-16 4700S-base campaign (M0, M2full, M4, T1, M5, M6) plus the
inherited state it was built on. Read-only audit; no firmware action.

## 0. Verified end-state of the campaign (baseline for the audit)

| Rung | Image (SHA-256 prefix) | Content | Boot result |
|---|---|---|---|
| M0 | `bb2cf51d` | C0A-stock as-is | SILENT (no LED detail captured) |
| M2full | `72acddad` | C0A + verbatim native APCB | SILENT (assumed same class) |
| M4 | `856af24b` | M2full + native L1 BL graft | SILENT (assumed same class) |
| T1 | `b803cb4c` | pre-m0 native + 1-byte memclk pin | **BOOTED to Linux** (P0/P1 PASS); pin `0x7E5` reverted `0x23`->`0xFF` by firmware (P2 FAIL) |
| M5 | `3a80f9a8` | M4 + native PEI/NVRAM ranges | SILENT, LED static red, no LAN (oracle established here) |
| M6 | `3e75177e` | pre-m0 native + M4 PSP region `0x8E0000-0xAB1000` | SILENT, LED static red, no LAN (operator-confirmed 2026-09-17) |

Flash discipline was never broken: every write had VERIFIED + independent
readback hash match; recovery chain (stock `83c4e420`, pre-m0 `3f836668`)
intact; no brick. The board boots its native lineage (T1 proved it
post-campaign). The campaign verdict is sound:

- The C0A PSP region (PSP dir + bodies + BHD, incl. dummy L1 BL replaced by
  the native BL graft in M4/M5/M6) is the kill locus: with everything else
  native (M6), the board still halts with zero signs of life.
- The halt mechanism inside the PSP chain (ROM->BL->TOS/ABL->SMU) is
  UNRESOLVED; no observation channel existed to localize it.
- Track B (native base) is the only live base; T1 proved the native base
  still boots after all 4700S experiments.

## 1. Error register

### Level 0 — inherited conditions (not campaign errors, but context)

- **F1. VCN routes were already exhausted before the campaign.** The
  2026-09-12 verdict (five runtime experiments, D3-A flash disproof, D3-B2
  signature-fatality) closed every software-reachable route to the VCN
  power grant on this board. The 4700S campaign did not target any closed
  blocker; the C0A SMU (0.46.12.0) is OLDER than the native one (0.58.6.0),
  so the VCN equation on the 4700S base was strictly worse than on native.
  The campaign plan still listed VCN as stage P3 on that base.
- **F2. A G6 breaker breach was already on record** (D11R-D14: 4+ same-class
  DXE-time gasket failures; logged in the 2026-09-12 flash-ladder audit).
  The rule "after three same-class failures, change method class" existed
  and had demonstrably not been enforced once before.
- **F3. Worker claims entered the decision record without rationale.**
  Deep-research worker E7 ranked P5.00 first and concluded
  "reject 4700S/coreboot/OVMF" with the rationale never delivered (logged
  in the worker registry: "worker claims UNVERIFIED"). The operator
  contested an unsupported claim — correctly — and the contest was then
  settled empirically (5 flash cycles) instead of by delivering the missing
  evidence. Worker-process failure: a rank without reasons cannot be
  reviewed, only re-tested.

### Level 1 — strategy and base choice

- **S1. No goal-to-base mapping existed before the first flash (G3 gap).**
  The operator's goals (working VCN, working OC, FastBoot, TPM route, more
  modern BIOS) map almost entirely onto the native side: OC universe is
  native-only (CBS trio 71f/1193q; D22), VCN routes are board-side,
  FastBoot already present (E3), the host SMU governor already delivers
  memory OC (1500->2230 MHz proven). C0A uniquely contributes only the
  fTPM stack (5 modules, 327,696 B) — which was ranked LAST (T3/P4) in both
  ladders. No written memo stating "the 4700S base serves exactly one goal,
  and that goal is graftable onto the native base anyway" was produced
  before M0. G3 (state which existing route addresses the goal and why it
  is insufficient) would have produced exactly that memo.
- **S2. Risk ranking ignored boot execution order.** The M0 GO memo ranked
  residuals: (1) memory training, (2) VRM sequence, (3) SIO misdrive,
  (4) video, (5) PSP acceptance ("mildest possible case"). The PSP chain
  (SoC ROM -> L1 BL -> TOS/ABL/SMU) executes BEFORE any PEI/VRM/SIO code:
  if it halts, ranks 1-3 are unreachable and unfixable from those surfaces.
  The killer (the C0A PSP region) was the earliest-executing and the least
  portable link (all drop key kids differ; the 96EA OEM policy key is
  native-only; this was provable statically from cert trees in Phase 1 and
  was only proven after M2full failed, in the "PSP-path findings" block).
- **S3. "Viable" framing overstated the base.** Verdict V1's headline
  ("same family, different drop; 4700S base stays viable") led with the two
  sameness facts (FW_XHCI byte-identical, shared layout) while the DIFF
  list — different AGESA drop, different SIO chip class, BC250-only VRM
  PEIMs, different SMU/TOS/ABL versions, different drop keys, missing
  0x24/0x45 carriers, 128 diff / 31 donor-only / 20 BC250-only modules —
  described a full porting project, not a compatibility probe. A base
  whose boot requires a port of that size is not "viable as a base"; the
  ladder then needed M2full/M4/M5/M6 to rediscover that.

### Level 2 — gates and discipline

- **G-A. M0 was flashed with a hard prerequisite unsatisfied.** The GO memo
  lists "P0-signal method defined (video vs serial vs beep/post-card)" as a
  hard prerequisite; the T+5 intent records "P0 signal method: STILL OPEN at
  write time". Consequence: the first and second observations carried no
  discriminating detail, and M2full/M4 silence was ASSUMED same-class
  (gap admitted at M5; oracle established only at M5, four silent rungs
  into the campaign).
- **G-B. G6 breaker honored in words, overridden in behavior.** After the
  M2full G7 correction explicitly ordered "stop flash-ladder rungs; resolve
  the C0A PSP boot path + key compat statically, then build ONCE... No
  third blind rung", the campaign still flew M5 and M6 — same class, same
  1-bit outcome. Mitigation recorded here, not as excuse: M4 was the
  promised "build once" and was sound; M5/M6 were explicit operator choices
  from decision prompts; and they completed the elimination matrix. The
  residual error: the prompts presented rung choices instead of presenting
  the cheaper decisive test first (see M-B).
- **G-C. The Track B trigger was applied to a condition it did not meet.**
  Plan §4: pivot after "3 consecutive P0 failures with distinct, documented
  causes". The causes were never distinct — the same undiagnosed silence
  three times. Root declared "TRACK B TRIGGERED" anyway, the operator
  rejected the pivot, and a G7 correction followed ("a campaign-plan
  trigger authorizes ANALYSIS, not a base change"). Two direction changes
  in one flash window cost a wasted cycle (T1) and mixed ladders.
- **G-D. A flashed, never-observed rung was knowingly overwritten.** The
  G7 block states "board holds T1 unbooted. Next flash overwrites it.";
  M5 proceeded anyway without a T1 boot protocol. The loss was recovered by
  accident: pre-M5 NVRAM drift forensics proved the board EXECUTED T1
  firmware (pin reverted), and the operator later confirmed the boot. Had
  the drift not touched our edited byte, a real observation would have been
  silently destroyed.
- **G-E. T1 build skipped the G4 intent log** (logged in place as a LAPSE;
  low impact).

### Level 3 — method and observation

- **M-A. No boot-observation channel was ever established. This is the
  single deepest reason there is no result.** J5 = UART, TPMS1 = LPC/POST
  debug, J2 = CPU JTAG (1.8 V domain) have been CAD-recorded since
  2026-09-11 and were never populated, probed, or ruled out. Every silent
  boot in the campaign is therefore an unlocalizable halt somewhere in
  ROM->BL->ABL->PEI->DXE. A BIOS port through a 1-bit oracle (LED on/off)
  is not a debugging method; it is a coin-flip ladder. Every "next rung"
  decision after M0 was made without a mechanism observation, which is why
  the ladder oscillated (fix-C0A vs native-plus-C0A-PSP) instead of
  bisecting.
- **M-B. The bisection ran from the wrong end.** To localize the kill locus
  with the oracle available, the cheapest decisive test was: native base
  (known booting) + replace the ONE suspected region -> M6's design. From
  the native side this is ONE experiment; the campaign approached from the
  C0A side (M0, M2full, M4, M5) and reached the same conclusion after five.
  M6's outcome was, in retrospect, predictable enough that it should have
  been the second experiment ever flown (after M0), not the sixth.
- **M-C. P5.00 was never flashed.** The official same-board newer BIOS
  (BC250_5.00.bin, retroweb-verified bytes in `evidence/donor/
  retroweb-20260916/`, worker top pick E7, "synthesis top base pick")
  directly serves three goals (modernity, best Track B base, newer SMU for
  a VCN re-probe) and sat idle through the whole campaign.

### Level 4 — records and hygiene

- **R-A. The m0-window log lost append-only chronology**: T1 review/approval/
  flash-done records were appended inside the M6 flash section. Consequence
  observed today: the stop state was misread as "chip holds T1" when the
  chip provably holds M6 (readback `post-m6-readback.bin` is the newest
  capture). Repair: chronology below and in the report table.
- **R-B. The entire 2026-09-16 state is uncommitted** (last commit `f6d3db0`
  predates the campaign): decisions D19-D23, six builder scripts, three
  specs, six action logs, three incidents.
- **R-C. Stray artifact in repo root**: `C:\Users\OWNER\e1_setup_ifr.txt` — a
  script invoked with a Windows-style path on Linux created a literal file
  (its content shows the failed HII scan of that run). The real E1 IFR dump
  products were used by T1 scoping. Housekeeping item; harmless bytes.
- **R-D. The on-chip identity dispute (`c0f5f1c5` vs `addef288`)** lingered
  from 09-14 until the T+4 double capture settled it. The fresh-capture
  rule existed; applying it once, earlier, removes the class of dispute.

### What was NOT an error (recorded for balance)

- M0-as-is first (pure discriminator, PD4): sound design.
- M4 as the single static-resolved build after the key analysis: sound; its
  pre-commit ("if silent, 4700S base dead") was honest and it held.
- M5/M6 as operator-directed rungs: they completed the elimination matrix
  with a confirmed oracle (PEI/VRM/SIO/training en bloc excluded; C0A PSP
  excluded as a base).
- T1: produced a genuine positive — native base re-proven bootable after
  the campaign, and a new firmware behavior (AmdSetup pin revert) recorded
  as OQ-T1d.
- Flash safety: 6/6 writes VERIFIED + independent readback; recovery chain
  never broken; no irreversible step at any point.

## 2. Causal chain: why there is still no result

1. The campaign spent 6 of 7 flash cycles on base selection, and 5 of 6 on
   a base whose boot probability the static evidence already priced near
   zero (S1-S3).
2. With no observation channel (M-A), every negative was undiagnosable, so
   each "next step" was a choice between ladders, not a localization step.
3. The gates that exist to prevent this — G3 goal mapping, G6 breaker,
   hard prerequisites in the GO memo — were documented but not enforced
   (G-A, G-B, G-C).
4. Net information gain is real (elimination matrix, key map, oracle, T1
   boot, OQ-T1d) but goal progress is zero: VCN unchanged (already
   exhausted), OC route via naive NVRAM pin disproved (revert), TPM never
   attempted, modern BIOS never flashed.

## 3. Forward decision tree (PROPOSED — every flash behind operator approval)

- **R0. Restore the board to a booting image.** Chip holds M6 (silent).
  Recommended source: `pre-m0-read-a.bin` `3f836668` (this board's own
  bytes, T1-lineage proven booting). Cost: 1 flash cycle. This un-blocks
  the daily use of the machine and is the control for everything after.
- **R1 (modernity + best base). Flash official P5.00** (`0d6f136c`,
  same board, AGESA 46.1.2.220426 newer than the P3.00-lineage dump, SMU
  t8 `13c93c08` newer than dump's `6a3da1ef`). Expected boot per same-board
  official provenance; becomes the base for all later rungs. Decision
  needed: P5.00-stock vs P5.00_clv shape (clv = P5.00 + full CBSG 1896 B,
  OC-capable shape; community origin 2025-10-05 — provenance review first).
- **R2 (OC).** On the chosen base, in ascending blast radius:
  (a) T1-down discriminator — pin 1000 MHz (`0x14`): if it sticks while
  1750 reverted, the revert was a train-fail fallback (answers OQ-T1d);
  if it also reverts, NVRAM-pin control is rejected outright — 1 cycle;
  (b) T1b staged CBS master flips (OC forms first; 123-flip list ready);
  (c) host SMU governor remains the proven no-flash fallback.
- **R3 (TPM).** Static first: does the native/P5.00 PSP carry fTPM app
  support (PSP dir t-types vs donor), then M3c fTPM DXE/PEI graft via the
  proven D8-envelope same-slot method. Donor surface already inventoried
  (5 modules, fits).
- **R4 (VCN).** The exhausted-routes verdict stands for the current SMU.
  The one cheap re-open: re-run the proven S2 runtime probe suite
  (unlock -> dom6 -> 0x61 -> gasket -> single-reg arbiter) on a P5.00-SMU
  board — runtime only, cold-cycle reversible, no additional flash beyond
  the R1 base. New SMU fw = new dom14 behavior question; negative result
  closes the branch for the newer drop too.
- **Instrument first (applies to all rungs).** Before the next flash
  campaign: establish at least one observation channel — J5 UART (3.3 V
  TTL check first), TPMS1 POST decode, or a post-code card on LPC — or
  explicitly waive it. Rule proposed for the campaign file: no rung N+1
  flies until rung N's failure is localizable or a new observation channel
  exists (anti-G6 standing rule).

## 4. Standing corrections to record (G7)

- M6 result: true silence (oracle-confirmed), 4700S base exhausted with the
  C0A PSP region as the kill locus; halt mechanism inside the PSP chain
  unresolved.
- T1 verdict complete: P0/P1 PASS, P2 FAIL, pin revert = firmware behavior,
  OQ-T1d open.
- BHD 0xAB0000 byte-identical across C0A-stock / native / M2full; APCB size
  is self-describing (APCB+8); no BHD repoint class of defect exists in
  M2full/M4/M6.
- Process rule promoted from this audit: instrument-first, goal-map memo
  before base selection, and the anti-G6 standing rule above.
