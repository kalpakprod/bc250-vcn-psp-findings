# G7 correction: item-17 listing verifier launch and output binding

Date: 2026-09-21. Scope: offline continuation of the independent SVC #6 reachability review.

## Failed assumptions and observed corrections

- Initial dispatcher selection searched case-sensitively for `0x6D20`; the bound verifier uses lowercase `0x6d20`. It reported no verifier candidates and exited `1`, without a patch. The exact verifier path was subsequently bound from the preserved traceback.
- After correcting the mnemonic expectation from `pop.w` to `pop`, direct execution exited `1` with `NameError: OUT is not defined` at the result-output line. The output directory binding was missing from verifier source.
- A wrapper retry exited `1` with `NameError: sys is not defined` because it referenced `sys.argv` without importing `sys`. That wrapper approach was abandoned; the source was minimally corrected to set `OUT=BASE` and run directly.
- A report-transaction preflight exited `1` with `KeyError: 'direct_svc_callsites'` because the key is in captured summary stdout, not top-level result JSON. This harness error happened before any write; the corrected check reads stdout separately.
- A second inline transaction harness failed to parse with `SyntaxError: invalid syntax` (exit `1`) while constructing a triple-quoted f-string. No Python body ran and no project write occurred; the method was changed to a standalone temporary script.

## Corrective method and evidence

- Final invocation: `/usr/bin/python3 -B evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/reachability/verify_item17_gate_listing.py`. Observed status `PASS`, 83/83 checks, stderr empty, exit `0`; stdout and JSON are retained under `evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/reachability`.
- The selected conditional path bypasses the three direct SVC-wrapper callsites and reaches a data-dependent `BLX R0` callback table; global SVC #6 reachability remains unresolved. Prior conditional base `0x57100` and item-17 mapping are reused, not rechecked.
- Failed predicate/invocation outputs remain in the evidence directory. No item-17 table mapping was repeated; no raw-byte verifier was retried; no ROM/firmware/hardware operation occurred.

## Boundary

This is observed-bytes/static-analysis evidence on the pinned CLV ABL1 only. It does not identify callback targets or the external SVC handler, and does not establish a clock-register write, physical clock, or 1800 MHz application.

## Final-QA correction (2026-09-21)

The first final readback used an over-specific expected sentence and exited 1; the report's exact wording correctly says the result does not prove global SVC #6 unreachability. A changed, wording-grounded QA command passed all role, result, diff-reconstruction, baseline, modified, and rollback checks. This was a QA predicate mismatch, not an evidence or report failure.
