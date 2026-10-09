# CLV ABL1 function-pointer/dataflow follow-up — intent

Timestamp: 2026-09-20T07:18:00+05:00 (+05:00)
Actor: sync_stage2_consumer executor
Target: exact ABL1 function `0x95FC/0x95FD`; recover raw function-pointer/table references using reviewed runtime-base/provenance evidence, then distinguish exact shared-structure `[r4+0x2BC]` aggregate accesses from channel `[r0+0x20]` writes.

Method change: do not treat flat linear disassembly's zero direct calls as a caller-absence proof. Use raw pointer-word/Thumb-branch checks plus existing exact disassembly and register provenance.

Next executable action: run `evidence/firmware-audit/20260920-clv-abl1-downstream-pointers/abl1_pointer_dataflow_verify.py` against the pinned decompressed ABL1 body and reviewed provenance reports.

Expected effect: own pointer/dataflow evidence/report/log only. No firmware, ROM, hardware, shared plan/memory, Ghidra/Cutter/MCP, candidate, installation, voltage or settings changes.

Rollback: remove only this unique evidence directory, report and action log.

## Manifest and final readback

Timestamp: 2026-09-20T07:21:00+05:00 (+05:00).

`sha256sum -c evidence/firmware-audit/20260920-clv-abl1-downstream-pointers/SHA256SUMS` exited `0`; all three own entries returned `OK`. Final verifier rerun: exit `0`, stderr empty, `13/13` checks passed.

```text
8c2630f5930efd3e1dd1df2108e7e60c8f16456a92fc7675330672f6c1fe2a6b  evidence/firmware-audit/20260920-clv-abl1-downstream-pointers/abl1_pointer_dataflow_verify.py
dcf1e3d637934701d7fe0410953ab6a7c756de0f184fa0ea59377a20dd51e9fa  evidence/firmware-audit/20260920-clv-abl1-downstream-pointers/abl1-pointer-dataflow-result.json
cbbaec9f4a3bc8ca418a02c4058ac6ee8c21d172f33601f73b964db7d3e9b01b  docs/research/20260920-clv-abl1-downstream-pointers.md
```
