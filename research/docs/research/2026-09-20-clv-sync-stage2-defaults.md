# Stage 2 — Native AmdSetup defaults and precedence (exact clv)

## Conclusion

The selected clv image has a concrete two-level default path for the five requested fields:

1. **Existing `AmdSetup` NVRAM wins** when `GetVariable` returns the expected `EFI_BUFFER_TOO_SMALL` probe (`0x80000005`), reports the expected `0x8B5`-byte buffer, and the second read succeeds.
2. **Missing/invalid-variable initialization falls back to a compiled helper**. In `CbsSetupDxe`, the helper is RVA `0x2FE4`; in `CbsBasePei`, the same default structure is reached through six read-failure branches to instruction RVA `0x650`.
3. **The `+0x704` default source is statically resolved, but not executed**. `CbsSetupDxe` registers a callback at RVA `0x950`. Its action branch distinguishes `2` (`EFI_BROWSER_ACTION_RETRIEVE`) from `0x1000` (`EFI_BROWSER_ACTION_DEFAULT_STANDARD`): action `2` goes to the retrieve path, while only `0x1000` calls helper `0x2FE4`; that helper writes `AmdSetup+0x704 = 0x03E8` (1000). Browser-side invocation is gated by the question's `EFI_IFR_FLAG_CALLBACK`, not by the helper's internal QID. The exact IFR package separately declares defaults for `0x316`, `0x330`, `0x6A3`, and `0x703` as `0xFF`, `0xFF`, `0x0F`, and `0xFF`; these are **IFR-declared values**, not an executed browser/reset observation.

This is a byte-backed precedence result, not execution on a board. It means a stored NVRAM profile cannot be made into a true first-boot default merely by changing the compiled fallback; a candidate must also define how an existing `AmdSetup` variable is migrated/invalidated, while preserving the statically traced `0x704` callback default and separately testing live persistence.

## Pinned inputs and provenance

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- ROM SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- `CbsSetupDxe` module: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260919-inv-token-consumers/CbsSetupDxe-7ff717d51c9a.bin`
- `CbsSetupDxe` SHA-256: `7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8`
- `CbsBasePei` module: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.bin`
- `CbsBasePei` SHA-256: `6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77`
- Exact menu audit: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-df-init-route/menu-result.json`
- Stage-1 NVAR report: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-sync-stage1/stage1-report.json`

## Byte-backed result

### Existing NVRAM (`AmdSetup` body base `0x4CF`)

Direct ROM bytes at the known `AmdSetup` body base are:

| body offset | absolute ROM offset | field                    | bytes       |  value |
| ----------- | ------------------: | ------------------------ | ----------- | -----: |
| `0x316`     |             `0x7E5` | `MemoryClockSpeed`       | `24`        |   `36` |
| `0x330`     |             `0x7FF` | `UclkDiv1M0`             | `01`        |    `1` |
| `0x6A3`     |             `0xB72` | `FclkDpm`                | `0F`        |   `15` |
| `0x703`     |             `0xBD2` | `DfClockOverrideControl` | `01`        |    `1` |
| `0x704`     |             `0xBD3` | `DfClockOvrd`            | `8c05` (LE) | `1420` |

These are persisted `AmdSetup` bytes in the donor image, not hardware clocks.

### Compiled missing-variable/default helper

The exact `CbsSetupDxe` helper at RVA `0x2FE4` writes the selected fields as:

| field   |     instruction RVA | exact bytes                     |    helper value |
| ------- | ------------------: | ------------------------------- | --------------: |
| `0x316` |            `0x3C80` | `c68116030000ff`                |          `0xFF` |
| `0x330` |            `0x3D22` | `c68130030000ff`                |          `0xFF` |
| `0x6A3` |            `0x4561` | `c681a30600000f`                |          `0x0F` |
| `0x703` |            `0x4741` | `c68103070000ff`                |          `0xFF` |
| `0x704` | `0x4748` + `0x474D` | `b8e8030000` / `66898104070000` | `0x03E8` (1000) |

The same values are independently present in `CbsBasePei`'s default structure: selected instruction RVAs `0x1A4B`, `0x1B3D`, `0x294B`, `0x2C0F`, and `0x2C1E`.

### Existing-variable versus fallback branch

At `CbsSetupDxe`:

- `0x5FE`: indirect call through runtime-services slot `+0x48` (`GetVariable`).
- `0x601`: compare against `0x8000000000000005` (`EFI_BUFFER_TOO_SMALL`).
- `0x610`: require returned size `0x8B5`.
- `0x647`: second `GetVariable` call.
- `0x64A` / `0x64D`: if the second call is not successful (`jge` fails), branch to `0x653`.
- `0x653`: relative call reaches compiled helper `0x2FE4`; `0x658` then calls the common follow-on routine at `0x5B60`.

The direct call to `0x2FE4` is also present at `0xA11` and `0xB86`, giving three helper call sites in the retained exact module. The callback compares actions `2` and `0x1000`, but only action `0x1000` reaches the helper call at `0xA11`; action `2` branches to retrieve at `0xA1D`. See the exact callback analysis below. The earlier statement that both actions enter the `0xA11` helper path was inconsistent with that analysis.

Independent `CbsBasePei` evidence shows six explicit fallback calls to default helper RVA `0x650`: call sites `0x333`, `0x344`, `0x355`, `0x5B4`, `0x5C5`, and `0x5D6`. Each call is reached from a failed status/size branch in one of its two config-read paths.

### IFR-declared defaults and callback default action

The exact-clv menu audit reports the following **declared IFR option defaults**:

| body offset | question                    |                  exact IFR default |
| ----------- | --------------------------- | ---------------------------------: |
| `0x316`     | Memory Clock Speed          |                      `Auto = 0xFF` |
| `0x330`     | UclkDiv1M0                  |                      `Auto = 0xFF` |
| `0x6A3`     | FCLK_DPM                    |                      `Auto = 0x0F` |
| `0x703`     | DF Clock Override Control   |                      `Auto = 0xFF` |
| `0x704`     | DF Clock Override (numeric) | **no IFR default option observed** |

The four enumerated declarations agree with the compiled missing-variable helper. The numeric `0x704` question has only bounds (`0..2000`) in the parsed package; no IFR default opcode/value was observed. That absence does **not** decide browser behavior: the callback path does.

The exact callback path is byte-backed:

- `CbsSetupDxe` constructs the `EFI_HII_CONFIG_ACCESS_PROTOCOL` at callback-registration code around RVA `0xAF6..0xB03`; the `interface+0x48` callback pointer is `RVA 0x950`.
- The callback receives `EFI_BROWSER_ACTION` in `RDX`. Its branch compares the action with `2` and `0x1000`; action `2` branches to `0xA1D` (retrieve), while `0x1000` is the standard-default action under the external-primary EDK II definition recorded at `evidence/firmware-audit/20260920-clv-sync-stage2-defaults/edk2-HiiConfigAccess.metadata.json`.
- The standard-default branch calls `0x2FE4` at RVA `0xA11`. The helper's exact `0x4748/0x474D` bytes load/store `0x03E8` into `AmdSetup+0x704`.
- EDK II `SetupBrowserDxe` source independently gates callback invocation in `GetQuestionDefault`/`ProcessRetrieveForQuestion` on `QuestionFlags & EFI_IFR_FLAG_CALLBACK`. In the exact selected menu: `FCLK_DPM` (`QID 0x7045`, offset `0x6A3`) has `CALLBACK`; `Df Clock Override` (`QID 0x37E`, offset `0x704`) does not. Thus the browser does not directly invoke this callback for QID `0x37E`; `+0x704=1000` can be written as a side effect when the callback-bearing FCLK_DPM question takes the standard-default path. The standard-default branch itself does not consume the QID (`R14`) in its helper path.

This establishes the source/branch statically. It does not execute the browser, write NVRAM, reset the board, or prove downstream clock/training behavior.

## Reproduction

Command:

```text
python3 evidence/firmware-audit/20260920-clv-sync-stage2-defaults/stage2_defaults_verify.py
```

Observed stdout:

```text
{"callback_default_action": {"action_0x1000": "EFI_BROWSER_ACTION_DEFAULT_STANDARD", "action_2": "EFI_BROWSER_ACTION_RETRIEVE -> callback path 0xA1D (not helper 0x2FE4)", "branch_target": "0x2fe4", "callback_rva": "0x950", "execution_status": "STATIC_ONLY_CALLBACK_NOT_EXECUTED", "numeric_0x704": 1000, "question_gates": {"0x316": {"callback": false, "qid": "0x20f"}, "0x330": {"callback": false, "qid": "0x229"}, "0x6A3": {"callback": true, "qid": "0x7045"}, "0x703": {"callback": false, "qid": "0x37d"}, "0x704": {"callback": false, "qid": "0x37e"}}, "registration": "EFI_HII_CONFIG_ACCESS_PROTOCOL interface+0x48"}, "checks": {"failed": 0, "passed": 72, "total": 72}, "existing_nvar": {"0x316": 36, "0x330": 1, "0x6A3": 15, "0x703": 1, "0x704": 1420}, "load_defaults_ifr_declared": {"0x316": {"status": "STATIC_DEFAULT_PRESENT", "value": 255}, "0x330": {"status": "STATIC_DEFAULT_PRESENT", "value": 255}, "0x6A3": {"status": "STATIC_DEFAULT_PRESENT", "value": 15}, "0x703": {"status": "STATIC_DEFAULT_PRESENT", "value": 255}, "0x704": {"status": "NO_IFR_DEFAULT_OPCODE_OBSERVED", "value": null}}, "missing_variable_fallback": {"0x316": 255, "0x330": 255, "0x6A3": 15, "0x703": 255, "0x704": 1000}, "status": "PASS"}
```

- Exit status: `0`
- Stderr: empty
- Machine result: `evidence/firmware-audit/20260920-clv-sync-stage2-defaults/stage2-defaults-result.json`
- Verifier stdout/stderr: `evidence/firmware-audit/20260920-clv-sync-stage2-defaults/verifier.stdout` and `verifier.stderr`

## Acceptance boundary

- **PASS** — immutable clv hash and exact module hashes.
- **PASS** — direct bytes for current NVRAM fields.
- **PASS** — compiled helper/default bytes and call edges.
- **PASS (static)** — exact IFR-declared defaults for four enumerated questions.
- **PASS (static)** — callback registration and `EFI_BROWSER_ACTION_DEFAULT_STANDARD (0x1000)` branch to helper `0x2FE4`, including numeric `+0x704 = 1000`.
- **PASS (static)** — browser invocation gate: selected FCLK_DPM `QID 0x7045` has `CALLBACK`; numeric `+0x704` `QID 0x37E` does not. The helper branch is a side effect of the callback-bearing path, not a direct callback for `QID 0x37E`.
- **UNRUN/INCONCLUSIVE** — live browser `Load Optimized Defaults`, callback execution, post-reset NVRAM readback, and persistence semantics after a real reset.
- **UNRUN** — firmware execution, boot, training, physical clock/voltage measurement, hardware acceptance.

## Actionable implication

A true default profile requires two separate controls: (a) the compiled missing-variable/IFR/callback defaults, and (b) a deliberate migration or invalidation policy for an already-existing `AmdSetup` variable. Patching only one of those leaves the donor's persisted `0x7E5/0x7FF/0xB72/0xBD2/0xBD3` values authoritative. The numeric `+0x704=1000` source is statically traced as a side effect of the callback-bearing `FCLK_DPM` standard-default path; direct callback invocation for QID `0x37E` is gated off, and live browser/reset persistence remains unrun.
