# 2026-09-23: re-ranking operator-confirmed — v003-class first, deletion demoted

Intent: the operator challenged the deletion-first flash ranking («как тебе
твоё решение удалить») and ordered the lateral skill. Run assumption inversion
on the deletion decision, present the corrected ranking, and record the
operator's confirmation («подтверждаю») in the plan of record: a chat approval
is invisible to the next session.

Result:

- `.procoder/plans/psp-breach.md`: appended the section "Re-ranking
  2026-09-23 (operator-confirmed): v003-class first, deletion demoted" —
  product and first rung = v003-class (V11 driver on the FD community base,
  zero PSP-byte changes, zero deletions, `0fafe2c1` lineage, single unknown =
  boot-time mailbox acceptance); v005 (pure absence, `28cc548d`) = optional
  single-variable rung, after or never; v004 (two-variable monolith,
  `2981b252`) withdrawn from the flash queue, package and runbook retained as
  provenance only; the staged v003 package predates the Probe2/bake step and
  must not be flashed before the rebuild. sha256
  `1b81ae8905c14dd63796b66d47c8ba7f0e472c994c645e0631e37212e2ed7424`.
- `MISTAKES.md`: new top entry — a two-variable candidate was ranked as the
  primary flash target; prevention rule for flash-queue admission
  (single-variable check, inversion of the rung's assumptions, donor diff =
  hint not proof). sha256
  `91d9f39c1ddc4b0141abfe04c5614e4eb34dc7681f273a4df6bbd46ce84e8f91`.
- Plane issue #5 (PSP breach campaign): comment with the decision.
- Gates: both files above carry pre-existing local formatting styles
  (baseline scoped `procoder check` unformatted before this change; history
  untouched, only appended); this log is scoped gate-clean.
- No firmware image, board, or setting was touched. No flash performed.
