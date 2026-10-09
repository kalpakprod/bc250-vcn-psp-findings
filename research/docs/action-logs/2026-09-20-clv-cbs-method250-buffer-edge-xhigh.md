# CLV CBS method 0x250 output-buffer consumer edge — intent

- Timestamp: 2026-09-20T14:30:00+05:00 (Asia/Almaty; exact result timestamp appended)
- Actor: subagent `/root/svc4_register_target`
- Scope: follow one exact CBS method-0x250 indirect gateway edge from wildcard descriptor selection through adapter-owned output buffer/size pointer into the AmdFabric reader; identify serializer-only boundary versus token-0x1204 consumer.
- Inputs (read-only): pinned ROM; exact CbsBasePei/AmdFabric bodies; prior cbs dispatch and caller-chain machine results; no generic token census and no ABL fallback descriptor.
- Method: hash/reopen prior exact results, validate descriptor bytes and concrete D-buffer/D-size provenance, and report the first consumer after serialization.
- Expected effect: new verifier/result/stdout/stderr/report/manifest/action log only; no firmware/hardware/settings/shared plan/memory/MCP/Cutter/install/global config writes.
- Rollback: remove only this evidence directory, report and action log.

## Execution/result

- Initial verifier syntax error (f-string bracket) was corrected; no inputs changed.
- Two checker-only descriptor slice/endianness corrections were made against observed raw bytes; final command exited `0`, stdout `PASS`, `21/21` checks, stderr empty.
- Concrete result: method 0x250 wildcard/event descriptor selects callback +0x10; adapter owns D.buffer/D.size and serializes; AmdFabric uses size pass, HOB-backed fill pass and same-buffer `$INV` gate at 0x1DFC.
- Token-specific 0x1204 requester/final actuator remains unresolved; no runtime/hardware claim.
- Evidence/report/action paths reopened and hashes recorded in SHA256SUMS.final; no firmware/hardware/settings/shared edits.
- Rollback: remove only the unique evidence directory, report and action log.
