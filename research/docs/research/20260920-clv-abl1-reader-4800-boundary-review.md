Current: the raw Thumb BL at ABL1 payload 0x1FE0 targets 0x4800; explicit-target LLVM disassembly confirms the helper entry and its downstream BL.

# CLV ABL1 helper 0x4800 instruction-boundary review

## Verdict

The ABL1 0x4800 helper entry is valid. Raw little-endian Thumb-2 BL bytes at 0x1FE0 are 02 f0 0e fc; independent BL-immediate decoding yields target 0x4800. Raw target bytes begin 7c b5, disassembled from 0x4800 as PUSH {R2,R3,R4,R5,R6,LR}. At 0x481C, raw bytes 00 f0 d6 f8 decode as BL 0x49CC.

The existing full linear Thumb listing has no standalone row at 0x4800; it begins a 32-bit decode at 0x47FE and displays f700 b57c across the true call target. That linear row is not the entry decode for the call at 0x1FE0. LLVM 22.1.8 with explicit Thumb target and start address 0x4800 emits the valid prologue and body through the 0x49CC provider call.

This does not invalidate prior raw-byte/provider assertions at 0x4800. It qualifies how the code must be disassembled: use the direct branch target and explicit Thumb decoding, not the overlapping linear row. The prior provider result is reused by hash only; it was not rerun. The bounded fresh verifier passed 24/24 and independently decodes both BL targets.

## Direct bounded bytes

- Caller: ABL1[0x1FE0..0x1FE4] = 02 f0 0e fc -> Thumb BL target 0x4800.
- Entry: ABL1[0x4800..0x4808] = 7c b5 04 46 0d 46 40 1e; target disassembly starts PUSH then moves/argument setup.
- Helper call: ABL1[0x481C..0x4820] = 00 f0 d6 f8 -> Thumb BL target 0x49CC.
- Explicit command: llvm-objdump -D --triple=thumbv7m-none-eabi --start-address=0x4800 --stop-address=0x4830 /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o.
- Observed explicit-target disassembly, literal stdout: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-4800-boundary-review/target-disassembly.stdout; stderr is empty; exit status 0.
- The exact provider result reused from /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-apcb-consumer-resume/abl1-apcb-consumer-result.json is 36/36 PASS (SHA-256 3950e5136254db2aa9c96c91caba4d48da4a11c369b38a36703c9f54cef45ee9). The explicit target window is structurally consistent with its 0x4800-to-selector-0x0F-to-0x49CC claim. No token semantics or hardware meaning is inferred.

## Exact inputs

- ABL1 payload /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin — SHA-256 af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a; size 94624 bytes.
- Existing exact ELF object /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o — SHA-256 54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135.
- Full Thumb listing /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt — SHA-256 b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65.
- Prior provider result /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-apcb-consumer-resume/abl1-apcb-consumer-result.json — SHA-256 3950e5136254db2aa9c96c91caba4d48da4a11c369b38a36703c9f54cef45ee9.
- LLVM version: 22.1.8.

## Limits

This is observed-byte/static-analysis instruction-boundary verification only. It proves the direct branch destination and a valid Thumb entry under explicit disassembly. It does not revise provider runtime/backing claims, assign a field meaning, establish runtime execution, physical clocks, MCLK=UCLK=FCLK, or hardware behavior. No firmware, ROM, setting or hardware input was changed.

## Artifacts

- Report: /home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl1-reader-4800-boundary-review.md
- Machine result: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-4800-boundary-review/4800-boundary-result.json (SHA-256 cd50b0d4079f3adfab594b2b0d988c95d2e3ffc188d18fb9bcb9a6f83bc8ff3e)
- Action log: /home/OWNER/orca/projects/bc250/docs/action-logs/20260920-clv-abl1-reader-4800-boundary-review.md
- Manifest: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-4800-boundary-review/SHA256SUMS.final
