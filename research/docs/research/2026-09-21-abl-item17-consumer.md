# CLV ABL1 service item 0x17: conditional memory-speed policy callback

Date: 2026-09-21  
Evidence class: observed-bytes and static-analysis  
Scope: offline trace of ABL1 service item 0x17 through its candidate callback, memory-policy routine, and first opaque ABL service boundary. No firmware modification or hardware action.

## Finding

The exact CLV ABL1 caller at payload address 0x7E3A passes item 0x17 and the same context pointer to the service dispatcher at 0x0C60. The dispatcher uses a callback table whose pointer literal is 0x0006E224. Under the **conditional** candidate ABL1 base 0x57100, this table is at payload offset 0x17124; its unique item-0x17 row at 0x17134 contains Thumb pointer 0x000606FD, which maps to local payload entry 0x95FC. That entry reads per-channel halfwords at structure offset +0x20 and contains a conditional multi-channel minimum/rewrite block.

This is a **conditional static correlation**, not proof that the loader uses base 0x57100 or executes this callback at runtime. The exact local helper chain also shows that helper 0x6D10 returns 1 and 0x6C20 stores that value at output +4. At 0x95FC, the value is loaded from [SP+0x164] and the <=1 branch goes through 0x9744 to 0x984E, bypassing the multi-channel minimum and all-channel +0x20 writeback block for this locally produced value. Do not describe that block as executed for this path or claim that this path rewrites every channel.

The first unresolved consumer remains outside the extracted ABL1 payload: the SVC #6 handler/recipient reached by ABL transfer helpers. This trace does not identify a clock applier. Physical MCLK, a PLL, GDDR6 rate conversion, training outcome, voltage, and hardware behavior remain unestablished.

## Input and provenance

- TARGET ROM: /home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin; 16,777,216 bytes; SHA-256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8. It is the preserved CLV 5.00 local donor image. Its local provenance manifest records the RetroWeb BC-250 board page (ID 20611), retrieval date 2026-09-16, and source ZIP SHA-256 27ce5d5b023254370d14ead6ff5afcc50798795c86a33eb91f1011cc5246d675. The manifest identifies community redistribution of vendor firmware, uploader unknown; it is not an authorization or safety claim.
- ABL1 decompressed payload: evidence/firmware-audit/20260921-abl-item17-consumer/ABL1-clv-decompressed.bin; 94,624 bytes; SHA-256 af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a.
- Thumb ELF wrapper: evidence/firmware-audit/20260921-abl-item17-consumer/ABL1-clv-full-thumb.elf.o; SHA-256 adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6, matching the pre-existing wrapper. The raw payload is the source for all payload offsets; the ELF wrapper is used only for address-labelled Thumb-2 disassembly.
- Local direct source references: evidence/donor/retroweb-20260916/SHA256SUMS and manifest.json. The ABL1 payload and wrapper are preserved copies in this task's unique evidence directory; the baseline ROM and prior work were not modified.

## Trace

1. Caller. In the exact Thumb listing, 0x7E34 loads r0 from [r4], 0x7E36 sets r1=0x17, 0x7E38 copies r4 to r2, and 0x7E3A calls 0x0C60. Thus the observed input is the requested item plus the same context pointer; the caller does not itself establish what hardware consumes the value.
2. Dispatcher and row. At 0x0C60 the dispatcher selects one of local table walkers 0x0E50 or 0x0FD8 from helper metadata. They compare the request ID against 8-byte {callback pointer, selector} entries and branch through the selected callback pointer. Both code paths load table literal 0x0006E224. The raw payload row at 0x17134 is:

       fd 06 06 00 17 00 00 00

   Interpreted little-endian, this is pointer 0x000606FD and selector 0x00000017. The bounded table parse finds one matching key and a null-pair sentinel at row index 10. Base subtraction and Thumb-tag removal yield 0x95FC only under candidate base 0x57100. Other non-null rows also map to observed local Thumb prologues under that same hypothesis; this is consistency evidence, not loader-base proof.

3. Candidate callback. Under the conditional mapping, 0x95FC begins with a Thumb-2 function prologue. It reads 16-bit values from context pointer +0x0C at offset +0x20 (for example, ldrh at 0x9672) and the function contains a multi-state reduction that compares temporary values, stores a reduced aggregate at +0x2BC, and has an all-channel +0x20 halfword write path.
4. Guard on the exact helper path. At 0x962C, 0x95FC calls 0x6C20 with a scratch buffer beginning at SP+0x160. In 0x6C20, the result of 0x6D10 is written at buffer +4 (instruction 0x6C2E). 0x6D10 invokes its local helper and then returns constant 1 (0x6D1E movs r0,#1; 0x6D20 return). The caller reads [SP+0x164] at 0x963E, compares against 1 at 0x9644, and branches at 0x9646 to 0x9744, which immediately branches to 0x984E. This bypasses the intervening multi-channel reduction/minimum and all-channel +0x20 writeback block. The separate pstate-precedence result independently records the bounded 0x984E single-state window as having no channel-speed store.
5. Conditional service calls. Other branches in this policy function call 0x0DD4, 0x118C, and 0x10C0. Their local wrappers include selector values 0x0B and 0x0C and lead to the 0x12AC wrapper/SVC #6 site. These calls are conditional alternatives; their static presence does not show that the helper-6D10==1 branch reaches or executes them.
6. Opaque boundary. Wrapper 0x12AC retains its input data pointer in r4, clears byte [r4+0x40], loads the local literal 0x0006A41C, and executes SVC #6 at 0x12C0. The supervisor/handler implementation is outside the extracted ABL1 body in this trace. A candidate-base mapping of the literal to a nearby “Slave: ABL, return result” string is only a string correlation and does not define the interrupt semantics.

## Verification

Existing project route reused: exact local CLV ABL1 extraction, existing address-labelled Thumb ELF wrapper, LLVM disassembly slices, and the bounded deterministic verifier. No duplicate analyzer was introduced. The verifier script is evidence/firmware-audit/20260921-abl-item17-consumer/item17_consumer_verify.py (SHA-256 c349a0670d6c82481839cd05bf2d19efe4355363b4e09a462b744077b255a535); runtime was Python 3.14.7. Disassembler was /usr/bin/llvm-objdump, LLVM 22.1.8.

The completed verifier run was:

    python3 evidence/firmware-audit/20260921-abl-item17-consumer/item17_consumer_verify.py

It exited 0, wrote no stderr, and reported PASS with 136/136 assertions. Its recorded stdout is evidence/firmware-audit/20260921-abl-item17-consumer/item17-verifier.stdout; its exit and stderr ledgers are item17-verifier.exit and item17-verifier.stderr. The machine result is item17-consumer-result.json (SHA-256 4330bdf964f5ebd3fc7211af953e38d4062a0a1d64276a43cac398b2fc916cd3). The final evidence manifest is evidence/firmware-audit/20260921-abl-item17-consumer/SHA256SUMS.final (SHA-256 eb835b9e42300724b0f1b66107bee65a266da66353333654d37898bb368bb52b); its 40 listed files all pass checksum reconciliation. The verifier rechecks exact ROM, payload, wrapper and prior-result hashes; dispatcher table bytes/rows and local prologues; the guard dataflow; the conditional service ABI; and the SVC literal/callsite. All captured bounded disassembly command ledgers checked by the verifier record exit 0 and empty stderr, including the three callback-anchor windows.

Earlier verifier failures were checker defects, not firmware-test failures: the anchor exit ledger was per-address rather than scalar, then a byte-valued JSON detail was not serializable. Both were corrected in the task-local verifier and the pinned-input run above passed. The original ROM, source payload, copied wrapper, and borrowed prior results were hash-checked by the verifier.

## Limits and next decisive evidence

- Loader/runtime base 0x57100 and actual runtime callback dispatch: unproven. The prior base review is evidence/firmware-audit/20260921-abl-item17-consumer/prior-base-review-result.json (SHA-256 ecb7953571d3b008e76798718d216362bf819a4b0ffcb3dc52da58e23e2c483b); it supports only conditional static coherence and reports no recovered runtime loader mapping.
- AmdSetup+0x316 / $INV 0x11ED to CBS/APCB token 7 or this item-0x17 callback context: not established.
- SVC #6 handler/recipient, resulting service-side structure semantics, any UMC/PLL consumer, units, MCLK, GDDR6 data-rate conversion, training and applied setting: unresolved.
- Hardware or board behavior, performance, voltage, synchronization, and firmware acceptance: not tested. No ROM, NVRAM, register, firmware, candidate, board, network, or installed-tool write/action occurred.
- Independent review requested by the parent: incomplete in this execution. The separate item17 reachability review has an intent log but no completed review result was available here; send this report and its evidence manifest to the parent for review.

No firmware patch or candidate was produced. Rollback for this offline research output is deletion of this report and the unique evidence directory only; retain the append-only action log and preserve every pre-existing source/evidence file.

## G7 correction — conditional branch after helper-6B78 fill

The independent reachability review `docs/research/2026-09-21-item17-reachability-review.md` and its `128/128 PASS` machine result corrected an overstatement in this report. `0x6D10` initially returns `1`, and `0x6C20` writes it at `[SP+0x164]`, but before the compare at `0x9644`, `0x95FC` calls `0x6B78` at `0x963A` with dynamic destination `R4+0x278`, fill byte `0xFF`, and length `0x40`. Static evidence does not establish whether `R4+0x278..R4+0x2B7` aliases the stack block `SP+0x160..SP+0x178`. Therefore `0x9646 -> 0x9744 -> 0x984E`, and the derived `context+0x2BC` value on that path, are conditional on no alias/clobber; they are not guaranteed by the helper return alone. The earlier bounded 95FC branch decoding remains valid, but the runtime/local object-alias relation is unresolved. No units or hardware implication follows.
