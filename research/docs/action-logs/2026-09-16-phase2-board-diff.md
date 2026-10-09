# Action log: Phase 2 board-diff risks + M0 go/no-go memo (2.1-2.5)

Date: 2026-09-16 (UTC). Actor: root. Read-only (parsers + byte diffs).

## 2.1 FCH identity — PARTIAL (chip part still open, config identical)
- FCH strings in SbDxe/FchDxe: generic init-task names both sides, no part
  numbers. No lspci/board-access record in repo (searched memory/docs/
  evidence/recon: none).
- APCB FCHG group (0x1706): body byte-IDENTICAL both sides (23fab72e).
  FCH *configuration* is shared; the discrete chip may still differ
  (4700S manual says A77E; BC250 part unknown).
- OQ-B2 resolution path (user-completable): (a) live `lspci -nn` from
  BC250-01 if reachable, or (b) operator photo of the FCH marking.
  Does NOT block M0: identical FCHG + proven recovery bounds the risk.

## 2.2 APCB token map — DONE (exact)
- Same 6 groups, same offsets, stock DFG both sides. UNKN/DFG/FCHG bodies
  IDENTICAL. Differences: PSPG inst-2 (32 B), MEMG inst-7/8 (see 2.3),
  CBSG size 84 (donor stub) vs 1852 (BC250 full) — the whole ~1768 B delta.
- PSPG inst-96 identical (24 B). CBSG transplant surface deferred to M3.

## 2.3 Memory config — DONE (4 bytes)
- MEMG inst-7/8 (twins within each image): the ONLY cross-image delta is one
  4-byte field at subgroup+0x94: C0A `00 00 00 00`, BC250 `00 01 00 20`
  (bit0 of byte1 + bit5 of byte3). All other 41-token rows identical;
  inst-49/80/82/83 identical. M2 transplant = 4 bytes + APCB checksum byte.
- Interpretation (inference, not proven): per-channel population/mode flags
  (SKU topology). Discriminating test: M0-as-is boot behavior; if no-train,
  M2 flips exactly these 4 bytes (one variable).

## 2.4 PCIe/GPIO/SIO — DONE (static)
- PCIe: NbioPcieARIPei diff-body (AGESA-drop skew, like all silicon PEIMs);
  board topology differs (4700S x4 dGPU slot vs BC250 M.2 + iGPU outputs).
  dGPU-dependent donor paths (OpROM video) have no target on BC250.
- GPIO: AmdCpmGpioInit PEI/DXE/SMM both sides; PEIM diff-body (drop skew +
  possible table deltas — table extraction deferred to M2 design).
- SIO: different chips AND different init PEIMs (IT8772E vs NCT6686D).
  Misdrive risk: donor SIO init pokes IT8772E LDNs/ports that on BC250 may
  belong to NCT6686D or nothing. Bounded: SIO init runs late (PEI tail),
  after memory; worst static case = no-boot/hang, not damage (no voltage
  writes in SIO init path — inferred from module role, stated as inference).
- VRM: BC250 ISL69247/ISL95712 PEIMs have NO donor counterpart. Donor
  training/power sequence may mistune BC250 rails. Bounded by: identical
  silicon + recovery; flagged as the top M0 unknown after memory.

## 2.5 M0 GO/NO-GO MEMO — GO, with ranked residuals
GO (cross-flash C0A-stock `bb2cf51d...` as-is, zero bytes changed):
- Same Ariel silicon, identical PEI dispatch order, identical
  UNKN/DFG/FCHG APCB, 4-byte MEMG delta, proven CH347T recovery flow.
- M0 is a clean discriminator: it tests board-compat (train/SIO/VRM/video),
  not our edits. Any failure carries a precise next variable (M1/M2).
Residuals, ranked: (1) memory training across AGESA drops (RBNBDK 46.1.2 vs
CDBDK 44.0.0) + 4-byte topology delta; (2) VRM sequence without ISL PEIMs;
(3) SIO misdrive (hang-class); (4) no pre-OS video path either side (P0
signal may need serial/blink codes/post-card — define before flashing);
(5) PSP acceptance of a foreign-stock image on BC250 silicon (untested
class; same-vendor same-family stock is the mildest possible case).
Hard prerequisites before the write (all must be true): fresh 2x-matching
pre-write capture + chip identity; stock recovery re-verified readable;
explicit operator approval in the exact form with path+hash+board;
P0-signal method defined (video vs serial vs beep/post-card); operator
present for the flash window.

## Checks (G9)
- APCB/MEMG/PSPG/FCHG/CBSG byte diffs: PASSED (own runs). FCH chip part:
  UNRUN (handoff defined). GPIO tables, VRM sequence: UNRUN (M2 design).
- No candidate built; nothing flashed. M0 readiness: ANALYTICALLY GO,
  procedurally gated on the hard prerequisites above.
