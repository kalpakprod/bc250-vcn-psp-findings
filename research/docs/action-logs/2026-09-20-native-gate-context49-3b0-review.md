# Context+0x49 / +0x3B0 report integrity review — intent

Timestamp: 2026-09-20T14:10:00+05:00 (+05:00; exact execution time appended)
Actor: luna xhigh bounded reviewer
Target: `docs/research/2026-09-20-native-gate-context49-3b0.md` and exact ABL1 payload/listing.

Bounded action: independently verify the report's C058 instruction boundary, PC-relative pool address and stored literal, actual register used for the +0x3B0 store, and whether the same fallback initializer preserves that register as the context+0x44 table base through C058. Reconcile the literal `0x006E5082` under conditional base `0x57100`; do not infer that an outside-payload mapping is invalid solely from its size, and do not decode the external target body. Reuse the existing SMU map report only to state a conditional concordance after the ABL1 arithmetic is independently established.

Read-only anchors:

- ABL1 payload `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Exact Thumb listing `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`, SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- Author report/result `docs/research/2026-09-20-native-gate-context49-3b0.md` and `evidence/firmware-audit/20260920-native-gate-context49-3b0/`.

Method: temporary ARM ELF from exact payload, fresh LLVM disassembly of C020-C07A, B228-B2F8, and helper 109BC, direct raw-byte/PC-relative arithmetic, and a bounded symbolic register-offset ledger for R1 from fallback table installation to C058. No existing verifier or worker output is overwritten.

Rollback: remove only this unique review evidence directory, report and action log.

## Observed independent result

Timestamp: 2026-09-20T14:18:30+05:00 (+05:00).

Fresh temporary ELF/disassembly and direct raw-byte verifier completed:

```text
python3 -B evidence/firmware-audit/20260920-native-gate-context49-3b0-review/verify_context49_3b0_base.py
```

Observed exit `0`, `61/61 PASS`, stderr empty. Exact findings:

- C056 PC-relative literal resolves to C3D4; pool u32 is `0x006E5082`; C058 store uses R1 plus `0x3B0`.
- Fallback B26A loads table pointer into R1; B274 stores it into context R4+0x44.
- R1 add/sub/post-index ledger from B282 through C058 has net delta zero; C058 therefore writes table-body+0x3B0.
- Helper 109BC reads context-R4+0x3B0, so the report’s C058-as-context+0x3B0 interpretation mixes object bases.
- HEAP/fallback branch shape is statically closed, but runtime selection is unresolved.
- Context+0x40 high-bit merge into descriptor fields is statically closed; its runtime value is unresolved.

This corrects the author report’s pointer-target interpretation without modifying its files or result. The literal’s outside-payload arithmetic under conditional base `0x57100` is retained as a numeric fact only, not a proof of invalidity or external executable mapping.
