# CLV ABL1 item 0x17: SVC #6 ABI and consumer boundary

Date: 2026-09-21  
Evidence class: observed-bytes and static-analysis  
Scope: fresh bounded inspection of the ABL-side SVC #6 wrapper and the conditional call paths from the already established item-0x17 candidate callback. No hardware, firmware, ROM, NVRAM, register, or network action.

## Conclusion

The visible ABL1 code does not write a PLL or clock register in the inspected wrapper/caller window. It prepares an opaque service call: wrapper 0x12AC preserves the incoming data pointer in r4, calls the local metadata helper 0x6C20, loads literal 0x0006A41C into r0, clears byte [r4+0x40], and executes SVC #6 at 0x12C0. It sets r5 to zero before the SVC and moves r5 to r0 afterward; assuming the supervisor preserves the callee-saved r5 register, this is a zero return. The actual SVC handler/recipient and its interpretation of the literal, selector, and buffer are outside this extracted ABL1 body.

Therefore the strongest supported classification is **ABL-side opaque-service forwarding, with final consumer semantics unresolved**. It is not evidence of a PLL/clock-selector write. The exact locally produced helper value 0x6D10 == 1 still takes 0x95FC through 0x9646 -> 0x9744 -> 0x984E; that path bypasses the SVC-reaching alternatives.

## Bound object and continuation state

- TARGET: exact CLV ABL1 Thumb-2 ELF wrapper /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-consumer/ABL1-clv-full-thumb.elf.o, copied from the prior bounded run and SHA-256 adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6.
- Prior state attachment: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-consumer/item17-consumer-result.json; its recorded status is PASS, 136 checks, conditional callback base 0x57100, and unresolved SVC #6 boundary.
- Fresh input command: /usr/bin/llvm-objdump LLVM 22.1.8, --section=.data --triple=thumbv7 --start-address=0x0d00 --stop-address=0x1300.
- Fresh output: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-svc6-consumer/svc6-abi-window.objdump (exit 0, empty stderr). The continuation controller binding is retained in controller-state.json.

The prior item-0x17 mapping is not repeated here. It remains conditional under base 0x57100; no loader/runtime-base proof is added by this continuation.

## Observed ABI

### SVC wrapper 0x12AC

Fresh disassembly gives:

    12ac: b530          push {r4, r5, lr}
    12ae: b087          sub  sp, #0x1c
    12b0: 4614          mov  r4, r2
    12b2: 4668          mov  r0, sp
    12b4: ...           bl   0x6c20
    12b8: 2500          movs r5, #0
    12ba: 4803          ldr  r0, [pc, #0xc]       ; literal at 0x12c8
    12bc: f884 5040     strb.w r5, [r4, #0x40]
    12c0: df06          svc  #0x6
    12c2: b007          add  sp, #0x1c
    12c4: 4628          mov  r0, r5
    12c6: bd30          pop  {r4, r5, pc}

The raw little-endian word at 0x12C8 is 0x0006A41C. Under the already-qualified candidate base 0x57100, subtracting the base gives payload offset 0x1331C, where the bytes are the string "\nSlave: ABL, return result\n\0". This is only a conditional string correlation; it does not assign SVC semantics to the literal.

At wrapper entry, callers set values 0x0B or 0x0C in r1 and a data/context pointer in r2, but 0x12AC saves only r2 in r4. The intervening 0x6C20 call invokes several subcalls and can use caller-saved r0-r3; the extracted SVC handler is absent, so the exact post-helper values of r1-r3 at the supervisor boundary are not established. The values 0x0B/0x0C are observed wrapper-call arguments, not proven SVC selector arguments. What is directly observed before SVC #6 is the literal load into r0, the [r4+0x40] = 0 preparation, and the SVC instruction itself.

### Callers reachable from the candidate 0x95FC function

The previously mapped candidate function contains these conditional edges:

- 0x9780 -> 0x0DD4, with local selector setup r1 = 0x0B; 0x0DD4 calls 0x0FB8. The fresh visible 0x0FB8 body only gathers a 0x20-byte block and calls 0x6C20; it contains no SVC #6.
- 0x97E4 -> 0x118C; the caller builds a stack data record and at 0x11E6 sets r1 = 0x0C, r2 = sp, then calls 0x12AC.
- 0x9800 -> 0x10C0; the caller builds a stack data record and at 0x10FA sets r1 = 0x0B, r2 = sp, then calls 0x12AC.

Thus the two visible SVC-reaching alternatives are data-exchange wrappers for service values 0x0B and 0x0C, not direct clock-register writes. The exact local 0x6D10 == 1 gate does not reach either alternative: 0x9646 branches to 0x9744, then 0x984E.

## What remains opaque

0x12C0 is the SVC instruction site, not the handler implementation. The supervisor/ROM recipient, its dispatch table, and any downstream ABL/PSP/SMU/UMC operation are not present in the extracted payload. The ABL bytes therefore cannot establish whether service 0x0B or 0x0C changes a clock, returns data, updates a training structure, or performs another operation.

No direct PLL, clock-selector, MMIO, or hardware register write was observed in the bounded wrapper/caller code. This is a bounded negative only; it is not a census of all ABL1 or supervisor code. Physical MCLK, GDDR6-rate conversion, training, voltage, synchronization, and hardware behavior remain unrun.

## Evidence and rollback

Machine-readable result: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-svc6-consumer/svc6-abi-result.json (SHA-256 b7754c735923c383f01d4926ce82e5bb5e5b4dea012ecec8a81afcb2a1bb0d16). Evidence manifest: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-svc6-consumer/SHA256SUMS.final (SHA-256 9dd082682b39df665f2ecd6c0da1a055d17a58703d55775fc103a09291f84acf; all six listed entries pass). Fresh disassembly, stderr, exit status, controller binding, and final checksums are in the same directory. The report and append-only action log are new owned outputs; the prior item-0x17 evidence and exact ROM/payload remain unchanged.

Rollback is deletion of only this report, this action log, and /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-svc6-consumer/. No firmware candidate was produced. Independent review remains pending with the parent.

## G7 correction — branch-to-984E alias qualification

The helper `0x6D10` returns `1`, and `0x6C20` stores it at `[SP+0x164]`; however, `0x95FC` then calls fill helper `0x6B78` at `0x963A` with destination `R4+0x278`, fill byte `0xFF`, and length `0x40` before the `0x9644` compare. The independent review confirms that no static address relation proves the target range disjoint from `SP+0x160..0x178`. Thus the `0x9646 -> 0x9744 -> 0x984E` bypass is conditional on no alias/clobber, not guaranteed by `0x6D10=1` alone. The SVC6 wrappers/callsites described above remain static observations; this report makes no global SVC6 reachability or handler-absence claim.
