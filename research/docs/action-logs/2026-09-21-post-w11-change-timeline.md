# Post-W11 change timeline audit — intent and observed result

## Intent — 2026-09-21T07:51:00+05:00 (Asia/Almaty)

- Actor: project executor `/root/post_w11_change_timeline`, assigned by root.
- Target: create `docs/research/2026-09-21-post-w11-change-timeline.md`; append this action log.
- Scope: read saved project action logs/reports only to reconstruct documented post-W11 firmware, NVRAM/CMOS, and physical VRM/board changes. The operator replied `да менял` to the project's change-history question; do not infer which change this means and do not ask a new question in this pass.
- Inputs: `/home/OWNER/.codex/attachments/9d7bcc99-0793-46b7-a070-9d0a73377101/pasted-text-1.txt`; `AGENT_CONTRACT.md`; `memory/INDEX.md`; task-relevant `memory/project-state.md`, `memory/oc-recheck.md`, `memory/evidence-model.md`, `memory/decisions.md`, and applicable instincts; bounded W11, boot, NVRAM, voltage, and hardware-baseline action logs/reports under `docs/action-logs/` and `docs/research/`.
- Existing route: use the already-created dated ledgers and primary saved evidence; do not perform a corpus-wide search, hardware/programmer action, or new parser/probe.
- Expected effect: separate explicit dated records from inference; name paths, dates and hashes; state precisely whether any post-readback physical changes can be reconstructed from records, and preserve the current operator statement as an unspecified report.
- Rollback: remove only the new report and this action log if a source/date/hash reconciliation disproves the result. Do not alter source records, memory, candidate images or primary captures.
- Safety: no board contact, flash, NVRAM/CMOS/register access or modification, voltage probe, network access, raw chat export, or secret inspection.

## Observed result — 2026-09-21T07:58:56+05:00 (Asia/Almaty)

- Read the supplied task attachment, `AGENT_CONTRACT.md`, `memory/INDEX.md`, and the task-relevant project-state, OC-correction, evidence-model, decision, and instinct records to their ends. Reused the already-indexed W11 identity report, W12 boot ledger, 2026-09-20 offline-build action log, and 2026-09-21 ROM/NVRAM/voltage baseline ledgers; did not inspect raw chat exports or access secrets.
- Recomputed hashes of the decisive retained files. `/home/OWNER/orca/projects/bc250/evidence/programmer/reads/20260919/postwrite-vcn-unlock-w11-v001.bin` and its matching candidate both hash to `3c50bc9a65194b75ca805e6ed31c5778369de1fe8eca4600f44e15fae3b40fc3`; `cmp -s` exited `0`. W12 dmesg hash is `17d62f1e3b694a8a443576a964b5816642eb0a0a56182db062b2fea9f19079c1`. Source report hashes are listed in the new research report.
- `stat` observed W11 file mtime `2026-09-19 02:42:20.647188878 +0500`, size `16777216`; W12 dmesg mtime `2026-09-19 03:43:03.373835206 +0500`, size `136707`. These are filesystem mtimes only, not flash/boot event timestamps.
- Result: the selected later records identify offline candidate/report work and no specific subsequent BIOS flash, post-W11 NVRAM/CMOS readback or clear, or physical VRM/feedback change. The 2026-09-20 action log _reports_ W11 still installed but has no fresh chip readback. The only saved feedback-adjustment story is dated 2026-09-05, before W11 and without board/firmware/instrument identity. Operator's current `да менял` remains unspecified and is not resolved by saved artifacts. This is a bounded missing-record finding, not proof no change occurred.
- Created and reopened `docs/research/2026-09-21-post-w11-change-timeline.md`; final SHA-256 `9425d0ad3316b95115bb4c0745291188984a14477b1c469dd723e68fd91e3fbe`. Reopened this log and the report; line-format checks: both UTF-8, LF-terminated, zero CR; trailing-whitespace lines `0` after a formatting cleanup. No source capture, candidate, memory file, firmware, NVRAM/CMOS, register, board, or hardware state was changed.
- Verification status: report/readback/hash checks **PASS**; current installed firmware/NVRAM/CMOS/VRM state and identity of operator-reported change **UNRESOLVED**; no hardware action performed. Rollback is deletion of only this report and action log; source artifacts remain untouched.

## G7 timestamp correction — 2026-09-21

The `Intent` timestamp `07:51:00+05:00` above was typed before checking the host clock and is not a measured action time. Read-only `stat -c '%w'` records this log's first creation at `2026-09-21 07:54:45.755332399 +0500`; that creation time supersedes the typed intent timestamp. The original text is retained as a correction record. No source, evidence, or finding changed.

## G7 report-hash correction — 2026-09-21T08:05:41+05:00

The report hash in the earlier observed-result paragraph (`9425d0ad…`) was measured before the final wording/formatting cleanup and is superseded. Final reopened report SHA-256 is `2adfd230502027bc2a1bbbd08fd7588c48b88ad12037a64917412c9bf2c59a2f`. The conclusion and source evidence did not change; the report was re-opened and its hashes were recomputed.
