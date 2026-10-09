# Luna fixed-rail PEI applicability — intent and result

## Intent

Timestamp: 2026-09-21T00:04:24+05:00 (Asia/Almaty). Actor: subagent `/root/luna_fixed_rail_conditions`; parent `/root` owns scope, integration, and final review.
Target: immutable CLV donor `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`, plus the already-decoded TE disassemblies in `evidence/firmware-audit/20260920-fixed-voltage-independent-decode/` and the existing UEFITool report/extractions.
Question: what static PEI depex, platform-ID, and VR-identity conditions determine whether the two modules `ISL69247` and `ISL95712` reach their Setup-dependent mailbox write paths?
Existing route: use the exact prior CLV TE decodes, FFS identities, UEFITool report and extracted PEI-dependency sections; do not rescan token `0x1364`, duplicate the producer/consumer scan, or use hardware/register/ROM actions. A narrow direct FFS/depex read will validate the depex bytes from the pinned donor and compare them with existing UEFITool extraction. A bounded review of the existing entry-path disassembly will enumerate its conditional branches.
Expected effect: one fresh read-only machine evidence record with donor/FFS/depex hashes, both parsed dependency expressions, and the relevant entry-path branch offsets; one English report and this append-only action log. No candidate, firmware image, NVRAM, register, hardware, network, or shared-memory write.
Acceptance: report either one new evidence-based applicability condition or the exact unresolved gate; do not turn static dispatch potential into a claim of PEIM execution, applied voltage, rail identity, or safety.
Rollback: remove only `evidence/firmware-audit/20260921-luna-fixed-rail-conditions/`, `docs/research/2026-09-21-luna-fixed-rail-conditions-current.md`, and this log.

## Observed result

Timestamp: 2026-09-21T00:10:55+05:00 (Asia/Almaty). Actor: subagent `/root/luna_fixed_rail_conditions`.

Reproducible command:
`PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260921-luna-fixed-rail-conditions/applicability_check.py`

Observed: exit `0`, stderr `0` bytes, stdout SHA-256 `7a4b42a127f0badeae0994aed103b52d188b0c10281f7821bc0707fe5e0019e9`, machine `status=PASS`. It matches the initial one-off direct FFS/depex read byte-for-byte (`cmp -s` exit `0`). The reproducible checker SHA-256 is `7380ffb4980ed2b3070e9f7f568fb9146f2c03f169d5f63aa7e183a937b62623`; `sha256sum -c SHA256SUMS.final` passed for all 8 listed evidence files.

Fresh observations (static-analysis over the pinned bytes and pre-existing disassembly):

- Donor hash/size stayed `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8` / 16,777,216 bytes.
- Both target FFS files have type `0x06` and current state `0xF8`; both raw depex sections decode to the same `PUSH F894643D-C449-42D1-8EA8-85BDD8C65BDE`, `PUSH 01F34D25-4DE2-23AD-3FF3-36353FF323F1`, `AND`, `END` expression. ROM bytes match UEFITool extracted depex bodies and their parsed output. ROM TE sections match the previously extracted TE binaries and exact hashes in the report.
- Entry-window conditional branch lists: ISL69247 `0x2BF, 0x312, 0x386, 0x3B0, 0x421`; ISL95712 `0x27C, 0x2BA`. Their meanings are respectively the PPI-lookup-shaped call result, field-enable, and loadline checks; the branch paths rejoin before the mailbox/controller writes. Static entry code shows no board/SKU or VR-ID conditional.
- The unresolved dispatch input is whether/when the exact opaque PPI `01F34D25-4DE2-23AD-3FF3-36353FF323F1` is installed in the selected live PEI. No source/provider mapping or runtime dispatch was established. Thus potential write reachability is bounded, actual module execution and physical effect are not.

Evidence outputs: `evidence/firmware-audit/20260921-luna-fixed-rail-conditions/` (`SHA256SUMS.final` SHA-256 `df6459d59cf7de5fca61806de2dbdda07a2ab5c8f716297b25ed672b495a1e06`; `VERIFICATION.txt` SHA-256 `ea6a75bcceec3d0fd5856563574ff0869629feee159953ca806aaea647ab1241`). Report `docs/research/2026-09-21-luna-fixed-rail-conditions-current.md` SHA-256 `a62b77e80e13a1b61b97986b83bc23eeca02284b99ecc45a6f85bc86439df2b2`.

No token `0x1364` rescan, hardware/register/ROM/NVRAM action, network access, or shared-memory write occurred. No physical rail identity, applied voltage, or safety conclusion is made.
