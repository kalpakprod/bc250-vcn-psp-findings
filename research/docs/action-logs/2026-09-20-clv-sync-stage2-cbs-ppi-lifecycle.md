# CLV phase-2 CBS PPI registration/dispatch lifecycle — intent

Timestamp: 2026-09-20T06:08:00+05:00 (+05:00)
Actor: sync_stage2_consumer executor
Target: trace the exact CbsBasePei PPI owner (`04126c85-5c4e-458f-abc1-29f1f7da365e`) from entrypoint InstallPpi/NotifyPpi descriptors through method `RVA 0x250` and its callback dispatch, then compare one concrete counterpart registration record (Gfx and SMU) carrying the same GUID/event descriptor.

Next executable action: run `evidence/firmware-audit/20260920-clv-sync-stage2-cbs-ppi-lifecycle/cbs_ppi_lifecycle_verify.py`; decode GUID/interface/notify descriptors and exact indirect callback dispatch bytes.

Inputs: pinned clv ROM SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; exact Cbs/Gfx/SMU bodies and instruction metadata under the retained census.

Expected effect: own PPI lifecycle evidence/report/log only. No firmware, ROM, hardware, shared plan/memory, Ghidra/Cutter/MCP, candidate, installation, voltage or settings changes.

Rollback: remove only this unique evidence directory, report and action log.

## Observed result

Timestamp: 2026-09-20T06:12:00+05:00 (+05:00).

Final command:

```text
python3 -B evidence/firmware-audit/20260920-clv-sync-stage2-cbs-ppi-lifecycle/cbs_ppi_lifecycle_verify.py
```

Exit status: `0`; literal summary: `status=PASS`, `checks=26`. Cbs owner descriptor, InstallPpi/NotifyPpi calls, interface method RVA `0x250`, callback dispatch bytes, and Gfx/SMU counterpart registration records were checked. This establishes static registration/dispatch ownership; runtime invocation and token consumer remain unverified.

Corrections retained: counterpart descriptor parsing starts after both 16-byte GUIDs (`CBS GUID + Notify GUID`), not immediately after the CBS GUID. Final 26-check run passed.

## Manifest and final readback

Timestamp: 2026-09-20T06:13:00+05:00 (+05:00).

`sha256sum -c evidence/firmware-audit/20260920-clv-sync-stage2-cbs-ppi-lifecycle/SHA256SUMS` exited `0`; all three own entries returned `OK`. Final hashes:

```text
4daf338db0aa88a9b0e6bb2bb4a00b7c367c3f2b58eb32b5d42da1a02ebf0bab  evidence/firmware-audit/20260920-clv-sync-stage2-cbs-ppi-lifecycle/cbs_ppi_lifecycle_verify.py
3da09849219856afed76fc6c192e54f14ddcb4949d6fa75269d2b2c0c93cc9b1  evidence/firmware-audit/20260920-clv-sync-stage2-cbs-ppi-lifecycle/cbs-ppi-lifecycle-result.json
f370f592dfa14b7fca7da8c211fe333364a00e38076cbb58b591d9b4d42dfa49  docs/research/20260920-clv-sync-stage2-cbs-ppi-lifecycle.md
```

Final verifier rerun: exit `0`, stderr empty, `26/26` checks passed. Static CBS PPI registration and callback dispatch ownership is proven; runtime invocation remains unrun.

## Final target wording correction

Timestamp: 2026-09-20T06:35:00+05:00 (+05:00).

The corrected target mapping is explicit: FCLK uses record `0x1331` from the observed `+0x6A3` serializer source; UCLK uses `0x1204`. The earlier prose phrase `token-0x1332 consumer` is superseded and withdrawn as a target description; historical wording remains preserved in this action log.

## Correction result and final readback

Timestamp: 2026-09-20T06:37:00+05:00 (+05:00).

Corrected lifecycle report/verifier/result prose: target wording is now explicit FCLK record `0x1331` from observed `+0x6A3` source and UCLK record `0x1204`; stale `token-0x1332 consumer` target wording is withdrawn. Old wording remains preserved in superseded action-log history.

Final verifier: exit `0`, stderr empty, `26/26` checks passed. Manifest check: exit `0`, all entries `OK`.

```text
5fd3c326d58400cd41be1bc2cfec2dd39579760d78573bb60fcb7d48f56998ed  evidence/firmware-audit/20260920-clv-sync-stage2-cbs-ppi-lifecycle/cbs_ppi_lifecycle_verify.py
0167fd38f96553e3521705f947982d8091e2cc57f32a71728a9fb580ba59040c  evidence/firmware-audit/20260920-clv-sync-stage2-cbs-ppi-lifecycle/cbs-ppi-lifecycle-result.json
f370f592dfa14b7fca7da8c211fe333364a00e38076cbb58b591d9b4d42dfa49  docs/research/20260920-clv-sync-stage2-cbs-ppi-lifecycle.md
```
