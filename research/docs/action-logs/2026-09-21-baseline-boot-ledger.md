# Action log: 2026-09-21 baseline boot and training ledger

## Intent (BEFORE report write)

- Timestamp: 2026-09-21 (Asia/Almaty, execution time to be appended from host clock).
- Actor: delegated project executor; root-owned integration.
- Target: retained user-board primary boot, kernel, training/error, BIOS-identity, and programmer readback artifacts under this repository.
- Scope: read-only audit only. Locate actual stdout/readbacks and distinguish historical board evidence, donor firmware, and current-vs-historical state. No board reconnect, network access, programmer transaction, firmware/NVRAM/register write, or hardware change.
- Existing route: reuse retained `evidence/runtime/`, `evidence/programmer/reads/`, dated action logs, `memory/project-state.md`, and `docs/research/2026-09-19-oc-baseline-identity.md`; do not create a duplicate parser or hash ledger for ROM sources.
- Expected effect: one factual report `docs/research/2026-09-21-baseline-boot-ledger.md` with fact -> primary path -> time -> firmware identity -> evidence class, including BIOS revision, fallback/errors, clock observations, and current-vs-historical boundaries.
- Safety: avoid copying hostname/IP/account names or credentials; inspect only non-sensitive fields from retained logs.
- Rollback: remove only the new report and this action log if a material provenance error is found; all source evidence remains unchanged.

## Observed result (AFTER report write)

- Timestamp: 2026-09-21T03:49:42+05:00 Asia/Almaty (host clock; report readback completed after this time).
- Read-only evidence sweep reopened `memory/INDEX.md`, `memory/project-state.md`, `memory/decisions.md`, `memory/corpus.md`, `memory/evidence-model.md`, the focused `bc250-reverse-engineering` skill, and `docs/knowledge-sources.md`; no hardware, network, programmer, NVRAM, or register operation was attempted.
- Primary output reviewed: `evidence/runtime/20260918-w7/baseline.json`; W9/S9 `dmesg.txt` and its duplicate `dmesg-boot1.txt`; W10 `dmesg.txt` and `cpuinfo.txt`; W12-mode2 partial `dmesg.txt`; T1 action-log/readback references; the 2026-09-12 D10R/mode1 PP/DPM action-log output; latest W11 readback references and the 2026-09-21 ROM provenance result.
- Direct `sha256sum` on the six retained runtime text/JSON files produced the non-ROM hashes recorded in the report. W9/S9 `dmesg.txt` and `dmesg-boot1.txt` compare byte-identically (`cmp -s` exit `0`), so they are one captured log, not two independent boots.
- Exact `grep` checks reproduced the P5.00 DMI strings (W9/W10) and the same string in W12 warning stack frames; the W9/W10 prior-reset parity text; the W10 8-core/16-thread CPU count; W12 VCN `mmUVD_PGFSM_STATUS` / ring `-110` / GPU probe failure; and W9/W10 AMDGPU fence fallback lines. A bounded memory-error grep returned exit `1` in all three kernel logs; the broader EDAC term search found only `EDAC MC: Ver: 3.0.0` for W9/W10, not a corrected/uncorrected error record. The W9/W10 `tsc` values are CPU time-source calibrations, not memory clocks.
- The 2026-09-12 action-log PP/DPM value `pp_dpm_mclk: 450` is retained as an older D10R/mode1 software-reported observation; the source document contains a date/time conflict between its title and PP/DPM subsection, and no separate raw PP/DPM stdout file was identified in the inspected runtime inventory. No physical-clock interpretation is made.
- T1 evidence supports only this sequence: the 1750 request byte `0x23` was on the flashed T1 image, firmware later wrote it back to `0xFF` (Auto), and the operator confirmed that run reached Linux. The source itself leaves range rejection, training fallback, and POST/default restoration open. No training diagnostic or measured memory clock distinguishes them.
- Identity cross-check: `docs/research/2026-09-19-oc-baseline-identity.md` says W10-to-cpuinfo image identity is unestablished and the W9-labelled candidate is not the original W9 readback. The separate latest readback is W11-labelled. Its SPI-layer identity does not establish a successful W11 boot. The last retained reachability status is from 2026-09-20; the present board/chip state remains unverified.
- Report created and reopened: `docs/research/2026-09-21-baseline-boot-ledger.md`; observed size 12,384 bytes; final SHA-256 `105214926ad00762feab06a0f906e0a53505b5c867c5405031ba31ead866d8e4`.
- Correction during review: an initially added contextual pointer to `evidence/runtime/20260912-mode1-probe-boot-journal.txt` was removed because it belonged to a different earlier boot than the D10R PP/DPM action-log session. The D10R row now cites only its own action log and records the timestamp conflict.
- Checks: requested boot-evidence audit PASSED at the retained-file/report layer; actual present board identity, current NVRAM, pre-OS training behavior, physical memory clocks, and current runtime remain UNVERIFIED/UNRUN. No source file, ROM, or other shared artifact was changed.
- Rollback: delete only this report and this action log; all primary evidence remains untouched.
