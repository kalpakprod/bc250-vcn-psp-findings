# 2026-09-21 plain-CLV goal continuation verification — action log

## Intent — 2026-09-21T13:56:46+05:00

- Actor: delegated project executor (Luna xhigh), root-owned integration.
- Scope: reopen original objective and current target/checkpoint, then run one existing read-only parser verification against the bound plain CLV source. No hardware, firmware, NVRAM, register, network, or board operation.
- TARGET: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`; expected SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Selected completed artifact for independent corroboration: `docs/research/2026-09-20-clv-sync-stage2-memory-pstate-discrimination.md` with action log `docs/action-logs/2026-09-20-clv-sync-stage2-memory-pstate-discrimination.md`.
- Existing route: `scripts/nvar_audit.py`, source SHA-256 `16d35db736f5ca0e4423c444ff892b9d2b583bd8efcafda1a5e752ff04cb1160`. Reuse the bounded command template from `docs/action-logs/2026-09-21-baseline-nvram-ledger.md`; change only input to the bound plain CLV TARGET and output to unique `/tmp` directory `/tmp/bc250-goal-continuation-pstate-7xcq6z9y`.
- Expected check: selected `AmdSetup` NVAR fields relevant to the MCLK/P-state baseline; result proves saved bytes only, not physical clocks/training.
- Rollback: delete only this log/report and unique `/tmp` result if requested; TARGET and all existing artifact/registry files remain unchanged.

## Observed result — 2026-09-21T13:56:46+05:00

- Runner source was reviewed before execution: `scripts/nvar_audit.py` SHA-256 `16d35db736f5ca0e4423c444ff892b9d2b583bd8efcafda1a5e752ff04cb1160`; bounded argparse NVAR reader, output directed outside the repository.
- Selected completed artifact: `docs/research/2026-09-20-clv-sync-stage2-memory-pstate-discrimination.md`; action log `docs/action-logs/2026-09-20-clv-sync-stage2-memory-pstate-discrimination.md`. A machine-readable command array in its evidence directory was `not found`; used the existing NVAR command template from the baseline NVRAM action log with only target/output paths changed.
- Exact command: `["/usr/bin/python3", "-B", "scripts/nvar_audit.py", "/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin", "--store-offset", "0", "--store-length", "0x20000", "--variable", "AmdSetup", "--output", "/tmp/bc250-goal-continuation-pstate-7xcq6z9y/clv-nvar.json"]`. Literal stdout: `{"output": "/tmp/bc250-goal-continuation-pstate-7xcq6z9y/clv-nvar.json", "records": 53, "selected": 1, "errors": 0}`; stderr: ``; exit status: `0`. Output: `/tmp/bc250-goal-continuation-pstate-7xcq6z9y/clv-nvar.json`; size `24756`; SHA-256 `ddf79399db3d860a99f05ad0f5ad5e3e8e2c97cd4125a4bf15f3917551255ee3`. Field summary: `[]`.
- Result is observed saved-NVAR bytes only. It does not close token consumer, frequency units, training, physical synchronization, SoC safety/application, or performance requirements. No board/hardware/firmware changes; no registry edit.

## Field-output qualification — 2026-09-21T12:58:00+05:00 (Asia/Almaty)

- The first summary walker matched no field names because the parser stores them in the `selected_fields` list. A changed read-only command reopened only the unique JSON output and printed that list; no source or output was modified.
- Selected fields: `MemoryClockSpeed@0x316=36 (0x24)`, `UclkDiv1M0@0x330=1`, `PhyPowerSaving@0x368=255`, `MemoryPstate@0x36D=255`, `FclkDpm@0x6A3=15`, `VddcrVddOffsetControl@0x6E5=0`, `VddcrVddOffset@0x6E6=0`, `VddcrGfxOffsetControl@0x6EA=0`, `VddcrGfxOffset@0x6EB=0`, `DfClockOverrideControl@0x703=1`, `DfClockOvrd@0x704=1420`.
- New finding: the bound plain CLV target itself stores the native 1800 MHz request (`0x24`) with UclkDiv1M0 enabled, Memory P-state/FCLK_DPM Auto, DF override 1420, and zero CBS voltage offsets. This is saved-byte evidence only; no physical synchronization, training, voltage, or performance claim follows.

## Intent — ABL1 P-state input-gate verifier rerun (2026-09-21T14:39:44+05:00)

- Objective attachment re-read in full; TARGET remains `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` with verified SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Pending exact checkpoint: `docs/research/2026-09-21-pstate-precedence-next.md`; input slots `[SP+0x164]` and `[SP+0x174]`; caller/provider meanings are explicitly unknown in that report.
- Command metadata arrays were checked in the checkpoint evidence directory; none were present. Fallback runner named in the checkpoint: `evidence/firmware-audit/20260921-pstate-precedence-next/pstate_precedence_verify.py` (SHA-256 `b5d70cf67ca3c585d8dba3d09ff260d3e44fb8157c2f24b4919ac10333f31043`).
- Execute only this existing bounded verifier in a disposable clone; final evidence output path: `evidence/firmware-audit/20260921-goal-continuation-abl1-inputtrace-143944-3018034`. No 0x1204/HOB repeat, no whole-corpus scan, no firmware/hardware operation.
- Rollback: remove only this new evidence directory plus this review report/log if requested; pinned CLV and existing checkpoint remain unchanged.

## Observed result — ABL1 P-state input-gate verification (2026-09-21T14:39:44+05:00)

- Command: `["/usr/bin/python3", "-B", "/tmp/bc250-pstate-precedence-recheck-hy0pi02k/evidence/firmware-audit/20260921-pstate-precedence-next/pstate_precedence_verify.py"]`; isolated CWD `/tmp/bc250-pstate-precedence-recheck-hy0pi02k`; runner source hash `b5d70cf67ca3c585d8dba3d09ff260d3e44fb8157c2f24b4919ac10333f31043`.
- Literal stdout: `{"branch_precedence": {"slot_164_gt_1_and_slot_174_eq_0": "0x964E/0x9650 branches to 0x9746/0x9794; it gathers channel+0x20 values, calls helpers 0x118C and 0x10C0, then writes the output slot to context+0x2BC (0x981E) and each channel+0x20 (0x983C). Helper selection semantics are opaque.", "slot_164_gt_1_and_slot_174_ne_0": "Collects per-channel+0x20 values at 0x9672/0x9674; zero slave-table entries substitute 0x7D1 at 0x96E4..0x96E8; a 0x7D1-initialized current value is lowered on smaller candidates at 0x971E..0x9722; selected value is stored to context+0x2BC at 0x973E and each channel+0x20 at 0x9758.", "slot_164_le_1": "0x9644/0x9646 branches to 0x9744 then 0x984E system-master/table retrieval; the selected table value is stored to context+0x2BC at 0x989A. The bounded single-state window does not store a value to channel+0x20."}, "checks": {"failed": 0, "passed": 47, "total": 47}, "setup_raw": {"DfClockOverrideControl": 1, "DfClockOvrd": 1420, "FclkDpm": 15, "MemoryClockSpeed": 36, "MemoryPstate": 255, "UclkDiv1M0": 1}, "status": "PASS"}`; stderr: ``; exit `0`; result summary: `{"failed": 0, "passed": 47, "total": 47}`.
- Unique evidence directory: `evidence/firmware-audit/20260921-goal-continuation-abl1-inputtrace-143944-3018034`. Target CLV hash `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`. No target/firmware/hardware write.
- Verifier confirms static branch effects for input stack slots `[SP+0x164]` and `[SP+0x174]`; their producer/meaning and the `$INV 0x11ED` to ABL1 input edge remain unresolved. Next action is the bounded caller/input-construction trace stated in the report.

## Dispatcher path correction

A previous bounded attempt returned `BOUND_ABL1_REVIEW_ARTIFACT_MISSING` with wrapper exit `1` before any verifier was launched. It expected the stale/mismatched path pair `docs/research/20260920-clv-abl-memory-review.md`, `docs/action-logs/2026-09-20-clv-abl-memory-review.md`, and its evidence directory. No input or output file was written by that aborted dispatcher. The correction used the actual newest checkpoint `docs/research/2026-09-21-pstate-precedence-next.md` and its named existing verifier `pstate_precedence_verify.py`, then ran it in a unique disposable tree as logged above.
