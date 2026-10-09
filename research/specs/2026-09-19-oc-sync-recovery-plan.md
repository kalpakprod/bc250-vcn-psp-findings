# BIOS-applied memory latency and clock synchronization investigation

## Scope and planning anchor

Recover the latest recorded user goal: reduce BC-250 memory latency using a BIOS-applied synchronous clock mode; investigate the proposed SoC 1.15V rather than assume its encoding or safety. This plan authorizes no flash or voltage change. Root owns evidence reconciliation, integration and verification. No worker is needed for task creation.

Latest session anchor: docs/action-logs/2026-09-19-oc-recheck.md (17:05:31+05:00), memory/oc-recheck.md. Reconstruction uses dated project records, not raw chat exports. Current board firmware and runtime state have not been measured in this recovery task.

## Current state audit + refined roadmap

- Recorded byte audit: nine historical OC candidates are confined to NVRAM, but none proves applied clocks, synchronization, safe voltage or improved latency.
- sync_v002 requests memory enum labelled 1750MHz and DF 1500; it is not evidence of 1:1:1. FclkDpm=0 means Disabled; Auto=0x0F.
- vdd80 stores raw 80. Its voltage units, target rail and relation to 1.15V are unresolved. Existing voltage and combined profiles remain NO-GO from the latest review.
- Existing candidates use plain clv, not a verified integrated W9/8-core/Steam-logo baseline. Feature retention must be established, not assumed.
- Earlier NVAR checks started at 0x1000 and missed AmdSetup at record 0x4BB, body 0x4CF.
- Equal exported UCLK/FCLK values are not independent evidence when both originate in MemclkFrequency.
- VCN research is a separate backlog, not a prerequisite for this OC task. Historical KDB equality and failed boots must not be promoted to proof of every verifier path or universal impossibility.
- G7 audit correction (2026-09-19): previous DF/UCLK identities hardcoded in verifiers; no 1:1 patch justified; promised research report docs/research/oc-fabric-domain-identification.md was absent and is now created.
- SMU helper 0x2360C rate conversion decoded: U9.16 fixed-point (bits [8:0] integer, bits [31:16] unsigned fraction scaled by 1/65536.0, bits [15:9] ignored).
- Combined with helper 0x1CAD8 (AMD DFS DID divider formula), exact rate decoding function reproduces all stored P-state rates in DF P-state table (0xCF0C) across domains 0x0E, 0x0F/0x11, 0x10/0x12.
- Telemetry/semantic labels classified as 'observed/static' firmware state fields; physical clock/rail assignment and synchronization remain unverified.

## Connected groups and existing routes

- scripts/build_clv_oc_candidate.py: reuse only after explicit source identity, supported profiles and output gates are corrected and tested. Field-local checks are not full-image identity checks.
- scripts/nvar_audit.py and tests/test_nvar_audit.py: reuse for correct NVAR store selection and target-record validation; zero selected records must not count as validation.
- scripts/probe_bc250_clocks_readonly.py: existing kernel-file collection route. Audit metric provenance before interpreting it as independent clock/rail measurement.
- evidence/firmware-audit/amdsetup-ifr-field-map.json: field labels and offsets, not hardware semantics.
- memory/tools.md: existing disassembly, firmware parsing and external-stack routes. Do not add another builder or probe wrapper without a demonstrated gap.

## Use cases

1. Establish what the current baseline actually contains and measures without modifying the board.
2. Distinguish requested BIOS settings from applied clocks and physical rail voltage.
3. Produce a minimal candidate only when its control semantics and rollback are established.
4. Accept a profile only if measured latency improves and training/stability checks pass.

## Implementation checklist

- [x] R0 Recover the latest dated decision and create the durable plan and session tasks.
- [x] R1 Local identity reconciliation complete; operator explicitly selects plain 5.00 clv for this OC track on 2026-09-19. Source: evidence/donor/retroweb-20260916/BC250_5.00_clv.bin, SHA-256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8 freshly checked. Recovery copies and feature manifest: docs/research/2026-09-19-oc-baseline-identity.md. W9/core/logo integration no longer blocks this selected scope; no implied exact-image flash approval.
- [x] R2 Trace clock controls and telemetry. Follow MemoryClockSpeed, UclkDiv1M0, FclkDpm and DfClockOvrd consumers plus driver/SMU metric producers. CBS serialization to IDs 0x11ED/0x1204/0x1331/0x1373/0x1374 mapped; driver telemetry aliasing between SMU_FCLK/SMU_MCLK/MemclkFrequency verified; SMU mailbox discriminating commands identified: PPSMC_MSG_QueryDfPstate (Queue 0 msg 0x13, handler 0x1E988 in Robin 5), PPSMC_MSG_QueryVddcrSocClock (msg 0x11, handler 0x2EA74), and SetMaxDeepSleepDfllGfxDiv (Queue 0 msg 0x1A, handler 0x2B634 in Robin 5 / 0x2B2F4 in Robin 3). Telemetry probing updated to flag aliased driver metrics. Control semantics verified offline; hardware verification unrun.
- [ ] R3 Trace voltage control. Follow VddcrVddOffsetControl and VddcrVddOffset to their consumer, encoding and target rail. Acceptance: distinguish SoC from other rails and identify a defensible measurement/safety basis, or explicitly close voltage changes as blocked. Raw 80 and the user's 1.15V target are not calibration evidence. Depends on R1; can run independently of R2.
- [ ] R4 Add regression tests and harden existing tools. First reproduce wrong-source acceptance, missed AmdSetup selection and misleading combined-profile semantics without generating a flash artifact. Then enforce approved full-source identity, target-record presence, supported ranges, one-variable semantics and non-overwriting image/manifest output. Acceptance: known-good and malformed/wrong-source tests, exact byte-delta checks; rejected inputs leave no candidate. Depends on R1-R3; do not enable unresolved voltage paths.
- [ ] R5 Prepare one no-voltage candidate and experiment runbook only if the previous gates support it. Record one changed control, expected signal, source/output hashes, allowed deltas, independent parser checks, rollback and stop conditions. Independent review must inspect the actual artifact and failure path. If a single control cannot test the hypothesis, document that limitation rather than call a multi-control change single-variable. Depends on R2 and R4.
- [ ] R6 Execute a board trial only after separate approval of the exact image and target, verified recovery and instrumentation prerequisites. Compare baseline and candidate under the same workload: applied clocks, independent synchronization evidence where available, training, errors, latency and stability. Report pass/fail/inconclusive/unrun separately. Depends on R5 and operator approval; currently BLOCKED.

## Open questions

- R1 resolved by operator selection of plain clv; flashing availability confirmed by operator. Current chip contents and exact-target recovery preflight remain hardware-stage checks, not blockers for offline tracing.
- Blocking voltage changes: which rail does this field control, what are its units, and what establishes a board-specific safe range?
- Blocking synchronization claims: is there an independent measurement of each clock domain rather than duplicated driver metrics?
- Non-blocking for task creation: full last-chat transcript was not inspected. Latest project record identifies the OC correction as the last action.

## Decision log

- 2026-09-19: Trace DF P-state table (0xCF0C) population in SMU Robin 5. Provenance established: table is static hardcoded ROM default data (FCLK 1200 / UCLK 875 max), NOT populated or overwritten by host PPTable or mailbox transfers. BIOS Setup cannot alter fabric frequencies.
- 2026-09-19: prioritize the latest OC goal over restarting older VCN or signature investigations.
- Preserve existing candidates and reports; no new flash recommendation from this plan.
- A negative or inconclusive investigation result is acceptable. Completion does not require finding a working overclock or an exploit.

## Verification and completion

Plan creation: verify source paths, checklist, session task presence, UTF-8 readback and absence of unintended edits. Research completion: per R1-R6 acceptance criteria, with measured evidence class and reproduction procedure. No hardware or binary-correctness claim follows from this documentation task.
