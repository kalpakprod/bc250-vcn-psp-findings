# CLV native-sync semantic gate audit — intent

Timestamp: 2026-09-20T11:31:02+05:00 (+05:00; intent written before execution)
Actor: luna xhigh bounded executor
Target: conditional native-sync specification `docs/research/20260920-clv-sync-conditional-candidate-spec.md`, pinned CLV donor, exact native IFR/menu and serializer evidence.

Bounded action: perform a read-only offline semantic gate audit of the proposed four-byte template (`AmdSetup+0x316`, `+0x330`, `+0x704`, with `+0x703` asserted unchanged). Reopen exact native defaults/IFR/help, serializer/token ownership and existing verifiers; build a requirement-by-requirement matrix; determine whether the template is internally coherent or remains blocked by consumer, unit/rate, UclkDiv1M0/crossing, Memory-P-state/training, and precedence uncertainties. No ROM build, candidate write, firmware/settings/globalconfig/MCP change, installation, network or hardware operation.

Expected effect: create only this uniquely named evidence directory, report and append-only action log. Verifier reruns may rewrite only their own deterministic existing result files; hashes will be compared before/after and restored if they differ. All generated output remains under this evidence directory or `/tmp`.

Rollback: delete only this evidence directory, report and action log; restore any existing verifier result byte-for-byte if a rerun changes it. No firmware or source rollback is needed.

## Observed gate audit result

Timestamp: 2026-09-20T11:45:52+05:00 (+05:00).

Executed bounded read-only audit on the exact clv target and existing evidence; no build or hardware action was run. The target was confirmed as 16,777,216 bytes with SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`. Fresh results:

- `configuration_domain_matrix.py`: exit 0, `44/44 PASS`.
- `stage2_defaults_verify.py`: exit 0, `72/72 PASS`, browser callback remains `STATIC_ONLY_CALLBACK_NOT_EXECUTED`.
- `memory_pstate_verify.py`: exit 0, rerun `9862/9862 PASS`; result was restored from retained superseded copy to manifest-pinned SHA-256 `237546fe5cc4edf44659dab93ce2ccd13ecbd817a6808ef18fa599b1da0b87c7`.
- `discrimination_verify.py`: exit 0, rerun `22/22 PASS`; result was restored from retained superseded copy to manifest-pinned SHA-256 `5f19242d614102ff92391753a3459ff7a57357adbc95c19cec8b05e7057f4eb9`.
- `uclk_semantics_verify.py`: exit 0, `31/31 PASS`; no exact-clv ratio assignment is established.
- `token_matrix_verify.py`: exit 0, `45/45 PASS`.
- `record_ownership_verify.py`: exit 0, `12/12 PASS`; corrected `+0x6A3 -> token 0x1331`.
- `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_clv_oc_builder.py' -v`: exit 0, `7/7 PASS`; test includes rejection of unsupported `sync`, voltage, and frequency profiles; temporary outputs only.
- `scripts/nvar_audit.py` exact-ROM default-window run: exit 0, 42 records, **0 selected `AmdSetup` records**. This negative default-window result was not used as positive evidence; direct pinned-ROM bytes and focused existing verifiers supply the field table.
- `native_gate_audit.py`: exit 0; matrix `BLOCKED`, 12 rows: 3 PASS / 1 PARTIAL / 6 BLOCKED / 2 UNRUN.

New F1 is a closure condition rather than a proven firmware rejection: the four potential changed bytes are exactly `0x7E5`, `0x7FF`, `0xBD3`, `0xBD4`; `0xBD2` (`+0x703`) is assert-only and is **not** part of the change count. Under an interpretation that native help is a required precondition, `+0x36D=0x00` adds the fifth changed field at `0x83C`; absent such an interpretation, the four-byte placeholder still is not build-ready because the Auto behavior/consumer/training relation is unresolved. No assertion that five bytes is required unconditionally is made.

Worker evidence integrity: existing `SHA256SUMS.final` checks in the Memory-P-state and discrimination directories returned exit 1 because the current verifier scripts do not match their pinned historical script hashes; each result JSON did match its manifest and was restored to its manifest hash after rerun. No existing worker result remains altered. The mismatch is a recorded artifact-integrity qualification, not a firmware semantic result.

Owned output paths:

- `docs/research/20260920-clv-sync-native-gate-audit.md`
- `evidence/firmware-audit/20260920-clv-sync-native-gate-audit/`

Post-action rollback: remove only those three uniquely owned outputs (report, this log, evidence directory). No plan, shared memory, firmware, candidate, builder, existing worker result, or hardware state requires rollback.

## Final readback

Timestamp: 2026-09-20T11:46:33+05:00 (+05:00). Reopened the report, action log, machine matrix, verifier, and evidence manifest at their absolute project paths. `sha256sum -c evidence/firmware-audit/20260920-clv-sync-native-gate-audit/SHA256SUMS.final` returned `OK` for all 45 entries. The exact CLV donor remains `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; restored worker-owned Memory-P-state and discrimination result hashes equal their prior manifest entries. No source, plan, candidate, ROM, board, or shared-memory change occurred.
