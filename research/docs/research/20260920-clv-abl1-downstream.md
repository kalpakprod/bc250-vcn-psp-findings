# Exact CLV ABL1 function-0x95FC downstream boundary

## Result

A fresh full-body Thumb disassembly was generated from the exact decompressed ABL1 payload (`af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`) using `llvm-objcopy`/`llvm-objdump` in the own evidence directory. The complete body contains **no direct `BL`/`BLX` call to function offset `0x95FC`**.

The reviewed function listing still proves its internal selection/writeback behavior:

- selected aggregate is stored at `[r4+0x2BC]` (`0x973E`);
- selected halfword is written back to each channel `[r0+0x20]` (`0x9758`);
- aggregate is written again at `[r4+0x2BC]` (`0x981E`) before return.

The exact downstream caller is therefore not present as a direct call in this ABL1 body. Indirect/vector dispatch or a closed external component remains unresolved; no historical global offset or imported source was used to infer it.

## Reproduction

```text
llvm-objcopy -I binary -O elf32-littlearm -B arm ABL1-clv-decompressed.bin ABL1-exact.o
llvm-objdump -D --triple=thumbv7 --start-address=0 --stop-address=0x17320 ABL1-exact.o
```

Executed through:

```text
python3 -B evidence/firmware-audit/20260920-clv-abl1-downstream/abl1_downstream_trace.py
```

Exit status: `0`; `6/6` checks passed. Direct-call count to `0x95FC`: `0`.

Artifacts:

- `evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o`
- `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`
- `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-downstream-trace-result.json`
- `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1_downstream_trace.py`

Evidence class: observed bytes + static analysis. No firmware execution, hardware operation, settings, source, shared plan/memory, Ghidra/Cutter/MCP or installation change occurred.

## Boundary

This is a concrete method/tool boundary after changing from snippet inspection to a fresh full-body disassembly. It does not prove that ABL1 is never invoked: indirect/vector calls and external/closed callers remain unknown. The next evidence would require a recovered dispatch table/caller or an authorized runtime trace, not another direct-literal scan.
