# PEI-time DF-aperture patch for VCN bridge — candidate specification

Date: 2026-09-13. Status: PROPOSED/BLOCKED (design valid; V1 target list
EMPTY — see §8 verdict. No image built, nothing flashed).

## 1. Title and scope

A minimal PEIM patch (0196 `AmdNbioBaseARIPei`, unsigned PEI FV) that programs
the VCN DF-window set through the stock CPU DF-indirect primitive during PEI
(fabric open), so the routing SURVIVES the ReadyToBoot ext-config lock into OS.
Staged variants: V0 (observe-only recon, no patch) → V1 (DF-windows-only:
0x03A201xx + 0x3E810/14 + 0x032201xx + PCI-CFG small addrs) → V2 (+ VCN-bank
program/commit IF V1 shows bridge-open-but-dark, AND only after bank-write
safety is re-proven). V1 explicitly EXCLUDES VCN-bank writes (island-down
wedge predicted, same mechanism as D12-D19).

Explicitly NOT in scope: PSP/`$PS1`/signed-region changes, NVRAM/APCB changes,
SMU-proxy writes, DXE-driver injection, any flash (separate exact-image gate).

## 2. Planning anchor

- 0196 `0x3cf2` (validated DF-write primitive, our bytes): die<2, unit<4,
  func<8, reg<0x400 aligned; sel==0xff direct store via E0000000 wrap, else
  index(0x405C)/data(0x4098). Stock `0x2996` programs 7 aperture sets/0x21c4
  every boot (MSR-fed) through this exact primitive. Transport + primitive
  proven open in PEI.
- Runtime-proven write SET (A1v2 1461 triples, parsed): DF-class =
  0x03A201xx block (0x14/0x18←0x22222222, 0x1C←0x87FF, 0x20←0xFFFF0000, rest 0),
  0x210 pair (0x3E810←0 FINAL, 0x3E814←0xF853C480 FINAL — differs from the C2
  recipe's 6/0x2544C382: replay-path values win), 0x032201xx block (0x203/0x281
  program/commit pairs), PCI-CFG small addrs (0xD428-0xD448), NBIO 0x1F820/
  0x1F8A4 (0x03E810-class context, NOT patched: 0x1F8xx is hazard).
- Window model: CPU DF-indirect OPEN in PEI + DXE-dispatch, CLOSED at
  ReadyToBoot by 0021 (ext-config disable); programmed WINDOWS (routing)
  persist into OS. SMU-proxy-to-island writes wedge whenever island down
  (any phase) — excluded from V1.
- `$VNI` builders ×3 share the 658-entry map but feed DXE-phase consumers;
  PEI DF programming is MSR-fed, NOT `$VNI`-fed → the patch injects
  (reg,val) PAIRS (code-level, new 0x2996-style call or extended pair loop),
  not struct defaults. Struct-source hunt PARKED (not on the patch path).

## 3. Connected groups / observed logic

- DF-indirect formula (0x3cf2): fabric=((die<<2|unit)-8)&0x1f (<<15);
  index=((sel<<5|func)<<11 | reg&0x7fc)|1. Full bit-exact decode in
  `docs/action-logs/2026-09-13-pei-vni-hunt.md` follow-up + session notes.
- 0x0322 vs 0x03A2 (same low 0x2011C) = two DF units/instances of one window
  class; 0x3E810/14 = paired instance select/data (shape differs).
- t28 PSP zeros 0x1F8C4..D4 at boot (verified byte-exact in our image);
  0x1F8xx secure reads WEDGE the mailbox (G7 hazard, 2026-09-13) → the V1
  patch MUST NOT touch 0x1F8xx; power-follows is a hypothesis, not a lever.
- Metrics oracle (Q0 table 6, 244B, quiesced) is the standing observer:
  VCLK=0/DCLK=1111 baseline; post-flash VCLK rise = power signal.

## 4. Use cases

- UC-V0 (recon, no patch): quiesced/live DF topology via SAFE PCI reads
  (dev 18h funcs) + single bounded CPU DF-indirect read (E0000000 window,
  /dev/mem or msr path; abort-on-wedge, costs at most one cycle) to resolve
  the (unit→component) map and validate the 0x03A2/0x0322/0x3E8 conversion.
- UC-V1 (minimal patch): 0196 image with injected DF-window pairs
  (0x03A201xx + 0x3E810/14 + 0x032201xx + PCI-CFG small set; exact pair list
  TBD after UC-V0 conversion). Expected signals, in order: (a) board boots
  (no PEI wedge); (b) VCN MMIO ladder not-all-F (bridge OPEN); (c) VCLK>0 in
  metrics (power FOLLOWS) and/or VCN probe binds. Any wedge → stock recovery
  flash (programmer + verified dump, existing procedure).
- UC-V2 (contingent, NOT designed): + VCN-bank program/commit ONLY if V1
  shows (b) without (c). Needs a fresh bank-write safety case first.

## 5. Implementation checklist

- [ ] UC-V0a: DF PCI topology (dev 18h funcs 0-7 config reads, SAFE).
- [ ] UC-V0b: DF-view→(die,unit,func,reg) conversion table for 0x03A201xx,
  0x3E810/14, 0x032201xx (formula + topology; document each bit-field).
- [ ] UC-V0c (bounded live): ONE CPU DF-indirect read quiesced + alive check
  (proves CPU-path reads safe; abort class on wedge).
- [ ] V1a: pair list (reg,val) with order + grouping (program/commit preserved
  from A1v2 where present).
- [ ] V1b: patch mechanics decision (new 0x2996-style call site vs extended
  pair loop vs data-table append) with byte-exact diff plan + no-reloc
  constraint (TE reloc stripped; position-dependent code must stay valid).
- [ ] V1c: build candidate image (new file, stock preserved), structural
  validation (FV/FFS checksums, TE parse, disasm spot-check of patched
  region), changed-range report + hashes.
- [ ] V1d: independent review (diff + evidence + failure path; different
  model family when available) — review ≠ flash approval.
- [ ] V1e: SEPARATE flash gate (exact image, recovery dump verified,
  explicit approval, readback procedure) — not this spec.

## 6. Open questions

- OQ1 (blocking V1b): exact (die,unit,func,reg) per DF target (needs UC-V0).
- OQ2 (blocking V1c interpretation): is DF-windows-only SUFFICIENT for
  bridge-open (testable only by V1 flash) — no static oracle exists.
- OQ3 (blocking UC-V2): does power FOLLOW addressability, or is an explicit
  (PSP-gated) power grant required — decided by V1's (b)/(c) split.
- OQ4 (non-blocking): VCN-bank x86-PEI writability (CF8/CFC SMN vs PSP
  firewall) — needed only for V2.
- OQ5 (non-blocking): IDS protocol installer identity (DXE-side; parked).

## 7. Decision log

- 2026-09-13: PEI pair-injection chosen over `$VNI`-struct patch (PEI DF
  programming is MSR-fed; `$VNI` feeds DXE-phase consumers = wrong timing).
- 2026-09-13: V1 excludes VCN-bank writes (D12-D19 wedge mechanism
  generalizes to any phase while island down; prediction recorded).
- 2026-09-13: 0x1F8xx excluded from all variants (G7 secure-read hazard +
  PSP-guard inference).
- 2026-09-13: A1v2 replay-path finals (0x3E810←0, 0x3E814←0xF853C480) chosen
  over C2-recipe values (6/0x2544C382) for the V1 pair list (replay is the
  x86-view ground truth; C2 is the PSP-view).
- Flash remains separately gated; this spec authorizes design + recon only.

## 8. UC-V0 verdict (2026-09-13 — V1 BLOCKED, mechanism proven)

- UC-V0a PASS: Ariel DF topology (`13F0-13F7`); F0 xB8 locked `0x280`
  (write does not stick — not the post-boot indirect port); F3 xB8 dead;
  kernel SMN (7.2.0) is MMIO-based (no PCI residue); /dev/mem EPERM.
- UC-V0b PARTIAL: conversion STRUCTURALLY proven for seg-0x03/off<0x400 →
  INDEX (sel=bits[23:16], func=off[12:10], reg=off[9:0]); all seg-3 addrs
  fit with func=0. Live proof BLOCKED (all OS paths locked or hang —
  see below). Seg-0/seg-9 transports unresolved.
- UC-V0c FAILED: read-only dfprobe kmod hard-hung the board at `insmod`
  (dmesg lost; DF-cycle vs SMN-guarded attribution unknown). OS-side
  DF/SMN probing is now a PARKED hazard class (G7). Remaining live-proof
  road: UEFI-Shell .efi pre-ReadyToBoot (not built; needs USB+operator).
- TARGET VERDICT: stock→VCN gasket seg-3 delta = EMPTY (91/91, zero
  diffs); VCN delta = 56 seg-9 HWID-12 writes only; Cezanne donor
  confounded (113 lines, extra 0x3D201xx instance, DRAM-map values).
  V1-as-specified (DF-windows-only) HAS NO TARGET LIST → V1 BLOCKED.
- MECHANISM (proven, reusable): 0196 `0x3c0b/0x3cf2` read/write pair +
  0021 DXE mirror + RMW + die/unit discovery, pure-MMIO @ E0000000
  (no CF8/CFC — old trace retracted); stock PEI = class-0 DIRECT only
  (ebx=0 ×7 sites); 0021 DXE DOES program DF (9 write sites, incl.
  runtime-(sel,func) RMW = IDS-driven second injection path AND an
  override risk for PEI injection — must enumerate pre-flash).
- OQ UPDATES: OQ1 answered structurally for seg-3 (live proof deferred
  to Shell-.efi); OQ2/OQ3 untestable (no V1 target); NEW OQ6 (blocking
  any injection): seg-9 transport + x86-PEI writability of 0x0900Cxxx
  (Shell-.efi reads first); NEW OQ7: enumerate 0021 DXE DF-write sites'
  runtime targets (override risk).
