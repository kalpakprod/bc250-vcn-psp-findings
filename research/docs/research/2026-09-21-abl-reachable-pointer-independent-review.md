# ABL1 reachable-output pointer identity — independent bounded review

## Result

The exact Thumb code supports this **local, conditional** edge:

```text
0x7E40: R6 = [R0 + 0x2BC]
0x7E6E: R2 = R6
0x7E70: R1 = R5
0x7E72: R0 = R4
0x7E74: BL 0x5E68
0x5E70: R5 = R0                ; caller context
0x5E74: R4 = R2                ; scalar argument, not the context pointer
0x5FBA: STRH R3, [R5 + 0x78]   ; explicit context-field write
0x6024: POP {..., R4, R5, ..., PC} ; restores caller's saved R4
```

Thus, in the `0x5E68` frame, **R4 is not the context/object pointer**: it receives scalar R2; R5 carries the context. The function writes a derived halfword to context `+0x78`, a real pointee mutation. The direct code does not write through the R4 scalar.

For the later path, the exact caller code has `ADD.W R4,R4,#0x2C0` at `0x7F4C` and `SUB.W R4,R4,#0x2C0` at `0x7FC2`, then calls the indirect trampoline at `0x83B0`; at `0x8426..0x8428`, it passes current R4 to `0x10200`. The trampoline is:

```text
0x10958: PUSH {R4,R5}
0x1095A: R4 = [R0 + 0x660]       ; dynamic callback target
0x1095E: R3 = R2
0x10960: R2 = R1
0x10962: R12 = R4
0x10964: POP {R4,R5}             ; restores its caller's R4/R5
0x10966: R1 = 1
0x10968: BX R12                  ; unresolved indirect callback
```

The trampoline itself restores the caller's R4 before dispatch. The subsequent local `0x10200` code copies its R0 context to R4 at `0x10208`; it calls `0x10958` at `0x107E0` and then reads `[R4+0x78]` at `0x107E4`.

**Adjudication:** the unresolved R4 _address-identity_ risk is a possible register clobber at the dynamically selected callback target, not the `0x5FBA` pointee write. Under **AAPCS32**, R4 is callee-saved, so if the callback target conforms, the R4 identity should survive. That is an explicit ABI assumption, not proven target behavior: the callback pointer at context `+0x660` and its implementation/ABI are unresolved and are outside this review. The context is explicitly mutated at `+0x78` by `0x5FBA`; the unknown callback receives the context in R0 and could also mutate it, but this review found no direct write in the `0x10958` trampoline and makes no claim about the unresolved callback body. Pointee mutation can change contents; it does not by itself change the pointer value.

The author report's “same object not proven” boundary is therefore retained without global alias promotion. A more precise statement is: the local caller/callee/store edge is byte-backed; identity through the later dynamic callback is **conditional on AAPCS-conforming callees**; callback pointee effects are **unknown**. No clock unit, frequency, training, or hardware result follows. This review does not inspect or infer the field-`0x660` initializer; its owner remains responsible for that scope.

## Inputs and evidence

| Input                                                                                                               | SHA-256                                                            |
| ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Plain CLV ROM `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`                                                 | `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8` |
| ABL1 decompressed payload `evidence/firmware-audit/20260921-abl-item17-consumer/ABL1-clv-decompressed.bin`          | `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a` |
| Exact Thumb wrapper `evidence/firmware-audit/20260921-abl-item17-reachable-output/ABL1-clv-full-thumb.elf.o`        | `adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6` |
| Author's latest report `docs/research/2026-09-21-abl-item17-reachable-output.md`                                    | `6c3c528cc2b8669d48a7a98067b3241c0adb9daf983b9dca539f80f06d597122` |
| Author's machine result `evidence/firmware-audit/20260921-abl-item17-reachable-output/reachable-output-result.json` | `814215209b0a13a54b32786d5012f9ae41350d28f39ad862b21877697f178beb` |

Evidence class: `observed-bytes` + `static-analysis`. The disassembly was freshly generated from a disposable copy of the exact ELF wrapper with `/usr/bin/llvm-objdump`, `--triple=thumbv7a-none-eabi`. Raw payload windows were independently read from a disposable payload copy with `od`. The earlier default-ARM `llvm-objdump -d` attempt produced headers/no instructions and is explicitly **not** used for this conclusion. A later corrected invocation showed Thumb code.

## Fresh disassembly excerpts

Exact commands and complete outputs are retained in `/tmp/bc250-abl-r4-callback-review-vai8maaf/` and `/tmp/bc250-abl-r4-register-vs-pointee-x5yapp6u/`; all selected direct-disassembly/raw-window commands exited `0`, with empty stderr. The callee epilogue was separately reopened in `/tmp/bc250-abl-5e68-epilogue-corrected-fzhen0gr/` and exited `0`.

```text
00007e40: f8d0 62bc     ldr.w r6, [r0, #0x2bc]
00007e6e: 4632          mov r2, r6
00007e70: 4629          mov r1, r5
00007e72: 4620          mov r0, r4
00007e74: f7fd fff8     bl 0x5e68

00005e68: e92d 47ff     push.w {r0,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,lr}
00005e70: 4605          mov r5, r0
00005e74: 4614          mov r4, r2
...
00005fba: f8a5 3078     strh.w r3, [r5, #0x78]
...
00006024: e8bd 87ff     pop.w {r0,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,pc}

000083ae: 4620          mov r0, r4
000083b0: f008 fad2     bl 0x10958
...
00008426: 4620          mov r0, r4
00008428: f007 feea     bl 0x10200

00010958: b430          push {r4,r5}
0001095a: f8d0 4660     ldr.w r4, [r0, #0x660]
0001095e: 4613          mov r3, r2
00010960: 460a          mov r2, r1
00010962: 46a4          mov r12, r4
00010964: bc30          pop {r4,r5}
00010966: 2101          movs r1, #0x1
00010968: 4760          bx r12

000107e0: f000 f8ba     bl 0x10958
000107e4: f8b4 0078     ldrh.w r0, [r4, #0x78]
```

## Execution ledger and scope limits

- Parent's `26/26 PASS` command `abl1_memory_review_verify.py` was found scope-mismatched to the pointer-identity question and is not accepted for this review.
- The first wrong-object/default-ARM listing and the subsequent wrapper typo are retained in the owned action log with their observed outputs/statuses; neither is used as positive evidence.
- Accepted execution event: exact Thumb disassembly and raw byte reads above from the hash-pinned object/payload copies, with tool exit `0` and empty stderr.
- AAPCS32 preservation is an ABI expectation, **not evidence that the unknown indirect target at `[context+0x660]` is conforming**. The target and any writes through R0/pointee remain unexamined.
- No HOB/heap verifier, float test, global alias search, hardware, network, ROM, firmware, NVRAM, register, candidate, or guide test was run in this review.
