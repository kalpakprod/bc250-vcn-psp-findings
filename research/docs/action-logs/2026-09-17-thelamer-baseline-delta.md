# Action log: thelamer/bc250-vcn baseline verification

Date: 2026-09-17 (UTC). Actor: root. Target: repository records only.

## Intent (BEFORE writes)
Operator anchor: https://github.com/thelamer/bc250-vcn as the initial state;
verify the project is genuinely advancing the unlock from it and not
drifting. Plan: clone to /tmp, hash HEAD, diff against the local imported
copy, map its five open threads to current evidence, adopt unmined leads
into the campaign checklist. No firmware or hardware action.

## Result (AFTER writes)
- Cloned to /tmp/bc250-vcn-ref; HEAD `e53aa40d8a51c11a1a0fa939928164938924c4b0`
  (2026-08-18, single "initial notes" commit, README-only, no license).
- Local corpus copy `upstream/thelamer-bc250-vcn/README.md` is byte-identical
  to GitHub HEAD — provenance closed; the project demonstrably started from
  this exact state.
- Delta recorded: `docs/research/2026-09-17-thelamer-baseline-delta.md`
  (threads #1-#5 -> closed/partial/blocked-with-cause; new verified results
  beyond baseline; adopted leads).
- Campaign spec §6 checklist extended:
  `specs/2026-09-17-vcn-fclk-mem-campaign.md` (v2000a chain comparison,
  8c-unlock runtime rung incl. ACPI-table graft, feature-bit naming,
  collective Ghidra reuse for V1).
- Rollback: revert the two files (uncommitted). /tmp clone disposable.

## Checks (G9)
- README identity: PASSED (diff empty).
- Thread-status mapping: every row cites a dated hardware-verified or
  static-analysis record already in memory/logs.
- Adopted leads marked as leads (unrun), not findings.
