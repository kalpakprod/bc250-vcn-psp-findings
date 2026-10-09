# SPEC: unified 5.00-CLV firmware — in-firmware 8-core unlock + all patches

Status: OPERATOR REQUIREMENT FIXED 2026-09-22 ~02:25+05:00. No build yet.

## 1. Title and scope

Operator: "хочу себе [такой же мод] на пять-ноль-СЛВИ: 8 ядер в прошивке
плюс все сделанные патчи". Deliverable = one flashable 16 MiB image on a
5.00-lineage base that contains: (a) in-firmware 8-core unlock
(`Bc250CoreUnlockDxe` class + `Unlock CPU Cores` menu), (b) all community
patch classes already proven on 3.00 lineage (chipset-menu unhide,
NVRAM/defaults shape, logo optional), (c) the 5.00/CLV OC menu surface.
Out of scope: voltage changes, PSP/signed-region edits, 5.00_clv Discord
file (no public hash — not a base).

## 2. Planning anchor

- Base candidates (decision open, §6-Q1): CLV donor `ea578104…`
  (RetroWeb, full CBSG, unauthenticated) vs stock P5.00 `0d6f136c…`
  (multi-source) + CBSG port vs W11 `3c50bc9a…` (CLV-derived + B6250780,
  boot unverified). Default lean: CLV donor (OC surface already in).
- Delta sources: FD v2.2 driver set (donor `606a7a7f…`, 6 FFS) +
  Setup-unhide patches (`899407D7` same-size, `B1DA0ADF` +0x27) +
  behavior reference `8_cores_steam.rom` (`c99cbca1…`, P3.00).
- Starting point: `candidates/BC250_5.00_clv_MeiMeiDXEv3-drivers-only_v001.bin`
  (`0968a70c…`, 6 drivers injected, static-only, UNREVIEWED, UNFLASHED).

## 3. Connected groups / existing logic

- Rejected method: whole-FV graft (`af531026…`, single green blink,
  no LAN/video 2026-09-17). This spec uses surgical injection only.
- W11 `3c50bc9a…`: CLV-derived + B6250780, no MeiMei in main DXE; 8-core
  boot claim has no flash-to-log join (weak).
- Community reference `docs/reference/.../bios/flashing.md`: Method 2/3
  programmer discipline; CHIPSETMENU `48fbe5d3…` multi-source; P5.00_clv
  unavailable publicly.
- Flash method: programmer only (CH347 + flashrom, capture-x2/VERIFIED/
  readback, LED-oracle P0, DP-direct, CMOS). AFU explicitly not primary.

## 4. Use cases

- UC1: operator flashes via programmer → Setup shows unlock menu →
  8 cores in OS on 5.00 base, board daily-usable (gaming).
- UC2: CLV OC menu surface available for the staged P3.00-runbook successor.
- UC3: rollback to pre-write capture or stock at any failure.

## 5. Implementation checklist

1. [ ] Q1 base decision (operator-visible, evidence-backed).
2. [ ] Extract + verify Setup-unhide patch bytes vs 5.00-base Setup/AMITSE.
3. [ ] Build v002 = base + 6 drivers + unhide (+logo decision) via new
       builder script; new file only.
4. [ ] Structural validation: firmware_audit + independent re-scan
       (PSP/APCB/BHD identity, FV/FFS checksums, LZMA round-trip, DEPEX,
       changed-range report).
5. [ ] Independent second-family review (REQUIRED, currently unstaffed).
6. [ ] Programmer flash gate: fresh chip ID + capture-x2 + exact approval.
7. [ ] P0 (POST+video, LED oracle) → 8-core verify (`nproc`=16) → menu
       verify → stability soak → NVRAM readback.
8. [ ] On any fail: rollback capture, root-cause, no blind re-rung (G6).

## 6. Open questions

- Q1 (BLOCKING build): which 5.00 base? Needs provenance + OC-surface + W11-lesson comparison.
- Q2 (blocking): will 3.00-built MeiMei drivers dispatch on 5.00 DXE?
  Static DEPEX says satisfiable (1 intra-set GUID); boot is the only proof.
- Q3: Setup-unhide port method on 5.00 Setup (same-size patch vs IFR defaults)?
- Q4: NVRAM defaults for v002 — keep CLV stored requests
  (1800/Enabled/Auto/Auto/Manual-1420) or ship all-Auto?
- Q5: logo/branding — include or skip (blast radius)?
- Q6 (non-blocking build, blocking flash): second-family reviewer source.
- Q7 (state, non-blocking): operator reports "5.00 CLV installed, just
  flashed community BIOS"; live readback 2026-09-22 02:05 shows DMI P3.00,
  uptime 4:10, NVRAM == baseline `6f266c3c…` (no reboot, no change).
  Join unresolved — which file, when, which board state.

## 7. Decision log

- 2026-09-22 D-REQ1: requirement fixed as §1 (operator verbatim intent).
- 2026-09-22 D-METH1: surgical injection; whole-FV graft stays rejected.
- 2026-09-22 D-FLASH1: programmer-only flash method for this spec.
- 2026-09-22 D-BASE1: Q1 CLOSED — base = CLV donor `ea578104…` (operator
  choice). Build v002 = CLV + 6 MeiMei drivers + all patch classes.
- NVRAM shape, logo: OPEN (Q4/Q5).
