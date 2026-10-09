# CLV ABL1 SVC#4 exact fallback descriptor-table pointer join

## Current

The bounded symbolic Thumb dataflow **establishes the same fallback table base** at the exact static stores relevant to callback index `0x61E`:

```text
B26A: R1 = TABLE = [SP+0x0C]           (fallback allocation result)
B274: [context+0x44] = TABLE
...
C202/C206/C210: R1 = TABLE+0x70; R0 = R1+0x1808 = TABLE+0x1878
               [TABLE+0x1878] = 0x006CA7C0
               -> table index 0x61E
CC18/CC22:     R1 = TABLE+0x70; R2 = 0x1AB8
               [TABLE+0x1B28] = 0x006F47C0
               -> table index 0x6CA
```

Therefore the exact **fallback** descriptor chain is:

```text
table[0x61E] = 0x006CA7C0
nested_index = (0x006CA7C0 >> 12) & 0xFFF = 0x6CA
table[0x6CA] = 0x006F47C0
```

The nested raw descriptor is `0x006F47C0` (low12 `0x7C0`, bits0..5=`0`, bits6..11=`31`, raw kind bits27..29=`0`, bit30=`0`). The callback later merges `[context+0x40]` into descriptor bits15..19, 20..27, and 28..31, so the final kind/R4 is not fixed by the raw descriptor alone. The existing HEAP path at `B264/B266` returns before fallback initialization; active HEAP-versus-fallback selection remains unresolved.

No physical SMN/MMIO address is claimed. The exact SVC#4 map/translation and runtime context merge remain unavailable.

## Exact static path

`0xB228` first queries HEAP key `0x01240000` through `0x6374`. If the lookup succeeds, it installs `[SP+0x18]` at `[context+0x44]` and returns; the fallback table initializer is skipped. On lookup miss, it allocates size `0x26C0`, type `4`, key `0x01240000` through `0x6238`, stores the returned pointer at `[context+0x44]`, zeroes `0x652` entries, and continues through the large fallback initializer.

The symbolic CFG starts at `B26A` with `R1=TABLE` and follows direct Thumb branches/arithmetic. It reaches both target stores with `R1=TABLE+0x70`; the extra `+0x70` is why a linear `R1+0x1878` transcription was wrong. The stores are:

- `C202/C206/C210`: `R1+0x70 + 0x1808 = TABLE+0x1878`; pool `C47C` contains `0x006CA7C0`.
- `CC18/CC22`: `R1+0x70 + 0x1AB8 = TABLE+0x1B28`; pool `CF40` contains `0x006F47C0`.

This is an exact same-base join for the fallback path, not a runtime capture.

## Callback and helper boundary

The prior exact callback result remains reused by hash (`58/58 PASS`, not rerun). Its callback reads `table[0x61E]`, then `table[(first_slot>>12)&0xFFF]`, merges context fields, and passes `R1=R4` to `0x6DA4`/`0x6E70`. This continuation adds the fallback numeric table chain only.

The raw descriptor `0x006F47C0` has kind bits `0`; context `[+0x40]` can rewrite high descriptor fields before the kind dispatch. The callback's `context+0x49` is separately provider-sourced; neither value is promoted to a physical address. SVC#4's page split still gives only the caller encoding contract.

## Inputs and hashes

- Exact ABL1 payload: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Exact Thumb listing: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`, SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- Prior descriptor-source result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-source-xhigh/descriptor-source-result.json`, SHA-256 `14f71a9b17faa3b669681c574036ccb8edb3d75b7fde966a73aa0beb9dd9f7c0`.
- Exact SMU map report reused for context only: `docs/research/2026-09-20-oc-df-init-route.md`, SHA-256 `3122a0dce28bc61942a22d567acdc29e318a714097b48877eb0391094a7d0e43`.

## Verification

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-join-xhigh/verify_descriptor_join.py \
  > /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-join-xhigh/verifier.stdout \
  2> /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-join-xhigh/verifier.stderr
```

Observed exit `0`, `56/56 PASS`, stderr empty.

- Verifier: `evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-join-xhigh/verify_descriptor_join.py`.
- Machine result: `evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-join-xhigh/descriptor-join-result.json`.
- Literal stdout/stderr: `verifier.stdout`, `verifier.stderr` in the same directory.
- Manifest: `SHA256SUMS.final` in the same directory.
- Action log: `docs/action-logs/2026-09-20-clv-abl1-svc4-descriptor-join-xhigh.md`.

Evidence class: `observed-bytes` + `static-analysis`. No firmware, hardware, settings, shared plan/memory, MCP/Cutter, install, global configuration, source inputs, candidate, or commit changed.

## Remaining boundary / gate

The static fallback chain is now joined. The remaining blocker is whether the active context uses fallback or an existing HEAP body and what `[context+0x40]`/`[context+0x49]` contain at invocation. A stronger physical-register claim requires an authorized read-only runtime capture or PSP SVC#4 handler/translation recovery. No write is proposed.

## Superseding correction to earlier descriptor-source candidate wording

The final CFG check establishes that the two previously highlighted linear candidates are **not** the FCLK table slots:

- `C7DE/C7E8` is reached with `R1=TABLE+0x70`; `R0=R1+0x1878` therefore stores `0x006D17C0` at `TABLE+0x18E8`, table index `0x63A`.
- `C79A/C7A0` is reached with `R1=TABLE+0x70`; `R2=0x1B44` therefore stores `0x0800027C` at `TABLE+0x1BB4`, table index `0x6ED`.

They must not be used as `table[0x61E]` or `table[0x6CA]`. The prior conditional `0x0800027C -> R4=0x5027C` concordance is withdrawn as an FCLK-table conclusion. The exact fallback FCLK chain is instead:

```text
table[0x61E] = 0x006CA7C0    (C210; R1=TABLE+0x70, +0x1808)
table[0x6CA] = 0x006F47C0    (CC22; R1=TABLE+0x70, +0x1AB8)
```

This is a G7 correction to the earlier `descriptor-source` report's candidate-only language; prior artifacts remain historical and unedited. The raw descriptor `0x006F47C0` has low12 `0x7C0` and raw kind zero; callback `[context+0x40]` merge can alter the high kind fields before R4 dispatch. No physical SMN/MMIO address follows.
