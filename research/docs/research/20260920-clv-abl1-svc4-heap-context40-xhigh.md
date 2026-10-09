# CLV ABL1 SVC#4 HEAP/fallback branch and context+0x40 producer

## Current

The exact HEAP-versus-fallback branch is resolved at the caller/consumer boundary:

```text
0xB23A: BL 0x6374
0xB23E: CBZ R0,0xB264

0x6374 match:    0x63B6 sets R0=0
                  -> B264/B266 installs [SP+0x18] at [context+0x44]
                  -> B268 returns through B25E; fallback initializer is skipped

0x6374 no-match: 0x63E2 sets R0=2
                  -> B240/B252 requests fallback allocation
                  -> B26A/B274 installs [SP+0x0C] at [context+0x44]
```

This is exact static polarity, not a runtime observation. An invalid HEAP signature returns nonzero and does not take B264; later handling is outside this bounded branch.

The nearest exact producer of callback context+`0x40` is also resolved:

```text
function 0x7378:
  R5 = arg0                    (0x737C)
  R6 = arg1                    (0x7384)
  R4 = [R6+0x3C4]              (0x73AE)
  [R5+0x8] = R4                (0x73B2)
  R0 = [R4+0x4]                (0x73B6)
  [R5+0x40] = R0               (0x73B8)
```

Callback `0x9AD8` reads `[R5+0x40]` at `0x9B82`, then inserts source bits into descriptor bits `15..19` and `28..31`. Thus the raw fallback descriptor chain is now qualified by a precise dynamic high-field source: `context+0x40 <- [[arg1+0x3C4]+0x4]` for the initializer function's parent object.

## Boundary

The active dispatcher at `0x10958` loads `[R0+0x660]`; this bounded check does not prove that its current `R0` object is the same object used as `R5` at `0x7378`. Runtime HEAP contents, active context identity, SVC#4 translation, physical SMN/MMIO destination, and hardware behavior remain unresolved. No stronger address claim follows.

## Inputs and hashes

- Exact ABL1: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Exact listing: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`, SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- Prior descriptor join result reused by hash: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-join-xhigh/descriptor-join-result.json`, SHA-256 `31e2c2952d6d4074ddaf52fea5bed68f7656ec6a0867e225e06aab7b432f6a5c`.
- Prior callback result reused by hash: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/abl1-context660-callback-result.json`, SHA-256 `cf16bf73c370bac1c4426f7c79e64890898a11da7743304528ddeccfe3cd7ecb`.

## Verification

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-heap-context40-xhigh/verify_heap_context40.py \
  > /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-heap-context40-xhigh/verifier.stdout \
  2> /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-heap-context40-xhigh/verifier.stderr
```

Observed exit `0`, `37/37 PASS`, stderr empty.

- Verifier: `evidence/firmware-audit/20260920-clv-abl1-svc4-heap-context40-xhigh/verify_heap_context40.py`.
- Machine result: `evidence/firmware-audit/20260920-clv-abl1-svc4-heap-context40-xhigh/heap-context40-result.json`.
- Literal stdout/stderr: same directory, `verifier.stdout`, `verifier.stderr`.
- Manifest: same directory, `SHA256SUMS.final`.
- Action log: `docs/action-logs/2026-09-20-clv-abl1-svc4-heap-context40-xhigh.md`.

Evidence class: observed-bytes + static-analysis. No firmware, hardware, settings, shared plan/memory, source input, MCP/Cutter, installation, global config, candidate or commit changed.

## Next gate

A stronger active-path claim requires an authorized read-only capture or independent static join proving the current dispatcher `R0` object equals the `0x7378` parent object, plus the runtime HEAP/body selection and context fields. Do not map the dynamic descriptor to a physical register without SVC#4 translation evidence.
