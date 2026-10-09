# Native candidate-readiness review — intent

- Timestamp: 2026-09-20T00:00:00+06:00 (Asia/Almaty; exact wall clock to be appended in result)
- Actor: Codex subagent `/root/candidate_gate_semantics`
- Scope: read-only readiness assessment for a minimal offline semantic experiment on exact CLV; trace the exact ABL1 SVC#4 mapped-register caller contract, bind it to native `AmdSetup` fields and serializer records, and enumerate pre-build gates.
- Target baseline: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`; no source bytes may be changed.
- Inputs: existing native-gate follow-up (46/46), conditional candidate specification, exact SVC#4 mapping evidence, exact callback/target semantics evidence, native field/serializer result artifacts, and existing defaults/consumer reports.
- Planned procedure: run only read-only verifiers and a new deterministic matrix verifier that hashes and reopens the named artifacts, checks direct byte-backed field values and canonical serializer IDs, and records the SVC#4 resolved/unknown boundaries. No candidate ROM, patch, NVRAM, settings, firmware, hardware, installation, global configuration, MCP/Cutter, or plan write is authorized.
- Expected effect: create a machine-readable readiness matrix and a report/action-log result only. The result must not claim `1:1:1`, hardware acceptance, applied defaults, physical clocks, or safety.
- Rollback: remove only `evidence/firmware-audit/20260920-native-gate-candidate-readiness/` and this report/log; preserve all pinned inputs and the original CLV bytes.

## Verification correction before result

- Timestamp: 2026-09-20T12:00:00+06:00 (exact wall clock to be replaced by final observed time)
- First readiness-verifier run exited `1` because it incorrectly expected supplemental `PhyPowerSaving +0x368` to be present in `menu-result.json`; the exact menu file does not carry that field. No output result was emitted and no input was changed.
- Correction: the verifier now treats `+0x368` as sourced from the retained exact discrimination/all-fields evidence and checks the other native fields against `menu-result.json`. This changed only the new verifier logic, not any source or candidate.
- Second verifier run exited `1` for the same class of fixture-boundary mistake: `MemoryPstate +0x36D` is also supplemental and absent from `menu-result.json`. No source or candidate bytes changed.
- Correction: skip menu assertions for both supplemental fields and rely on exact memory-pstate/all-fields results for them.
- Third verifier run exited `1` because the all-fields retained result intentionally covers six fields and omits FCLK_DPM; the FCLK_DPM canonical `+0x6A3 -> 0x1331` source is the retained 45/45 token matrix. No source or candidate bytes changed.
- Correction: use the all-fields result for six fields and the token matrix for `+0x6A3`; this preserves the canonical destination-pointer mapping.

## Result

- Timestamp: 2026-09-20T12:38:45+05:00 (Asia/Almaty)
- Commands:
  - `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-clv-abl1-svc4-mapping/verify_svc4_mapping.py > evidence/firmware-audit/20260920-native-gate-candidate-readiness/svc4.stdout 2> evidence/firmware-audit/20260920-native-gate-candidate-readiness/svc4.stderr; printf '%s\\n' "$?" > evidence/firmware-audit/20260920-native-gate-candidate-readiness/svc4.exit`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-clv-abl1-context660-target-semantics/abl1_context660_semantics_verify.py > evidence/firmware-audit/20260920-native-gate-candidate-readiness/context660.stdout 2> evidence/firmware-audit/20260920-native-gate-candidate-readiness/context660.stderr; printf '%s\\n' "$?" > evidence/firmware-audit/20260920-native-gate-candidate-readiness/context660.exit`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-native-gate-candidate-readiness/readiness_matrix_verify.py > evidence/firmware-audit/20260920-native-gate-candidate-readiness/verifier.stdout 2> evidence/firmware-audit/20260920-native-gate-candidate-readiness/verifier.stderr; printf '%s\\n' "$?" > evidence/firmware-audit/20260920-native-gate-candidate-readiness/verifier.exit`
- Observed result: SVC#4 rerun `PASS`, `59/59`, exit `0`, stderr empty; callback-target rerun `PASS`, `96/96`, exit `0`, stderr empty; readiness matrix `BLOCKED / DO_NOT_BUILD_ROM_YET`, `67/67` checks, exit `0`, stderr empty.
- Literal readiness stdout: `{"candidate_class": "semantic-experiment only; no artifact generated", "checks": {"failed": 0, "passed": 67, "total": 67}, "decision": "DO_NOT_BUILD_ROM_YET", "status": "BLOCKED"}`
- Direct finding: SVC#4 maps a caller-supplied aligned high address into a returned base used with low12, but handler/table, physical target, runtime descriptor, active callback, actuator, units, crossing and hardware behavior remain unresolved.
- Direct field finding: canonical native map is `0x7E5->0x11ED`, `0x7FF->0x1204`, `0x837->0x1237`, `0x83C->0x123C`, `0xB72->0x1331`, `0xBD2->0x1373`, `0xBD3..0xBD4->0x1374`; older `0x123D` pairing is superseded.
- Direct `0x83C` finding: baseline `FF / Auto`; native `Disabled=00`; `46/46` follow-up found no Auto-to-Disabled branch. `0x83C=00` is not observed-enforced, is only a hard-help closure branch, and is unsafe/unjustified to change now.
- Source readback: CLV size `16,777,216`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; source bytes unchanged.
- Report: `docs/research/2026-09-20-native-gate-candidate-readiness.md`, SHA-256 `af5d3b93f470df4098fb0c7df1ae8ba6c1ef6e9d32b403a354cab9b92ccea15b`.
- Owned machine result: `evidence/firmware-audit/20260920-native-gate-candidate-readiness/candidate-readiness-result.json`, SHA-256 `1ec74f3612e350ab357c53ec66bdabd82717d24dbe666374d70b4fc8b8372cfa`.
- Rollback: delete only the owned readiness evidence directory and this report/action log; preserve the pinned CLV and all prior source evidence.
- Remaining uncertainty: offline `$INV 0x1204` final consumer/actuator, SVC#4 physical mapping and active binding, units/rate, divider/crossing, FCLK_DPM precedence, Memory-P-state/training, and default migration.

## Timestamp correction

- The pre-write intent header used `+06:00`; the host-reported timezone for this run is `Asia/Almaty` at `+05:00` (observed with `date --iso-8601=seconds` at `2026-09-20T12:38:45+05:00`). The intent wall-clock placeholder is corrected here; no artifact or source claim changes.
