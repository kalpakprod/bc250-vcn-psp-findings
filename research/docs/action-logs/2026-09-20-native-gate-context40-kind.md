# ABL1 context+0x40 source and kind-selection capability — intent

- Timestamp: 2026-09-20T15:00:00+05:00 (Asia/Almaty; exact result time to be appended)
- Actor: Codex subagent `/root/candidate_gate_semantics`
- Scope: fresh exact-byte check of the source chain feeding callback context `+0x40`, its merge mask, and the resulting kind1..4 branch capability. Do not repeat prior descriptor-table join or broad candidate matrices.
- Inputs (read-only): exact ABL1 payload/listing, prior context+0x40 result for hash/provenance only, and prior fallback descriptor result for the raw descriptor value.
- Planned check: assert `0x7378` parent/child pointer dataflow, `[child+0x4] -> [parent+0x40]`, callback merge instructions, exact replacement mask, kind dispatch, and symbolic examples of source high bits selecting kinds1..4 while preserving low12.
- Expected effect: one machine-readable source/capability result plus report/action log. No ROM/candidate, firmware, hardware, settings, shared plan, MCP/global config, installation, commit, or child-agent action.
- Rollback: delete only this owned evidence directory/report/action log; preserve all original inputs and earlier evidence.

## Verification correction

- First verifier run exited `1` because exact LLVM listing renders payload labels as bare `7378:`/`9b82:`/`9c00:` rather than `0x...` strings. No source bytes changed.
- Correction changes only listing-presence guards to bare-address form; byte/dataflow assertions are unchanged.

## Result

- Timestamp: 2026-09-20T15:10:00+05:00 (Asia/Almaty; host correction to follow)
- Command: `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-native-gate-context40-kind/verify_context40_kind.py > evidence/firmware-audit/20260920-native-gate-context40-kind/verifier.stdout 2> evidence/firmware-audit/20260920-native-gate-context40-kind/verifier.stderr; printf '%s\\n' "$?" > evidence/firmware-audit/20260920-native-gate-context40-kind/verifier.exit`
- Observed exit `0`; `38/38` assertions passed; stderr empty; status `CAPABILITY_STATIC_RUNTIME_VALUE_UNRESOLVED`.
- Direct finding: `context+0x40 <- [[arg1+0x3C4]+0x4]` is a full-u32 source; exact merge mask `0xFFFF8000` preserves low12 and replaces high kind fields. Symbolic source values `0x08000000/0x10000000/0x18000000/0x20000000` select kinds1/2/3/4 respectively.
- Decision: kind1–4 selection is structurally possible, but actual runtime provider/value and active dispatcher object identity remain unresolved; no physical/map claim follows.
- Report: `docs/research/2026-09-20-native-gate-context40-kind.md`, SHA-256 `e7e40c9c62cba10e6f322febe0f8e1e4e5d99d940e2672c3e1ec1f30622ec11d`.
- Machine result: `evidence/firmware-audit/20260920-native-gate-context40-kind/context40-kind-result.json`.
- No ROM/candidate, firmware, hardware, settings, shared plan, MCP/global state, installation, commit, or child-agent action changed.

## Timestamp correction

- Host time observed after result append: `2026-09-20T14:57:48+05:00`; this supersedes the approximate result timestamp above. Evidence and command outcome are unchanged.
