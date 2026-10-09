# CLV ABL1 record +4 callback reader for table 0x6E1C8

Date: 2026-09-21. Scope: bounded static trace from the exact table-base literal xref at RVA 0x18A8 through the record+4 callback callsite and its immediate return-dependent dispatch. This is not a hardware/runtime claim and does not repeat the 0x7378 callback-body analysis.

## Conclusion

A second reader of the same conditional table base 0x6E1C8 (payload RVA 0x170C8 only if base 0x57100 applies) consumes record+4 and uses it as an indirect-call target. The first row's raw word at RVA 0x170CC is 0x5E479. Under that conditional base it is the Thumb pointer for RVA 0x7378 (pointer value 0x7379), and the row pointer is loaded at 0x18F2 then invoked by BLX r7 at 0x18C4. This closes the static data-to-callsite link for this table field, but not loader relocation or runtime execution.

The reader computes records with stride 0x1C (28 bytes), not 0x24 (36 bytes) or decimal 24. It reads row+4 as callback/sentinel and row+0xC as the callback's R2 argument. Row1+4 at RVA 0x170E8 is zero. The branch enters the first iteration with index zero; after a zero return the loop increments to row1, where the zero +4 word terminates the walk. If the callback instead returns nonzero, a different dynamic handler path is taken rather than advancing directly to row1.

## Exact inputs and assumptions

- Donor ROM: evidence/donor/retroweb-20260916/BC250_5.00_clv.bin, 16,777,216 bytes, SHA-256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8; ABL1 PSP type 0x31 at SPI offset 0x99FD00 per the existing provenance report.
- Raw ABL1: evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin, 94,624 bytes, SHA-256 af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a.
- ELF32 little-endian ARM wrapper: evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/ABL1-exact.o, SHA-256 adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6; its .data was previously reconciled byte-for-byte to raw ABL1.
- Disassembler: /usr/bin/llvm-objdump 22.1.8, explicit Thumb triple thumbv7m-none-eabi.
- Candidate base 0x57100 remains unproven; all VA-to-RVA mapping below is conditional.

## Bounded reader/call path

Fresh listing range: [0x18A4,0x1920), command and literal streams retained under evidence/firmware-audit/20260921-abl660-entry7378-plus4-reader-xref/run-20260921T220000+0500/.

- 0x18A8 loads R9 from literal pool word at 0x1B1C; that word is 0x6E1C8. Conditional payload table RVA: 0x170C8.
- 0x18A6 initializes R5=0; 0x18B6 branches directly to 0x18EA (skipping the increment at 0x18E6), so the first calculated record index is 0.
- 0x18EA computes 7*R5 in R1 via RSB; 0x18EE scales by four and adds R9, yielding table_base + 28*R5 (stride 0x1C).
- 0x18F2 loads R7 from [record+0x4]; 0x18F4 compares it to zero; nonzero goes to 0x18B8.
- At 0x18BE the reader loads [record+0xC] into R2. It sets R0=R6 at 0x18C2, preserves R1=R4, sets R3=SP+8, stores R10 at [SP], then calls the record+4 pointer with BLX R7 at 0x18C4.
- After that callback returns, 0x18C6 branches to index increment on R0==0. For nonzero R0, 0x18D0 re-reads the current record+4 as a nonzero check; if nonzero, 0x18D4..0x18DA calls an object-relative handler loaded from [[R6+0x1C]+0x48] via BLX R1. That dynamic handler is not followed here.
- If the callback returns zero, the next index is 1 and raw row1+4 at RVA 0x170E8 is zero, so the +4 loop exits at 0x18F8. No count field is read by this bounded loop.
- The adjacent +8 callback reader at 0x1B24 is distinct and uses row+8; it is not used to establish this +4 path.

## Evidence and limits

- Fresh llvm-objdump: exit 0, stderr empty. Raw-field verifier: exit 0, 7/7 checks, stderr empty.
- Observed raw values: table literal 0x6E1C8; row0+4 0x5E479; row0+0xC 0x6E154; row1+4 0; row0+8 0x62059 (not read by this reader).
- Evidence class: observed bytes + static analysis. The candidate base/relocation, live table selection, callback execution, callback return value, object identity between R6 and the 0x10958 consumer's R0, and the behavior of the dynamic handler remain unknown.
- No ROM, firmware, NVRAM, register, network, or hardware mutation occurred.

## R8+0x48 object-relative handler join

A bounded raw read resolved the field used by the reader's post-callback path. The 7378 argument R8 is the table's row0+0xC value 0x6E154 (conditional VA). Its +0x48 cell is conditional VA 0x6E19C / payload RVA 0x1709C; the pinned raw dword is 0x5E615. Under the still-unproven base 0x57100, it maps to Thumb RVA 0x7515 / entry 0x7514. The target body was previously captured in the same unique context-join evidence run as a two-instruction stub: MOVS R0,#0; BX LR.

The object chain is statically joined:

- Reader callback call 0x18C4 passes R0=R6 (the heap output pointer).
- 7378 receives that R0 in R5, receives the descriptor R8 in R2, and at 0x74EE stores R8 to [R5+0x1C].
- 7378 returns R0=1 on its successful initialization path (0x7504 then branch to epilogue 0x745C). The reader's 0x18C6 CBZ is therefore not taken for that path.
- The 7378 prologue/epilogue saves/restores caller R6. Reader 0x18D4 then reloads the same descriptor from [R6+0x1C], 0x18D6 loads its +0x48 target, and 0x18DA calls that target with R0=R6. Thus the handler receives the same symbolic heap-root object that was initialized by 7378.
- AF90 at 0x74E0 is entered with R0=R5. A fresh AF90 prologue and bounded return read show R5 saved at 0xAF90 and restored at 0xB148.

The resolved +0x48 target is 0x7514, not the 0x7E74 code window. The latter's first listed instruction is BL 0x5E68; the 0x109BC call occurs later at 0x7EF0. These are distinct locations, and no edge from this specific +0x48 target to 0x7E74/0x10958 is established. The active 0x10958 wrapper's current R0 therefore remains unjoined to this heap root.
