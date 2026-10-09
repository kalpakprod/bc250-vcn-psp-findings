# Native candidate SVC#4 bridge gate — intent

- Timestamp: 2026-09-20T12:45:00+05:00 (Asia/Almaty; observed result timestamp to be appended)
- Actor: Codex subagent `/root/candidate_gate_semantics`
- Scope: one read-only discriminator after SVC#4 mapping: identify whether exact CLV bytes join the native `AmdSetup`/`$INV` request to the active ABL1 callback's runtime descriptor and its mapped SMN target; decide whether this one bridge gate can close offline from available source bytes.
- Target input: exact CLV donor `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (read-only), ABL1 decompressed payload, and existing Thumb listing. Preserve all bytes.
- Planned check: hash exact inputs and assert byte-backed load/dispatch/table/SVC sites for token `0x61E`; inspect exact nested table-load dataflow and occurrence/initialization boundary. Compare only the existing PEI direct-reader map for `$INV 0x1204`; do not repeat prior 46-check follow-up or rebuild its matrix.
- Expected effect: create a small machine-readable result plus a supplemental report documenting one blocking semantic gate and offline closure boundary. No ROM/candidate, firmware, settings, hardware, MCP/global config, install, commit, or memory change.
- Rollback: remove only the owned bridge-check evidence directory and this report/action-log; all original CLV, ABL1, and prior reports remain intact.

## Verification correction

- First verifier run exited `1` at the initializer `STR.W [R4,#0x660]` byte assertion: raw little-endian instruction bytes are `c4f86006`, not the listing-rendered halfword string `c4f86060`.
- Correction changes only the expected raw-byte encoding to match the exact payload; no input or ROM bytes changed.

## Result

- Timestamp: 2026-09-20T12:53:00+05:00 (Asia/Almaty; host time recorded below)
- Command: `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-native-gate-svc4-bridge/verify_field_to_smn_bridge.py > evidence/firmware-audit/20260920-native-gate-svc4-bridge/verifier.stdout 2> evidence/firmware-audit/20260920-native-gate-svc4-bridge/verifier.stderr; printf '%s\\n' "$?" > evidence/firmware-audit/20260920-native-gate-svc4-bridge/verifier.exit`
- Observed exit `0`; `42/42` assertions passed; stderr empty. The machine result status is `BLOCKED`, decision `HOLD_ROM_CANDIDATE_UNTIL_FIELD_TO_MAPPED_ACTUATOR_JOIN`.
- Literal stdout: `{"checks": {"failed": 0, "passed": 42, "total": 42}, "decision": "HOLD_ROM_CANDIDATE_UNTIL_FIELD_TO_MAPPED_ACTUATOR_JOIN", "single_prebuild_gate": {"acceptance": "For the candidate field (starting with Setup+0x330 / INV 0x1204), byte-backedly join its record to the actually active consumer/callback, recover the runtime +0x44 table entry and encoded descriptor, and decode the target register/field effect sufficiently to predict the candidate result.", "can_close_offline": "PARTIAL_ONLY_FROM_CURRENT_BIOS. The caller/serializer bytes are local and a static producer/table trace could identify the encoded SMN address; however current exact callback table entries and active object binding are runtime dataflow gaps, and the on-die SVC#4 handler/translation table is absent from this BIOS image. The encoded descriptor target may be closable offline if its exact producer and active registration are recovered, but the physical mapped window is not closable from this BIOS corpus alone.", "id": "G-ACT", "name": "native field -> active consumer -> runtime descriptor -> encoded SMN target (mapped actuator identity)", "why_now": "SVC#4 is a mapped-register service, so a callback descriptor can address SMN/MMIO rather than only local context; unknown descriptor therefore hides the actual write target."}, "status": "BLOCKED"}`
- Direct byte observation: CbsBasePei loads `Setup+0x330` and emits `$INV 0x1204`; the two direct exact Fabric generic-reader calls request `0x10FF`/`0x1104`; ABL1's caller token `0x61E` dynamically indexes `[context+0x44]` and nested descriptor tables; those descriptor values are not immediate at the byte-backed lookup sites. Candidate pointer installation at initializer object `+0x660` is observed, but the active dispatch object's identity with that initializer remains unresolved.
- New implementation decision: hold every ROM candidate until `G-ACT` is satisfied; close its logical encoded-target portion offline only if the exact active registration and descriptor producer are recovered. The physical mapped window is outside the current BIOS image and remains unresolvable from this corpus alone. No candidate was built.
- Target readback: CLV size `16,777,216`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; ABL1 SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`; both original inputs unchanged.
- Supplemental report: `docs/research/2026-09-20-native-gate-svc4-bridge.md`.
- Rollback: remove only this evidence directory and supplemental report/action log; preserve all source bytes and earlier readiness work.
- Remaining uncertainty: exact active callback binding, runtime descriptor-table producer/value, `$INV 0x1204` consumer/ABL1 join, decoded SMN target/field effect, physical map/window, hardware behavior.

## Timestamp correction

- The preceding result line used an approximate `12:53:00+05:00` stamp; the host time returned immediately after that append was `2026-09-20T13:05:47+05:00`. The host-reported time is authoritative for this action-log observation; command/evidence outcome is unchanged.

## Report readback

- The supplemental report was reopened after adding its explicit link to the earlier readiness report. Final report SHA-256: `9c3a15b3d0f093d54f04e0b0848e3c0fd764695e3d504770d6d236c55bfeea50`.
