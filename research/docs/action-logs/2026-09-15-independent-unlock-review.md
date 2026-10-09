# 2026-09-15 — independent unlock review update

## Intent

- Actor: `sol-reviewer`.
- Target: `BC250_UNLOCK_REVIEW_2026-09-15.md` and task-local
  `.orchestra/tasks/4/TODO.md` in the review worktree.
- Procedure: review the PEI track at exact HEAD
  `aaec2dffed418d1b1b45b736436311bf452926fa`, reconcile its report, KB,
  and task evidence against the read-only project evidence root, then update
  the version-pinned verdict and preserve deferred checks.
- Rationale: add the newly completed PEI track and correct evidence calibration
  in the prior review.
- Expected effect: documentation only; no firmware image, mailbox, register,
  programmer, board, or external service change.
- Rollback: revert the review commit; no hardware recovery is required.
- Remaining uncertainty before the update: PEI target encoding, PEI module
  replacement acceptance, ASSERT enforcement semantics, `$IDS` producer, and
  hardware VCN behavior remain unverified.

## Observed result

- Runtime HEAD `d402163af175b1f3ca1bf896bdf3960c910f4751` corrects the
  stage4-label, D-R1 scope, and H1-falsifier defects identified in `cb92048`.
- PEI HEAD `aaec2dffed418d1b1b45b736436311bf452926fa` reproduces exact
  input hashes and several static relationships, but misattributes the 0193
  `0x14A35`/`0x14B1F` listing to 0196, assumes ASSERT calls enforce rejection,
  and promotes DXE-only replacement acceptance to PEI modifiability.
- The review and task-local TODO were updated. No firmware/hardware operation
  occurred. Rollback remains a revert of this documentation-only commit.

## UEFI interim review result

- UEFI HEAD `fa34af718082cf9ee8dd62691be46c025890316c` was reviewed at
  its exact report, action-log, task, and KB paths. It is not accepted pending
  the author's corrected HEAD.
- Direct checks reproduce the dated read-a/read-b identity and 234-module
  extraction. Exact re-extraction gives 0196 SHA-256 `51d96c1e...`; inventories
  identify the report's `c5b99650...` as 0189 `AmdFabricAriPei`, proving a
  module-attribution error rather than a readback delta.
- Shell observation cannot establish PEI/DXE ownership; stage4 reads do not
  prove a closed bridge; inspected source is not proven equivalent to each
  supplied EFI binary; and the proposed MMIO read must abort if MSE/BAR/aperture
  prerequisites fail.
- No probe was built or executed. No firmware or hardware state changed.

## UEFI corrected review result

- UEFI HEAD `b780ff0b49beaceaf3e6519681434d8d46b2f0ba` was read in full
  at its report, action-log, task research/TODO, and KB paths.
- The Shell-observation hypothesis, stage4 evidence boundary, EFI
  source/binary provenance, dated-readback scope, 0189/0196 manifest identity,
  and MSE/BAR-bound probe prerequisites are corrected.
- Offline evidence/probe-constraint review PASS. Hardware observation and any
  VCN unlock remain INCONCLUSIVE/UNRUN; no probe was built or executed.
- Residual calibration: the report's “bridge-control timing boundary is
  earlier” sentence is an inference. PEI programming and later DXE
  writes/locking do not identify the decisive VCN bridge owner or target.

## PEI corrected review result

- PEI HEAD `999a6115bf0aebd73aa129f433fa702a27e29dac` was read in full
  at its report, KB, task research/TODO, and action-log paths.
- The exact 0196 attribution, unresolved ASSERT semantics, and unverified PEI
  replacement acceptance are corrected. Static evidence review PASS; PEI
  acceptance and working unlock remain INCONCLUSIVE/UNRUN.
- The V1 route remains blocked: segment-3 supplies no target list and the 56
  segment-9/HWID-12 writes have unresolved PEI encoding/reachability.

## Reporting correction

- Two WIP messages prewrote commit identities before reading the corresponding
  `git commit` result; those handwritten identities were wrong. Direct
  `git rev-parse HEAD` established the actual current WIP identity.
- Final handoff procedure: finish all artifact edits and commits first, then
  capture unedited output from `git rev-parse HEAD`, `git status --porcelain`,
  and the review-artifact `sha256sum` into one external `/tmp` evidence file.
  Send the file path instead of retyping hashes. Do not create another commit
  merely to record its own identity.

## Final verification and pre-mortem

- PASS: all exact runtime, PEI, and UEFI report/action-log/task/KB paths exist;
  their pinned worktrees are clean at `d402163af175b1f3ca1bf896bdf3960c910f4751`,
  `999a6115bf0aebd73aa129f433fa702a27e29dac`, and
  `b780ff0b49beaceaf3e6519681434d8d46b2f0ba` respectively.
- PASS: independent re-hash confirms the matched 2026-09-14 reads and exact
  0196 hash; the review preserves 0189/0196 identity separation.
- PASS: `git diff --check`; stale stage4 labels are used only as retracted
  terms, the ROM checksum mismatch is not promoted to non-bootability, and
  superseded report versions remain explicitly identified.
- Pre-mortem: plausible downstream regressions are treating a static PASS as
  hardware authorization, losing the unresolved checks, or applying offsets
  across different module identities. The report counters these with scoped
  verdicts, `.orchestra/tasks/4/TODO.md`, exact hashes, and explicit no-flash/
  no-probe disposition. No secret values or raw security material were added.
- Unverified by design: D-R1, PEI replacement acceptance, UEFI binary/source
  equivalence and Shell timing, live chip/BAR state, PSP transform, bridge
  transition, VCN rings/codecs/stability, and all proposed hardware tests.
- Review route: no additional model review was launched; this task is the
  independent review and the coordinator explicitly prohibited another
  reviewer. Acceptance rests on the direct checks recorded above.

Relocation note (2026-09-27): the original root report now resides at docs/research/2026-09-15-independent-unlock-review.md, bytes unchanged.
