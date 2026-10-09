# ABL item 0x17 SVC #6 ABI and consumer-boundary trace — intent

Timestamp: 2026-09-21T17:20:00+05:00 (Asia/Almaty)
Actor: `/root/memory_clock_units`; offline static trace only.

## Continuation controller binding

- ACTIVE_OBJECT: exact CLV ABL1 Thumb-2 ELF wrapper from the prior item-0x17 run.
- LAST_CONFIRMED_RESULT: prior machine result is PASS with 136 checks; item `0x17` maps conditionally under base `0x57100` to `0x95FC`; helper `0x6D10` returns `1`; first unresolved boundary is the SVC `#6` handler/recipient at `0x12C0`.
- NEXT_EXECUTABLE_ACTION: fresh bounded LLVM Thumb disassembly of the ABL service/caller ABI spanning `0x0DD4..0x12C0`, with the SVC wrapper and item-0x17 conditional call paths in one unique evidence directory.
- INPUT_PATHS: exact prior result JSON, exact decompressed ABL1 payload, and exact Thumb ELF wrapper listed in `evidence/firmware-audit/20260921-abl-item17-svc6-consumer/controller-state.json`.
- ACCEPTANCE_EVENT: fresh disassembly starts and exits `0` with empty stderr; classify whether the visible ABL-side ABI writes a clock/PLL selector, forwards an opaque service, or cannot be resolved. Do not repeat the item-0x17 table mapping or 136/136 verifier.

## Scope and safeguards

TARGET remains the exact CLV ABL1 wrapper. Preserve conditional base `0x57100` and the local `0x6D10 == 1` branch qualification. No ROM, firmware, NVRAM, register, hardware, network, install, or candidate write. Existing input artifacts remain immutable. New owned outputs are this action log and `evidence/firmware-audit/20260921-abl-item17-svc6-consumer/`; rollback is deletion of only those new outputs.

## Observed result and final reconciliation

Timestamp: 2026-09-21T17:52:00+05:00 (Asia/Almaty)

- Executed exactly one fresh bounded disassembly against TARGET:

      /usr/bin/llvm-objdump -D --section=.data --triple=thumbv7 --start-address=0x0d00 --stop-address=0x1300 /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-consumer/ABL1-clv-full-thumb.elf.o > /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-svc6-consumer/svc6-abi-window.objdump 2> /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-svc6-consumer/svc6-abi-window.stderr

- Observed command status: svc6-abi-window.exit contains 0; stderr is zero bytes; the listing is 44,144 bytes. Tool /usr/bin/llvm-objdump reports LLVM 22.1.8.
- Finding: wrapper 0x12AC executes SVC #6 at 0x12C0, after preserving r2 in r4, calling 0x6C20, loading literal 0x0006A41C into r0, and clearing byte [r4+0x40]. The post-SVC path copies r5 to r0 after setting r5=0; exact return value assumes the unavailable supervisor preserves callee-saved r5. The conditional item-0x17 function has SVC-reaching alternatives via 0x118C / 0x10C0 with wrapper-entry r1 values 0x0C / 0x0B; those are not proven SVC selector inputs because 0x6C20 runs before the SVC and r1-r3 post-helper are unavailable. The visible 0x12AC wrapper prepares an opaque service; no direct PLL/clock-selector write is observed in the bounded window, and final supervisor semantics remain unresolved.
- The preserved exact gate remains 0x6D10 == 1, which branches 0x95FC through 0x9646 -> 0x9744 -> 0x984E; the SVC alternatives are conditional and not reached on that exact local gate path. Callback base 0x57100 remains conditional only.
- Result JSON: evidence/firmware-audit/20260921-abl-item17-svc6-consumer/svc6-abi-result.json, SHA-256 b7754c735923c383f01d4926ce82e5bb5e5b4dea012ecec8a81afcb2a1bb0d16. Evidence manifest SHA256SUMS.final, SHA-256 9dd082682b39df665f2ecd6c0da1a055d17a58703d55775fc103a09291f84acf; all 6/6 listed files pass.
- Report: docs/research/2026-09-21-abl-item17-svc6-consumer.md, SHA-256 61dba4ad3f34e2f64f156f3fd80fc43cad97c708bbdea24ae6bcd4f6100fdaae. Exact previous result, payload, wrapper, and ROM hashes reopened unchanged: 4330bdf964f5ebd3fc7211af953e38d4062a0a1d64276a43cac398b2fc916cd3, af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a, adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6, and ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8 respectively.
- Tool error preserved: an attempted removal command was rejected before shell execution because rm -f style commands are prohibited; no target changed and no child exit status was returned. A first manifest check then reported missing files because its entries were repository-root-prefixed while verification ran from inside the evidence directory; that wrapper did not expose the command exit code. The command was corrected to write/check basenames from inside the directory, and the final 6/6 manifest verification passed. The initial partial manifest is retained and hashed as evidence; do not treat it as the final check.
- No ROM/NVRAM/register/firmware/board/network action occurred. Rollback remains deletion of only this unique report/evidence output; preserve source and append-only logs. SVC handler/recipient, runtime base, PLL/MCLK/training consumer and hardware effect remain unresolved.

## G7 correction intent — SVC-reaching alternatives are conditional

Timestamp: 2026-09-21T18:31:00+05:00 (Asia/Almaty)

The independent reachability review finds a later `0x6B78` fill at `0x963A` can alter the status word at `[SP+0x164]` if dynamic `R4+0x278` aliases `SP+0x160..0x178`. Append a qualifier to this report: the local `0x9646 -> 0x9744 -> 0x984E` bypass is conditional on non-alias/no-clobber; the two alternate SVC-reaching branches are not categorically unreachable from `0x6D10=1` alone. Preserve the direct SVC6 callsite observations and avoid any global SVC handler/absence claim.
