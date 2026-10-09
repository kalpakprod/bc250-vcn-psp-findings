# Action log: loop 377650c2 run #2 — C3 mining, checklist closeout

Date: 2026-09-17 (UTC). Actor: root (loop run #2). No hardware action.

## Intent (BEFORE writes)
State carried from run #1 + inter-run session work: V1/V2/O4/O3/T1/O1-prep
verdicts committed (`fe3a06a`, `cb10ea5`, `e30a86f`, `17774ed`, `018adb9`,
`8a4e0a6`, `44f1273`, `1ca4cc8`); worker reports A/B/C reviewed.
Remaining authorized items: C3 (v2000a VCN power-up mining + 8c-unlock
rung documentation), V3 leftover (feature-bit naming), spec checklist
update, memory G7 corrections.
Plan: dispatch one worker (G8: worker, medium, read-only + one report
file) for C3; root updates spec checklist + memory; per-item commits.
Rollback: revert files; no hardware state exists.

## Result (AFTER)
C3 report delivered and committed: v2000a driver path assumes SMU-side
PowerUpVcn (msg 0x9) which is NULL on BC250 SMU — from the host the power-up
is impossible without the PSP release block or a patched SMU. 8c-unlock rung
documented as FV-graft surface (reversible runtime rung). Checklist in spec
updated; memory appended. Unrun: all runtime checks (operator gates).
Rollback: revert docs/spec/memory files.
