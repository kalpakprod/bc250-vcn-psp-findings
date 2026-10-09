# V3+V4 flash pair — operator runbook DRAFT (2026-09-23)

Status: DRAFT. Executes only on the operator's explicit «го» naming BOTH hashes.
Method class: programmer-only, board unpowered, battery out, clip verified, 3.3 V.
Backends/paths follow the proven 2026-09-11 procedure (flashrom ch347_spi 1.875M).

## Standing rules applied

- Instrument-first (2026-09-17 audit): UART/POST observation channel BEFORE the first write.
  If the J5/POST pad location is unknown, the session proceeds only with the understanding
  that a park outcome will be unlocalized.
- Exact-approval gate: the «го» must name both target hashes below.
- Rollback preserved: stock `evidence/programmer/reads/20260911/read-a.bin`
  (`83c4e420...`); rollback is a separate write with its own approval.

## Targets (one sitting, independent discriminators)

1. V3 `candidates/BC250_5.00_clv_ROOTKEY-swap-0x09_v001.bin`
   sha256 `46ec00bbcda7a4d0e6fbe6b9a39457395b573f8667141919e58e7f146ca8ecbf`
   - Tests: does the PSP ROM hash-anchor the raw type-0x09 root key blob?
   - Boot normal -> software re-root ladder opens (rung 2).
   - Park -> root anchored; EMFI target confirmed at this exact check.

2. V4 `candidates/BC250_5.00_clv_PSP-entry-absence_0x24-0x45_v001.bin`
   sha256 `02d6e33f3c8a99db27a003b1da8d093163ad4583181e958a5cda214c19e3127c`
   - Tests: does the platform lock VCN by default when the lock carriers are absent?
   - Boot + VCN gated -> absence lane dead. Boot + VCN present -> jackpot. Park -> absent
     required entries halt; lane dead.

## Procedure (per target, x2)

1. Preflight: board unpowered, battery out, clip orientation check, programmer probe
   (expect Winbond `W25Q128.V` 16 MiB). No game running anywhere, board SSH-reachable check
   N/A (board is down since P0 obs#1).
2. Pre-write full capture: `-r evidence/programmer/reads/20260923/prewrite-<tag>.bin`;
   hash it; RECORD which image the chip actually holds (expect af531026 per P0 obs#1).
   Any unexpected state = STOP, report.
3. Write: `-w <candidate>`; expect exit 0 + `VERIFIED`; save log.
4. Independent readback: `-r .../postwrite-<tag>.bin`; `cmp` with candidate must be
   IDENTICAL; run `firmware_audit.py` (PSP fletcher must match the candidate's value) and
   `psp_ps1_verify.py` (containers as built).
5. Disconnect programmer, battery back, ONE cold boot.
6. Observation table (fill per boot): LEDs (green blink count / static red), fan, ethernet
   link LEDs, ping, display. Do NOT repeat boot cycles; one boot per target.
7. Flash target 2 only after recording target 1's outcome.

## Outcome matrix (pre-committed, no post-hoc reinterpretation)

| Outcome                 | Meaning                      | Next                                                     |
| ----------------------- | ---------------------------- | -------------------------------------------------------- |
| V3 boots normal         | ROM does not anchor 0x09     | build rung 2 (re-sign KDB, swap 96ea7cfe, re-sign locks) |
| V3 parks                | 0x09 anchored                | V3 ladder dead; EMFI target confirmed; keep V4 result    |
| V4 boots, VCN gated     | defaults lock                | absence lane dead                                        |
| V4 boots, VCN alive     | jackpot                      | run codec test, archive everything                       |
| V4 parks                | absent required entries halt | absence lane dead                                        |
| anything + UART present | localize the park stage      | add to the wedge taxonomy                                |
