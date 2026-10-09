# CLV latency/performance measurement plan — intent

Timestamp: 2026-09-20T21:52:00+05:00 (Asia/Almaty)
Actor: bounded performance/latency planner (worker brief 7 of 8: latency/performance measurement plan).

Target: existing BC-250 native OC request fields (`AmdSetup+0x316/+0x330/+0x36D/+0x6A3/+0x703/+0x704`), the existing read-only capture route `scripts/probe_bc250_clocks_readonly.py`, the existing runbooks `docs/runbooks/2026-09-19-df1400-request-test.md`, `docs/runbooks/2026-09-20-oc-stock-capture.md`, `docs/runbooks/2026-09-20-clv-native-1330-capture-sheet.md`, and the existing historical latency claims (`140–150 ns` at DF 1000, `131.4 ns` at DF 1800; participant/photo class only).

Hypothesis: the current latency evidence is not instrumented, so no OC setting can be classified as a real gain or as inert. A deterministic, same-binary, same-input A/B protocol with a recorded method identity turns "140 ns vs 131 ns" into a bounded measurement with a decision rule.

Bounded action: define the A/B protocol and implement exactly one dependency-free harness (`scripts/measure_bc250_perf.py`) with an explicit method-identity field, a refusal path for a non-BC-250 host, a `compare` decision rule, one unit test file, and one operator runbook. Prove executability with real runs of the harness self-test and unit tests on this workstation.

Exclusions and boundaries: no ROM/NVRAM/flash write; no voltage change (all voltage fields stay `Auto`/zero); no SMU/mailbox, `/dev/mem`, or raw PCI access; no package installation; no benchmark claim from this workstation (it reports PCI `1002:1900`, not the target `1002:13fe`); no invented performance percentages.

Expected effect: this action log, one research plan, one operator runbook, one harness script, one unit test file, and one evidence directory with literal self-test stdout/stderr/exit plus hashes. No firmware, NVRAM, hardware, or existing evidence file changes.

Rollback: delete only this action log, the uniquely named plan/runbook/script/test/evidence files listed in the result section.
