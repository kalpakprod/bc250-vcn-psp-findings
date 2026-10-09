# Exact CLV ABL1 aggregate consumer and classifier semantics review

## Result

Independent raw-byte checks confirm the downstream path outside the memory-speed producer:

```text
0x75CC: r0 context -> r6
0x7E3E: r0 = [r6]
0x7E40: r6 = [r0 + 0x2BC]
0x7E44: r0 = [sp + 0x20]  ; selector
0x7E52: r1 = r6
0x7E54: BL 0x751C
0x7E58: UXTB result
0x7E5A: store aggregate/result stack state
```

Classifier `0x751C` semantics are more specific than “index range”:

- loads a table pointer from literal at `0x7540`: raw value `0x0006DB04`;
- loops exactly eight times (`r4=8`, index `r2=0..7`), reading halfwords at `table + 2*index` and comparing each against `r1`;
- match and no-match both converge to `0x7532`; no error/status return distinguishes no match;
- compares selector `r0` with `6`; returns class `7` if equal, otherwise class `0`.

The table pointer `0x0006DB04` lies outside the exact decompressed ABL1 payload (`0x171A0` bytes), so exact table values are **not available** from this payload and are not inferred. Selector provenance is byte-backed: initialized `0xFF` at `0x75DC/0x75DE`, conditionally set to `6` at `0x7636/0x7644`, then consumed at `0x7E44`.

## Boundary

This proves a control-classifier consumer of aggregate `+0x2BC`, not its units or physical domain. No MCLK/UCLK/FCLK identity, divider, synchronization, or hardware behavior follows. The upstream producer context and external classifier table remain unresolved.

## Reproduction

```text
python3 evidence/firmware-audit/20260920-clv-abl1-aggregate-review/abl1_aggregate_review_verify.py
```

Observed status: `14/14 PASS`.

Owned evidence:

- `evidence/firmware-audit/20260920-clv-abl1-aggregate-review/abl1-aggregate-review-result.json` — SHA-256 `a0f69ced2b24295b109562278c1717ae256c4dfaa7007e3ac828032d92ac6973`
- `evidence/firmware-audit/20260920-clv-abl1-aggregate-review/abl1_aggregate_review_verify.py` — SHA-256 `ca8d739ac1ed2f74e53d22ee75aa2d24613ecad74bf80dc6ab8cf096b885fddd`
