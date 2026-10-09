# Task 7 — target-board capture/tool readiness audit

## Intent — 2026-09-21T03:22:25+05:00

Actor: Task 7 worker, root-directed. Confirmed project root with `pwd` as `/home/OWNER/orca/projects/bc250`.

Requested scope: audit existing capture/verification procedures and saved outputs for distinguishing an authorized BC-250 board from the analysis workstation; identify reusable offline raw-dump and NVRAM tools; assess only via `--help` and static source inspection. No board connection, live telemetry capture, probe, firmware/NVRAM/register write, package install, or broad private-home scan is permitted or planned.

Planned read-only procedures: inspect the existing clock telemetry runbook, performance capture sheet, root scripts and tests, saved fixture-verification output, and named board-readback reports; inspect source/CLI help for existing offline dump/NVAR analyzers. New artifact targets are `docs/research/2026-09-21-baseline-tools-ledger.md` and this log. Expected result is an evidence-bounded inventory and recommendation that labels host observations as host-only. No existing project/source/evidence input will be modified. Rollback: remove only the new report and this log if their contents are incorrect; do not alter preserved captures, tool outputs, or source scripts.

## Worker registry (seven technical tracks named from the supplied research brief)

This registry records topic slots, not additional worker dispatch receipts. Root retains task assignment/integration ownership; this worker has direct evidence only for Track 7.

| Track | Topic                                                                                      | Owner / status in this log                                              |
| ----- | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| 1     | Historical/current BC-250 hardware baseline and artifact identity                          | Root-coordinated sibling task; owner/result not verified by this worker |
| 2     | MCLK/UCLK/FCLK relationship and native synchronization controls                            | Root-coordinated sibling task; owner/result not verified by this worker |
| 3     | SoC 1.15 V request and actual SoC control path                                             | Root-coordinated sibling task; owner/result not verified by this worker |
| 4     | PUS1/RT8237E versus PUA1/ISL69247 board-level rail mapping                                 | Root-coordinated sibling task; owner/result not verified by this worker |
| 5     | Voltage offset/fixed-voltage fields and actual firmware consumers                          | Root-coordinated sibling task; owner/result not verified by this worker |
| 6     | Vendor/BC-250 voltage, frequency, and safety guidance                                      | Root-coordinated sibling task; owner/result not verified by this worker |
| 7     | Existing target-vs-workstation capture procedures and offline raw-dump/NVAR tool readiness | Assigned to this worker; in progress                                    |

## G7 correction — `--help` on the clock script executed a host probe

While checking CLI help, `python3 scripts/probe_bc250_clocks_readonly.py --help` exited `0` but this script has no argument parser; it unconditionally ran its read-only collection path and printed local workstation metadata. This was an unintended workstation-only probe, not a BC-250 connection: the output identified the local `card1` as non-target device `0x1900`, emitted no matching cards, and made no firmware, NVRAM, register, network, or board access. It also read `/proc/cmdline` and DMI files before output; their contents are intentionally not recopied here. The mistake disproves the assumption that `--help` is safe for this no-CLI script. All later checks must use static inspection for it; only argparse-backed scripts may be queried with `--help` after confirming parsing occurs before effects. Per the assignment's no-shared-memory-edit boundary, this worker records the correction here and asks root to promote it into the applicable memory/incident record before any further project investigation.

## Authorized G7 incident record and final result — 2026-09-21T03:50:54+05:00

Root authorized this worker as sole writer of the new path `memory/incidents/2026-09-21-readonly-probe-help-side-effect.md` only; no existing memory file was edited. The incident record preserves the error and output boundary without copying command-line or DMI values.

Completed the static/read-only tool ledger at `docs/research/2026-09-21-baseline-tools-ledger.md`. Reopened/checks:

- Report exists (88 lines, 14,359 bytes), SHA-256 `ed2f07aecfa09ab6158ec0e99f6f201208dd35b5796cb330748dad769e8e6da6`.
- New incident exists (19 lines, 2,152 bytes), SHA-256 `e7b696b609b06fa0277f92f947e33542bccf222d70cc87a050539b40790bd740`.
- This action log is being appended after both writes; no input image, existing script, test, runbook, saved result, or existing memory file was changed.
- Parser-first help invocations returned status `0` for `firmware_audit.py`, `nvar_audit.py`, `apcb_detail.py`, `collect_stock_runtime_readonly.py`, and `measure_bc250_perf.py`. The clock script was **not** invoked again; its parserless entrypoint was inspected statically.
- Existing synthetic capture output and saved NVAR reports were inspected, not rerun. The offline full-dump/NVAR/APCB command shapes are available; for AmdSetup analysis of a full SPI image, the stored reports demonstrate why its `nvar_audit.py` default `0x1000` start is insufficient, while the prior `dump-2-nvar-primary.json` uses offset `0`/length `0x10000`.
- No current board capture, physical memory clock, voltage, performance, training, or stability result was produced. No board/network access, install, or firmware/NVRAM/register action occurred; no raw workstation metadata was saved in the report or incident.

Status: requested tool-readiness audit completed with the incident exception recorded. Rollback, if the research report is rejected, removes only the new report and this task log; the G7 incident record is retained as a correction unless root explicitly supersedes it. All source/capture artifacts remain unchanged.
