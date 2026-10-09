# Context+0x49 / +0x3B0 report integrity review

## Conclusion

The author report correctly proves the helper's `+0x49` byte width and indirect-call shape, but it **misbinds the C058 store base**. Fresh exact disassembly and an explicit R1 offset ledger show:

- Fallback path `0xB26A` loads the allocated table pointer into `R1` and `0xB274` stores that pointer into the context object's `[R4+0x44]`.
- Through `0xC058`, every explicit R1 adjustment is paired; the post-index store at `0xB326` also restores its temporary offset. Net R1 delta is zero.
- `0xC056` is a PC-relative literal load resolving to pool `0xC3D4`; the pool word is `0x006E5082`.
- `0xC058` executes `STR.W R0,[R1,#0x3B0]`, therefore writing **fallback table base + `0x3B0`**, not proven `context_R4 + 0x3B0`.
- Helper `0x109BC` separately loads `[R4+0x3B0]` and calls it. The author’s phrase “sole direct `+0x3B0` writer” must not be interpreted as proof that C058 initializes the helper’s context callback slot.

Thus `0x006E5082 - 0x57100 = 0x68DF82` being outside the local ABL1 payload is not, by itself, evidence of an external function target. In this corrected binding it is a field value stored in a fallback table object; its semantic use remains unresolved.

The HEAP/fallback branch shape and `context+0x40` high-bit merge are statically decoded, but runtime branch selection, table contents, context object identity, callback output, and physical/hardware effect remain unknown.

## Fresh independent evidence

Inputs:

- ABL1 payload: `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, 94,624 bytes, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Thumb listing: `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`, SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.

Independent verifier:

```text
python3 -B evidence/firmware-audit/20260920-native-gate-context49-3b0-review/verify_context49_3b0_base.py
```

Observed exit `0`, `61/61 PASS`, stderr empty. Fresh LLVM disassembly is preserved in `fresh-disassembly.txt`; all source/input bytes remained unchanged.

## Exact C058 boundary

Raw bytes and fresh disassembly establish:

```text
0xC056:  df 48       LDR R0,[PC,#0x37C]
0xC058:  c1 f8 b0 03 STR.W R0,[R1,#0x3B0]
0xC3D4:  82 50 6e 00 = u32 0x006E5082
```

PC calculation: `(0xC056 + 4) & ~3 = 0xC058`; `0xC058 + 0x37C = 0xC3D4`. The literal resolution is exact.

## Base/object correction

At `0xB228`, `R4=R0` is the context object. On the fallback path:

```text
0xB26A: LDR R1,[SP,#0x0C]       ; allocated table body
0xB274: STR R1,[R4,#0x44]       ; context->table = R1
```

The bounded R1 ledger from `0xB282` through `0xC058` contains these paired adjustments:

```text
+0x518/-0x518; +0x70/post-index -0x70;
+0x174/-0x174; +0x17C/-0x17C;
+0x264/-0x264; +0x284/-0x284; +0x2A4/-0x2A4; +0x2C4/-0x2C4;
+0x160/-0x160; +0x1A4/-0x1A4; +0x92C/-0x92C;
+0x0C8/-0x0C8; +0x5AC/-0x5AC; +0x5D4/-0x5D4.
```

Net delta is zero. Therefore C058 writes to `table+0x3B0`, while helper `0x109BC` reads `context+0x3B0` through `R4`; these are distinct bases unless an additional object alias is proven.

## HEAP/fallback and context+0x40 status

Static branch shape:

- `0xB23A` calls HEAP lookup `0x6374`; `CBZ R0,0xB264` selects the returned pointer path when status is zero.
- Nonzero status requests fallback allocation via `0x6238`; `CBZ R0,0xB26A` selects the returned table pointer and zeroes `0x652` dwords.
- Actual helper statuses, pre-existing HEAP node contents, and active path remain runtime-dependent.

The candidate callback loads `[R5+0x40]` at `0x9B82` and merges:

- bits `15..19` -> descriptor bits `15..19`;
- bits `20..27` -> descriptor bits `20..27`;
- bits `28..31` -> descriptor bits `28..31`.

The merge instructions are statically closed; the context value is not.

## Claim boundary

- **Corrected:** C058 is a fallback table-body `+0x3B0` write, not established initialization of helper `context+0x3B0`.
- **Observed/static:** literal resolution, register base, R1 ledger, HEAP/fallback control flow, and `context+0x40` bitfield merge.
- **Unresolved:** active HEAP/fallback selection, table contents, context/table object identity, external callback target semantics, callback output byte, physical register/map, clock or hardware behavior.

No existing worker output, firmware, ROM, settings, hardware, plan, memory, installation, MCP, or global configuration was modified.
