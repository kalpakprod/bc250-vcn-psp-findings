# Native UclkDiv1M0 consumer trace — intent

Timestamp: 2026-09-20T00:00:00+05:00 (recorded during bounded offline run)
Actor: native_consumer_luna executor
Target: exact BIOS 5.00 clv, SHA-256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8; exact-clv census module CbsBasePei (SHA-256 6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77).
Command/procedure: read-only byte-backed analysis of existing `evidence/firmware-audit/20260919-inv-token-consumers` artifacts; verify Setup+0x330 -> record 0x1204 serializer, callback-table edge to 0x36c0 -> 0x36f0, and bounded absence of a final direct 0x1204 consumer in the retained census.
Rationale: advance one narrow native UclkDiv1M0 path without repeating generic mailbox searches or modifying firmware/shared plans.
Expected effect: produce a machine-readable evidence report and reproducible verifier; no ROM, hardware, installation, global setting, shared analysis, plan, or memory write.
Rollback: delete only the uniquely named evidence/report files and this action-log pair; source artifacts remain untouched.

## Observed result

Timestamp: 2026-09-20T04:05:32+05:00 (+05:00).

Executed:
`python3 /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-native-uclk-luna/uclk_consumer_trace.py`

Observed stdout:
`{"status": "PASS", "checks": 21, "fresh_result": "For setup bytes 00/01/7f at +0x330, the immediate callback output record remains ID 0x1204 with value 00/01/7f respectively. The first static callback is an INV adapter (0x36c0->0x36f0), not a clock/register consumer."}`

Artifacts written only under the uniquely named evidence/research/action-log paths:

- `evidence/firmware-audit/20260920-native-uclk-luna/uclk_consumer_trace.py`
- `evidence/firmware-audit/20260920-native-uclk-luna/uclk-consumer-trace.json`
- `docs/research/20260920-native-uclk-luna.md`

Readback: 21 checks passed. Exact path is `AmdSetup+0x330 -> CbsBasePei+0x9cc4/0x9ce4 -> INV record 0x1204 -> callback table RVA 0x13e20 -> 0x36c0 -> 0x36f0`. Final UCLK/DF actuator remains unresolved at the bounded census boundary. No firmware, shared plan/memory, hardware, installation, global setting, or commit was changed.

Rollback/readback: delete only the three artifacts above and this uniquely named action-log file; original ROM/module hashes remain unchanged.

Final readback ledger:

- `evidence/firmware-audit/20260920-native-uclk-luna/artifacts.sha256` records the final own evidence hashes.
- Recheck source hashes matched the pre-write ledger byte-for-byte; JSON parse and verifier rerun passed.

## G7 correction from independent review

Timestamp: 2026-09-20T04:25:00+05:00 (+05:00).
Reviewer: `docs/action-logs/2026-09-20-uclk-luna-independent-review.md`.

Corrections applied to the own report, verifier, and JSON:

- Final consumer wording now says **unresolved within bounded static-analysis coverage of the 233-module census**. It no longer implies that the consumer lies outside the census.
- The caller-matrix statement now says CbsBasePei is **omitted by the matrix-generation rule**, not negatively classified as a non-reader.
- `+0x9ce4` is identified as the Setup+0x330 source load; the actual record-byte store is explicitly checked and reported at `+0x9cea` (`88 41 03`).
- Verifier check count increased from 21 to 22; rerun required below.

Observed correction test:
`python3 /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-native-uclk-luna/uclk_consumer_trace.py`

The corrected run must report `status=PASS`, `checks=22`. Reopen/read back the corrected JSON and research report before returning. No shared plan/memory or source evidence was edited.

Correction readback result: corrected verifier exited 0 with observed `status=PASS`, `checks=22`. JSON re-open confirmed the `+0x9cea` store check passed and the bounded-coverage wording is present. Research report re-open confirmed the matrix-omission qualification and no exclusion claim. Pinned ROM/module hashes remain unchanged.
