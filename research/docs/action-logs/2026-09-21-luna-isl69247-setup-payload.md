# ISL69247 Setup payload and page sequencing — action log

## Intent

- Timestamp: 2026-09-21T01:17:15+05:00 (Asia/Almaty)
- Actor: Luna, bounded static reverse-engineering follow-through
- Target: new report `docs/research/2026-09-21-luna-isl69247-setup-payload.md`; existing immutable CLV disassembly `evidence/firmware-audit/20260920-fixed-voltage-independent-decode/ISL69247.disasm.txt` and its cited fixed-voltage reports.
- Procedure: read `memory/oc-recheck.md` to EOF, the relevant BC-250 reverse-engineering/research-provenance skills, `docs/knowledge-sources.md`, and the prior independent decode result; run a changed inline Python verifier over the exact disassembly hash and instruction windows for page helper `0x5D3`, VCORE/GFX Setup-word loading, fixed-voltage branches, and mailbox payload helper `0x6ED`. No ROM, NVRAM, firmware, board, I/O-port, or register write.
- Rationale: determine whether Setup VCORE/GFX u16 values are numerically transformed before mailbox staging, and whether command `0x21` uses page 0/1 conditionally or follows fixed page sequencing.
- Expected effect: report observed instruction flow separately from inferred VR/PMBus semantics; preserve the distinction between raw Setup payload and physical voltage.
- Rollback: remove only this new report and this action log. Existing disassembly and prior evidence remain untouched.

## Observed result

Pending report write/readback. The first verifier attempt used an incorrect assumption for helper `0x6ED` (`mov` instead of the decoded `push DWORD PTR [esp+0x14]`) and exited nonzero with an assertion failure; no project artifact changed. The corrected verifier is recorded in the report and passed.

## Result and readback

- Timestamp: 2026-09-21T01:25:00+05:00 (Asia/Almaty)
- Input disassembly reopened with SHA-256 `cb15e09a6b7c35bb6dff13c40f61b3b076c999f3ce60c62b99476bbb1db34aab`; prior report hashes were read before this task and are recorded in the report.
- Corrected inline verifier (changed after the initial assertion error on helper `0x6ED` operand wording) exited `0` with literal `PASS 17/17`; it verified page-0/page-1 helper calls and payloads, VCORE/GFX flag branches, direct Setup-word loads, helper target passing, low/high byte staging, and trigger fields.
- Finding: Setup words are zero-extended then byte-split unchanged; fixed-page sequence is page payload `0`, then `1`, not flag-selected. `0x21` is called on both enable outcomes, with stored u16 versus default `0x384` chosen by flags.
- Qualification: register/PMBus semantics, physical rail, raw-to-mV conversion, PEIM dispatch, mailbox execution and applied voltage remain unverified. No board, I/O ports, bus, firmware, NVRAM, or register operation occurred.
- Report path: `docs/research/2026-09-21-luna-isl69247-setup-payload.md`.
