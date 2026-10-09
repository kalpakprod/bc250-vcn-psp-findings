# Exact CLV ABL1 memory-speed function independent review

## Result

Independent `llvm-objcopy`/`llvm-objdump` decoding and raw-byte checks confirm the exact clv ABL1 payload contains a Thumb-2 memory-speed policy function at payload offset `0x95FC`:

- Payload SHA-256: `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Raw little-endian prologue: `2d e9 f0 4f`; Thumb disassembly: `e92d 4ff0` (`push.w {r4-r11,lr}`).
- Context: `0x9600` loads `r4=[r0]`.
- Per-channel input: `0x9672` loads `ldrh r0,[r0,#0x20]`; `0x9674` stores it to `[r1,#0x278]`.
- Channel count: `0x96F0` loads `[r4+0x3C4]`, `0x96F4` loads byte `+0x74`.
- Reduction: `0x971A` loads `[r2+0x278]`, `0x971E` compares against the current candidate, `0x9722` updates the candidate when lower, and `0x973E` stores the selected value at `[r4+0x2BC]`.
- Writeback: `0x9758` stores the selected halfword to `[r0+0x20]`, loop count from `[r5+0x4B]` at `0x975A`.

This is a concrete memory-speed synchronization/training-policy structure match. It does **not** prove that `AmdSetup+0x316`/`$INV 0x11ED` populates this context, identify MHz units, connect UclkDiv1M0/FCLK, or establish 1:1:1 behavior.

## Independent evidence

- Worker source-aligned report: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-sync-stage2-abl-memory-function.md`, SHA-256 `b5cc539ca4acf00e047d557433565048e42c350fc43a2d97f2109468cccb45ed`.
- Worker result: `evidence/firmware-audit/20260920-clv-sync-stage2-abl-memory-function/abl1-memory-function-result.json`, `27/27 PASS`.
- Independent review result: `evidence/firmware-audit/20260920-clv-abl-memory-review/abl1-memory-review-result.json`, SHA-256 `e06dba13765d30d1040f2fb6bfeec65120ef6d7aed3152683c587936c811fd23`, `20/20 PASS`.
- Independent Thumb disassembly: `evidence/firmware-audit/20260920-clv-abl-memory-review/abl1-thumb-95fc-9870.txt`, SHA-256 `0ed462d9ee84d880b304ab7788bce83913621a7e4ebe1b2e8530799cbffec13a`.

Historical `ABL1_decompiled.c` is structurally aligned with this function, but source-text-to-binary identity remains unclaimed. The observed `-0x100` address delta is an alignment observation, not a flat-base assumption.

## Boundary

The function's minimum reduction is over runtime table/context values, not a decoded frequency unit. The missing decisive edge is the caller/provider that populates `[r0+0x20]` and the context at `[r4+0x3C4]`, then connects it to native `$INV`/APOB inputs. Firmware execution, memory training, physical clocks, voltage, synchronization, and hardware acceptance remain unrun.

## Address/base and function-boundary correction

The exact `$PS1` header for ABL1 has `load_address=0x00000000`, `rom_size=0xC020`, and decompressed length `0x171A0`. Therefore `0x95FC` is an exact payload-relative address under the header; no nonzero relocation base is encoded. The ARM entry at payload `0x0` is:

```text
0x0000: e92d4010    push {r4,lr}
0x0004: e59f2004    ldr r2,[pc,#4]
0x0008: e12fff32    blx r2
0x0010: 0005e02d    literal target 0x0005E02D
```

The literal `0x0005E02D` is outside the decompressed payload, so the entry trampoline does not provide a direct in-payload call to `0x95FC`; its external/runtime target remains unknown. No physical runtime address beyond the payload-relative model is claimed.

Independent disassembly extends the function body beyond the worker's `0x95FC..0x9870` window: `0x9744 -> 0x984E`, continuation through `0x98AA`, and a code-to-data boundary at `0x98AC` where the raw string begins `\nAGESA MEM - Multi-Die - DRAM Speed Sync`. The effective bounded code range is `0x95FC..0x98AB`; `0x984A` is one return path, while `0x984E..0x98AA` is a continuation block reached by an alternate branch.

Observed register contract in this function: `R0` points to a context pointer (`0x9600: ldr R4,[R0]`); `R5` is a caller-supplied outer structure accessed at `+0x0C/+0x4B`; `R1` is formed as `R4 + (channel_index<<2)` for the `+0x278` table store. These are static calling/dataflow observations, not a recovered caller or physical memory-domain identity.
