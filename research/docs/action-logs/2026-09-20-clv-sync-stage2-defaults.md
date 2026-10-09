# Stage 2 — Native AmdSetup defaults and precedence

## Intent (before own evidence writes)

- Timestamp: 2026-09-20T06:05:00+05:00 (Asia/Almaty)
- Actor: delegated project executor (`gpt-5.6-luna`, xhigh; effective runtime identity not independently exposed by this shell)
- Target: immutable clv donor `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`; expected SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Scope: offline, byte-backed precedence for AmdSetup body offsets `0x316`, `0x330`, `0x6A3`, `0x703`, `0x704`; reuse the existing 233-module census and exact-clv menu audit. Trace one concrete initializer/default callback and distinguish existing NVRAM, missing-variable fallback, and IFR Load Defaults coverage.
- Existing route reused: `scripts/nvar_audit.py`, existing stage-1 machine report, `evidence/firmware-audit/20260920-df-init-route/menu-result.json`, and retained `CbsSetupDxe`/`CbsBasePei` instruction records. No new serializer/mailbox/handoff search.
- Expected effect: create only a uniquely named evidence directory, machine-readable verifier/result, human report, and this append-only action log. No ROM, candidate, firmware, plan, memory, hardware, installation, MCP target, or shared analysis mutation.
- Rollback: delete only `evidence/firmware-audit/20260920-clv-sync-stage2-defaults`, `docs/research/2026-09-20-clv-sync-stage2-defaults.md`, and this action-log addition; immutable donor and existing evidence remain unchanged.
- Safety: no archive/executable execution; no secrets or raw security-like variable bodies copied.

## Observed result

Timestamp: 2026-09-20T06:12:00+05:00 (+05:00).

Executed:

```text
python3 evidence/firmware-audit/20260920-clv-sync-stage2-defaults/stage2_defaults_verify.py > evidence/firmware-audit/20260920-clv-sync-stage2-defaults/verifier.stdout 2> evidence/firmware-audit/20260920-clv-sync-stage2-defaults/verifier.stderr
```

Observed exit status: `0`.
Observed stdout (literal):

```text
{"checks": {"failed": 0, "passed": 48, "total": 48}, "existing_nvar": {"0x316": 36, "0x330": 1, "0x6A3": 15, "0x703": 1, "0x704": 1420}, "load_defaults_ifr_observed": {"0x316": {"status": "STATIC_DEFAULT_PRESENT", "value": 255}, "0x330": {"status": "STATIC_DEFAULT_PRESENT", "value": 255}, "0x6A3": {"status": "STATIC_DEFAULT_PRESENT", "value": 15}, "0x703": {"status": "STATIC_DEFAULT_PRESENT", "value": 255}, "0x704": {"status": "NO_IFR_DEFAULT_OPCODE_OBSERVED", "value": null}}, "missing_variable_fallback": {"0x316": 255, "0x330": 255, "0x6A3": 15, "0x703": 255, "0x704": 1000}, "status": "PASS"}
```

Observed stderr: empty.

The result is byte-backed/static only. Existing `AmdSetup` values are authoritative on the success path; missing/invalid `GetVariable` paths reach the compiled helper. The IFR audit independently establishes four enumerated defaults and leaves numeric `0x704` without a default opcode.

## Own artifact readback

The own evidence directory was reopened after generation. Final SHA-256 values:

```text
27fad998574a9e3ae3071cfa30f9aa18cae7e1a0bfed9b3baa5b6553b05bfb99  docs/research/2026-09-20-clv-sync-stage2-defaults.md
```

Additional hashes are recorded in `evidence/firmware-audit/20260920-clv-sync-stage2-defaults/SHA256SUMS.final`.

## Remaining uncertainty and rollback

- Live BIOS `Load Optimized Defaults`, reset, and post-reset readback remain unrun.
- Numeric `AmdSetup+0x704` Load Defaults source remained unresolved at the earlier 48-check checkpoint; this is superseded by the callback branch result below.
- No ROM, candidate, hardware, shared plan, shared memory, installation, MCP listener, or commit was changed. Rollback is deletion of this uniquely named evidence/report/log set only.

## Readback correction

The first manifest check was invoked from project root and failed only because the manifest stores evidence-directory-relative `./...` paths (`sha256sum -c` exit `1`; files were not missing). The corrected, evidence-preserving command was:

```text
(cd evidence/firmware-audit/20260920-clv-sync-stage2-defaults && sha256sum -c SHA256SUMS.final)
```

Observed corrected result: exit `0`; four/four own evidence files `OK`; stderr empty. This path/cwd correction does not change any finding or input bytes.

## Continuation intent — close +0x704 Load Defaults coverage

- Timestamp: 2026-09-20T07:02:00+05:00 (+05:00).
- Scope: inspect the exact `CbsSetupDxe` callback at RVA `0x950`, bind its action constants from an external-primary EDK II header, and verify the `EFI_BROWSER_ACTION_DEFAULT_STANDARD (0x1000)` branch reaches helper `0x2FE4` which writes `AmdSetup+0x704 = 1000`. Correct prior wording so IFR values are labelled declared/static until callback execution is observed.
- External source: `https://raw.githubusercontent.com/tianocore/edk2/master/MdePkg/Include/Protocol/HiiConfigAccess.h`, read-only metadata only; no dependency installation.
- Expected effect: extend only own stage2 evidence/report/action log and rerun verifier; no ROM, candidate, plan, memory, hardware, or shared artifact changes.

## Continuation observed result — callback/default action

Timestamp: 2026-09-20T07:08:00+05:00 (+05:00).

External-primary semantic check:

```text
URL: https://raw.githubusercontent.com/tianocore/edk2/master/MdePkg/Include/Protocol/HiiConfigAccess.h
SHA-256: 14329260b381a77f01c09a47a415a0826349da86bf6b61c475185422b16c3730
Observed: EFI_BROWSER_ACTION_RETRIEVE=2; EFI_BROWSER_ACTION_DEFAULT_STANDARD=0x1000
```

The exact clv callback at RVA `0x950` is registered at `EFI_HII_CONFIG_ACCESS_PROTOCOL` interface `+0x48`. Its byte-backed branch compares action `2` and `0x1000`; the `0x1000` standard-default branch calls helper `0x2FE4`. The helper's already-verified bytes write `AmdSetup+0x704=1000`.

Rerun command:

```text
python3 evidence/firmware-audit/20260920-clv-sync-stage2-defaults/stage2_defaults_verify.py > evidence/firmware-audit/20260920-clv-sync-stage2-defaults/verifier.stdout 2> evidence/firmware-audit/20260920-clv-sync-stage2-defaults/verifier.stderr
```

Observed exit status: `0`; stderr empty; `59/59` checks passed. Literal stdout is preserved in `verifier.stdout` and now reports:

```text
{"callback_default_action": {"action_0x1000": "EFI_BROWSER_ACTION_DEFAULT_STANDARD", "action_2": "EFI_BROWSER_ACTION_RETRIEVE", "branch_target": "0x2fe4", "callback_rva": "0x950", "execution_status": "STATIC_ONLY_CALLBACK_NOT_EXECUTED", "numeric_0x704": 1000, "registration": "EFI_HII_CONFIG_ACCESS_PROTOCOL interface+0x48"}, "checks": {"failed": 0, "passed": 59, "total": 59}, "existing_nvar": {"0x316": 36, "0x330": 1, "0x6A3": 15, "0x703": 1, "0x704": 1420}, "load_defaults_ifr_declared": {"0x316": {"status": "STATIC_DEFAULT_PRESENT", "value": 255}, "0x330": {"status": "STATIC_DEFAULT_PRESENT", "value": 255}, "0x6A3": {"status": "STATIC_DEFAULT_PRESENT", "value": 15}, "0x703": {"status": "STATIC_DEFAULT_PRESENT", "value": 255}, "0x704": {"status": "NO_IFR_DEFAULT_OPCODE_OBSERVED", "value": null}}, "missing_variable_fallback": {"0x316": 255, "0x330": 255, "0x6A3": 15, "0x703": 255, "0x704": 1000}, "status": "PASS"}
```

Wording correction applied in the own report: `0x316/0x330/0x6A3/0x703` are now explicitly **IFR-declared/static defaults**, not executed Load Defaults results. Numeric `0x704` is no longer called unresolved at source level: its standard-default callback branch is statically traced to helper value `1000`; live callback/browser execution and post-reset NVRAM readback remain unrun.

## Third-reviewer handoff request

The current 59-check result supersedes the earlier 48-check checkpoint while preserving that earlier result in the report/action history. A third independent reviewer (`sync_stage2_review`) should inspect the actual verifier, callback branch, EDK2 metadata, exact module bytes, and corrected wording; no reviewer receipt is treated as a finding. This environment exposes no collaboration dispatch tool to this worker, so the request is recorded for root orchestration.

## Final continuation readback

- Corrected report re-opened after wording fix; it now distinguishes IFR-declared values from callback execution and states `+0x704=1000` as a static standard-default callback result, with live execution unrun.
- The prior `48/48` stdout checkpoint is preserved at `evidence/firmware-audit/20260920-clv-sync-stage2-defaults/stage2-defaults-48-checkpoint.stdout` (SHA-256 `906809da26fbbc16a2c264b02899f400e81c1485f8b4ede45adc988ba687dae2`).
- Current own evidence manifest check: `(cd evidence/firmware-audit/20260920-clv-sync-stage2-defaults && sha256sum -c SHA256SUMS.final)` exit `0`, six/six files `OK`.
- Current result: `72/72` checks PASS; static callback source branch established with execution unrun; live browser/reset persistence and hardware behavior remain unrun.

Final report SHA-256: `730961631555b17bd0ba9c77152b6eadeee8d24b8903790dc5f44efe139bb76a`.

## Final verifier correction

The machine-result limitation wording was corrected to match the closed static branch: `+0x704` standard-default source is traced to `1000`; only live browser/reset persistence is unrun. Verifier rerun remained exit `0`, `59/59` PASS. Final own manifest rerun from the evidence directory remained exit `0`, six/six `OK`.

## Continuation intent — callback invocation gate and QuestionId coverage

- Timestamp: 2026-09-20T07:21:00+05:00 (+05:00).
- Scope: independently verify whether `EFI_BROWSER_ACTION_DEFAULT_STANDARD` reaches the exact callback for every question or only `EFI_IFR_FLAG_CALLBACK` questions; bind the selected question IDs/flags and correct the `EFI_BROWSER_ACTION_RETRIEVE` interpretation if needed.
- Reuse: exact clv menu result and `CbsSetupDxe` bytes; external-primary EDK2 `SetupBrowserDxe/Setup.c` and `Presentation.c` source excerpts only for browser dispatch semantics.
- Expected effect: own supplemental gate evidence/report/action-log updates only; no shared plan/memory, firmware, candidate, hardware, or patch changes.

## Callback invocation gate result

Timestamp: 2026-09-20T07:28:00+05:00 (+05:00).

External-primary SetupBrowser excerpts were independently read and hashed:

- `Setup.c` SHA-256 `183743078ef483db5c800080cd338a7ec8108014f801f5c617ee6e884e80df9a`: `GetDefaultIdForCallBack()` maps Standard to `EFI_BROWSER_ACTION_DEFAULT_STANDARD`; `GetQuestionDefault()` invokes `ConfigAccess->Callback` only when `QuestionFlags & EFI_IFR_FLAG_CALLBACK`.
- `Presentation.c` SHA-256 `525002bfdac874432e5d6d46b014be7551bd4d3813a383eb37a6394fa7bf47ab`: `ProcessRetrieveForQuestion()` returns `EFI_UNSUPPORTED` without the callback flag and otherwise calls callback with action `RETRIEVE`.

Exact clv gate table (from `menu-result.json`):

```text
+0x316 QID 0x20F CALLBACK=false
+0x330 QID 0x229 CALLBACK=false
+0x6A3 QID 0x7045 CALLBACK=true
+0x703 QID 0x37D CALLBACK=false
+0x704 QID 0x37E CALLBACK=false
```

The verifier now checks the gate, the callback branch (`59`-check result extended to `72/72`), and that the standard-default helper path does not consume the QID. Action `2` (`RETRIEVE`) branches to `0xA1D`; only action `0x1000` falls through to helper `0x2FE4`.

Interpretation: the browser does not directly invoke this callback for numeric `+0x704` QID `0x37E`. The callback-bearing FCLK_DPM QID `0x7045` is the selected route through which the helper can write the complete setup structure, including `+0x704=1000`, as a side effect. This is static coverage; browser execution, reset, NVRAM readback, and downstream hardware application remain unrun.

Supplemental own evidence: `edk2-SetupBrowser-callback-gate.metadata.json`, `edk2-SetupBrowser-Setup-snippet.txt`, `edk2-SetupBrowser-Presentation-snippet.txt`.

## Manifest freshness correction for reviewer

After the supplemental callback-gate files and `72/72` verifier update, the evidence manifest was regenerated and independently checked from its owning directory:

```text
(cd evidence/firmware-audit/20260920-clv-sync-stage2-defaults && sha256sum -c SHA256SUMS.final)
```

Observed: exit `0`; nine/nine listed files `OK`.
Final manifest SHA-256: `7718a2954a08901efaa32d76aa7868150be9052102edec8f718af8ffdb1dcee9`.
Current verifier stdout SHA-256: `0bf00046483694b01e40a390c3a15d4a694331316dfeef08802f9013611440fd`.
The 48-check checkpoint remains preserved separately; current supplemental result is 72/72.
