# Item-17 callback-to-service reachability review — intent

- Timestamp: 2026-09-21T16:45:00+05:00 (+05:00)
- Actor: `/root/pstate_precedence`; offline local static work only.
- Bound target: exact CLV ROM `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; exact ABL1 payload SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Objective/ownership read: full `docs/action-logs/2026-09-21-abl-item17-consumer.md`; its scope stops at ABL-side callback/service boundary. `/root/apob_abl_handoff` owns HEAP `0xA04E` and APOB msg `0x61`; `/root/smu_clock_entrypoints` owns PMFW queue work. This review will not read/modify those tracks beyond noting the first opaque boundary.
- Newest item17 state metadata read: `evidence/firmware-audit/20260921-abl-item17-consumer/item17-helper-metadata.exit`=`0`, `item17-helper-metadata.stderr` empty. Reopened prior local `abl1-pstate-inputs-result.json`=`PASS`, `54/54`. Existing exact disassembly/template available at `evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o`; existing table, dispatch and SVC windows are retained under the item17 evidence directory.
- Goal: test whether the conditional pointer row `{0x000606FD, key 0x17}` at payload `0x17134` conditionally maps under base `0x57100` to Thumb `0x95FC`, then whether that selected handler reaches `0x0DD4` or the local `SVC #6` wrapper under exact `0x6D10` return/guard behavior. Do not relabel candidate base as runtime-proven.
- Existing tools/route: reuse `/usr/bin/llvm-objdump` LLVM 22.1.8 and existing ELF wrapper `ABL1-exact.o`; do not rerun whole-payload pointer census, the earlier 47- or 54-check verifier, APOB/HEAP work, or SVC ABI research owned by `memory_clock_units`.
- Next executable action: fresh narrow Thumb disassembly of item17 dispatcher/table, `0x95FC` guard/helper, `0x0DD4`/`0x0FB8`, branch helpers `0x118C`/`0x10C0`, and `0x12AC/SVC #6`; run one bounded verifier joining table key/pointer, the branch gate, the DD4 service path, and exact SVC6 callsite relation.
- Acceptance: observed command/status, exact conditional callback edge accepted or rejected, and exact reachable/unreachable claim limited to the `item17 -> 0x95FC` route. The loader base, external caller/dispatch execution, SVC handler/recipient, clock effect and hardware remain open.
- No ROM/firmware/NVRAM/register/hardware write, network, install, candidate, or spawning. Output belongs only in `evidence/firmware-audit/20260921-item17-reachability-review/` and this unique report/log. Rollback: delete only this report, action log, and unique evidence directory.

## Dispatcher table-consumer window extension (intent before write)

The initial fresh window stopped at `0x0D10`; the key-match loop itself is at `0x0E50..0x0ED0`, and its PC-relative table-pointer literal is at `0x0F10`. Before writing additional output, extend this unique evidence with those two exact ranges and the caller's `0x7E30..0x7E40` selector setup. Also use the exact retained full listing only to enumerate direct `BL 0x12AC` sites (no generic pointer scan). This extension tests whether selector `0x17` reaches the candidate table row, not just whether the word at `0x17134` happens to equal a candidate code pointer.

## SVC6 fallback caller window extension (intent before write)

The direct SVC6 caller inventory from the retained full listing includes `0x102C`; this site is inside the alternate `0x0FD8` dispatch branch selected only when the `0x0C60` local gate fails. Capture the exact `0x0FD8..0x1038` Thumb window fresh so the item-17 gate can be joined to or excluded from that SVC wrapper callsite without repeating a whole-payload disassembly.

## Reachability verifier/action intent (before new write)

The new `0xE50` instruction window confirms an 8-byte table loop with key compare and indirect `BLX`; the fresh `0x7E30..0x7E40` window passes selector `0x17` into dispatcher `0x0C60`. Next write is a small deterministic verifier over these exact windows plus the already-reproduced `6C20/6D10` helper and `0x95FC` guard. It will model only the per-item control-flow edges to `0x0DD4`, `0x10C0`, `0x118C`, and their `0x12AC/SVC #6` callsites. It will also preserve a filtered exact direct-call list for `0x12AC` from the retained full Thumb disassembly. No source code, full-scan output, ABL/APOB/SUM helper, or other agent-owned artifacts will be changed.

## Reachability verifier implementation intent

Create `item17_reachability_verify.py` in the unique evidence directory. It will use the fresh narrow objdump windows and immutable payload bytes to check: table literal `0x6E224`, base-relative table `0x17124`, row key `0x17`, pointer `0x606FD -> 0x95FD -> entry 0x95FC` under conditional base `0x57100`; dispatcher branch `0x0C60 -> 0x0E50` after `0x6D10=1`; table key compare/BLX; `0x95FC` return-zero and `0x0E50` exit at `0x0E84`; and the absence of a reachable `0x0DD4`/`0x12AC/SVC #6` edge on this path. It will not decode or name the SVC6 handler.

## Verifier attempt 1 and correction intent

- Timestamp: 2026-09-21T17:12:00+05:00
- Command: `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260921-item17-reachability-review/item17_reachability_verify.py > evidence/firmware-audit/20260921-item17-reachability-review/verifier.stdout 2> evidence/firmware-audit/20260921-item17-reachability-review/verifier.stderr; printf '%s\\n' "$?" > evidence/firm17-reachability-review/verifier.exit`
- Observed exit `1`; stderr reports verifier tuple-unpack `ValueError` before checks/result emission. This is a checker source error, not a disassembly/input failure. Preserve source/stdout/stderr/exit under `attempt1/` and correct only the loop unpacking.

## Verifier attempt 2 and correction intent

- Timestamp: 2026-09-21T17:13:00+05:00
- After fixing the first loop, the same checker source had the same tuple-unpack mistake in the table-loop list; exit `1`, no result emission, stderr only. Preserve attempt under `attempt2/`; normalize all bounded instruction lists to `(window,address,mnemonic,operands)` before rerun. No input/disassembly changes.

## Verifier attempt 3 and correction intent

- Timestamp: 2026-09-21T17:14:00+05:00
- Instruction tuple normalization passed, then checker stopped at the raw-byte assertion because `PAY` was a `Path` rather than bytes; exit `1`, no result emission. Preserve attempt under `attempt3/`; change only to `pay_bytes=PAY.read_bytes()` and keep all checks/inputs unchanged.

## Verifier attempt 4 and correction intent

- Timestamp: 2026-09-21T17:15:00+05:00
- Checker ran and emitted a result (`42/56 PASS`, exit `1`). Failures were assertion-source issues: one table-loop call still used `ins(m,...)` instead of `ins(w,...)`, and raw Thumb bytes were compared in disassembler halfword order rather than payload byte order (`0x95FC`, `0x6D10`, `0x9848`). Preserve attempt under `attempt4/`; fix only these assertions and rerun.

## Final observed result

- Timestamp: 2026-09-21T17:17:00+05:00 (+05:00)
- Fresh local disassembly windows: all `13` bounded objdump commands exited `0`; all stderr empty. Verifier command exited `0`; literal stdout status `PASS`, `56/56` checks; stderr empty.
- Machine result: `evidence/firmware-audit/20260921-item17-reachability-review/item17-reachability-result.json`.
- Accepted claim: conditional static edge `item 0x17 -> row 0x17134 -> pointer 0x606FD -> Thumb entry 0x95FC` under candidate base `0x57100`.
- Rejected reachable-edge claims: item-17 path does not reach `0x0DD4` because `0x6D10=1` forces the `0x95FC` bypass branch; it does not reach `0x12AC/SVC #6` because `0x0C60` selects `0x0E50`, callback `0x95FC` returns zero, and dispatcher exits at `0x0E84` while the row pointer is nonzero.
- Candidate base remains unproven as loader/runtime base. No SVC handler/recipient or clock/training effect is named.
- No hardware, ROM, NVRAM, register, firmware, candidate, network, installation, or shared-memory write occurred.

## Reachable-edge refinement before final verifier write

The current path answer must account for `0x0E50`'s pre-dispatch guard: item `0x17` is not `0x08`, so the dispatcher calls `0x0FB8`; that helper returns `0`, which selects the table scan at `0x0E8C`. On key match, `0x0EA6` uses `BLX R2`; the selected callback returns zero, then the nonzero row pointer sends the dispatcher to `0x0E84`. Capture these exact edges and the fallback direct SVC6 caller window before finalizing. This distinguishes conditional item-17 dispatch from the later rejected DD4/SVC6 edges; no global SVC6 reachability claim is intended.

## Attempt 5 result and bounded extension intent

The initial table-path verifier now passes `56/56`; its result and source are preserved under `attempt5/` before extension. The verifier is being extended only to make the reachability acceptance explicit across the dispatcher precheck (`0x0C60 -> 0x0E50`), `0x0E50`'s `0x0FB8` setup/return gate, DD4's own `0x6C20` gate, and the exact direct caller locations of wrapper `0x12AC/SVC #6`. The fixed branch facts remain unchanged; no SVC ABI semantics are added. Reuse fresh windows and direct-call listing only, no new whole-payload disassembly or worker-owned source.

## Final verifier attempt 6 and table-boundary correction intent

- Timestamp: 2026-09-21T17:20:00+05:00
- Expanded verifier reached the code checks (`118/121 PASS`, exit `1`). Two failures used a nonexistent separate returner window (the exact instructions are in the fresh `helper-6c20-6d22` window), and one expected a null table row at `0x1717C` instead of the observed terminator at `0x17174`. Preserve this result/script under `attempt6/`; correct only those input-window/terminator expectations and rerun.

## Table-clear alias boundary check intent

Reopening the item-17 chain shows `0x95FC` calls byte-fill helper `0x6B78` on dynamic target `R4+0x278` after `0x6C20` wrote its local status block at `SP+0x160`. Before promoting the `0x6D10=1` branch to an unconditional DD4-unreachable claim, execute one narrow disassembly of the fill helper and verify the two address expressions. If the ABL object alias/base is unresolved, preserve DD4 reachability as conditional rather than infer non-aliasing. No additional pointer scan or hardware step.

## Stack/table alias boundary refinement intent (before final verifier update)

A final control-flow audit found one qualification needed before rejecting the DD4 edge: after `0x6C20` writes `[SP+0x164]=1`, `0x95FC` calls the bounded byte-fill helper `0x6B78` on dynamic destination `R4+0x278` (`0x9636/0x963A`). The helper writes 0x40 bytes at its R0 destination. Whether that dynamic table range aliases the SP+0x160 status block is not proven by the retained code; therefore DD4 reachability cannot be categorically rejected from the helper return alone. Freshly disassemble the exact fill helper, preserve the range expression, and refine the claim to `conditional/unresolved alias` for DD4. Keep the SVC6 direct-edge analysis separate: the direct SVC6 wrapper callsites remain in the FD8/10C0/118C alternatives; do not promote global SVC6 absence.

## G7 alias correction and exact memory-range test intent

The prior result's categorical phrase “DD4/SVC6 rejected as reachable” overreaches for DD4 because `0x95FC` calls `0x6B78` after `0x6D10` returns `1`. The fill target is dynamic `[R4+0x278]`; it writes `0x40` bytes of the supplied fill byte. Static evidence does not establish that this region is disjoint from the local status buffer at `SP+0x160`. Narrow the claim: `6D10=1` is the value initially written to `[SP+0x164]`, and `BLS 0x9744` follows absent alias/clobber; exact actual reachability remains unresolved pending pointer-range identity. Capture the exact fill loop and the upstream creation of `R4=[R5]` (`0x7548/0x754C`) before the final check. SVC6 conclusions must remain path-bounded and must not become global absence claims.

## Final corrected observed result

- Timestamp: 2026-09-21T18:02:00+05:00 (+05:00)
- Fresh local windows: `16` objdump files, all command exits `0`, all stderr empty; filtered direct `BL 0x12AC` extraction exit `0`, exact sites `0x102C`, `0x1104`, `0x11E8`.
- Final verifier: exit `0`, literal stdout status `PASS`, `128/128` checks, stderr empty; machine result `item17-reachability-result.json`.
- Accepted: conditional static item-17 -> keyed row -> `BLX 0x95FC` under candidate base `0x57100`; dispatcher setup `0x6D10=1` -> `0x0C60 BLS 0x0E50`, E50 helper `0x0FB8` returns zero, keyed callback returns status zero, and E50 exits at `0x0E84` after nonzero row-pointer check.
- Corrected DD4 status: **conditional/unresolved**, not categorically rejected. `0x95FC` calls `0x6B78` with dynamic `R4+0x278`, count `0x40`, before comparing `[SP+0x164]`; static bytes do not prove whether this target aliases `SP+0x160..0x178`. Non-alias selects `0x984E` and skips DD4; alias could alter the gate. DD4 independently gates its own `0x0FB8` on `0x6D10=1`.
- SVC6 status: **rejected on known direct item-17 paths, not globally**. The direct wrapper callsites remain `0x102C`, `0x1104`, `0x11E8`; item 17 selects E50 rather than FD8, and alternate helper `+0x14` gates return before wrapper calls. SVC handler/recipient remains unresolved.
- No ROM, firmware, NVRAM, register, hardware, network, installation, candidate, or shared-memory write occurred.
