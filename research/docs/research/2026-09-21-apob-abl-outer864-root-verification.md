# Root direct readback — ABL1 outer+0x864 / HEAP argument correction

## Result and evidence class

A bounded manual cross-read of fresh aligned LLVM Thumb windows and independent GNU `od` raw-byte captures supports the G7 correction in `docs/research/2026-09-21-apob-abl-outer864-origin.md`: the inspected selector-`0x0F` call path passes zero as provider `0x49CC`'s second stacked argument, `0x6238` sets the fill byte `R1=0`, and `0x6B78` stores `R1` repeatedly. This is static-analysis / observed-bytes evidence only. There is no aggregate machine-verifier PASS; the prior orchestrator stopped on `NameError: toolver`, and the root's discarded parser trial stopped on a Thumb halfword byte-order assertion. Neither failure contradicts the direct bytes.

## Pinned inputs

- CLV donor: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Decompressed ABL1: `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, 94,624 bytes, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Exact Thumb object: `evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o`, SHA-256 `54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135`.
- Tool: LLVM `22.1.8 llvm-objdump`; raw byte reader: GNU `od` `9.11`.

## Direct command evidence

Fresh `llvm-objdump -D --section=.data --triple=thumbv7m-none-eabi --start-address=... --stop-address=... ABL1-exact.o` captures under `evidence/firmware-audit/20260921-apob-abl-outer864-root-review/` exited `0` with empty stderr for `caller_463c`, `reader_1fb4`, `helper_4800`, `provider_49cc`, `alternate_selector_0d`, `heap_6238`, `bytefill_6b78`, `constructor_b84`, `constructor_c00`, and `constructor_field_store`.

The exact little-endian raw byte windows from `od -An -tx1 -v -j OFFSET -N LENGTH ABL1-clv-decompressed.bin` include:

| RVA              | Raw bytes                                           | Instruction consequence                                                                                                              |
| ---------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `0x4664`         | `00 92 01 92`                                       | `STR R2,[SP]`; `STR R2,[SP+4]` (R2 was zero at `0x464C`)                                                                             |
| `0x1FC0`         | `dd e9 0c 79`                                       | Thumb `LDRD R7,R9,[SP,#48]`, caller's two stack words                                                                                |
| `0x1FD2`         | `cd f8 00 90`                                       | `STR.W R9,[SP]`, forward second word                                                                                                 |
| `0x4808..0x481C` | `06 99 ... 0f 20 cd e9 00 31 ...`                   | helper loads zero stack word, sets selector `0x0F`, stores `(R3,R1)` outgoing pair                                                   |
| `0x49CC`         | `2d e9 ff 4f fe 48 9b b0`                           | provider saves 13 registers and reserves `0x6C` bytes                                                                                |
| `0x4B54..0x4B60` | `29 99 8d f8 1c 00 05 a8 01 f0 6c fb`               | load provider `[SP+0xA4]`, then call `0x6238`                                                                                        |
| `0x6316..0x6324` | `00 21 6a 68 05 f1 10 00 53 46 00 f0 2a fc`         | zero fill byte, node length, node payload destination, `R10` only in `R3`, call `0x6B78`                                             |
| `0x6B78..0x6B82` | `01 e0 00 f8 01 1b 52 1e fb d2`                     | branch into `STRB R1,[R0],#1` / decrement / loop                                                                                     |
| `0xC29E..0xC2B2` | `01 f6 64 00 c1 f8 6c 28 ... 29 90 ... c1 f8 64 28` | constructor computes `outer+0x864`, saves it at constructor-local `[SP+0xA4]`, and stores literal `0x006CD4D0` into the object field |

Provider frame arithmetic: 13 saved registers = 52 bytes; local allocation `0x6C` = 108 bytes; total 160. Its `[SP+0xA4]` therefore equals provider entry `SP+4`, the second stacked argument. The constructor has a distinct stack frame, so its `[SP+0xA4]` is unrelated despite the same displacement.

The raw `$PS1` field at container offset `0x68` is `00 00 00 00` (`load_address=0`); pointer literal at ABL1 RVA `0xC4B4` is `d0 d4 6c 00`. No runtime ABL1 load base is established, so do not classify the pointer's real target region.

## Preserved prior result and limitations

Read-only `sha256sum -c evidence/firmware-audit/20260921-heap-populator-independent-verify-155804-3347325/SHA256SUMS.final` returned exit `0`, seven entries `OK`; the old JSON records `34/34 PASS`. The old verifier was not rerun, and this manifest confirms file integrity only—not the withdrawn source-copy semantics.

No ABL1 execution, runtime object population, APOB/`$INV 0x11ED` join, SMU actuation, clock measurement, training, voltage, or hardware acceptance was performed. Other `0x6238` call sites and later node population remain unclassified.
