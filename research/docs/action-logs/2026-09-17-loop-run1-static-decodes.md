# Action log: loop 377650c2 run #1 — campaign static-decode sweep

Date: 2026-09-17 (UTC). Actor: root (loop run #1). Target: repository
records + offline candidate build only. No hardware action.

## Intent (BEFORE writes)
First run of the 2h campaign loop. Backlog note: all 2026-09-16/17 records
are uncommitted (audit R-B); first action = one record-preservation commit,
then per-item commits.

Plan (authorized items only, no operator gates):
1. Preserve backlog commit (existing dated records, no candidates/hardware).
2. V1/V2: extract P5.00 PSP bodies t8 (SMU, expect `13c93c08`) and t28
   (expect `5b6828bf`) via `scripts/firmware_audit.py`; binary-diff both
   vs the 0.58.6.0 bodies from `dump/2.bin`; decode changed ranges
   (targeted, not whole-body) as the first-pass version delta.
3. O4: CBSG byte-level verdict across clv/dump/P5.00 APCB.
4. O3: FCLK coupled control/value pair map from the IFR field map JSON.
5. T1: static fTPM PSP-app check (PSP dir entry census dump vs P5.00 vs clv
   vs C0A).
6. O1 prep: build T1-down candidate (0x316 -> 0x14) from pre-m0 into
   candidates/ (BUILD ONLY).
7. V3/C3: as time allows; remainder carries to run #2.
## Result (AFTER)
Completed: backlog commit `18fc1db`; V1/V2 first-pass body diffs + targeted
constant decode (t8: 139,508 B delta across ~82 ranges, domain-table data
byte-identical but shifted -0x30, dom/gasket/core-mask literals absent as
constants in both — computed registers; t28: five-register program and
(addr,value) table @0x188d8 byte-identical, only layout shifted +212);
O4 CBSG verdict (schema 0717; dump 1852 B/68 tok, clv 1896 B/72 tok with
352 differing bytes, P5.00 84 B 0xFF-padded stub); O3 map (MemoryClockSpeed
@0x316 with 1000MHz=0x14; FclkDpm @0x6A3); T1 fTPM census (zero TPM strings
in P5.00/clv/dump; donor-only stack); O1-prep candidate built
`candidates/BC250_O1prep_T1down_memclk-1000MHz_v001_from_pre-m0.bin`
sha256 a8a813b9..., 1 byte @0x7E5 0xFF->0x14, hardware acceptance unverified.
Deferred: V1 deep msg-table decode (Ghidra lens), V3, C3 -> run #2.
Full findings: docs/research/2026-09-17-loop-run1-verdicts.md.
Rollback: revert docs/scripts/candidates files; no hardware state touched.
