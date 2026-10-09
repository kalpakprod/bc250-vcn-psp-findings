# Exact ABL1 relocation-base coherence check

## Result

The bounded candidate relocation test **falsifies base `0x60000` as a universal runtime base**, while leaving the actual loader relocation unresolved.

Three independent PC-relative/absolute-literal anchors were checked against the exact payload:

1. Classifier `0x751E` loads literal at `0x7540`; literal value is `0x0006DB04`. Under candidate base `0x60000`, this maps to payload offset `0xDB04`, which contains an 8-halfword structured array:
   `0x01AC, 0x1800, 0x07C0, 0x0075, 0x17C0, 0x0075, 0x01B4, 0x1800`.
2. `0x8188` PC-relative literal load targets exact payload string `0x820C`, `"Synchronize MEMCLK Across Channels and Set Limits"`; this confirms internal PC-relative payload relationships but does not itself establish a physical base. Exact related strings at `0x81D4`, `0x8271`, and `0x828D` remain payload offsets; no direct xref is promoted from mixed code/data disassembly.
3. `0xB1F6` loads literal at `0xB218`, value `0x00067ABD`, then `0xB1F8` stores it into callable callback slot `[r0+0x52C]`. Under base `0x60000`, it maps to payload offset `0x7ABD`, whose bytes are ASCII `"lock Speed       :"`, not a local callable code prologue. This contradicts base `0x60000` as a universal code/data runtime base.

The `$PS1` header records `load_address=0`, but no relocation table or loader contract in the bounded container fields establishes the physical runtime base. Keep all addresses payload-relative until an external loader/runtime map is recovered.

## Boundary

- Exact table values under candidate `0x60000` are provisional observations only; candidate coherence is falsified by the callback pointer.
- The callback implementation remains external/indirect or otherwise unresolved.
- No MHz, physical domain, clock, synchronization, training, firmware execution, or hardware claim follows.

## Reproduction

```text
python3 evidence/firmware-audit/20260920-clv-abl-relocation-coherence/abl1_relocation_coherence_verify.py
```

Observed status: `15/15 PASS`.

Owned result: `evidence/firmware-audit/20260920-clv-abl-relocation-coherence/abl1-relocation-coherence-result.json` — SHA-256 `1f9b84eba2a9b44d959eec7e52217ba800aca873f602cf31a1d273325b78ecfe`.
