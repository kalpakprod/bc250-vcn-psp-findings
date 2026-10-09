# Fallback descriptor map relation — intent

- Timestamp: 2026-09-20T14:10:00+05:00 (Asia/Almaty; exact result time to be appended)
- Actor: Codex subagent `/root/candidate_gate_semantics`
- Scope: read-only comparison of the exact fallback nested descriptor `0x006F47C0` (low12 `0x7C0`, bits6..11 `31`) against existing exact SMN/aperture map evidence, plus a direct check whether native `AmdSetup+0x703/+0x704` candidate fields can be shown to reach the ABL1 `0x61E` descriptor path.
- Inputs: exact ABL1 payload/listing, final descriptor-join result, final conditional map-correlation result, exact CLV native token matrix/consumer result, and `docs/research/2026-09-20-oc-df-init-route.md`. No source bytes may change.
- Planned check: assert raw fallback literals and descriptor bitfields; calculate all kind-1 addresses from low12 `0x7C0` and byte49; compare only to byte-backed map addresses `0x5027C/0x5227C`; search exact ABL1 for native token literals `0x1373/0x1374` and trace observed `#0x703` uses to their local helper without equating namespaces. Record whether +0x703/+0x704 reaches token/index `0x61E`.
- Expected effect: a new evidence result/report/action log only. No ROM/candidate, firmware, hardware, settings, shared plan, MCP/global config, installation, commit, or child-agent action.
- Rollback: remove only this owned evidence directory/report/action log; preserve all prior artifacts and original bytes.

## Verification correction

- First verifier run exited `1` because two Thumb halfword stores were entered in listing order rather than exact little-endian payload order (`0xC210` raw `0260`; `0xCC22` raw `8850`). No source bytes changed.
- Correction changes only verifier byte expectations; descriptor/map interpretation is unchanged.
- Second verifier run exited `1` on one longer kind-4 window due another listing-halfword byte-order expectation (`0x9CCE` raw begins `44f4e034a4e7`). No source bytes changed.
- Correction changes only this raw-byte expectation.

## Result

- Timestamp: 2026-09-20T14:32:00+05:00 (Asia/Almaty; host time correction to follow)
- Command: `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-native-gate-fallback-map/verify_fallback_map_and_native_reach.py > evidence/firmware-audit/20260920-native-gate-fallback-map/verifier.stdout 2> evidence/firmware-audit/20260920-native-gate-fallback-map/verifier.stderr; printf '%s\\n' "$?" > evidence/firmware-audit/20260920-native-gate-fallback-map/verifier.exit`
- Observed exit `0`; `57/57` checks passed; stderr empty; result status `BLOCKED_NO_MAP_OR_NATIVE_REACH`.
- Direct finding: fallback `0x006F47C0` has low12 `0x7C0`, low six `0`; exact known map bases `0x5027C/0x5227C` have low six `0x3C`; kind-1 constructions produce `0x507C0/0x527C0` for byte49 `0/1`, not the known map bases. No exact map relation is promoted.
- Direct native-reach finding: native fields are `$INV 0x1373/0x1374`; ABL1 local `#0x703` at `0xA57E` calls helper `0x4830`, no `#0x704/0x1373/0x1374` immediates are decoded, and no direct edge reaches `BL 0x10958`. No bridge to fallback table `0x61E/0x6CA` is established.
- Report: `docs/research/2026-09-20-native-gate-fallback-map.md`, SHA-256 `12665bb6a6dda2a2b38955943879a76cc43b6048f7f447e1330cc75069051fcd`.
- Machine result: `evidence/firmware-audit/20260920-native-gate-fallback-map/fallback-map-result.json`.
- No ROM/candidate, firmware, settings, hardware, shared plan, MCP/global state, installation, commit, or child-agent action changed.
- Remaining uncertainty: dynamic context+0x40 merge, active HEAP/fallback selection, SVC#4 translation, and any indirect bridge from native UEFI records to ABL1 token 0x61E.

## Timestamp correction

- Host time observed after result append: `2026-09-20T14:24:53+05:00`; this supersedes the approximate result timestamp above. Evidence and command outcome are unchanged.
