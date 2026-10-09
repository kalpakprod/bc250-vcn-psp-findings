# ABL1 APCB writer census (sync fork J1, executed window)

Date: 2026-09-23. Question from `2026-09-23-sync-track-consolidation.md` (next executable
action): inside the proven ABL1 native window, is there ANY writer that fills the watched
APCB offsets from a source other than CMOS / native-APCB (i.e. does an AmdSetup carrier
path reach the PLL arguments at runtime)?

Verdict: **CLOSED-NEGATIVE for the executed window.** No writer outside the known
CMOS/APCB-native paths touched the watched APCB offsets. The only watched-channel writes
in all three cases are the two stores to `nested+0x2C` (policy channel). J1's producer
join does not live inside this window.

## Method

Script: `scripts/abl1_apcb_writer_census.py` (run with
`tools/abl-emulator-venv/bin/python`, unicorn 2.1.4). Executes the proven native window
(entry `0x221D`, Thumb) from `2026-09-23-cmos-native-acceptance/native_provider.py`
verbatim, plus:

- a real APCB copy modeled at `0x7B000` (native reads enum at APCB+0x482 = SPI `AB1482`);
- a write hook that classifies EVERY memory write by target: watched APCB offsets
  (+0x482..0x484 item7, +0x86E..0x872 token21/UclkDiv, +0xB99..0xB9B DF gate/value),
  other APCB, nested+0x2C, context 0x2B0/0x278 windows, other context, stack,
  0x57100-copy region, other;
- three cases: `BASELINE_APCB` (item7=0x24, CMOS 1750), `MODIFIED_APCB_item7_0x23`
  (item7=0x23, CMOS 1650), `CMOS_ONLY_pristine_APCB` (pristine APCB, CMOS 1650).

Native guards retained from the acceptance harness: provider call must be `[7, 2]`, code
must be unmodified at exit (`mem_read(0, len(ABL1)) == ABL1`), final policy must match the
acceptance expectation (1800 / 1750 / 1800).

Evidence: `evidence/firmware-audit/20260923-abl1-apcb-writer-census/writer-census-result.json`.

## Result

All three cases PASS native guards. Watched writes per case: exactly 2, both class
`NESTED+2C` (the known policy store), values = the CMOS intermediate then the final
policy. Write-set diffs between cases contain ONLY the `nested+0x2C` final value
(`0x708`=1800 vs `0x6d6`=1750):

| case                     | final_policy | watched_writes     | other classes                     |
| ------------------------ | ------------ | ------------------ | --------------------------------- |
| BASELINE_APCB            | 1800         | 2 (nested+2C only) | STACK 194, CTX_OTHER 2, OTHER 252 |
| MODIFIED_APCB_item7_0x23 | 1750         | 2 (nested+2C only) | same                              |
| CMOS_ONLY_pristine_APCB  | 1800         | 2 (nested+2C only) | same                              |

Zero writes to the APCB copy itself in every case (the enum at +0x482 is READ by native
`0x4C16`, never written). Zero writes into the `+0x278` handler window.

## Interpretation (fork J1)

For the executed window `0x221D..0x1F000` (the proven phase-2 native provider): the
producer join is DEAD here. Everything the window writes derives from CMOS and the native
APCB read path; PLL arguments do not pass through any AmdSetup-carrier channel in this
window. Per the consolidation report's fork logic: J1 closes negative for the executed
window, and the join — if it exists — must live OUTSIDE it: either in the un-executed
part of ABL1 (entry → `0x221D` prologue) or in another module entirely. Next in the sync
plan per the consolidation's fork order: J2 (classify the type-1 PSP mailbox payload and
its unit semantics), which is untouched offline work.

## Scope and limits

- Evidence class: PROVEN-STATIC (emulation of a proven window, native guards green).
- Covers the executed window ONLY; makes no claim about the full ABL1 entry-to-window
  range or about hardware behavior.
- The 194 STACK / 252 OTHER writes are scratch (stack frames, temporaries); none alias
  the modeled APCB region (`classify()` would have tagged them).
- Census fix this session: the second-stage register setup (`R0=CTX, R1=2, SP=0x308000,
LR=END|1`) was missing before the main `emu_start`, causing UC_ERR_WRITE_UNMAPPED;
  copied verbatim from the acceptance harness, guards unchanged.
