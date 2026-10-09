# Campaign plan: VCN unlock + FCLK/MEM OC stabilization

Date: 2026-09-17. Actor: root. Status: PROPOSED (no flash, no candidate build
under this plan yet; base change requires explicit operator choice per the
2026-09-16 G7 rule).

## 0. Operator completion condition (stop condition, verbatim intent)

Work stops only when: a BIOS exists that (1) unlocks VCN usage, (2)
stabilizes FCLK and MEM overclocking to reduce latency, and (3) uses
everything extractable from the available BIOSes and similar-board
information. Decomposed into verifiable sub-conditions:

- **C1 VCN**: `vcn_v2_0` attaches, rings init, a real encode/decode job
  completes (hardware-verified), OR a documented per-version closure: every
  obtainable SMU/PSP firmware version probed and the blocker shown
  version-independent (negative result preserved as evidence).
- **C2 FCLK/MEM**: FCLK and MEM clock increases applied at boot, latency
  measured below stock baseline, stable under a soak test (one variable per
  flash; training-fail revert used as the built-in safety indicator).
- **C3 Donor exhaustion**: checklist in §6 fully answered — every obtainable
  image mined for graftable material; each item either used or proven
  unusable with evidence.

## 1. Standing rule from the 2026-09-17 error audit

Instrument-first: attempt a boot-observation channel (J5 UART after 3.3 V
TTL verification, or TPMS1 POST decode) before the next flash rung, or
record an explicit waiver. No rung N+1 flies while rung N's failure is
non-localizable.

## 2. Base decision (operator gate)

Proposal: **P5.00 official** (`0d6f136c`, retroweb-verified bytes,
`evidence/donor/retroweb-20260916/`). Same board, newest drop (AGESA
46.1.2.220426, SMU t8 `13c93c08`, t28/t40 `5b6828bf`), the one base that
serves C1 (new SMU to probe) and C2 (newest AGESA) simultaneously.
Alternative: `P5.00_clv` (`ea578104`, P5.00 + full CBSG 1896 B,
community OC shape, 2025-10-05) — requires provenance review before use.
Current native lineage (P3.00, `3f836668`) is the fallback control.

## 3. Phase V — VCN re-open hunt (answers "search vulnerabilities again?")

Yes, but pointed: the 2026-09-12 exhaustion verdict binds to SMU 0.58.6.0
(body `5c805026...`). The P5.00 SMU was never decoded or probed. Method
class changes from flash-rungs to firmware RE (G6-compliant).

- **V1 (no flash, start immediately)**: static decode of P5.00 SMU t8
  `13c93c08` — msg table (count/stride/anchors), domain table + boot-default
  states (+0x14 bytes for dom6/7/14/15/17), PowerUpDomain chain
  (0.58: 0x2362c -> 0x23b14), poll/timeout structure, ISO/reset references.
  Deliverable: diff report vs the existing 0.58.6.0 map
  (`evidence/firmware-audit/20260914-smu-address-trace/slot-domain-map.json`,
  msg-table dump, `recon/func_23b14_full.txt`).
  Decisive questions: does dom14 still boot `0x41` born-busy; do the
  three infinite polls still have no timeout; is any new
  power/ISO-releasing message exposed.
- **V2 (no flash)**: static decode of P5.00 t28 boot-time five-domain
  program (`5b6828bf`) — what the newer PSP writes at boot
  (`0x1F8A4`, `0x1F8C4..D4` in the old body) and whether the dom14
  boot-time treatment changed.
- **V3 (no flash, leftover from OQ9/2026-09-12)**: the never-completed
  Q3 msg-table deep decode + ISO-chain hunt, now on the new body: the 147
  handlers of 0.58 are dumped; decode the secure-cluster range
  (`0x27..0x2F`, flags `0x201`, gated) and any unmapped handler that could
  be the real PowerUpVcn equivalent; enumerate the ISO/reset holders around
  the dom14 cluster.
- **V4 (1 flash cycle, after base decision)**: flash P5.00, then re-run the
  proven runtime suite on the new SMU: unlock (Q2 0x23) -> dom6 power ->
  0x61 clocks -> read-only domain statuses (`read_domain_status.py`) FIRST,
  gasket 59/59 -> arbiter single-register reads. Identical born-busy
  statuses + all-ones arbiter = version-independent isolation documented
  (C1 closes as per-version negative). Any delta = new surface, follow the
  doorbell-with-host-timeout ladder (S2-L6b method).
- **V5 (parked research lane)**: on-die ROM svc#6/#0x63 verifier and PSP
  key-material RE — remains out of campaign-critical path (mathematically
  and statically bounded before); resume only if V1-V4 all close negative
  and the operator re-opens the lane.

## 4. Phase O — FCLK/MEM overclocking and stabilization

- **O1 (1 flash cycle on the new base)**: T1-down discriminator — pin
  AmdSetup+0x316 = `0x14` (1000 MHz) via the proven 1-byte builder. If it
  sticks while 1750 reverted, the T1 revert was a training-fail fallback
  (OQ-T1d answered; safe pin path exists). If it also reverts, the naive
  NVRAM-pin class is dead and O2/O3 carry the goal.
- **O2 (static, then 1 cycle)**: T1b staged CBS master flips — OC forms
  first from the ready 123-flip list (AmdSetup offsets + current values
  already resolved); D8 envelope + same-slot method; menu recon photos at
  each boot.
- **O3 (static)**: FCLK surface — coupled control/value pairs only
  (`FCLK_DPM +0x6A3`, `DF Clock Override Control +0x703` with value
  `+0x704`; map: `evidence/firmware-audit/amdsetup-ifr-field-map.json`).
  Candidates built only with the coupled-pair rule; SMU metrics
  (`cur_uclk`, pp_dpm clocks via the read-only collector) as the oracle.
- **O4 (static)**: CBSG shape decision for the base — compare clv CBSG
  1896 B (`b073915e`) vs native dump CBSG 1852 B vs P5.00 stub 84 B; adopt
  or reject the community shape with a byte-level verdict.
- **O4b (static, from the 2026-09-04/05 chat export)**: decode DFG 0x1703
  tokens idx6/idx8 on the clv base (u16 99/35, paired type-0x0005/0x0006
  subblocks at 0xAB112A/0xAB112E) — semantics unknown; the collaborator's
  four one-variable variants + checksum-valid ckfix are preserved in
  `evidence/donor/chat-oc-profiles-20260904/`. Chat-measured context: FCLK
  ceiling 1400 @0.9 V SoC auto, 1800 @~1.2 V manual (hardware pots);
  latency baselines 140-150 ns / 60-66 GB/s read; NVRAM-pin class dead
  (chat + our T1 revert).
- **O5 (per-candidate)**: measurement harness — stock baseline first:
  memory latency probe + SMU metrics + gamescope/MangoHud fps and 1% lows
  (board already games), then one-variable candidates; stability soak as
  the gate for "stabilized". MEMG/DFG token edits are the boot-safe APCB
  surface (D3-A/D8-D19 proven) but only move with a training-proof loop.

## 5. Phase T — TPM route

- **T1 (static)**: does the chosen base's PSP carry fTPM app support (PSP
  dir entry types vs the donor's requirements); C0A donor fTPM DXE/PEI
  graft surface already inventoried (5 modules, 327,696 B, fits free
  space).
- **T2 (1 cycle)**: fTPM graft via D8-envelope same-slot method; kernel TPM
  node + quote test as the oracle.
- **T3 (fallback)**: dTPM via TPMS1/LPC header (unproven; only if T2
  closes negative).

## 6. Donor-exhaustion checklist (C3 — "everything possible is used")

| Source | Material | Status before plan | Consumed by |
|---|---|---|---|
| C0A 4700S `bb2cf51d` | fTPM stack (5 modules) | inventoried, not grafted | T1/T2 |
| C0A 4700S | SMU 0.46 / ABL 22.4 / TOS 0.20 | proven unusable as base (M0-M6) | closed with evidence |
| P2.00 / P3.00 natives | older same-board drops | hashed; superseded by P5.00 | closed (older versions) |
| P5.00 native | newest SMU/t28/APCB PSPG | bodies diffed + first-pass decode (loop#1, workers A/B, 2026-09-17): msg 0x8/0x9 NULL both; t28 five-domain program unchanged | V1 residual (svc handlers), V4 |
| P5.00_clv | full CBSG shape | hashed; byte verdict done (72 tok vs 68, schema 0717) — O4 CLOSED | O4b token decode |
| dump P3.00-lineage | full CBSG, SMU 0.58 map | mapped (SMU), CBSG baseline | O4 baseline |
| thelamer/bc250-vcn baseline | community state 2026-08-18 | local copy == HEAD (e53aa40); threads #1-#5 closed/partial — see `docs/research/2026-09-17-thelamer-baseline-delta.md` | reference anchor |
| amd/firmware_binaries v2000a | closest APU relative, VCN power-up chain | unmined lead from baseline | V1 comparison |
| 8c CPU unlock (GabriWar/Forbidden-Darkness/mendesrr) | mask `0x115A870` `0x77`->`0xFF` + ACPI tables | substrate verified on board (D10R reads `0x77`); write never applied | C3 runtime rung (reversible) |
| bc250-collective Ghidra project | full SMU decompile | local, partially used | V1 method template |
| PS5 / coreboot / OVMF | out of scope (H2/H3) | closed 2026-09-16 | — |

## 7. Order of execution (cheapest decisive first)

1. V1+V2+V3 static decodes (no flash, no operator gate — read-only RE).
2. Base flash decision (operator): P5.00 vs clv vs stay-on-current.
3. V4 runtime probe on the chosen base.
4. O1 discriminator, then O2/O3/O5 ladder; T1/T2 in parallel static.
5. C3 checklist sign-off + final BIOS assembly; review gate per release.

Every flash: fresh pre-write capture x2, exact-text approval, VERIFIED +
independent readback, LED-oracle boot protocol + 5-min wait + ping, G4
log before/after. Commit checkpoints per completed rung (audit R-B).
