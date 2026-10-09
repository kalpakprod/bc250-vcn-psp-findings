# CLV ABL1 +0x660 initializer/consumer object identity — intent

Timestamp: 2026-09-21T19:00:00+05:00 (Asia/Almaty)
Actor: `/root/memory_clock_units`; offline static investigation only.

## Bound object and reuse

- TARGET: exact CLV ABL1 Thumb-2 wrapper `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-consumer/ABL1-clv-full-thumb.elf.o`, SHA-256 `adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6`.
- Existing, exact same-field report and result are reused first: `docs/research/20260920-clv-abl1-context660-callback-xhigh.md` (97/97 PASS) and `evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/abl1-context660-callback-result.json` (SHA-256 `cf16bf73c370bac1c4426f7c79e64890898a11da7743304528ddeccfe3cd7ecb`). Do not repeat the pointer mapping or callback-body scan. This continuation tests only the missing object-identity edge from the caller of initializer `0x7378` into active `0x10958` R0.
- Existing provider/callsite evidence: full local listing `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt` (SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`). Initial direct search showed no direct BL to `0x7378`; this does not exclude indirect calls.

## Goal, procedure, and acceptance

Trace initializer entry R0 through `0x7378 -> 0xAF90 -> 0xB0C4` and compare the installed base with the current R0 consumed by `0x10958`. Reuse `/usr/bin/llvm-objdump` LLVM 22.1.8 and the exact local Thumb wrapper. Capture only constructor/body `0x7378..0x7500`, setter `0xAF90..0xB0D0`, active dispatcher `0x10958..0x1096C`, and an exact direct-BL-to-0x7378 search over the retained listing. The prior candidate pointer `0x60BD9 -> 0x9AD8` is referenced, not rescanned or renamed as runtime-proven.

Acceptance: observed exact constructor R0/object writes; observed direct-call search result; observed consumer register base; name the precise missing caller/object-address input if the initializer's R0 cannot be joined to consumer R0. Do not repeat a generic array scan or disassemble unrelated callback tables.

## Safeguards

No ROM, firmware, NVRAM, register, hardware, network, install, candidate, or other-worker artifact changes. New owned paths only: this action log, `evidence/firmware-audit/20260921-abl660-object-identity/`, and `docs/research/2026-09-21-abl660-object-identity.md`. Rollback is deletion of only this report and evidence directory; preserve the append-only log and all prior source/evidence.

## Observed result and final reconciliation

Timestamp: 2026-09-21T19:58:49+05:00 (Asia/Almaty)

- Existing exact same-field report `20260920-clv-abl1-context660-callback-xhigh.md` was reopened, hashed, and reused: 97/97 PASS; it already contains the initializer literal, conditional candidate target, and disassembly of candidate callback body. No repeat callback scan or base proof was run.
- Fresh targeted windows: 0x7378..0x7500, 0xAF90..0xB0D0, and 0x10958..0x1096C. All exited 0 with empty stderr. Exact direct-BL search for 0x7378 in retained full Thumb listing returned exit 1 and zero matches; this does not exclude an indirect or external invocation.
- R0 at entry 0x7378 is saved as R5, the root-object pointer. Function 0x7378 passes R5 as R0 to 0xAF90. AF90 temporarily advances R4 by +0x3C, then the writeback load at 0xB04E subtracts 0x3C and restores the same incoming R0 root before 0xB0C4 stores the initialized literal to [root+0x660].
- Active 0x10958 instead loads [current R0+0x660] and branches through it. The constructor caller supplying R0 to 0x7378 was not found as a direct BL in the exact retained listing; indirect/external call remains possible. Therefore root-object identity with the active consumer R0, and whether the initialized callback is the active target, remain unresolved. Exact missing input: the indirect invocation/call frame for 0x7378 including its R0 object address, or a same-run address trace to compare that value with 0x10958's incoming R0.
- The request to ask `/root/pstate_precedence` could not be sent because no collaboration/message tool was exposed in this runtime; the existing field+0x660 report was nevertheless reopened and reused, avoiding duplicate analysis.
- Result JSON: `evidence/firmware-audit/20260921-abl660-object-identity/field660-identity-result.json`, SHA-256 `e3a47fa8c47766a56edc233ae6cafd31207820aee6cf26df81db076b5f80dedf`. Manifest: `SHA256SUMS.final`, SHA-256 `59536e3d3b469d46cf81ca677324cb20ec38e49b2540b73191f79edfe58206a9`; all listed evidence entries pass. Report: `docs/research/2026-09-21-abl660-object-identity.md`, SHA-256 `099a7ae60e4d88c55f3fcacb0f6e027cad85bcdafe68e2bc8dca455fe34d8720`.
- No ROM, firmware, NVRAM, register, hardware, network, candidate, or install change occurred. Rollback remains deletion of only this report and unique evidence directory; preserve this append-only log and prior evidence.
