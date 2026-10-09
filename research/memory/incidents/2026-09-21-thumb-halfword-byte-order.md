# G7 correction: LLVM Thumb halfword display is not raw byte order

Date: 2026-09-21. Scope: offline ABL1 static analysis for the CLV 5.00 donor.

## Measurement and error

The root-only `verify_abl1_arg_flow.py` trial read the exact ABL1 payload and emitted fresh LLVM Thumb windows, but its first raw-byte anchor transcribed the disassembler's printed halfword `9200` as bytes `92 00`. Direct payload bytes at offset `0x4664` are `00 92` (little-endian Thumb halfword `0x9200`). The verifier therefore exited `1` with `AssertionError: bytes_04664: payload[0x4664:0x4666]=0092 expected=9200`; this is an evidence-script endianness assertion error, not a firmware mismatch.

## Correction

LLVM `llvm-objdump` prints Thumb instruction halfwords in instruction-word notation. Convert each printed 16-bit halfword to little-endian bytes before comparing with the raw payload (for a 32-bit Thumb instruction, convert each halfword separately and concatenate). The disassembly semantics remain subject to the exact code/data boundaries; align window starts at known instruction boundaries and byte-reconcile the output.

Retained failure evidence is under `evidence/firmware-audit/20260921-apob-abl-outer864-origin/verify_abl1_arg_flow.py` and `verifier.stderr`; the script was not used for a result and the previous 34-check verifier was not rerun. The corrected verification must use a separate root-owned output location and must not overwrite the concurrently-produced `outer864-origin` evidence files.

## G6 method-class pivot

The owned outer+0x864 action log records seven earlier verifier retries for assertion/parser/address-window errors before this root trial; the root-only eighth script also stopped on the endian assertion above. Stop using that assertion-driven verifier. The next discriminator is a different method class: direct aligned LLVM Thumb windows paired with independent raw-byte dumps (`xxd -g1 -s OFFSET`) and manual AAPCS stack-slot reconstruction from exact instructions. Do not run either the old 34-check verifier or the concurrent root/worker verifier script while these repeated assertion failures remain unresolved.
