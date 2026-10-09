# ABL reachable-output pointer review — intent

- Timestamp: 2026-09-21T19:02:52+05:00 (Asia/Almaty).
- Actor: `/root/clock_claims_adjudication`, bounded independent static reviewer.
- Active object: latest ABL reachable-output pointer-identity claim, exact windows `0x7E40`, `0x7E74`, `0x5FBA`.
- Checkpoint: `docs/action-logs/2026-09-21-clv-111-heap-correction-transaction.md`; author-output finalized=True.
- Last confirmed result and next action: recorded in selected checkpoint; this run invokes its existing pointer verifier if present, otherwise checks only those three local instruction windows.
- Inputs: evidence/firmware-audit/20260920-clv-abl-memory-review, evidence/firmware-audit/20260921-apob-abl-outer864-root-review, evidence/firmware-audit/20260921-apob-abl-outer864-root-review, evidence/firmware-audit/20260921-abl-item17-reachable-output, evidence/firmware-audit/20260920-clv-abl1-downstream, evidence/firmware-audit/20260921-apob-abl-outer864-root-review, evidence/firmware-audit/20260921-abl-item17-consumer, evidence/firmware-audit/20260921-apob-abl-outer864-root-review; no float, heap, HOB, broad consumer, or user-prompt test cases.
- Expected effect: disposable child output only, plus this log and `docs/research/2026-09-21-abl-reachable-pointer-review.md`.
- Safeguards: offline; no board, network, ROM, NVRAM, register, or hardware changes.
- Rollback: remove only this review report, this action log, and the unique `/tmp` run directory.

## Observed execution

- Timestamp: 2026-09-21T19:02:52+05:00 (Asia/Almaty).
- Command: `python3 -B /tmp/bc250-abl-pointer-review-rf6rxkwu/project/evidence/firmware-audit/20260920-clv-abl-memory-review/abl1_memory_review_verify.py`; unique disposable directory `/tmp/bc250-abl-pointer-review-rf6rxkwu`.
- Exit status: 0; stdout/stderr/exit are preserved under that disposable directory.

## Corrected dispatch intent — exact pointer window

- Timestamp: 2026-09-21T19:07:25+05:00 (Asia/Almaty).
- The first selected runner was `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/abl1_memory_review_verify.py` and returned `26/26 PASS`, but it did not test the requested `0x7E40/0x7E74/0x5FBA` pointer edge; it is preserved as scope-mismatched and not accepted.
- Corrected action: inspect only the three specified instruction windows and their local output edge using copied inputs `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-consumer/ABL1-clv-decompressed.bin` and `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o` in a unique disposable directory.
- No global alias, clock-unit, HOB, heap, ROM, or hardware inference/test is included.

## Corrected exact-window command intent

- Timestamp: 2026-09-21T19:14:37+05:00 (Asia/Almaty).
- Prior selected `abl1_memory_review_verify.py` exited `0` (`26/26`) but did not exercise `0x7E40/0x7E74/0x5FBA`; its result remains scope-mismatched and is not an acceptance event for pointer identity.
- A second dispatcher attempt stopped at Python `AttributeError: 'PosixPath' object has no attribute 'bin'` while constructing a disposable filename, before child disassembly ran. Its exact wrapper exit status was not printed, so no exit code is claimed.
- Corrected next action: copy the exact hash-pinned payload and the specified `ABL1-clv-full-thumb.elf.o` to a unique `/tmp` directory; run existing LLVM objdump windows at `0x7E3E..0x7E80` and `0x5E60..0x5FC4`; read matching raw bytes from the copied payload with `od`. No HOB/heap/float checks or global alias scan.
- Input hashes: payload `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`, object `adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6`.

## Exact-window command execution

- Timestamp: 2026-09-21T19:14:37+05:00 (Asia/Almaty).
- Tool: `/usr/bin/llvm-objdump`; version `LLVM (http://llvm.org/):`.
- Temporary outputs: `/tmp/bc250-abl-pointer-window-x27immd2`.
- Command 1: `/usr/bin/llvm-objdump -d --start-address=0x7e3e --stop-address=0x7e80 /tmp/bc250-abl-pointer-window-x27immd2/ABL1-clv-full-thumb.elf.o`; exit `0`; stderr bytes `0`; stdout SHA-256 `5e64188f29bd869c30e7201ea84a0aa5e59cd25ed5f3bc12731da01022414eea`.
- Command 2: `/usr/bin/llvm-objdump -d --start-address=0x5e60 --stop-address=0x5fc4 /tmp/bc250-abl-pointer-window-x27immd2/ABL1-clv-full-thumb.elf.o`; exit `0`; stderr bytes `0`; stdout SHA-256 `5e64188f29bd869c30e7201ea84a0aa5e59cd25ed5f3bc12731da01022414eea`.
- Command 3: `od -An -v -tx1 -j 0x7e40 -N 0x40 /tmp/bc250-abl-pointer-window-x27immd2/ABL1-clv-decompressed.bin`; exit `0`; stderr bytes `0`; stdout SHA-256 `fbfb296773e05552635f84317de96d83727e493cc15c5e3fe68621351ff6fdd5`.
- Command 4: `od -An -v -tx1 -j 0x5fba -N 0x20 /tmp/bc250-abl-pointer-window-x27immd2/ABL1-clv-decompressed.bin`; exit `0`; stderr bytes `0`; stdout SHA-256 `cf5ece02d9a76bfc2a65be5b928025f7c24cec3396400735ca8ab8da1acf8260`.

## Latest-report direct-code review intent

- Timestamp: 2026-09-21T19:26:01+05:00 (Asia/Almaty).
- New input report: `docs/research/2026-09-21-abl-item17-reachable-output.md`; latest author action log: `not present`.
- Correction: the preceding `llvm-objdump -d` run used the wrong older `ABL1-exact.o`; it emitted only ELF headers and no instruction lines (exit 0), so it is not accepted for this claim.
- Corrected input object: `evidence/firmware-audit/20260921-abl-item17-reachable-output/ABL1-clv-full-thumb.elf.o` SHA-256 `adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6`; matching decompressed payload `evidence/firmware-audit/20260921-abl-item17-consumer/ABL1-clv-decompressed.bin` SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Next action: disassemble the exact object at only `0x7E40..0x7E80` and `0x5E68..0x5FC2`, and inspect copied raw payload bytes at the cited store/call. Then decide if R4 concern is register clobber, pointee mutation, or both; any AAPCS preservation inference must be explicit.
- No HOB/heap/float tests, global pointer scan, hardware, network, or ROM/NVRAM/register action.

## Latest-report direct-code command execution

- Timestamp: 2026-09-21T19:26:02+05:00 (Asia/Almaty).
- Command set ran in `/tmp/bc250-abl-pointer-final-nlwcl8x9` against copied exact input object/payload; no project evidence output was written.

## New-report object disassembly / raw payload review

- Timestamp: 2026-09-21T19:33:51+05:00 (Asia/Almaty).
- Inputs: report `docs/research/2026-09-21-abl-item17-reachable-output.md`; object `evidence/firmware-audit/20260921-abl-item17-reachable-output/ABL1-clv-full-thumb.elf.o` SHA-256 `adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6`; ABL1 payload `evidence/firmware-audit/20260921-abl-item17-consumer/ABL1-clv-decompressed.bin` SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- New method: LLVM `-D` on exact object plus raw payload `od`, all copies/output under `/tmp/bc250-abl-pointer-decode-mtfxglm4`. The preceding `-d` run on this exact object returned exit 0 but emitted no instructions; not accepted.
- Command 1: `/usr/bin/llvm-objdump -h /tmp/bc250-abl-pointer-decode-mtfxglm4/ABL1-clv-full-thumb.elf.o`; exit `0`; stdout SHA-256 `0a8c378810ca0340db8646d85c40efbdd613e181a7b90e90bef15c7903d02e2b`; stderr bytes `0`.
- Command 2: `/usr/bin/llvm-objdump -D --start-address=0x7e3e --stop-address=0x7e80 /tmp/bc250-abl-pointer-decode-mtfxglm4/ABL1-clv-full-thumb.elf.o`; exit `0`; stdout SHA-256 `1b8d202ab52d1e6f4f83846dabd8085b52a08cb66cf4f2ce4200ec9f268cb8bd`; stderr bytes `0`.
- Command 3: `/usr/bin/llvm-objdump -D --start-address=0x5e60 --stop-address=0x5fc2 /tmp/bc250-abl-pointer-decode-mtfxglm4/ABL1-clv-full-thumb.elf.o`; exit `0`; stdout SHA-256 `fa4f3654486eaa5df20be8b99de30fc162006b5885f24856f630c19522e3c92d`; stderr bytes `0`.
- Command 4: `od -An -v -tx1 -j 0x7e40 -N 0x40 /tmp/bc250-abl-pointer-decode-mtfxglm4/ABL1-clv-decompressed.bin`; exit `0`; stdout SHA-256 `fbfb296773e05552635f84317de96d83727e493cc15c5e3fe68621351ff6fdd5`; stderr bytes `0`.
- Command 5: `od -An -v -tx1 -j 0x5fba -N 0x20 /tmp/bc250-abl-pointer-decode-mtfxglm4/ABL1-clv-decompressed.bin`; exit `0`; stdout SHA-256 `cf5ece02d9a76bfc2a65be5b928025f7c24cec3396400735ca8ab8da1acf8260`; stderr bytes `0`.

## Corrected Thumb-mode disassembly intent

- Timestamp: 2026-09-21T19:41:28+05:00 (Asia/Almaty).
- The `-D` command on the copied ELF object defaulted to ARM-state decoding despite the target windows being Thumb; therefore it is not accepted for R4 analysis.
- Changed command: force `thumbv7a-none-eabi` target on the same hash-pinned ELF wrapper, use exact start/stop windows, and compare raw payload bytes in a new unique `/tmp` directory. This tests actual disassembled code, not report assertions.

## Corrected Thumb-mode disassembly execution

- Timestamp: 2026-09-21T19:41:28+05:00 (Asia/Almaty).
- Disposable directory: `/tmp/bc250-abl-thumb-review-uevykpa1`.
- Command 1: `/usr/bin/llvm-objdump -D --triple=thumbv7a-none-eabi --start-address=0x7e3e --stop-address=0x7e80 /tmp/bc250-abl-thumb-review-uevykpa1/ABL1-clv-full-thumb.elf.o`; exit `0`; stdout SHA-256 `b19bbd7847e09f18334b188865d9a68d8d0199b0f807fe90f9d558d754d9ddfd`; stderr bytes `0`.
- Command 2: `/usr/bin/llvm-objdump -D --triple=thumbv7a-none-eabi --start-address=0x5e68 --stop-address=0x5fc4 /tmp/bc250-abl-thumb-review-uevykpa1/ABL1-clv-full-thumb.elf.o`; exit `0`; stdout SHA-256 `436ce8bc00a0c43307dca9c9ce9139d897b2247127b2fcbe7c8b3ec2c3b9bca1`; stderr bytes `0`.
- Command 3: `od -An -v -tx1 -j 0x7e40 -N 0x40 /tmp/bc250-abl-thumb-review-uevykpa1/ABL1-clv-decompressed.bin`; exit `0`; stdout SHA-256 `fbfb296773e05552635f84317de96d83727e493cc15c5e3fe68621351ff6fdd5`; stderr bytes `0`.
- Command 4: `od -An -v -tx1 -j 0x5fba -N 0x20 /tmp/bc250-abl-thumb-review-uevykpa1/ABL1-clv-decompressed.bin`; exit `0`; stdout SHA-256 `cf5ece02d9a76bfc2a65be5b928025f7c24cec3396400735ca8ab8da1acf8260`; stderr bytes `0`.

## New decisive local R4/callback trace intent

- Timestamp: 2026-09-21T19:48:35+05:00 (Asia/Almaty).
- Bound target: exact Thumb code around callback dispatch `0x83B0`, later call `0x8428`, indirect helper `0x10958`, and the branch into local `0x10200`; no global alias or producer scan.
- Question: does actual code change R4 register, mutate the pointed-to object, or both; state any AAPCS assumption explicitly.
- Inputs: existing exact wrapper `evidence/firmware-audit/20260921-abl-item17-reachable-output/ABL1-clv-full-thumb.elf.o` and pinned payload `evidence/firmware-audit/20260921-abl-item17-consumer/ABL1-clv-decompressed.bin`. Fresh unique `/tmp` copy only.
- Expected effect: disassembly/raw windows and a conditional local-edge conclusion only; no hardware, network, ROM, NVRAM, register, or candidate changes.

## New decisive R4/callback trace execution

- Timestamp: 2026-09-21T19:48:35+05:00 (Asia/Almaty).
- Unique disposable directory: `/tmp/bc250-abl-r4-callback-review-vai8maaf`. LLVM Thumb mode used `--triple=thumbv7a-none-eabi`; raw payload windows read with `od`.
- `caller_callback_path` exit `0`, stdout SHA-256 `d576f5b36a17787e755db6dbc997e7c091fcbad741eb9872217af927b591fded`, stderr bytes `0`.
- `callback_dispatcher` exit `0`, stdout SHA-256 `0c2e2919acceab8c959836966dd4de6171120f6ebf0803ce860cab2ae34ec56d`, stderr bytes `0`.
- `downstream_reader_entry` exit `0`, stdout SHA-256 `8b263503563dce35b45f8a6a73665d21bc5d4f38941932112e63e71943ba3da4`, stderr bytes `0`.
- `caller_83b0` exit `0`, stdout SHA-256 `45f1db3550a980a042cb6abc569db465a57655121f003375155dbbf1482cb4dd`, stderr bytes `0`.
- `caller_8420` exit `0`, stdout SHA-256 `e0d9893f968f8380f773b212ed96025b00e7f9c3c5b92ce7366e2aa5f811bf83`, stderr bytes `0`.
- `call_8428` exit `0`, stdout SHA-256 `38afe8223c6118e76c29a7ab111bdc74e98f06d701df4a9a4c27fc92765f6d52`, stderr bytes `0`.
- `dispatch_10958` exit `0`, stdout SHA-256 `6cfcee4c6a033a91f2c1f880613bdf937cec76b6c41c26efcbc19ad39cef90de`, stderr bytes `0`.

## R4 persistence and field-use window intent

- Timestamp: 2026-09-21T19:51:27+05:00 (Asia/Almaty).
- Continue the same local trace only: inspect outer R4 +/-0x2C0 (`0x7F4C`/`0x7FC2`) and `0x10200` reader around `0x107E4`/`0x10820` from exact pinned object/payload copies.
- Purpose: determine where R4 is used after the callback and explicitly separate register preservation from pointee writes. No broad scan, no prior verifier replay.

## R4 persistence/field-use execution

- Timestamp: 2026-09-21T19:51:27+05:00 (Asia/Almaty).
- Disposable directory: `/tmp/bc250-abl-r4-register-vs-pointee-x5yapp6u`. LLVM Thumb disassembly covers only the two requested continuation windows; raw `od` captures cover only the four named instruction sites.
- `outer_adjust` command `/usr/bin/llvm-objdump -D --triple=thumbv7a-none-eabi --start-address=0x7f40 --stop-address=0x7fd0 /tmp/bc250-abl-r4-register-vs-pointee-x5yapp6u/ABL1-clv-full-thumb.elf.o` exit `0`, stdout SHA-256 `5d90d3d019811bfe90569c611ed7f4367e3cb76b1692b437fd832fee68b23306`, stderr bytes `0`.
- `reader_field_and_callback` command `/usr/bin/llvm-objdump -D --triple=thumbv7a-none-eabi --start-address=0x107d0 --stop-address=0x10840 /tmp/bc250-abl-r4-register-vs-pointee-x5yapp6u/ABL1-clv-full-thumb.elf.o` exit `0`, stdout SHA-256 `1619d4d4f7bb4bcd0f8725ff8998f3f74aa77bf6d0afd8a5d43e9c10095ce405`, stderr bytes `0`.
- `add_r4` command `od 0x7f4c 0x8` exit `0`, stdout SHA-256 `610014880640869b04c590fd4da8657ffc300614a0155e1d190332a3b5ab76f3`, stderr bytes `0`.
- `sub_r4` command `od 0x7fc2 0x8` exit `0`, stdout SHA-256 `a7676b835325f6dda34ad51efa11fde43e000ab52f9705be25996b80a7a3fca1`, stderr bytes `0`.
- `field_read_107e4` command `od 0x107e4 0x8` exit `0`, stdout SHA-256 `a1e3152fbc99910216ac755d665698bb69b3305dfdafab6cac8aa28229d393da`, stderr bytes `0`.
- `call_10820` command `od 0x10820 0x8` exit `0`, stdout SHA-256 `10e2583ba342ee4045ca25a640ef94129825230c913ee67959f2cb3d91b0dd48`, stderr bytes `0`.

- Callee epilogue command: `/usr/bin/llvm-objdump ' -D' --triple=thumbv7a-none-eabi --start-address=0x5fb0 --stop-address=0x6030 /tmp/bc250-abl-5e68-epilogue-sofe1szv/ABL1-clv-full-thumb.elf.o`; exit `2`; output captured under `/tmp/bc250-abl-5e68-epilogue-sofe1szv`.

- Corrected previous epilogue command typo: the attempted argv contained literal argument `" -D"` (leading space), so llvm-objdump printed usage and exited `2`; changed command uses `-D` exactly. The corrected window only covers the callee tail/restore.
- Corrected exact epilogue command: `/usr/bin/llvm-objdump -D --triple=thumbv7a-none-eabi --start-address=0x5fb8 --stop-address=0x6030 /tmp/bc250-abl-5e68-epilogue-corrected-fzhen0gr/ABL1-clv-full-thumb.elf.o`; exit `0`; stdout SHA-256 `5d3d02e3246ce2f7b353e30033aeb5f18f46699e5022972d23d60f4bee3bfd43`; stderr bytes `0`; disposable output `/tmp/bc250-abl-5e68-epilogue-corrected-fzhen0gr`.

## Independent pointer-identity adjudication

- Timestamp: 2026-09-21T17:00:00+05:00 (Asia/Almaty; closeout time rounded to minute).
- Fresh evidence: Thumb-mode disassembly of the exact wrapper/payload copy shows `0x7E74` passes `R0=R4` context, `R1=R5`, `R2=R6`; callee `0x5E68` sets `R5=R0`, `R4=R2`, writes at `0x5FBA STRH R3,[R5,#0x78]`, then restores saved caller `R4` at `0x6024 POP.W`.
- Exact trampoline: `0x10958` loads callback target from `[R0+0x660]`, copies it to `R12`, restores `{R4,R5}`, sets `R1=1`, and `BX R12`. The dynamic target is not resolved. Its AAPCS32 compliance is not observed.
- Later code: caller `R4` add/sub `0x2C0` is directly shown at `0x7F4C`/`0x7FC2`; it passes current `R4` in `R0` at `0x8428`. Function `0x10200` saves callee registers, copies R0 to R4 at `0x10208`, calls the dynamic dispatcher at `0x107E0`, then reads `[R4+0x78]` at `0x107E4`.
- Finding: the uncertainty in **R4 address identity** is a possible register clobber at the unresolved indirect callback; under AAPCS32, R4 is callee-saved, but that assumption is conditional on the target obeying the ABI. Pointee mutation is distinct: the 0x5FBA store to context+0x78 is observed, while mutation by the unknown callback is not. The callback wrapper itself has no direct store to the pointed-to object in its bounded listing.
- Accepted local edge: `0x7E40 -> 0x7E74 -> 0x5E68 -> 0x5FBA` with local register roles and output field. Rejected inference: unconditional same-object alias at `0x8428` without establishing the dynamic callback target/ABI; no global alias, unit, clock, or hardware conclusion.
- No analysis of the field-`0x660` initializer or its target was performed; that scope remains with its owner.
- New report: `docs/research/2026-09-21-abl-reachable-pointer-independent-review.md`, SHA-256 `84d5bd62102b06da0b6816b47073a7076e98a5c93db1cbbac0497acb71decb50`.
- No HOB/heap/float test or source/ROM/hardware/network action occurred.

## Timestamp correction (G7)

The preceding analysis-entry timestamp was rounded from an estimate and is not the observed wall-clock value. `date '+%Y-%m-%dT%H:%M:%S%:z'` immediately after append returned `2026-09-21T20:00:30+05:00`; use that actual timestamp for this closeout. The finding and command outputs are unchanged.
