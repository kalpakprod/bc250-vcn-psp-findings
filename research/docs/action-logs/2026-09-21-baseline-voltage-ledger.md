# Baseline voltage ledger — intent

Timestamp: 2026-09-21 (Asia/Almaty). Actor: bounded project executor `baseline_voltage_history`.

Target: new `docs/research/2026-09-21-baseline-voltage-ledger.md` and this task-owned action log only. Project root confirmed as `/home/OWNER/orca/projects/bc250`.

Question: audit retained physical-board voltage/telemetry records and historical participant voltage reports, with exact dates, board/firmware identity where available, and method. Determine whether a board-instrumented SoC `1.15 V` or exact rail measurement exists without treating one sanitized report as an absence proof. Separate physical feedback modification from BIOS offset/setpoint evidence.

Inputs: `memory/INDEX.md`, `memory/corpus.md`, `memory/evidence-model.md`, `memory/oc-recheck.md`, `memory/project-state.md`, applicable instincts, the supplied attachment, the sanitized report `docs/research/2026-09-20-chat-voltage-evidence-luna.md`, prior sanitized chat provenance `docs/research/2026-09-17-chat-export-20260904-05.md`, retained runtime logs under `evidence/runtime/`, voltage producer/consumer reports, and current PUS1/rail reports. Raw chat exports, access-bearing URLs, credentials, and private material are excluded.

Method: read-only inventory and selective source review; search curated `docs/research/`, `docs/action-logs/`, `memory/`, `evidence/runtime/`, `evidence/boardview/`, and named retained artifacts for instrument/measurement/rail/SoC terms; re-read the exact table-6 binary and mode2 telemetry log; compute hashes and parse only the voltage fields required for the ledger. No web search, firmware/NVRAM/register/board write, hardware probe, or shared memory update.

Expected effect: one English ledger with a bounded evidence table, explicit coverage/limits, and no voltage recommendation. Rollback: delete only this report and this action log; originals remain untouched.

## Observed result — 2026-09-21 (Asia/Almaty)

Created and reopened `docs/research/2026-09-21-baseline-voltage-ledger.md`; SHA-256 `06feaa99675064a35c5f325c938e64526d9abe236169d3f19cb5452401466080`. It records the historical participant messages separately from board-runtime firmware telemetry, static BIOS controls, and boardview evidence. No raw chat export, access-bearing URL, credential, or private material was copied.

Read-only checks:

- Recomputed source hashes for the sanitized chat reports, voltage producer reports, mode1 runtime audit, mode2 dmesg, and table-6 binary; values are recorded in the ledger.
- Parsed `evidence/runtime/20260913-quiesced-metrics-table6-244B.bin` as little-endian fields: file size `262144`; offset `0x50=1275`, offset `0x54=912`; file SHA-256 `b29f56ebb6680c8389b1e3d5d62e882a6b025ae7324afa1d4a224bb5a4c4bdcb`.
- Parsed `evidence/runtime/20260912-mode2-controlled-probe-dmesg.log`: `55` `BC250-TELEMETRY` records; every `gvolt_mV` and `vddcr_vdd_mV` value is `NA`; file SHA-256 `e9c830f8f231c1e803677d4b67ad7b3154885223a7d95ac86cabddd89169c66d`.
- Reopened `docs/research/2026-09-20-chat-voltage-evidence-luna.md` and confirmed its bounded conclusion: manual feedback modification and self-reported `~1.2 V`, not an instrumented rail measurement. Reopened `docs/research/2026-09-21-voltage-evidence-integration.md` and confirmed CBS/fixed-voltage fields remain static and physically unresolved.
- No ROM, NVRAM, firmware, register, board, hardware, network, or shared-memory action occurred.

Result: **PASS** for the bounded local audit and artifact creation. No retained instrumented exact-rail/SoC `1.15 V` record was found within the stated searched scope; the board-runtime `1275/912` telemetry sample is preserved as non-instrumented firmware telemetry with unresolved rail identity. This does not establish global absence. Rollback remains deletion of only the new report and this log.

## Correction addendum — table capture file size

A fresh `stat` on `evidence/runtime/20260913-quiesced-metrics-table6-244B.bin` showed the file is `262144` bytes, not `244` bytes as its name and prior prose imply. The 2026-09-12 Q0 action log reports `244 changed bytes`, matching the expected `SmuMetrics_t` length; it does not document a 244-byte on-disk file. The report now treats the 244-byte quantity as the changed metrics payload length and states the actual file size separately. No interpretation is made of the remaining buffer bytes. Final report SHA-256: `4347ed4d9882a69a6c01c784ed7ede9eed73a5dba86b85c019751fdec89e476f`.

## Evidence-class clarification

The phrase “non-instrumented firmware telemetry” in the result paragraph means “not independently measured with an external physical-rail instrument.” The 2026-09-13 record itself is a live SMU table telemetry read from the board; channel-to-rail identity and sensor/write provenance remain unresolved.
