# Action log: 4700S campaign recursive error audit

Date: 2026-09-17 (UTC). Actor: root. Target: repository records only.

## Intent (BEFORE report/memory writes)
Operator order: "рекурсивно ищи все совершенные ошибки и почему до сих пор
у нас нет результата" (recursively find every committed error and why there
is still no result). New datum first: M6 cold boot = LED static red, fans
spinning, ping 100% loss (operator, 2026-09-17) — true-silence class per the
M5-established oracle.

Scope of audit (read-only evidence sweep):
- `docs/action-logs/2026-09-16-m0-window.md` (full, 588 lines)
- `docs/action-logs/2026-09-16-phase2-board-diff.md` (GO memo)
- `docs/action-logs/2026-09-16-deep-research.md` + worker registry
- `memory/incidents/2026-09-16-m0-framing-correction.md`,
  `memory/incidents/2026-09-16-vcn-exclusion-misread.md`
- `memory/project-state.md`, `memory/decisions.md` (D19-D23),
  `memory/firmware-audit.md` (to end), `memory/open-questions.md`
- `specs/2026-09-16-4700s-base-campaign-plan.md`,
  `specs/2026-09-16-trackb-t1-memclk.md`
- Fresh byte checks this session: BHD 0xAB0000 byte-identical across
  C0A-stock / native pre-m0 / M2full (APCB size is self-describing at
  APCB+8; the M2full builder needed no BHD repoint — hypothesis disproved).

Planned writes: `docs/research/2026-09-17-campaign-error-audit.md` (the
register + forward decision tree), updates to `memory/project-state.md`
(campaign end-state), this log. No firmware, candidate, or hardware action.

## Result (AFTER writes)
- Report written: `docs/research/2026-09-17-campaign-error-audit.md`
  (error register L0-L4 with evidence, causal chain for "no result",
  forward decision tree R0 -> goal rungs on the native base).
- `memory/project-state.md` appended: campaign end-state section
  (supersedes the stale "awaiting M2-full boot" line).
- Rollback: revert the two files from git working tree (uncommitted;
  no history rewritten). No other changes.

## Checks (G9)
- All register entries cite log/memory lines or fresh byte checks: PASSED
  (own reads this session).
- Forward plan: PROPOSED only; every flash rung stays behind the operator
  exact-text approval gate (G4) and the P0 protocol (LED oracle + 5-min
  wait + ping/SSH).
- Remaining uncertainty: the C0A-PSP halt mechanism inside the PSP chain
  (ROM/BL/ABL/TOS locus) is UNRESOLVED; the register records candidate
  mechanisms and their discriminators, not a verified cause.
