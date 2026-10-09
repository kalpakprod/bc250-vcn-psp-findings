# CLV ABL1 SVC#4 R1 target report integrity review — intent

Timestamp: 2026-09-20T13:00:00+05:00 (Asia/Almaty; exact shell time will be added to result)
Actor: luna xhigh bounded reviewer
Target: latest `docs/research/20260920-clv-abl1-svc4-r1-target-xhigh.md` and its exact ABL1 bytes/evidence.

Bounded review: independently re-open raw ABL1 bytes and fresh disassembly for the R1 register construction, distinguish FCLK input token `0x61E` from the eventual SVC#4 helper R1, audit whether `0x9AD8` is bound to the active indirect callback or only a conditional initializer candidate, and test whether exact evidence establishes a static initializer for the callback candidate's `[context+0x44]` table pointer. Do not enumerate/decode table entries or reproduce another worker's table discovery. No firmware, ROM, board, settings, install, commit, network, shared plan/memory, or existing evidence result changes.

Read-only anchors:

- Exact ABL1 bytes: `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin` (SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`).
- Existing exact Thumb listing: `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt` (SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`).
- Target report/result/verifier: `docs/research/20260920-clv-abl1-svc4-r1-target-xhigh.md` and `evidence/firmware-audit/20260920-clv-abl1-svc4-r1-target-xhigh/`.
- Existing callback ownership boundary: `docs/research/20260920-clv-abl1-context660-callback-xhigh.md` and `evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/abl1-context660-callback-result.json`.
- Existing callback semantic classification: `docs/research/20260920-clv-abl1-context660-target-semantics.md` and its machine result.

Independent reproduction: create a temporary ELF object from the exact binary with installed `llvm-objcopy`, run a fresh `llvm-objdump` at only the bounded function/call/initializer spans, and independently read exact raw-byte slices with a small standard-library checker. Re-run no existing worker verifier and do not write any existing output path.

Expected effect: create only this new evidence directory, review report and append-only action log. Store commands, byte slices, fresh disassembly, hashes, and verdict. Rollback: delete only this new evidence directory, this report and this action log.

## Observed independent review result

Timestamp: 2026-09-20T13:22:37+05:00 (+05:00).

Exact ABL1 payload remained SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a` (`94,624` bytes). Fresh re-disassembly was produced from the exact payload bytes using a temporary ELF generated only under `/tmp`:

```text
llvm-objcopy --input-target=binary --output-target=elf32-littlearm --binary-architecture=arm evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin /tmp/svc4-r1-boundary-review-20260920/abl1.o
llvm-objdump -D --triple=thumbv7em-none-eabi --start-address=0x107E0 --stop-address=0x10830 /tmp/svc4-r1-boundary-review-20260920/abl1.o
llvm-objdump -D --triple=thumbv7em-none-eabi --start-address=0x10958 --stop-address=0x10970 /tmp/svc4-r1-boundary-review-20260920/abl1.o
llvm-objdump -D --triple=thumbv7em-none-eabi --start-address=0x9AD8 --stop-address=0x9B5C /tmp/svc4-r1-boundary-review-20260920/abl1.o
llvm-objdump -D --triple=thumbv7em-none-eabi --start-address=0x9C00 --stop-address=0x9D00 /tmp/svc4-r1-boundary-review-20260920/abl1.o
llvm-objdump -D --triple=thumbv7em-none-eabi --start-address=0x7378 --stop-address=0x7512 /tmp/svc4-r1-boundary-review-20260920/abl1.o
llvm-objdump -D --triple=thumbv7em-none-eabi --start-address=0xAF90 --stop-address=0xB14E /tmp/svc4-r1-boundary-review-20260920/abl1.o
llvm-objdump -D --triple=thumbv7em-none-eabi --start-address=0xB228 --stop-address=0xB284 /tmp/svc4-r1-boundary-review-20260920/abl1.o
python3 -B evidence/firmware-audit/20260920-clv-abl1-svc4-r1-boundary-review/verify_svc4_r1_boundary.py
```

Observed independent raw-byte verifier result: exit `0`, `44/44 PASS`, stderr empty. It checks the exact call/register bytes directly from the pinned decompressed input and reads existing reviewer records without invoking or altering other verifiers. Fresh LLVM output and raw byte slices are captured in this review's evidence directory.

Bounded correction: the FCLK branch's `R1=0x61E` is only the indirect callback selector/token. Candidate body `0x9AD8` passes `R4` as helper `R1` at `0x9C28/0x9D94`, but the active dispatcher target is not identified. Exact initializer `0xAF90` installs its conditional callback literal into the initializer parent `+0x660`; active FCLK caller passes current `R4`, and no object-identity join exists. Exact module function `0xB228` stores helper-supplied pointers into its `+0x44` field at `0xB266`/`0xB274`; no static table-base literal is used in those stores. This proves an in-module pointer-initialization path, not that this function ran for the active FCLK context or which lookup/fallback path supplied the live table.

Concurrent table-worker state was observed without rerunning or editing its artifacts. Earlier readback was hash `ef4f7cb0...` with `FAIL`, `71/75`; later readback at `13:18:10+05:00` was hash `14f71a9b17faa3b669681c574036ccb8edb3d75b7fde966a73aa0beb9dd9f7c0`, JSON status `PASS`, `75/75`. This review does not independently validate its table-slot/fallback values; use only after root reopens the latest owner artifact.

No claim is made that SVC#4 handler absence alone makes an encoded SMN target unrecoverable: a recovered active descriptor might identify an encoded target. This bounded review simply does not establish that active descriptor, a physical mapped window, or hardware effect. No firmware, hardware, settings, existing result, plan/memory, install, or commit was changed.

Owned outputs: `docs/research/20260920-clv-abl1-svc4-r1-boundary-review.md`, this log, and `evidence/firmware-audit/20260920-clv-abl1-svc4-r1-boundary-review/`. Rollback: remove only those owned outputs; do not remove or restore any other worker artifact.

## Result and correction

Timestamp: 2026-09-20T13:25:01+05:00 (+05:00).

Independent fresh `llvm-objcopy`/`llvm-objdump` output on the pinned ABL1 plus direct standard-library raw-byte checks established:

- FCLK `R1=0x61E` is moved by dispatcher to candidate callback `R2`; dispatcher loads `[current_context+0x660]` and branches indirectly.
- Candidate body `0x9AD8`, **if active**, passes `R4` to SVC helper `R1` at `0x9C28`/`0x9D94`; the numeric R4/active target is unresolved.
- Active binding `current R4+0x660 -> 0x9AD8` is not proven. The static initializer writes its conditional literal to the parent object `+0x660`, and constructor/active contexts are not joined.
- Exact function `0xB228` includes two `[R4+0x44]` pointer stores from helper-output stack slots (`0xB266`, `0xB274`); the base is helper-supplied, not a static table-base literal. This is a code-backed initialization mechanism, but its run/owner identity for the active FCLK object is unresolved. No table entries are decoded by this review.
- An encoded SMN descriptor could be statically identifiable without recovering an SVC#4 handler; this review does not establish the active descriptor, physical mapped window, or hardware effect, and does not claim handler absence makes target recovery impossible.

Independent raw-byte checker:

```text
python3 -B evidence/firmware-audit/20260920-clv-abl1-svc4-r1-boundary-review/verify_svc4_r1_boundary.py
```

Observed exit `0`, stdout status `PASS`, `44/44`; stderr empty. The first checker attempt wrote its own result with status `FAIL` (`36/44`) because eight expected raw byte strings were transcribed in disassembly halfword order instead of file-byte order. Failures were the expected values for `0x73AE`, `0xB22E`, `0xB264`, `0xB266`, `0xB26A`, `0xB274`, `0xB23A`, and `0xB252`; observed raw slices were the file-order values shown in the corrected checker. The first shell used `set -e` before capturing a separate exit file, so its numeric process exit is **not** claimed here. Only this new verifier script/result/output was corrected; ABL1 input and every pre-existing artifact remained unchanged.

Other worker table-discovery artifact status was separately read without execution/edit: at `13:18:10+05:00`, `descriptor-source-result.json` SHA-256 `14f71a9b17faa3b669681c574036ccb8edb3d75b7fde966a73aa0beb9dd9f7c0`, JSON `PASS`, `75/75`. Its previous hash/status snapshot `ef4f7cb0...`, `FAIL`/`71 of 75`, was superseded by that owner result. This review does not use its table entries as independently verified; no other worker artifact was changed.

No firmware, ROM, board, settings, candidate, plan, shared memory, install, network or commit action occurred. Exact source hashes at readback were unchanged. New outputs and rollback scope are exactly those named in the intent.

## Root-requested bounded fallback-store/base follow-up — intent

Scope addition (read-only): independently validate only the two candidate fallback stores at payload `0xC79A` and `0xC7DE`, calculate their word-slot offsets from `0x61E` and the nested index decoded from literal `0x006D17C0`, and trace the local source of the store-base register `R1` within the containing code path. Do not scan/decode the full table or accept worker assertions. Preserve that the fallback writer may or may not use the pointer installed at `context+0x44`; decide this from exact local dataflow rather than labels.

Expected effect: append only a small independent raw/disassembly/readback section to this review's owned evidence/report/log. No modification to the other worker's files and no hardware/runtime capture.

## Minimal descriptor arithmetic and map concordance

Timestamp: 2026-09-20T13:31:40+05:00 (+05:00).

The independent verifier now includes 11 additional raw/arithmetic checks (`55/55 PASS` total):

- `0x61E * 4 = 0x1878`.
- Raw payload `0xC9F0..0xC9F3 = c0 17 6d 00` -> candidate outer slot literal `0x006D17C0`.
- `(0x006D17C0 >> 12) & 0xFFF = 0x6D1`; `0x6D1 * 4 = 0x1B44`.
- Raw payload `0xC9D8..0xC9DB = 7c 02 00 08` -> candidate nested descriptor `0x0800027C`.
- Descriptor fields: kind bits `27..29 = 1`, bit30 `0`, low12 `0x27C`, field start `0x3C`, field end `9`.
- Conditional kind-1 arithmetic with `context+0x49=0` yields `R4=0x5027C`.

The independent PMFW report `docs/research/2026-09-20-oc-df-init-route.md` statically identifies the same `0x5027C`/`0x5227C` address bases as row+0x20 aperture targets written by SMU function `0x1EF18` through helper `0x2A74`; its exact SMU body is `smu_fw_robin_5`, SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`, and is byte-identical to the pinned CLV PMFW slice per that report. This supports a **conditional static address concordance** only. It does not join the fallback candidate `R1` base to the active `context+0x44` table, prove FCLK callback binding, establish that `0x5027C` is a physical clock register, or provide runtime/hardware evidence.

The prior report sentence “the exact runtime table slot values ... remain unavailable” remains correct for the active path; this supplemental raw arithmetic does not upgrade a candidate fallback literal into an active runtime slot.
