# CLV ABL1 aggregate+0x2BC consumer — intent

Timestamp: 2026-09-20T07:25:00+05:00 (+05:00)
Actor: sync_stage2_consumer executor
Target: exact in-payload load of shared aggregate `+0x2BC` outside function `0x95FC..0x98AB`, recover struct provenance and the first consumer control branch/call.

Next executable action: run `evidence/firmware-audit/20260920-clv-abl1-aggregate-consumer/abl1_aggregate_consumer_verify.py` using exact ABL1 bytes and reviewed Thumb disassembly.

Expected effect: own aggregate-consumer evidence/report/log only. No firmware, ROM, hardware, shared plan/memory, Ghidra/Cutter/MCP, candidate, installation, voltage or settings changes.

Rollback: remove only this unique evidence directory, report and action log.

## Observed result

Timestamp: 2026-09-20T07:28:00+05:00 (+05:00).

Final command:

```text
python3 -B evidence/firmware-audit/20260920-clv-abl1-aggregate-consumer/abl1_aggregate_consumer_verify.py
```

Exit status: `0`, stderr empty, `18/18` checks passed. The exact consumer edge is `0x7E40 [root+0x2BC] -> r1 -> BL 0x751C -> class result -> BL 0x130C`. No units or synchronization inference was made.

## Manifest and final readback

Timestamp: 2026-09-20T07:29:00+05:00 (+05:00).

`sha256sum -c evidence/firmware-audit/20260920-clv-abl1-aggregate-consumer/SHA256SUMS` exited `0`; all three own entries returned `OK`. Final verifier rerun: exit `0`, stderr empty, `18/18` checks passed.

```text
5a0658ec76dab560dbc96095c2ef4647c5017646342241e45c5b86ba6df87510  evidence/firmware-audit/20260920-clv-abl1-aggregate-consumer/abl1_aggregate_consumer_verify.py
a8e547c14b20ab58997ae37d9728e6a68a5a858d0882ad352e95c289a30e780e  evidence/firmware-audit/20260920-clv-abl1-aggregate-consumer/abl1-aggregate-consumer-result.json
5924f527982d9491ad3da983b9ecb85b8ad07c1eafd935c992187353eb9bbd8a  docs/research/20260920-clv-abl1-aggregate-consumer.md
```

## Final table-anchor correction

Timestamp: 2026-09-20T07:31:00+05:00 (+05:00).

Added exact PC-relative policy-table load/bytes at classifier `0x751C` (`0x751E` table load, `0x7540` table bytes). Final verifier rerun: exit `0`, stderr empty, `18/18` checks passed.

## Final readback

Timestamp: 2026-09-20T07:32:00+05:00 (+05:00).

Final verifier rerun: exit `0`, stderr empty, `18/18` checks passed. Manifest: exit `0`, all entries `OK`. Exact PC-relative classifier table anchor is now included; no units/synchronization inference.

## Final table-anchor correction and readback

Timestamp: 2026-09-20T07:31:00+05:00 (+05:00).

Added exact PC-relative policy-table load/bytes at classifier `0x751C` (`0x751E` table load, `0x7540` table bytes). Final verifier rerun: exit `0`, stderr empty, `18/18` checks passed. No units or synchronization inference.

## Final rerun/readback

Timestamp: 2026-09-20T07:33:00+05:00 (+05:00).

Exit `0`, stderr empty, `18/18` verifier checks passed; SHA256SUMS returned `OK` for the runner, result and current report after refreshing their manifest. Exact internal consumer is proven; downstream service semantics remain unresolved.
