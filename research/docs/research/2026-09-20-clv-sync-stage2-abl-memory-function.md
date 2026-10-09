# Stage 2 — Exact ABL1 memory-policy function match

## Exact function/control-flow match

The exact clv ABL1 decompressed payload (`SHA-256 af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`) contains a Thumb-2 function at payload offset `0x95FC` with prologue `e92d4ff0`. Its control/data structure matches historical `ABL1_decompiled.c` function `FUN_000096fc` (source label `0x96FC`; observed address delta `-0x100`, not assumed as a flat base):

- `R4 = [R0]` context at `0x9600`.
- Channel/P-state structure pointer `[R4+0x3C4]`, count byte `+0x74` at `0x96F0/0x96F4`.
- Per-channel memory-speed input: `LD RH [R0+0x20]` at `0x9672`, where `R0=[R5+0x0C]`.
- Per-channel table store: `STR.W ...,[R1+0x278]` at `0x9674`.
- Reduction loop scans table entries at `+0x278` and stores selected minimum to `[R4+0x2BC]` at `0x973E`.
- Writeback loop stores the selected value to `[R0+0x20]` at `0x9758`, for channel count `[R5+0x4B]` at `0x975A`.

The historical source contains the same memory-speed synchronization structure: per-channel reads from `param_1[3]+0x20`, table population at `+0x278`, reduction, and writeback. This is a concrete source-to-current-binary structural match for a memory-speed synchronization/training-policy function.

## What this does and does not establish

This function demonstrates a memory-speed synchronization policy over runtime structures and a selected/minimum speed writeback. It does **not** establish:

- that exact native clv `AmdSetup+0x316`/INV `0x11ED` populates this ABL context;
- that the selected values are MHz or which divider/rate conversion applies;
- that `UclkDiv1M0`/`Memory P-state`/FCLK controls reach this function;
- physical training acceptance, hardware clocks, or synchronous crossing.

The historical source remains provenance/decompilation evidence; source-file-to-binary hash identity is still not claimed. The exact function match is based on current payload bytes, ISA-aware disassembly, and shared field/control-flow offsets.

## Reproduction

```text
llvm-objcopy -I binary -O elf32-littlearm -B arm ABL1-clv-decompressed.bin /tmp/abl1-exact.o
llvm-objdump -D --triple=thumbv7 --start-address=0x95fc --stop-address=0x9870 /tmp/abl1-exact.o
python3 evidence/firmware-audit/20260920-clv-sync-stage2-abl-memory-function/abl1_memory_function_verify.py
```

Observed verifier exit `0`; stderr empty; `27/27` checks passed. Own evidence manifest exited `0`; all files `OK`.
