# CLV $INV 0x1363/0x1364 requester scan — intent

Timestamp: 2026-09-20 (Asia/Almaty)
Actor: bounded offline executor (root), no delegation.
Target: pinned `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (SHA-256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8) and the exact extracted module corpus `evidence/firmware-audit/20260919-inv-token-consumers/` (233 PE32 `.bin` + sibling `.instructions.json` + `.asm`, pinned by that directory's `SHA256SUMS`).
Reason: the superseded bounded result `evidence/firmware-audit/20260920-clv-voltage-offset-consumer-boundary/` (report SHA-256 be7a4eeb40e5bd4a0afe84c79fa75731e7e370216fece5b6d4679802eb03d845, status PARTIAL_BLOCKED_AT_CONSUMER) established serializer representation of `AmdSetup+0x6E5` -> record `0x1363` and `AmdSetup+0x6E6` -> record `0x1364`, but the value/consumer edge stayed open and the requester inventory was bounded to AmdFabricAriPei only.
Scope: read-only scan of the exact corpus for (T1) pinned-input hashes, (T2) instruction-level immediate/branch/memory operand occurrences of the full tokens `0x1363`/`0x1364` with an asm-text cross-surface check, (T3) adjacent u16 LE constant pairs `0x1363` -> `0x1364` inside 16 bytes as a table/computed-consumer hint.
Expected effect: one bounded machine-readable requester inventory plus a human-readable report; either a concrete external requester candidate or a corpus-wide immediate-absence statement bounded to this exact corpus. No firmware, ROM, NVRAM, register, or hardware mutation; no candidate build.
Rollback: delete only the new evidence directory `evidence/firmware-audit/20260920-clv-inv-1364-requester-scan/`, the new report `docs/research/20260920-clv-inv-1364-requester-scan.md`, and this action log.

# CLV $INV 0x1363/0x1364 requester scan — result

Timestamp: 2026-09-20 (Asia/Almaty). Actor: bounded offline executor (root), no delegation.

- Pinned inputs verified: clv `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; 951 corpus-local `SHA256SUMS` entries verified against `evidence/firmware-audit/20260919-inv-token-consumers/` (233 module `.bin` + `.instructions.json` + `.asm`). No mismatch or missing corpus-local entry.
- T2 instruction scan over all 233 modules: `14` immediate hits = `7` identical write-side emitter stubs (`mov [ebp-0x8],ecx` / `mov edx,<0x1363|0x1364>` / `mov eax,[ebp-0x8]`) in `AmdFabricAriPei` (`0x11924`/`0x11956`), `AmdNbioBaseARIPei` (`0x12734`/`0x12766`), `AmdNbioGfxARIPei` (`0xfaf4`/`0xfb26`), `AmdNbioPcieARIPei` (`0x13244`/`0x13276`), `AmdNbioSmuV10Pei` (`0x10444`/`0x10476`), `AmdSocBl5AriPei` (`0x10184`/`0x101b6`), `CbsBasePei` (`0xe3c4`/`0xe3f6`). The `4` memory-reference hits are rip-relative address references whose comments read `# 0x1364`; the `47` branch hits are targets such as `call 0x13641`. asm-text cross-surface check passed for the immediate class.
- T3 adjacent-constant scan: `7` forward `0x1363`->`0x1364` pairs inside the ROM and `1` per each of the same 7 modules, every delta `50 (0x32)` bytes; `0` reverse pairs; no table/data pair.
- T4 config-offset scan: `32` config-displacement hits in `9` modules. `CbsBasePei` and the six `Amd*` PEIMs read `[+0x6e5]` (u8) and `[+0x6e6]` (u32) inside the same stubs; `CbsBaseDxe` plus those modules zero-initialize the pair; `CbsSetupDxe` stores register values into the pair at `rva 0x46cd`/`0x46d4`.
- Verdict: `NO_DIRECT_IMMEDIATE_REQUESTER_IN_EXACT_CORPUS`. Record `0x1364` has no reader in this corpus; the value/consumer edge remains computed/indirect/HOB/runtime and stays unresolved.
- Fresh execution: scanner exit `0`, stdout SHA-256 `5e87d374b6080ddfe32d781565a624e97e053150ed144251845f60eef27a24b2`, stderr empty; re-run stdout byte-identical (deterministic). Pinned prior verifier re-run: exit `0`, stderr empty, stdout SHA-256 `4026f8cebb814fc11fddb58eb5f5fd4e1e41fc878dbba3d3745161ddb7667bd3`, and its `voltage-offset-boundary-result.json` stayed byte-identical to the superseded pin.
- Observed manifest drift (recorded, not resolved, outside this scan's scope): the corpus `SHA256SUMS` entry for `docs/research/2026-09-19-inv-token-consumers.md` expects `d531226f...1289`, the file hashes `5e3e50fb...d6e4`.
- Report: `docs/research/20260920-clv-inv-1364-requester-scan.md`. Machine result and hash pin in the new evidence directory. No firmware, ROM, NVRAM, register, or hardware write; no candidate build.
- Remaining uncertainty: no consumer/rail/unit/1.15 V claim. Rollback unchanged: remove the new evidence directory, the new report, and this action log only.
