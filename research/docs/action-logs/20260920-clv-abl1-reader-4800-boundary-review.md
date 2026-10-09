# CLV ABL1 helper 0x4800 instruction-boundary review — intent

Timestamp: 2026-09-20T11:42:38+05:00 Asia/Almaty
Actor: bounded independent decoder reviewer.
Target: exact raw ABL1 Thumb target reached by the `0x1FE0` BL, and the helper's `0x481C` BL target. Resolve the apparent linear-listing overlap at `0x47FE/0x4800` without broad analysis.

Question: independently decode the two actual BL targets from raw Thumb-2 immediates, then disassemble one function window from valid target `0x4800` with explicit Thumb architecture/base. Preserve the existing failure capture from the type-provider checker and determine whether prior `0x4800` helper claims rest on a valid boundary.

Pinned inputs:

- Exact ABL1 `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin` SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Existing exact object `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o` SHA-256 `54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135` for explicit-target LLVM disassembly.
- Existing full listing `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt` SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65` only as comparison evidence.
- Existing provider result `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-apcb-consumer-resume/abl1-apcb-consumer-result.json` SHA-256 `3950e5136254db2aa9c96c91caba4d48da4a11c369b38a36703c9f54cef45ee9`.

Expected effect: one fresh verifier, exact-target disassembly capture, report, manifest and this action log only. No ROM/settings/hardware/shared memory/plan/candidate writes and no semantic/hardware inference.

Next executable action: run raw Thumb BL decode plus LLVM `llvm-objdump -D --triple=thumbv7m-none-eabi --start-address=0x4800 --stop-address=0x4830` on the existing exact object, and assert the decoded target/prologue/callee BL.

Rollback: remove only this uniquely named evidence/report/action-log set. Preserve all pinned inputs and previous reports.

## Second verifier setup correction (2026-09-20T11:45:53+05:00 Asia/Almaty)

A patch command wrapper failed with Python quoting syntax before modifying the checker, then the shell continued and reran the stale checker, which repeated the bytes-versus-hex assertion failure. Preserve this failed execution; no inputs changed. Correct the checker using a plain Python replace, set shell-independent captured execution, and pin exact object hash 54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135.

## Verifier serialization and patch-command correction (2026-09-20T11:47:04+05:00 Asia/Almaty)

A JSON-ledger execution exited 1 because the raw helper-BL assertion retained a bytes object. A subsequent attempted patch command itself failed at Python syntax due unnecessary quote escaping; it did not execute or modify the checker. Correct only the ledger serializer and rerun the bounded verifier. No input bytes changed.

## Final observed result (2026-09-20T11:51:33+05:00 Asia/Almaty)

Verifier command: python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-4800-boundary-review/verify_4800_boundary.py; stdout='{"status":"PASS","checks":24,"reader_bl_target":"0x4800","helper_bl_target":"0x49CC","explicit_objdump_exit":0}'; stderr=''; exit status 0; 24/24 PASS. Its internal LLVM command was llvm-objdump -D --triple=thumbv7m-none-eabi --start-address=0x4800 --stop-address=0x4830 /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o, stdout captured in /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-4800-boundary-review/target-disassembly.stdout, stderr empty, exit 0.

Raw instruction proof: 0x1FE0 bytes 02 f0 0e fc decode to BL target 0x4800; target begins 7c b5 and explicit disassembly confirms a Thumb PUSH prologue. 0x481C bytes 00 f0 d6 f8 decode to 0x49CC. The prior 36-check provider result remains reused by hash; no broad reanalysis or hardware action occurred.

The previous xxd command failed because xxd is absent (shell error 127); direct bytes were read with Python. An llvm-objdump -d pass produced headers only for the non-executable .data section; corrected to -D and explicit Thumb target. The first persisted verifier had a bytes-versus-hex assertion error; subsequent checker-patch commands had quoting/serialization failures, retained above; the corrected exact-input verifier passes. No input bytes changed.

Final report SHA-256 6f47c4205e40eabfda672e70771d9a387868ea8480c3c97e0932389b1140d36b; result SHA-256 cd50b0d4079f3adfab594b2b0d988c95d2e3ffc188d18fb9bcb9a6f83bc8ff3e. Manifest covers these paths and captured outputs.
