# CLV native-sync semantic gate audit — four-byte template

> Audit 2026-09-27: read 2026-09-20-native-gate-followup.md and 2026-09-20-native-gate-candidate-readiness.md for the later help-precondition clarification. Auto not proven Disabled does not prove hardware requires a write. Four/five bytes below are possible field positions, not guaranteed changed-byte counts. MemoryPstate mapping is corrected to0x123C. Failed historical manifest checks below remain failures, not new PASS results.

## Conclusion

The conditional four-byte template is **BLOCKED** and is not internally closed for an offline native-sync candidate. No ROM or candidate was built. The exact CLV native menu gives DF override the help precondition **“FCLK > UCLK and Memory P-state is disabled”**, while the proposed template changes `+0x704` and asserts `+0x703=Manual` but deliberately leaves `+0x36D=Auto (0xFF)`. Exact IFR evidence identifies `+0x36D=0x00` as `Disabled`; no evidence shows that `Auto` is converted to `Disabled` before the DF override consumer. If the native help condition is treated as a required precondition, the minimum is at least five changed bytes, adding absolute ROM offset `0x83C` (`AmdSetup+0x36D=0x00`) to the proposed offsets `0x7E5`, `0x7FF`, `0xBD3`, and `0xBD4`.

This is an **offline semantic contradiction/closure condition**, not proof that firmware will reject `Auto`: the IFR question has no conditions and the retained evidence classifies the help text as guidance. The template remains blocked independently by the unresolved `0x1204` final consumer/actuator, units/rate conversion, `UclkDiv1M0` ratio/crossing semantics, `FclkDpm` precedence, training semantics, and migration/default execution. The existing builder remains `df1400`-only; no `sync` profile was added.

## Bound target and evidence

- Source: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- Source size: `16,777,216` bytes
- Source SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- `AmdSetup` body base: `0x4CF`
- Conditional specification audited: `docs/research/20260920-clv-sync-conditional-candidate-spec.md`
- Machine matrix: `evidence/firmware-audit/20260920-clv-sync-native-gate-audit/gate-matrix.json`
- Machine matrix and report/action-log SHA-256s: recorded in `evidence/firmware-audit/20260920-clv-sync-native-gate-audit/SHA256SUMS.final`

No firmware, ROM, settings, global configuration, MCP, installation, network, or hardware operation occurred.

## Exact native field readback

| Field                    | Body offset | Absolute ROM offset | Pinned bytes/value    | Exact IFR/default evidence                                              | Template treatment                     |
| ------------------------ | ----------: | ------------------: | --------------------- | ----------------------------------------------------------------------- | -------------------------------------- |
| `MemoryClockSpeed`       |    `+0x316` |             `0x7E5` | `24` / enum `1800MHz` | enum question; declared default `Auto=0xFF`                             | change to a proven enum                |
| `UclkDiv1M0`             |    `+0x330` |             `0x7FF` | `01` / `Enabled`      | enum question; declared default `Auto=0xFF`; help says relative to FCLK | change only after ratio/crossing proof |
| `MemoryPstate`           |    `+0x36D` |             `0x83C` | `FF` / `Auto`         | exact question QID `0x25E`; `Disabled=0x00`; no enclosing IFR condition | **held unchanged** by current template |
| `FclkDpm`                |    `+0x6A3` |             `0xB72` | `0F` / `Auto`         | callback-bearing question QID `0x7045`; serializer record `0x1331`      | held unchanged, precedence unresolved  |
| `DfClockOverrideControl` |    `+0x703` |             `0xBD2` | `01` / `Manual`       | question QID `0x37D`; same DF help text                                 | asserted unchanged                     |
| `DfClockOvrd`            |    `+0x704` |      `0xBD3..0xBD4` | `8C05` / `1420`       | numeric question QID `0x37E`, bounds `0..2000`, no IFR default opcode   | change only after unit/domain proof    |

Exact DF help string from `menu-result.json`:

```text
When you try to override FCLK, please make sure FCLK > UCLK and Memory P-state is disabled.
```

The exact `+0x36D` question has `conditions=[]`, `flags=0x10`, `Auto=0xFF` as declared default, `Enabled=0x01`, and `Disabled=0x00`; the native package path is `0x7000 -> 0x7008 -> 0x702E -> 0x7030 -> 0x7032`. This proves the native control and its serializer handoff, not training behavior or runtime enforcement.

## Requirement-by-requirement gate matrix

The complete machine-readable matrix is `gate-matrix.json` (`12` rows: `3 PASS`, `1 PARTIAL`, `6 BLOCKED`, `2 UNRUN`). Statuses below are current observations, not inherited claims.

| Gate | Requirement                                          | Status      | Evidence class                   | Observed result                                                                                                                 |
| ---- | ---------------------------------------------------- | ----------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| G0   | Exact pinned donor identity                          | **PASS**    | observed-bytes                   | 16 MiB; SHA-256 matches `ea578104...ca4cb8`.                                                                                    |
| G1   | Native IFR fields/defaults/help reopened             | **PASS**    | observed-bytes + static-analysis | Exact menu and field bytes match; native help is guidance, not execution.                                                       |
| G2   | Serializer ownership of candidate fields             | **PASS**    | observed-bytes + static-analysis | Existing token matrix `45/45 PASS`; ownership correction `12/12 PASS`; `+0x6A3 -> 0x1331`.                                      |
| G3   | `$INV 0x1204` requester/consumer/final actuator      | **BLOCKED** | static-analysis + host-tested    | `UclkDiv1M0` serializer path is byte-preserving; immediate edge is an INV adapter/registration candidate, not a final actuator. |
| G4   | Units/rate conversion/shared range                   | **BLOCKED** | static-analysis                  | UI Memory labels overlap DF numeric bounds only; common physical unit and GDDR6 conversion are absent.                          |
| G5   | `UclkDiv1M0` ratio and synchronous crossing          | **BLOCKED** | static-analysis + host-tested    | Existing verifier confirms no ratio arithmetic in serializers and no exact-clv ratio/crossing assignment.                       |
| G6   | Memory-P-state/training and DF override precondition | **BLOCKED** | observed-bytes + static-analysis | **F1:** template leaves `+0x36D=0xFF Auto` while applying DF override; native help names `Disabled=0x00`.                       |
| G7   | `FclkDpm`/override precedence                        | **BLOCKED** | observed-bytes + static-analysis | Callback-bearing `+0x6A3 -> 0x1331` is mapped, but precedence versus manual DF override is unresolved.                          |
| G8   | Existing NVRAM/default/fallback/migration precedence | **PARTIAL** | observed-bytes + static-analysis | Defaults verifier `72/72 PASS`; callback default branch is `STATIC_ONLY_CALLBACK_NOT_EXECUTED`; reset/readback unrun.           |
| G9   | Four-byte template internally coherent               | **BLOCKED** | observed-bytes + static-analysis | It does not satisfy the documented native Memory-P-state precondition without a new proof of `Auto -> Disabled`.                |
| G10  | Four-role native-sync candidate transaction/build    | **UNRUN**   | host-tested boundary             | Existing regression `7/7 PASS` and unsupported `sync` is rejected; no native-sync candidate/four-role transaction was built.    |
| G11  | Hardware acceptance                                  | **UNRUN**   | unrun-hardware                   | No current-target recovery/readback, clock/divider/crossing observation, training, performance, or stability run.               |

## F1 — new contradiction and closure condition

The specification calls the four-byte set `0x7E5`, `0x7FF`, `0xBD3`, `0xBD4` a conditional minimum while holding `+0x36D` and `+0x6A3` unchanged. The exact native help makes that minimum incomplete as a self-consistent _override_ profile:

1. `+0x703=0x01` is `Manual`, and `+0x704` is the value being overridden.
2. The same native question supplies the precondition “Memory P-state is disabled.”
3. Baseline `+0x36D=0xFF` is `Auto`; exact native `Disabled` is `0x00`.
4. The template leaves `+0x36D` at `0xFF` and no bounded consumer/default trace proves an `Auto -> Disabled` conversion.

Therefore:

- If the help condition is required, add `AmdSetup+0x36D=0x00` at absolute offset `0x83C`; the minimum becomes **five changed bytes** (`0x7E5`, `0x7FF`, `0x83C`, `0xBD3`, `0xBD4`).
- If the help condition is advisory, the four-byte set still cannot be called semantically closed until the `0x123D` consumer/training path proves what `Auto` does.
- Either branch remains insufficient for a `1:1:1` claim because the final `0x1204` consumer, units, ratio/crossing selection and physical clock relation are unresolved.

This does not mean `+0x36D=0` is authorized or safe to build. It is a closure condition for the specification, not a candidate recommendation.

## Reproduction ledger

All commands were run from the project root. Existing verifier outputs were compared before/after. The two reruns whose current scripts emitted a different JSON serialization/check count were restored byte-for-byte from their retained superseded result copies; no worker-owned evidence was left modified.

```text
python3 evidence/firmware-audit/20260920-clv-sync-configuration-domain-matrix/configuration_domain_matrix.py
exit 0; 44/44 PASS

python3 evidence/firmware-audit/20260920-clv-sync-stage2-defaults/stage2_defaults_verify.py
exit 0; 72/72 PASS; callback status STATIC_ONLY_CALLBACK_NOT_EXECUTED

python3 evidence/firmware-audit/20260920-clv-sync-stage2-memory-pstate/memory_pstate_verify.py
exit 0; current rerun 9862/9862 PASS; retained result restored to SHA-256 237546fe...0b87c7

python3 evidence/firmware-audit/20260920-clv-sync-stage2-memory-pstate-discrimination/discrimination_verify.py
exit 0; current rerun 22/22 PASS; retained result restored to SHA-256 5f19242d...7f4eb9

python3 evidence/firmware-audit/20260920-clv-sync-stage2-uclk-semantics/uclk_semantics_verify.py
exit 0; 31/31 PASS; no exact-clv ratio assignment

python3 evidence/firmware-audit/20260920-clv-sync-stage2-token-matrix/token_matrix_verify.py
exit 0; 45/45 PASS

python3 evidence/firmware-audit/20260920-clv-sync-record-ownership-correction/record_ownership_verify.py
exit 0; 12/12 PASS; +0x6A3 -> token 0x1331

PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_clv_oc_builder.py' -v
exit 0; 7/7 PASS; unsupported sync/voltage/frequency profiles rejected; no project candidate output

python3 evidence/firmware-audit/20260920-clv-sync-native-gate-audit/native_gate_audit.py
exit 0; machine result status BLOCKED; F1 recorded; 3 PASS / 1 PARTIAL / 6 BLOCKED / 2 UNRUN
```

The bounded `scripts/nvar_audit.py` check also exited `0` but selected `0` `AmdSetup` records in its default store window; it was not used as positive evidence. The direct exact-ROM byte read in `native_gate_audit.py` is the source of the field table above.

The rerun manifest checks for the two restored worker directories remain `exit 1` solely because their existing `SHA256SUMS.final` files pin older verifier-script hashes; their result JSONs were restored to the expected manifest hashes. This is recorded as an integrity qualification, not promoted to a firmware finding.

## Evidence boundary and next closure condition

- **Observed bytes:** source hash, field bytes, IFR options/help/conditions, serializer instruction records.
- **Static analysis:** `$INV` record ownership and bounded consumer/registration edges.
- **Host-tested/emulated:** serializer value preservation and builder refusal tests; no firmware execution.
- **Hardware:** entirely unrun in this audit.

Before any native-sync build, either (a) prove offline that `Auto` on `+0x36D` resolves to the disabled state before DF override, or (b) revise the conditional template to include `+0x36D=0x00`, then separately close the `0x1204` consumer/actuator, unit/rate, UclkDiv1M0 ratio/crossing, FclkDpm precedence and training gates. Only then should the existing builder be extended and independently reviewed. Do not label any resulting image `1:1:1` without hardware acceptance.
