# ABL1 context+0x49 / +0x3B0 dataflow — intent

- Timestamp: 2026-09-20T13:20:00+05:00 (Asia/Almaty; host result time to be appended)
- Actor: Codex subagent `/root/candidate_gate_semantics`
- Scope: exact-byte follow-up limited to the source of callback context `+0x49` used by ABL1 callback `0x9AD8` address construction and callback pointer field `+0x3B0` used by helper `0x109BC`; do not revisit context `+0x44` pointer ownership or candidate-gate matrix.
- Inputs (read-only): exact ABL1 payload and exact Thumb listing. Conditional base `0x57100` may be used only for the already anchored local callback literal `0x60BD9 -> 0x9AD8`; external pointer `0x6E5082` must not be treated as a local payload address without an anchor.
- Planned check: hash inputs; assert callback `+0x49` reads/address construction, helper `+0x3B0` load/indirect-call/output-byte/store sequence, the sole direct `+0x49` writer and sole `+0x3B0` writer, and initializer literal-pool values. Determine exact field widths and whether callback R0 or output byte supplies `+0x49`.
- Expected effect: one machine-readable source/field-width result and report/action log. No ROM/candidate, firmware, hardware, settings, shared plan, MCP/global config, install, commit, or child-agent action.
- Rollback: delete only this owned evidence directory and report/action log; preserve original ABL1/listing bytes and prior context+0x44 work.

## Verification correction

- First verifier run exited `1` because Thumb listing halfwords were entered as listing order rather than exact little-endian payload bytes at `0x109C4` (`9df80410`), `0x109D8` (`d4f8b023`), and `0x109F4` (`94f84900`). No source bytes changed.
- Correction changes only verifier expectations to exact payload byte order; the semantic interpretation remains unchanged.
- Second verifier run exited `1` only because listing whitespace/tab normalization differed from the hardcoded expected line; no source bytes changed.
- Correction: normalize the census to assert one matching line containing the exact address/instruction, rather than formatting.
- Verifier refinement adds the initializer's direct call site `0x7500`, proving the initial proposed selector is `0x00`; this is an input byte, not proof that final context `+0x49` remains zero because the optional callback can overwrite it.

## Result

- Timestamp: 2026-09-20T13:42:00+05:00 (Asia/Almaty; host time to be appended)
- Command: `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-native-gate-context49-3b0/verify_context49_3b0.py > evidence/firmware-audit/20260920-native-gate-context49-3b0/verifier.stdout 2> evidence/firmware-audit/20260920-native-gate-context49-3b0/verifier.stderr; printf '%s\\n' "$?" > evidence/firmware-audit/20260920-native-gate-context49-3b0/verifier.exit`
- Observed exit `0`; `45/45` assertions passed; stderr empty; machine result status `UNRESOLVED_SOURCE`, decision `DO_NOT_ASSIGN_EXACT_CONTEXT49_VALUE_OR_LOCAL_3B0_TARGET`.
- Literal result summary: `+0x49=u8`; initializer input `0`; optional callback via `+0x3B0`; final `+0x49` unknown; `+0x3B0=u32`; literal `0x006E5082`, not local under anchored `0x57100`.
- Direct finding: helper `0x109BC` ignores callback return `R0`; it reads a byte from `[SP+4]` after the optional callback and stores that byte to `[context+0x49]`. Therefore no exact returned value can be claimed from the local bytes.
- Direct target finding: the sole direct `+0x3B0` writer is `0xC058`; pool word `0xC3D4` is `0x006E5082`; `0x006E5082-0x57100=0x68DF82`, outside the exact `0x171A0` ABL1 payload.
- Report: `docs/research/2026-09-20-native-gate-context49-3b0.md`, SHA-256 `bc0a3d407fe8c3cf076289dfc6a1c2ae3be62b235b8892d3f4fa872556c5f949`.
- Machine result: `evidence/firmware-audit/20260920-native-gate-context49-3b0/context49-3b0-result.json`.
- No ROM/candidate, firmware, settings, hardware, shared plan, MCP/global state, install, commit, or child-agent action changed.
- Remaining uncertainty: target executable mapping for `0x006E5082`, runtime gate byte `0x006E0130`, callback output, active object identity, and physical effect.

## Timestamp correction

- Host time observed immediately after result append: `2026-09-20T14:01:36+05:00`. This supersedes the approximate result timestamp above; command output and evidence are unchanged.
