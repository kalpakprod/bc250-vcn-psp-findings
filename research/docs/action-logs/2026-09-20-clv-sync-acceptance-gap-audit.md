# CLV full 1:1 acceptance-gap audit — intent

Timestamp: 2026-09-20T11:15:00+05:00 (+05:00)
Actor: luna xhigh bounded executor
Target: current `specs/2026-09-20-clv-sync-development-plan.md`, exact pinned CLV donor, current offline builder/tests, existing safe stock/DF runbooks and exact-branch evidence provenance.

Bounded action: separate offline candidate semantic/build prerequisites from physical readback/default/synchronization/performance/stability gates; identify what safe board/recovery procedures are already validated and what remains unverified on the current target; inspect existing decoder provenance and only report already-documented outright-invalid/superseded branch claims. Execute the existing builder unit tests in a temporary test environment as a direct check of the current supported profile/refusal path. No new firmware/raw-byte scan, candidate output, hardware/network action, or plan/memory/global-config change.

Inputs/anchors:

- Plan `specs/2026-09-20-clv-sync-development-plan.md`; source identity is BIOS 5.00 clv `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16 MiB, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Existing host route: `scripts/build_clv_oc_candidate.py`, `tests/test_clv_oc_builder.py`.
- Existing procedures: `docs/runbooks/2026-09-19-df1400-request-test.md`, `docs/runbooks/2026-09-20-oc-stock-capture.md`, plus validated flash readback/recovery evidence in project action logs.
- Existing decoder provenance reviewed once: `docs/research/20260920-native-uclk-luna.md`, `docs/action-logs/2026-09-20-uclk-luna-independent-review.md`, `docs/research/20260920-clv-abl1-integration-review.md`, and current `memory/oc-recheck.md` corrections.

Expected effect: create only this uniquely named evidence directory, this report, and this append-only action log. The unit test writes only inside TemporaryDirectory; no project candidate is produced. No firmware/hardware/settings/network/plan/shared-memory/build/install/global config/MCP/source changes.

Rollback: delete only the unique evidence directory, research report, and this action log.

## Observed audit result

Timestamp: 2026-09-20T11:25:00+05:00 (+05:00)
Actor: luna xhigh bounded executor.

Read-only `get_goal` returned `goal: null`; no status mutation occurred. The active plan is `specs/2026-09-20-clv-sync-development-plan.md`, anchored to the exact CLV donor `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`, size 16 MiB. This audit did not open or alter firmware bytes beyond reading the already pinned donor metadata and existing manifests.

The existing builder regression route was actually executed in a temporary test environment:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_clv_oc_builder.py' -v
```

Observed exit `0`; 7 tests passed, including `test_unsupported_voltage_sync_and_frequency_rejected`. Literal stdout/stderr/exit are preserved in `evidence/firmware-audit/20260920-clv-sync-acceptance-gap-audit/builder-tests.stdout`, `.stderr`, `.exit`. All generated test candidate images/manifests were confined to `TemporaryDirectory`; no candidate was written under the project tree.

Source/test readback and decision: current `scripts/build_clv_oc_candidate.py` only exposes `df1400`, a stored request at `+0x704`, and the tests confirm `sync`, voltage, and unsupported frequency inputs are rejected. Existing `sync`-named output/manifests are historical stored-request artifacts, not physical 1:1 evidence. The offline semantic gates in the plan remain open, so the builder test does not authorize/build a 1:1 candidate.

Physical/recovery readback: existing action logs document successful `flashrom` + CH347T `W25Q128.V` full-chip capture/write/readback in prior sessions, including built-in `VERIFIED` and independent full-image `cmp`. The historical `read-a.bin` hash is `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`; it is not accepted here as a recovery image for the last recorded M6 chip state. The plan's requirement for two fresh current-target reads and current recovery/identity validation remains unrun. The readback _method_ is historically proven; current target state/recovery is not.

Decoder provenance readback: the native UclkDiv1M0 trace is raw-byte serializer evidence, not a clock branch decode. Existing reports already correct the earlier generic ABL1 fallback claim and reject a universal `0x60000` relocation base; no new raw scan or decoder run was performed. The exact ABL1 IFR comparison documents invalid selector codes `0x26`, `0x27`, and `0xFF` taking `0x232A`, which is relevant as a bounded selection rejection only; it does not establish a frequency or physical branch effect.

Report: `docs/research/20260920-clv-sync-acceptance-gap-audit.md`.
Evidence: `evidence/firmware-audit/20260920-clv-sync-acceptance-gap-audit/`.
Rollback: delete only this uniquely named evidence directory, report, and action log. No hardware, network, firmware, candidate, project plan, memory, install, global configuration or MCP state changed.

## Final artifact readback

Final `SHA256SUMS.final` contains 11 entries; `sha256sum -c` returned `OK` for all 11. The initially mistyped clock-applicability path was corrected to the existing path `evidence/firmware-audit/20260920-clv-independent-clock-counter-route/clock-counter-applicability-result.json`; no evidence bytes or findings changed.
