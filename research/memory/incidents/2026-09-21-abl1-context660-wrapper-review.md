# G7 correction: context+0x660 wrapper review and ELF data-section decoding

Date: 2026-09-21. Scope: static AAPCS analysis of the exact CLV ABL1 wrapper at `0x10958` only.

## Corrections

- The initial scoped filename search looked for `field660`/`10958` and missed the objective attachment named `docs/research/20260920-clv-abl1-context660-target-semantics.md`. The full attachment was then read; its completed 96-check report classifies the `0x9AD8` body as possible descriptor-indexed field RMW semantics, with active Fclk binding still unproven.
- The exact ABL1 ELF object places its `0x171A0`-byte payload in non-executable `.data` (VMA 0). `llvm-objdump -d` exited `0` but emitted only the ELF header and no instruction rows; this was not a successful decode. The corrected read-only command used `llvm-objdump -D -j .data` and byte-reconciled the extracted `.data` section to exact ABL1.

## Verified wrapper result

- Exact source: CLV 5.00 ROM SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; ABL1 SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`; size 94624 bytes.
- At `0x10958..0x1096A`, raw Thumb bytes are `30b4d0f8604613460a46a44630bc01216047`. The sequence loads callback target from `[R0+0x660]`, preserves incoming R0, sets R1=1, remaps entry R1/R2 to callback R2/R3, restores R4/R5, and tail-branches through R12.
- The wrapper-local claim “preserves the incoming pointer in R0 and does not store through it” is accepted (12/12 checks). The claim “the wrapper itself mutates the pointee” is rejected. The indirect callback's own effects remain unknown.

## Boundary

This is observed-byte/static-analysis evidence only. No initializer work, callback body, SVC handler semantics, runtime, MMIO/PLL, physical clock, or board behavior was checked. No ROM or firmware payload was modified.
