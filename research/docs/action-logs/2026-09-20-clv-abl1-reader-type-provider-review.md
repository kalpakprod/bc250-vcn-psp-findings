# CLV ABL1 FCLK type-pointer/provider boundary review — intent

Timestamp: 2026-09-20T11:20:06+05:00 Asia/Almaty
Actor: bounded independent reviewer.
Target: exact FCLK caller `0x463C..0x466A`, common reader `0x1FB4`, helper `0x4800`, and provider `0x49CC`; verify whether the FCLK type-byte pointer `SP+0x0C` is written by the provider or remains unproven. Do not duplicate the active `+0x660` callback discovery and do not modify shared memory/plan, firmware, settings, candidates, or hardware.

Bounded question: trace only the pointer argument from FCLK `R3=SP+0x0C` through reader `R10`, helper stack forwarding, and the exact provider output/store path. Preserve runtime/base uncertainty. Resolve whether the provider's byte-length/type write reaches the FCLK type local, or whether the exact stack slot remains ambiguous.

Pinned inputs:

- Active callback report `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl1-context660-callback-xhigh.md` SHA-256 `039d8024d8db386fc9d136bedd7943abb8dcbad8aeb6ed2594a15ce9572aa8ad`; result `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/abl1-context660-callback-result.json` SHA-256 `cf16bf73c370bac1c4426f7c79e64890898a11da7743304528ddeccfe3cd7ecb` (review only, no active-660 scan).
- Existing reader fallback/type report `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl1-reader-fallback-status-xhigh.md` SHA-256 `dfadcfec1e748ffdbcf20bdbe47bd44f944c8b75e3ccd45ee5e7848142b2a8ed`.
- Existing provider result `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-apcb-consumer-resume/abl1-apcb-consumer-result.json` SHA-256 `3950e5136254db2aa9c96c91caba4d48da4a11c369b38a36703c9f54cef45ee9`.
- Exact ABL1 `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin` SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Exact Thumb listing `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt` SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.

Expected outputs: one fresh verifier/result/report/manifest and this action log under the unique `reader-type-provider-review` name. No shared memory/plan write. Reopen report, result, action log, manifest and native role paths before reporting.

Next executable action: run a narrow raw-byte/listing verifier over FCLK call setup, reader preservation, helper stack forwarding, provider stack-slot read/write, and exact typed-store branches. No broad scan and no new callback research.

Rollback: remove only the new verifier/result/report/manifest/action-log set; preserve all pinned inputs and active callback artifacts.

## Scope correction and bounded stop (2026-09-20)

Root redirected the active review to the already-produced `0x9AD8` target-semantics result; do not duplicate callback discovery. The first type-provider verifier invocation exited `1` before result serialization because the LLVM listing omits a separate `0x4800` row (the entry bytes are overlapped by the preceding decoded 32-bit instruction); no input bytes changed and no result is claimed from that failed attempt.

A separate 18-check direct read-only review was executed against the existing target-semantics and callback result artifacts plus exact ABL1 bytes. It passed: `0x9AD8` remains conditionally compatible with descriptor-indexed field RMW, exact mapped word read/store paths at `0x6DA4`/`0x6E70` were corroborated, SVC `#4` is observed at `0x6DD4` and `0x6EAE`, and no exact SVC-4 API/handler/port mapping was found in existing project analyses outside the target report. Active FCLK binding remains unproven; no hardware or clock claim follows.

## Method correction after helper-boundary result (2026-09-20T17:30:16+05:00 Asia/Almaty)

The raw/explicit-target boundary review verified BL 0x1FE0 -> 0x4800 and BL 0x481C -> 0x49CC; full linear listing has no valid 0x4800 row. Reuse the explicit 0x4800 target disassembly and independently request an LLVM window starting at the actual 0x49CC BL target. The exact provider function window is the bounded path needed to follow the FCLK type pointer; do not use linear rows whose start was consumed by an overlapping decode. No new callback/0x660 search.

## Critical provider-frame correction (2026-09-20)

The fresh explicit-target verifier exited 1 because it expected the 0x49CC push as 0x30 bytes and therefore assigned the provider store to the wrong stack argument. LLVM disassembly shows push.w {r0..r11,lr}, which is 13 registers = 0x34 bytes, not 0x30. Correct stack accounting: provider arg1 = current SP+0xA0 (helper outgoing arg1, the FCLK type pointer); provider arg2 = SP+0xA4 (helper outgoing arg2, R9). The provider's 0x4BF0/0x4BFA load/store through SP+0xA0 therefore writes the FCLK type pointer. This reverses the previous tentative uncertainty; rerun the same bounded exact-target verifier with only frame-size/semantic assertions corrected.

## Stack-slot assertion correction (2026-09-20)

The corrected verifier reached the intended provider window but retained the old assertion that SP+0xA0 must be absent. The exact provider necessarily references SP+0xA0 at 0x4A0C, 0x4BF0, 0x4C1E and 0x4E38; change the assertion to require the 0x4BF0 access and separately require no SP+0x9C access. No inputs changed.

## Final assertion endian correction (2026-09-20)

The bounded verifier reached the final caller-stack checks; FCLK store instruction bytes are little-endian `00 92` and `01 92`, not the display-order strings `92 00`/`92 01`. Correct only expected hex text and rerun.
