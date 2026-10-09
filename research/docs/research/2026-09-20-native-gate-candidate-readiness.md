# Exact CLV native candidate readiness — SVC#4 mapped-register and field gate

Current: exact CLV / semantic-only offline experiment / ROM build blocked / next = close the listed static consumer and semantic gates.

## Conclusion

**Do not build a ROM candidate yet, even for a semantic experiment.** The exact ABL1 trace now proves a mapped-register **caller contract**: the callback path splits an encoded address into an aligned high part and a low 12-bit offset, invokes `SVC #4`, uses returned `R0` as a mapped base, performs a type-3 word access at `base+offset`, then invokes `SVC #5`. It does **not** recover the SVC handler/translation table, the runtime descriptor value, the active callback binding, the physical register, or clock semantics.

The exact native fields are byte-backed and their serializer ownership is closed, but they remain requests/records rather than proven clock/training actuators. The `$INV 0x1204` path ends at an NVTB/GUID-HOB generic-reader boundary in the retained static trace: direct reader calls request `0x10FF`/`0x1104`, not `0x1204`, and indirect/computed/HOB/DMA/runtime delivery is unresolved. Therefore the minimum offline semantic gate remains open and a `1:1:1` claim is not permitted.

`AmdSetup+0x36D` at absolute ROM `0x83C` is `0xFF` (`Auto`). The native IFR exposes `Disabled=0x00`; the 46/46 exact follow-up finds no `Auto -> Disabled` branch before DF serialization/defaulting. Thus `0x83C=0x00` is **not required by observed enforcement**. It is required only if the UI help phrase is imposed as a hard template precondition. That makes the byte an optional _specification branch_, not a safe change: there is no consumer, training, or hardware proof for writing `0x00`, so it should remain unchanged in any future minimal experiment until a new gate closes.

## Pinned baseline and direct checks

- Baseline: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- Size: `16,777,216` bytes
- SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- `AmdSetup` body base: `0x4CF`
- Read-only readiness verifier: `evidence/firmware-audit/20260920-native-gate-candidate-readiness/readiness_matrix_verify.py`
- Read-only verifier result: `candidate-readiness-result.json`, `67/67` checks, exit `0`
- SVC#4 direct rerun: `verify_svc4_mapping.py`, `59/59`, exit `0`, stderr empty
- Callback-target direct rerun: `abl1_context660_semantics_verify.py`, `96/96`, exit `0`, stderr empty
- Native gate follow-up: `native_gate_followup_verify.py`, `46/46`, exit `0`, stderr empty

The two first readiness-verifier failures were fixture-boundary corrections only: `+0x368` and `+0x36D` are supplemental fields absent from `menu-result.json`; FCLK_DPM is omitted from the all-fields result and comes from the canonical token matrix. No source or ROM bytes changed. The corrected verifier passed `67/67`.

## Exact SVC#4 mapped-register trace

Evidence: `docs/research/20260920-clv-abl1-svc4-mapping.md`; machine result `evidence/firmware-audit/20260920-clv-abl1-svc4-mapping/svc4-mapping-result.json` (`59/59 PASS`), rerun stdout `evidence/firmware-audit/20260920-native-gate-candidate-readiness/svc4.stdout`.

| Exact path              | Byte-backed operations                                                                                                                                                                                  | What is closed                                                          | What is not closed                                                                               |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Read helper `0x6DA4`    | `0x6DCC`: `R0=(R1>>12)`; `0x6DCE`: `R4=R1&0xFFF`; `0x6DD2`: restore alignment; `0x6DD4`: `SVC #4`; `0x6DD8`: returned `R0 -> R6`; type-3 `0x6E1A LDR R3,[R6,R4]`; `0x6E1E STR R3,[R5]`; `0x6DFC SVC #5` | The subsequent access uses returned mapped base + original low 12 bits. | SVC handler, translation table, physical window/page, and register identity.                     |
| Write helper `0x6E70`   | `0x6EA6..0x6EAC`: aligned high/low split; `0x6EAE SVC #4`; `0x6EB2`: returned `R0 -> R5`; type-3 `0x6EE6 LDR R0,[R4]`; `0x6EE8 STR R0,[R5,R6]`; `0x6ED6 SVC #5`                                         | A mapped word write is structurally possible on the callback path.      | Runtime descriptor value and whether this callback is the active FCLK callback.                  |
| Candidate body `0x9AD8` | Descriptor-table index/field extraction; local bit merge; calls `0x6DA4`/`0x6E70` on conditional normal/high paths.                                                                                     | Generic descriptor-indexed mapped field RMW semantics.                  | Active `R4+0x660` binding, live descriptor bytes, physical MMIO/PLL effect, and hardware result. |

The retained target-semantics result explicitly classifies active binding as unproven. It is not a valid basis for naming a physical clock register.

## Canonical native field and serializer map

The current exact map uses the all-fields/destination-pointer evidence; it supersedes older adjacent-ID pairings (in particular, `MemoryPstate +0x36D -> 0x123C`, not stale `0x123D`; `FclkDpm +0x6A3 -> 0x1331`).

| Native field             | Body offset |   Absolute ROM | CLV raw/value                     | Canonical `$INV` record | Direct interpretation                               |
| ------------------------ | ----------: | -------------: | --------------------------------- | ----------------------- | --------------------------------------------------- |
| `MemoryClockSpeed`       |    `+0x316` |        `0x7E5` | `24` / `36` (`1800MHz` IFR label) | `0x11ED`                | Stored request + serializer byte only               |
| `UclkDiv1M0`             |    `+0x330` |        `0x7FF` | `01` / `1` (`Enabled`)            | `0x1204`                | Stored byte + serializer byte; not decoded ratio    |
| `PhyPowerSaving`         |    `+0x368` |        `0x837` | `FF` / `255` (`Auto`)             | `0x1237`                | Distinct from Memory P-state                        |
| `MemoryPstate`           |    `+0x36D` |        `0x83C` | `FF` / `255` (`Auto`)             | `0x123C`                | Native enum; no proven training consumer            |
| `FclkDpm`                |    `+0x6A3` |        `0xB72` | `0F` / `15` (`Auto`)              | `0x1331`                | Callback-bearing IFR control; precedence unresolved |
| `DfClockOverrideControl` |    `+0x703` |        `0xBD2` | `01` / `1` (`Manual`)             | `0x1373`                | Control record; no actuator proof                   |
| `DfClockOvrd`            |    `+0x704` | `0xBD3..0xBD4` | `8C05` / `1420`                   | `0x1374`                | u16 record; no unit/domain proof                    |

The exact modules preserve these typed values into records; this does not prove that any record is consumed by a clock divider, training routine, PLL, or physical clock domain.

## Requirement matrix

Statuses are direct-evidence statuses for this review, not claims that a lower-level component works at runtime.

| Gate       | Requirement                                                      | Status            | Direct evidence                                                                                                                                              | Consequence                                                                         |
| ---------- | ---------------------------------------------------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| SVC4       | Exact mapped-register caller sequence                            | **PASS (static)** | 59/59 checks: aligned high + low12, `SVC #4`, returned-base type-3 LDR/STR, paired `SVC #5`.                                                                 | Physical map/register remains unknown.                                              |
| BIND       | Runtime descriptor/table and active callback identity            | **BLOCKED**       | 96/96 target checks pass, but context table/descriptor values and active `R4`/initializer `R5` identity are explicitly unproven.                             | Cannot bind SVC#4 to the clock actuator.                                            |
| FIELDS     | Native field bytes and serializer ownership                      | **PASS (static)** | `67/67` readiness checks; canonical records in both exact modules.                                                                                           | Field-to-record is closed; actuator is not.                                         |
| CONSUMER   | `$INV 0x1204` requester/consumer/final actuator                  | **BLOCKED**       | NVTB/GUID-HOB boundary found; direct reader calls are `0x10FF`/`0x1104`, not `0x1204`; indirect/computed/DMA/runtime paths remain open.                      | No semantic profile or candidate build.                                             |
| UNITS      | MCLK/FCLK/UCLK unit and GDDR6 conversion                         | **BLOCKED**       | UI labels `125..2000` overlap DF numeric bounds `0..2000` only; common unit/domain conversion is absent.                                                     | No trustworthy target value.                                                        |
| RATIO      | `UclkDiv1M0` ratio and synchronous-crossing selection            | **BLOCKED**       | Exact serializer is byte-preserving; bounded result reports no ratio arithmetic/assignment.                                                                  | `Enabled=0x01` is not a ratio or `1:1` proof.                                       |
| PRECEDENCE | `FCLK_DPM` versus manual DF override                             | **BLOCKED**       | `+0x6A3=0x0F` owns `0x1331` and is callback-bearing; no precedence over `0x1373/0x1374` is shown.                                                            | DF-only changes may be ignored/superseded.                                          |
| TRAINING   | Memory-P-state/DF guidance and training                          | **BLOCKED**       | Help says `FCLK > UCLK` and Memory P-state disabled; baseline `0x83C=FF`; 46/46 finds no Auto-to-Disabled branch.                                            | No training-safe profile.                                                           |
| DEFAULTS   | Existing variable/default/fallback/migration precedence          | **PARTIAL**       | 72/72 static checks; existing `GetVariable` path is authoritative; callback is `STATIC_ONLY_CALLBACK_NOT_EXECUTED`; live reset/browser/NVRAM readback unrun. | A future artifact can only be a stored-request experiment, never “applied/default”. |
| BUILD      | Minimal offline semantic candidate transaction                   | **BLOCKED**       | Existing builder remains `df1400`-only and rejects `sync`; no semantic manifest/four-role transaction/ROM output exists.                                     | Keep builder unchanged and do not build.                                            |
| HARDWARE   | Recovery, programmed readback, physical clock/training/stability | **UNRUN**         | No candidate or hardware operation in this review.                                                                                                           | Separate post-build acceptance gate.                                                |

## `+0x83C` decision

1. **Observed:** exact CLV `AmdSetup+0x36D` is `FF`; IFR options are `Auto=FF`, `Enabled=01`, `Disabled=00`; exact static CbsSetupDxe/CbsBasePei follow-up is `46/46 PASS` with `auto_to_disabled_branch_found=false`.
2. **Not proven:** firmware rejection of `Auto`; the help string is guidance in the retained evidence, and the IFR question has no local condition.
3. **If help is advisory:** `0x83C` is not a required field for a minimal _stored-request_ template, but leaving it at `Auto` still does not close training semantics.
4. **If help is a hard template precondition:** the proposed four-position allowlist would expand to five positions (actual byte differences require a built candidate comparison): `0x7E5`, `0x7FF`, `0x83C`, `0xBD3`, `0xBD4`.
5. **Safety classification:** changing `0x83C` to `00` now is **unjustified and unsafe to recommend**. There is no proven consumer, training effect, rollback need beyond the generic candidate controls, or hardware result. The minimal experiment should retain `FF` until a consumer/training gate closes; alternatively, revise the experiment explicitly as a five-position field hypothesis only after independent review.

“Optional” here means optional in the specification branch, not safe to write.

## Remaining pre-build gates and next decisive evidence

- Recover/resolve the runtime context table, encoded descriptor value, and active callback object; then map the returned SVC#4 window to a named register class.
- Resolve `$INV 0x1204` registration/indirection and final consumer/actuator, including any HOB/DMA/runtime handoff not covered by the current bounded function boundary.
- Derive common units/rate conversion and physical domain for MCLK/FCLK/UCLK.
- Resolve `UclkDiv1M0` divider and synchronous-crossing semantics.
- Resolve `FCLK_DPM` precedence relative to manual DF override.
- Establish Memory-P-state/training relation; decide whether `Auto` remains baseline or a separately justified `Disabled` branch is required.
- Record explicit existing-variable/default/migration precedence in a semantic manifest; live browser/reset/readback remains a hardware-acceptance requirement, not a proof substitute.
- Only after these offline gates close: extend the existing builder with a named conditional profile, require the four-role artifact transaction and independent review, then separately run hardware acceptance. Nothing in this report authorizes a flash.

## Evidence boundary

Evidence class: `observed-bytes` + `static-analysis` + retained `emulated-or-host-tested` serializer/default checks. No ROM/candidate was built; no firmware execution, NVRAM write/reset, hardware, physical clock, training, or `1:1:1` result was observed.

Owned evidence:

- `evidence/firmware-audit/20260920-native-gate-candidate-readiness/candidate-readiness-result.json` — SHA-256 `1ec74f3612e350ab357c53ec66bdabd82717d24dbe666374d70b4fc8b8372cfa`
- `evidence/firmware-audit/20260920-native-gate-candidate-readiness/readiness_matrix_verify.py` — SHA-256 `8a6540cc678d99158043eb0c769a90aa9718facd8df0b31606684af14e2e8ff7`
- `evidence/firmware-audit/20260920-native-gate-candidate-readiness/svc4.stdout` — SHA-256 `4b9fa6b22d418ee31f284025d2d5f84931e56d222a32e37cfd5d69e08ac39cf0`
- `evidence/firmware-audit/20260920-native-gate-candidate-readiness/context660.stdout` — SHA-256 `1fbe03c4af48c5c52247ab73430c9b02dbf2cfedd5150a79af6dd30734170a50`
- All owned `*.stderr` files are empty; all three exit files contain literal `0`.

No source ROM, candidate, settings, hardware, global configuration, MCP/Cutter, installation, or commit changed.
