# SMU clock entrypoint continuation — action log

## Intent (recorded before evidence execution)

- Timestamp: 2026-09-21T15:02:00+05:00 (Asia/Almaty).
- Actor: `/root/smu_clock_entrypoints`.
- Active object: exact plain CLV donor `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` and its byte-identical Robin-5 SMU payload.
- Last confirmed result: request candidates Queue 3 `0x1D` and raw Queue ID 4 `0x07` are statically mapped, but their data-source/provider edges and MCLK/UCLK/FCLK unit/selector semantics remain partial.
- Next executable action: run one new offline source/consumer verifier that traces Queue 3 `0x1D` mailbox input and P-state bulk-loader input into the shared target array, and Queue ID 4 `0x07` input into the static DF table/actuators; preserve CLV `AmdSetup+0x316=0x24`.
- Target: immutable CLV ROM SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; SMU Robin-5 SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37` at ROM `0x8FEF00`.
- Existing route check: reuse exact retained SMU byte/disassembly evidence and trace only new source edges; do not repeat queue-map census, telemetry aliases, `$INV` scans, or hardware probes.
- Safeguards: offline only; no board/register/NVRAM/network/install/ROM/candidate/flash action.
- Rollback: remove only this new evidence directory, report, and log if invalidated.

## Corrective rerun 1

The first dispatched verifier execution started but exited before producing a result JSON. Observed stderr: `ValueError: fromhex() arg must contain an even number of hexadecimal digits` at the assertion window for `FUN_0002EA08` low16-to-target bytes. This is a verifier literal transcription error, not an input/hash mismatch or firmware finding. The expected instruction bytes are corrected to the exact 30-hex-digit window `30e0f4a198a1000edad0cca0034c50`; rerun the same pinned test with explicit exit capture.

## Corrective rerun 2

The corrected literal windows passed, then the verifier stopped at the arithmetic check because the test passed the entire 32-bit row word into the U9.16 decoder. The existing static arithmetic uses the row's byte field (`row[0]` / `row[8]`) plus the DID byte, not a 32-bit packed row word. This is a verifier input-width error; it does not change source bytes or the candidate mapping. The rerun will use `u8(row+0)` and `u8(row+8)` for the fixed-point multiplier fields.

## Final result and readback

- Final verifier execution: exit `0`, status `PASS`, `25` checks; stderr empty.
- Result: `source-consumer-result.json` SHA-256 `08a30b4bc9f7153ff81f532ebf5203d355f27840c3aca59e58a51797b50f7b63`.
- Verifier: `trace_clock_sources.py` SHA-256 `540e8be034cdbdc8a42f63d504c2a3d4c42e7ad4feabd9e8ad9bdfec59afe233`.
- Evidence manifest: `SHA256SUMS.final`; readback must report `OK` for all listed files.
- Report final SHA-256: `0a3eb83123bb98c4c3d3494ed8e545d84cb068b25f46a1aef4b3d59f7cd644c4`.
- Bound object remained the exact plain CLV donor; `AmdSetup+0x316=0x24` remained unchanged. Hardware and provider-to-Setup joins remain unrun/unresolved.
