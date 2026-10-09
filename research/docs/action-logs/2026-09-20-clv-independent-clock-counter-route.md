# CLV independent clock-counter route — action log

## Intent (before write)

- Timestamp: 2026-09-20 Asia/Almaty
- Actor: independent reviewer, phase-2 measurement-route checkpoint
- Scope: inspect existing exact register headers and current firmware evidence for a non-aliased clock measurement mechanism; execute one bounded offline parser/check. No live telemetry, board access, firmware/settings/hardware writes, dependencies, installs, or shared MCP changes.
- Hypothesis: paired hardware clock counters with a common reference gate can distinguish a measured clock from aliased software metrics; existing evidence may expose only a GFXCLK/REFCLK pair, which would be a route prototype rather than proof for MCLK/UCLK/FCLK.
- Inputs: imported `gc_10_1_0_offset.h` and `gc_10_1_0_sh_mask.h`, existing CLV frequency-unit report, and existing SMU query/actuator report.
- Expected effect: machine-readable route result and report that separate demonstrated hardware-counter semantics from unresolved UMC/DF/UCLK mapping and synchronous-crossing status.
- Rollback: remove only newly created evidence/report files; no project binary or hardware mutation.
  a0ad8bffb3c07ec3824d306aff49c77bc40057f8760aec7a76ee58a60cc8e6a2 import/from-windows/Users/kukuruza/tmp_bc250/recon/gc_10_1_0_offset.h
  cba20414ecf02e91bafdcfbff7d4ba686326f0bdaf236d1a883364f08410c167 import/from-windows/Users/kukuruza/tmp_bc250/recon/gc_10_1_0_sh_mask.h

## Observed result after write

- Existing exact register headers and current alias/SMU reports were reopened; bounded verifier status `23/23 PASS`.
- A separate hardware-counter route is proven offline for GFXCLK/REFCLK: counters `0x4C30..0x4C33`, control `0x4C34`, status `0x4C35`, separate run/reset/sample and valid masks.
- This does not bind the route to exact CLV MCLK/UCLK/FCLK; no UMC/DF/UCLK counter/status map was recovered in the bounded check.
- Minimal truthful non-aliased mechanism requires domain-specific counter pairs plus common reference and synchronous-crossing status/selector. No live telemetry, firmware, hardware, or settings operation.
- Readback hashes:
  3dfa7e53ba044f9a9eae7104f3f94c37b4fc8a8f96618d00514250c0fef9bd3e docs/research/20260920-clv-independent-clock-counter-route.md
  6eaa6a027118cc88a47d909bfcce39841eac29870561c8c05a82f3da3f43dda0 evidence/firmware-audit/20260920-clv-independent-clock-counter-route/clock-counter-route-result.json
  08bcf62bbbdb04d9c228de8d884a232bbaf941de8fc32cd6fafc1c1d0cdddb4c evidence/firmware-audit/20260920-clv-independent-clock-counter-route/clock_counter_route_verify.py
- Rollback: remove only owned report/evidence files.

## Shared integration observed result

- Plan and memory updated append-only with GFXCLK/REFCLK counter prototype and explicit unresolved UMC/DF/UCLK mapping.
- Phase 2 remains `PARTIAL`; no hardware/clock/synchronization acceptance gate completed.
- Final readback hashes:
  3dfa7e53ba044f9a9eae7104f3f94c37b4fc8a8f96618d00514250c0fef9bd3e docs/research/20260920-clv-independent-clock-counter-route.md
  6eaa6a027118cc88a47d909bfcce39841eac29870561c8c05a82f3da3f43dda0 evidence/firmware-audit/20260920-clv-independent-clock-counter-route/clock-counter-route-result.json
  c24c0a61f532e88c695f86a8ee8c16a71f3d4ae2ab468adf3d0b70e7cf650545 docs/action-logs/2026-09-20-clv-independent-clock-counter-route.md
  3e704de88dc12c14523d1734880122ae24ea4ebcb14091386c9ca0ee6b581f01 specs/2026-09-20-clv-sync-development-plan.md
  bb46de07a84b753cbe687340a42117f046a75baca391e0ee34b947c8c9fc764c memory/oc-recheck.md

## Exact-clv applicability check intent (before write)

- Scope: qualify the RLC GFXCLK/REFCLK counter prototype against exact clv/Robin-5 firmware evidence without adopting it as a board measurement route.
- Procedure: parse exact clv PSP type-0x08 SMU payload and scan bounded exact bytes for direct counter register literals `0x4C30..0x4C35`; record header base-index/DWORD-index semantics and whether any local producer/consumer binds the block to CLV UMC/DF/MCLK/UCLK/FCLK.
- Expected result: either a byte-backed exact-image binding or a precise static applicability gap. No hardware/probe/MMIO action.

## Exact-clv applicability observed result

- The corrected bounded verifier ran against the pinned CLV ROM and returned `23/23 PASS`.
- Exact CLV PSP type-0x08 container: offset `0x8FEE00`, size `0x40200`; extracted body length `0x40100`; body SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`.
- Direct little-endian scalar scans for `0x4C30..0x4C35` returned no occurrences in the exact type-0x08 PMFW body.
- The retained SMU source contains no direct `RLC_CLK_COUNT_GFXCLK` symbol use; the existing report explicitly states that its software metrics do not sample hardware PLL counters.
- Decision: the GFXCLK/REFCLK counter block remains an external-primary/source static prototype. Exact-board MCLK/UCLK/FCLK applicability is not established; no UMC/DF/UCLK binding, indirect route, or hardware read was demonstrated.
- Two implementation corrections were recorded during the run: the verifier's hash helper now accepts byte buffers as well as paths; the exact extracted body length is `0x40100` (container includes a `0x100` header). Intermediate failed checks were not used as findings.
- Result artifact: `evidence/firmware-audit/20260920-clv-independent-clock-counter-route/clock-counter-applicability-result.json`.
- Verifier: `evidence/firmware-audit/20260920-clv-independent-clock-counter-route/clock_counter_applicability_verify.py`.
- Rollback: remove only the applicability verifier/result and this appended report section; source ROM and imported headers remain unchanged.

## Integration intent (before memory/plan append)

- Scope: append the exact-CLV applicability result to the durable checkpoint plan and OC review memory without changing any prior conclusion.
- Expected effect: preserve the `23/23 PASS` static applicability gap, exact body/hash and direct-literal negative evidence, and keep Phase 2 marked `PARTIAL`.
- Rollback: remove only the newly appended sections from `specs/2026-09-20-clv-sync-development-plan.md` and `memory/oc-recheck.md`.

## Integration observed result

- Plan and OC review memory were appended with the applicability gap; Phase 2 remains `PARTIAL`.
- Reopened hashes:
  2c039f3223fcb64598aaa590cc9f54a0f9ad6b14a427f6b6da096e761916b38d specs/2026-09-20-clv-sync-development-plan.md
  cf0faf0783d3b5a20d7f86dfa28ab5da6edbc645729759b5a70f43ad11f1155b memory/oc-recheck.md
  a8282b56dc3f33ee46c0a357438f3cef5f6be295bff54e032f02999380b03136 docs/research/20260920-clv-independent-clock-counter-route.md
  b0e1ec722dfacbc17fc24d4ee09b355b4e1117b84c327087f467623fdf2da77a docs/action-logs/2026-09-20-clv-independent-clock-counter-route.md
  87a396f7116852dc0beec25e73839a8f9a544f830bd15df864d2c104903c54c6 evidence/firmware-audit/20260920-clv-independent-clock-counter-route/clock-counter-applicability-result.json
  b8fee919c618016b05232c5b8ee0d1b5cea0d360c3054bb44b27db7df18fd723 evidence/firmware-audit/20260920-clv-independent-clock-counter-route/clock_counter_applicability_verify.py
