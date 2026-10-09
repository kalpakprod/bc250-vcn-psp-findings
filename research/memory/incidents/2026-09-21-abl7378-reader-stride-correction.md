# G7 correction: ABL1 0x1B24 reader stride arithmetic

Date: 2026-09-21. Scope: static correction of the table-walk arithmetic in docs/research/2026-09-21-abl7378-indirect-entry.md and its action log.

## Correction

The prior statement that the loop at ABL1 RVA 0x1B24 advances records by 0x24 (36 bytes) is contradicted by the saved bounded Thumb listing evidence/firmware-audit/20260921-abl7378-indirect-entry/run-20260921T200924+0500/xref-1b24-1b90.stdout. At 0x1B48, RSB r0,r4,r4,LSL #3 computes (8*i)-i = 7*i; at 0x1B4C, ADD r0,r6,r0,LSL #2 therefore computes table_base + 28*i, i.e. stride 0x1C, not 0x24.

Do not treat this 0x1B24 table as the requested stride-24 table. The saved listing's loop loads [record+0x8] for the indirect call. The candidate 0x5E479 at conditional RVA 0x170CC is row0 +0x4 if base 0x57100 and is not read by this loop. The previous 0x170F4 address is not row1 +0x8 for the actual 0x1C indexing. A fresh bounded verifier is required before relying on row1 contents.

## Evidence boundary

This is an observed-listing/static-arithmetic correction only. It does not establish which component uses row0 +0x4, prove that 0x5E479 is relocated, or identify the separate requested stride-24 reader. No firmware, ROM, hardware, or register state was modified.

## G7 correction — verifier output-column assumption

The first newly run verifier under evidence/firmware-audit/20260921-abl7378-reader-stride-correction exited 1 with 13/18 checks. Five instruction checks failed because the script assumed tab-delimited disassembly columns. All raw image/object hashes, table/count literals, 0x1C address formula computation, and the row values in the verifier output were consistent; the instruction predicates were not confirmed by that failed process. Preserve the failure output, change method class to independent instruction decoding, and do not treat the verifier FAIL as an ABL1 finding.

## Observed recheck

On 2026-09-21, a fresh bounded Thumb disassembly of 0x1B40..0x1B62 from the hash-pinned ELF exited 0 with empty stderr. The new direct raw-byte check exited 0, stderr empty, and reported raw ABL1 size 94,624 / SHA-256 af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a, table literal 0x6E1C8, count pointer 0x6E200, count 2, row0+4 0x5E479, row0+8 0x62059, and row1+8 at 0x170EC = 0. The loop's RSB/ADD arithmetic advances 0x1C bytes; its only record-member load in the loop is +0x8. The earlier 0x170F4 read was not row1+8.

## G7 correction — manifest entry count transcription

The first final evidence-ledger text said 14 entries. Readback with wc -l on the manifest and find-count of manifested files both returned 15. The manifest's sha256sum -c pass and all evidence hashes are unchanged; the count is 15, not 14.

## New bounded xref result: separate record+4 reader

A fresh exact literal-xref query found code xref RVA 0x18A8 -> pool word RVA 0x1B1C = VA 0x6E1C8. Fresh Thumb output [0x18A4,0x1920) shows a separate loop at 0x18EA/0x18EE computing table_base + 28*i, loading [record+4] at 0x18F2 and calling that pointer with BLX r7 at 0x18C4. It also loads [record+0xC] into R2 at 0x18BE. Under unproven base 0x57100, table RVA 0x170C8, row0+4 at 0x170CC is 0x5E479 -> conditional Thumb RVA 0x7378. The row1+4 sentinel at 0x170E8 is zero. This does not conflict with the separate 0x1B24 reader that consumes +8; it corrects the earlier missing +4-reader link. At 0x18D4..0x18DA a callback-return-dependent handler is loaded through [[R6+0x1C]+0x48] and invoked by BLX R1; this dynamic boundary remains untraced. No loader/runtime/hardware or active-object identity conclusion follows.

## G7 correction — ELF hash transcription in the new verification ledger

The newly created plus4-reader VERIFICATION.txt contains a mistyped ELF SHA-256. The expected pinned value from the prior identity check is adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6. Preserve the typo and supersede it with direct sha256sum readback before relying on this ledger.

## Observed correction of new verification-ledger typo

Direct sha256sum readback returned ELF SHA-256 adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6 and raw ABL1 SHA-256 af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a. This confirms the superseding hash value appended to the new VERIFICATION.txt; the original miscopied line remains explicitly superseded.

## G7 correction — template-path binding

The follow-up attempt initially referenced a missing helper-6238.command under the 22:40 run directory. Shell cat reported no such file and set -e stopped before output creation. The actual recorded full helper template is evidence/firmware-audit/20260921-abl660-plus4-reader-context-join/run-20260921T224000+0500/helper-6238-full.command. The path typo is corrected; no source/evidence input was changed by the failed dispatch.

## G7 correction: R8+0x48 callback target and symbolic object join

Fresh bounded raw read for R8=0x6E154 plus 0x48 found 0x5E615 at payload RVA 0x1709C. Under conditional base 0x57100 it maps to Thumb entry 0x7514, not 0x7E74. Fresh 7378 return-tail output shows the successful path sets R0=1 at 0x7504 and returns via 0x745C; the caller's 0x18C6 CBZ therefore falls through to 0x18D4 on success. At 0x7378, R5 is the heap root and R8 the descriptor, stored at [R5+0x1C] at 0x74EE. 7378 saves/restores caller R6, so the reader's R6 remains the same heap root; 0x18D4 reloads the same R8 descriptor and 0x18DA calls [R8+0x48] with R0=R6. AF90's fresh epilogue at 0xB148 restores R5. The active consumer 0x10958 R0 remains unjoined; 0x7E74 is not the resolved +0x48 target. No runtime/hardware claim follows.
