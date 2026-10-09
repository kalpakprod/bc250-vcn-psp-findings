# Item-17 alias boundary — ABL1 local stack versus context-table pointer

## Conclusion

The new bounded disassembly rejects the assumption that `0x6D10=1` alone guarantees `0x95FC` takes branch `BLS 0x9744 -> 0x984E`. The helper initially writes `1` to the stack output field `[SP+0x164]`, but the same function then calls `0x6B78` to fill 0x40 bytes through dynamic destination `R4+0x278` before reading the field. The local code does not establish whether those ranges alias.

- Stack output block: `[SP+0x160, SP+0x17C)`, with the comparison word `[SP+0x164, SP+0x168)`.
- Fill target: `[R4+0x278, R4+0x2B8)`, filled with `0xFF` bytes.
- The guard word is overwritten if these intervals intersect at `[SP+0x164, SP+0x168)`, equivalently if `R4+0x278 < SP+0x168` and `SP+0x164 < R4+0x2B8`.
- The callback argument lineage shows the base is caller-supplied and dynamic: item dispatch passes the outer context; the handler loads its root/context pointer from `[R0]`. No static address or lifetime relation to the handler's current SP is present in the bounded windows. Distinct registers/expressions are not proof of non-aliasing.

Thus the conditional `item 0x17 -> 0x95FC` table dispatch remains a static candidate under base `0x57100`; the actual `DD4` branch is **inconclusive on alias**. If disjoint, the field remains `1` and the branch reaches `0x984E`. If the fill overlaps the gate word, `0xFF` can change the branch condition and permit the multi-channel/`0xDD4` path. The next offline boundary is the actual callback context address/lifetime or loader/runtime mapping; this assignment had no live values with which to prove it.

### Checked outgoing value

On the non-overlap branch, `0x984E` reads a halfword from a runtime table at `0x986E`, stores it into context `+0x2BC` at `0x989A`, and returns callback status `R0=0`. Dispatcher `0x0E50` checks that status at `0x0EA8` and exits at `0x0E84` because the selected row pointer is nonzero. The table's numeric halfword was not identified from these bytes. It is not evidence for MHz, a physical rate, or 1:1:1.

If aliasing changes the gate and the callback enters `0xDD4`, that helper has its own separate local `0x6C20 -> 0x6D10=1 -> BLS 0xE14` path, which returns zero before the `0x0FB8` call. The SVC6 wrapper callsites remain on alternate paths; global or indirect SVC6 reachability is not concluded here.

## Inputs and source scope

- Exact ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, `16,777,216` bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Exact ABL1 payload: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-sync-stage2-abl-memory/ABL1-clv-decompressed.bin`, `94,624` bytes, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Existing exact ELF object reused read-only: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o`, SHA-256 `54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135`.
- Scope excludes the separate memory-clock reader work owned by `/root/memory_clock_units`, specifically its `0x7FC2 -> 0x8428` caller-pointer identity; this report follows only item-17 local argument registers through the callback entry to identify the missing address/lifetime fact.

## Reproduction and verification

Tool: `/usr/bin/llvm-objdump`, LLVM `22.1.8`. Four fresh bounded Thumb listings were generated from the existing exact object:

```text
llvm-objdump -D --triple=thumbv7 --start-address=0x0c60 --stop-address=0x0c8e ABL1-exact.o
llvm-objdump -D --triple=thumbv7 --start-address=0x0e50 --stop-address=0x0ea8 ABL1-exact.o
llvm-objdump -D --triple=thumbv7 --start-address=0x95fc --stop-address=0x9652 ABL1-exact.o
llvm-objdump -D --triple=thumbv7 --start-address=0x6b78 --stop-address=0x6b84 ABL1-exact.o
```

All four exited `0`, with empty stderr. Verifier command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  evidence/firmware-audit/20260921-item17-alias-review/item17_alias_bounds.py \
  > evidence/firmware-audit/20260921-item17-alias-review/alias-analysis.stdout \
  2> evidence/firmware-audit/20260921-item17-alias-review/alias-analysis.stderr
```

Observed result: command exit `0`; `32/32 PASS`; stderr empty; machine status `INCONCLUSIVE_ALIAS_UNRESOLVED`. This is a passed verification of the exact bounds/missing fact, not a positive no-alias result.

## Byte-backed argument/dataflow

1. Item dispatch passes caller R4 in R2 at `0x7E38`; dispatcher `0x0C60` retains R2 in R6 and calls `0x0E50` with it in R2. `0x0E50` saves that incoming value in R10; on key match it passes R0=R10 to the indirect callback at `0x0EA6`.
2. At `0x95FC`, entry instruction `0x9600` loads `R4=[R0]`. This dynamic caller-supplied pointer is the base later used for `[R4+0x278]`.
3. The function allocates its own local frame (`SUB SP,#0x17C` at `0x9602`). At `0x962A` it passes `SP+0x160` to `0x6C20`; `0x6C20` writes the return value from `0x6D10` at output offset `+4`. `0x6D10` returns literal `1`.
4. At `0x9636`, it separately computes `R0=R4+0x278`; `R1=0xFF` and `R2=0x40` are prepared, then `0x963A` calls `0x6B78`. Exact helper instructions `0x6B7A/0x6B80` store one byte through post-incrementing R0 and loop until R2 wraps below zero; the bounded fill covers 0x40 bytes.
5. At `0x963E/0x9644`, the function loads and compares `[SP+0x164]` after that fill call. The raw code supplies neither a concrete absolute `R4` value nor a stack pointer value to compare, and no object/allocation/lifetime edge in this slice proves disjointness.

## Reachability classification

| Question                                                 | Result                | Evidence boundary                                                                                                                         |
| -------------------------------------------------------- | --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Does local helper `0x6D10` return 1?                     | **PASS**              | Exact local instruction sets R0=1 before returning.                                                                                       |
| Does that initial value alone prove the `0x984E` branch? | **NO**                | Later `0x6B78` writes through dynamic `R4+0x278`; its possible overlap with `[SP+0x164]` is unresolved.                                   |
| Can the exact disassembly rule out the alias?            | **NO**                | The R4 base is passed in dynamically; no address/lifetime relation to current SP is present.                                              |
| What path/value is observed if no overlap?               | **PASS, conditional** | Single-state table halfword at `0x986E` goes to `context+0x2BC` (`0x989A`); callback returns status zero. Numeric table entry unresolved. |
| Can this establish DD4 reachability?                     | **INCONCLUSIVE**      | DD4 requires changed gate input or another caller; actual local alias not observed.                                                       |

## Result boundary and next test

The missing decisive value is the active R4/context address relative to the current handler SP at this callsite, or an exact allocation/lifetime contract that makes the two intervals disjoint. Static disassembly confirms both expressions and their dataflow but cannot provide that runtime address. The smallest next offline step is to inspect the item-17 context construction within this ABL1-local ownership slice for an allocation or pointer-to-stack provenance; if none is present, preserve the runtime address as an open boundary. Do not trace the separately owned `0x7FC2 -> 0x8428` path.

No hardware, ROM, NVRAM, register, firmware, network, installation, or candidate modification occurred. No clock, training, SVC handler, physical, or hardware behavior is claimed.

## Artifacts

- Report: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-item17-alias-review.md`
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-21-item17-alias-review.md`
- Evidence directory: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-item17-alias-review/`
- Verifier/result: `item17_alias_bounds.py`, `item17-alias-bounds-result.json`
- Fresh windows: `dispatch-context-0c60-0c8e.objdump`, `dispatch-callback-0e50-0ea8.objdump`, `frame-fill-95fc-9652.objdump`, `fill-loop-6b78-6b84.objdump`
- Manifest: `SHA256SUMS.final`
