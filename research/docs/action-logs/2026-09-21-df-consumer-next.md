# DF consumer handoff — 2026-09-21

## Intent (before artifact creation)

- Timestamp: 2026-09-21 (Asia/Almaty; exact execution time to be recorded in result append).
- Actor: bounded DF actuator trace worker.
- Target: immutable offline donor `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Requested edge: `AmdSetup+0x703` u8 / `$INV 0x1373` and `AmdSetup+0x704` u16 LE / `$INV 0x1374`, downstream FCLK request conversion/limits/runtime consumer; preserve the baseline `MemoryClockSpeed +0x316=0x24` (IFR label 1800 MHz).
- Existing route reused: exact clv extraction and disassemblies in `evidence/firmware-audit/20260919-clock-trace/` and `20260919-inv-token-consumers/`, ABL1 exact Thumb object/listings in `20260920-clv-abl1-downstream/`, and HII/menu verifier output in `20260920-df-init-route/`. Do not repeat corpus extraction or invent an analyzer.
- Procedure: create one unique evidence subdirectory `evidence/firmware-audit/20260921-df-consumer-next/`; run pinned-input direct GNU objdump windows on the existing exact PEI module copies and an LLVM Thumb window on the existing ABL1 object; byte-check their outputs against source modules; tie the observed ABL1 FCLK request descriptors and menu help/range metadata to the token handoff only if exact code proves that join. Report the first unresolved instruction boundary and qualify any negative as bounded.
- Rationale: distinguish actual x86 serializer behavior and a separate ABL1 FCLK request path from a demonstrated token-to-actuator chain; determine whether `FCLK > UCLK` appears as executable relation logic or only a help string within the inspected exact code.
- Expected effect: an offline reproducible, address-backed static edge result; no claim of runtime invocation, physical frequency, synchronization, or hardware acceptance unless directly evidenced.
- Prohibited: no hardware/register/MMIO/NVRAM/network/install/flash/ROM write; no modification of source ROM or shared memory/project plans; no candidate; no changes to another worker's artifacts.
- Rollback: remove only the uniquely named report/evidence directory/action log if the result is invalidated; all inputs remain unchanged.

## Result

Pending direct disassembly and readback.

## Corrective verification attempt (before rerun)

The first new verifier run exited `1` after 31 checks passed and one test-anchor assertion failed: its expected ABL1 context CMP address was `0x1080A`. The captured direct listing showed the instruction at `0x107F2` is the `cmp.w r0,#0x4b0` instruction; the failure was a wrong verifier expectation, not a ROM/input/hash mismatch. Preserve this error source/status in this log, correct the expected address to the observed disassembly, additionally byte-check the FCLK logger string at payload `0x469C`, and rerun the same pinned offline test. No firmware/input bytes or shared artifact are modified.

## Observed result (after execution)

- Target hash/size check: PASS; CLV SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`, size `16777216`.
- Direct verifier command: `python3 -B evidence/firmware-audit/20260921-df-consumer-next/verify_df_consumer_trace.py`.
- Final literal stdout: `{"status":"PASS","checks_passed":34,"checks_failed":0,"memory_request":"AmdSetup+0x316=0x24 (1800MHz label), preserved","df_serializer":"AmdSetup+0x703 u8->$INV 0x1373; +0x704 u16 LE->$INV 0x1374","fclk_path":"ABL1 0x463C -> descriptors 0x015F/0x0160 -> reader 0x1FB4 -> output [R5]","help_text_enforcement":"NOT_OBSERVED_IN_CHECKED_PATHS; GLOBAL_ENFORCEMENT_UNRESOLVED","first_unresolved":"token 0x1373/0x1374 receiver-to-ABL1 FCLK-key join; ABL1 helper/provider request data origin"}`.
- Final exit status: `0`; final stderr: empty.
- Initial verifier error retained: exit status `1` after `31` checks because the expected context compare address was incorrectly set to `0x1080A`; direct listing observed `cmp.w r0,#0x4B0` at `0x107F2`. Corrected verifier rerun passed `34/34`; no input bytes changed.
- Positive static result: `+0x703` u8 -> INV `0x1373`; `+0x704` u16 LE -> INV `0x1374`; separate ABL1 FCLK descriptor path `0x015F/0x0160` -> reader `0x1FB4` -> output `[R5]`.
- Enforcement result: no checked `FCLK > UCLK` comparison or Memory-P-state read/branch; exact phrase is HII help metadata, and QID `0x37E` bounds `[0,2000]` remain UI metadata.
- First unresolved instruction boundary: post-serializer receiver/provider that would join `0x1373/0x1374` to ABL1 keys `0x015F/0x0160`; ABL1 `0x1FB4 -> 0x4800` request/provider value origin is also unresolved.
- Evidence directory: `evidence/firmware-audit/20260921-df-consumer-next/`; manifest check from that directory returned `22/22 OK`.
- New report: `docs/research/2026-09-21-df-consumer-next.md`.
- New verifier SHA-256: `46678c4ddc82240e503c8f54496f4cf0004820c2e434376f3c9ed2d975dff49f`.
- New result SHA-256: `77c0cc533c925d50522acdd3ad2f0644af0366a7ee27094328ed75cd4da53449`.
- `VERIFICATION.txt` SHA-256: `af23f5c0541aebdb6fb23e724f7d2e89a12c478f3c7e55ef6fb5c6f6bcd07860`.
- `SHA256SUMS.final` SHA-256: `a9591a202d8c60b15f761491cb8dab68056d38bee5bdf526c746dcfa4d487f6f`.
- No firmware, ROM, NVRAM, register, hardware, network, installation or candidate write occurred. Runtime/hardware acceptance remains unrun.
