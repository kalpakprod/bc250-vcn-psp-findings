# Exact CLV ABL1 function-pointer and shared-structure dataflow

## Result

A raw pointer/Thumb-branch audit was applied to the exact decompressed ABL1 body (`af8cf562…74203a`) without treating flat mixed-code disassembly as a caller proof:

- raw little-endian function-pointer words `0x95FC` and Thumb entry `0x95FD`: zero occurrences;
- raw Thumb-2 branch candidates targeting `0x95FC/0x95FD`: zero;
- no downstream function-pointer owner is proven in this exact body.

The internal shared-structure dataflow is byte-backed:

- `0x9600` loads `r4=[r0]`, establishing the shared configuration root;
- `0x973E` writes selected minimum to `[r4+0x2BC]`;
- `0x9752` loads a separate channel pointer from `[r5+0xC]` and `0x9758` writes selected halfword to `[channel+0x20]`;
- `0x981E` writes the aggregate again to `[r4+0x2BC]`.

This distinguishes aggregate structure provenance from channel `+0x20` writes. No unit, MHz interpretation or 1:1 MCLK/UCLK/FCLK claim is made.

## Reproduction

```text
llvm-objcopy -I binary -O elf32-littlearm -B arm ABL1-clv-decompressed.bin ABL1-exact.o
llvm-objdump -D --triple=thumbv7 --start-address=0 --stop-address=0x17320 ABL1-exact.o
python3 -B evidence/firmware-audit/20260920-clv-abl1-downstream-pointers/abl1_pointer_dataflow_verify.py
```

Exit status: `0`; `13/13` checks passed. Machine result: `evidence/firmware-audit/20260920-clv-abl1-downstream-pointers/abl1-pointer-dataflow-result.json`.

Input: `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, full SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.

Evidence class: observed bytes + static analysis. No firmware execution, hardware operation, candidate, voltage, source, shared plan/memory, Ghidra/Cutter/MCP or installation change occurred.

## Boundary

The exact shared-structure consumer inside function `0x95FC` is proven; the downstream caller/function-pointer owner is not. Indirect/vector/external ownership remains the concrete blocker. This is not a blanket absence claim and does not infer synchronization or units.
