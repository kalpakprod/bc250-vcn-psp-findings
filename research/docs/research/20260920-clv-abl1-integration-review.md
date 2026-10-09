Current: offline integration review of the exact CLV ABL1 branch/HEAP evidence; no clock mode or MCLK=UCLK=FCLK result is established.

# CLV ABL1 bounded integration review

## Conclusion

Existing branch and HEAP results can be integrated as static control/data-flow evidence only. An independent 64-check review corroborates the exact 0xA04E lookup node fields and distinguishes the 0x63F8 HEAP-header initializer from an A04E-node producer. Phase 2 remains PARTIAL.

## Reviewed branch and callback

The 89-check branch report/result remains PASS on the pinned ABL1 and Thumb listing. The field at payload 0x107E4 is read as a halfword. The threshold branches choose R2 in {0, 0x260, 0x264, 0x464} and call helper 0x10958; the helper maps arguments to R1=1, R2=0x61E, R3=selected value before BX R12.

The helper loads the callback pointer from context+0x660. Its target/effect is not bound in this integration. The separate author target result is still pending; no guess or additional search was made. Subsequent halfword stores go through the pointer read from context+0x2C4. That pointer's address space is unknown: MMIO is possible, but not established; the available bytes do not positively prove non-MMIO. These later stores are not the branch-selected R2 values. No direct MMIO target is identified.

## Reader fallback and FCLK type uncertainty

Correct ordered-reader behavior from the existing 64-check status/type result:

- For an earlier item, helper failure/status R0=0 advances to the next candidate.
- If the earlier helper returns nonzero, its returned gate byte must be exactly 1 to advance; any other byte fails terminally.
- The final typed query's status failure is terminal. A successful typed sentinel is also terminal and does not advance to another candidate.

FCLK passes SP+0x0C as the reader type-byte pointer, but there is no explicit initialization of that local in the bounded FCLK caller before the reader call. Therefore actual type-2 execution for that FCLK request remains unproven. Do not collapse the gate-byte rule, provider status, and final sentinel result into one generic fallback claim.

## Runtime HEAP boundary: one independently checked edge

The existing heap follow-up result reports 90/90 PASS. This review independently checked 64 exact ABL1/listing assertions at 0x4B1A/0x4B34/0x4B38/0x4B3A, 0x6374 node handling, and 0x63F8 initialization/call at 0x6F78.

Selector 0x0F places immediate 0xA04E in descriptor [SP+0x24] and calls 0x6374. The lookup compares the requested key with node+0, reads node size at +4, metadata byte at +9, and next link at +0xC; on match it returns the body pointer (node+0x10+metadata) and adjusted length (size-minus-metadata) to descriptor +8/+4.

The 0x63F8 initializer is called at 0x6F78. It loads base 0x73000, loads the HEAP tag and stores it at [base+0]. This is HEAP arena/header/sentinel initialization, not evidence that it created or populated an entry with key 0xA04E. The producer/populator for such a linked node remains unresolved; this bounded check does not establish that no other producer exists.

The pinned APCB parse confirms CBSG group 0x1707 and two subgroups, but no schema-backed mapping from that APCB/CBSG data to runtime HEAP key 0xA04E. The prior raw-ROM check misses only exact contiguous four-byte little-endian scalar encodings. That result does not imply no ROM representation: decompressed ABL1 contains 0xA04E as a MOVW immediate at 0x4B1A and 0x73000 as table-base literals. The remaining gap is the APCB/CBSG-to-runtime-HEAP producer/schema link, not whether these constants occur in decompressed ABL1.

## Limits

All findings here are observed-bytes/static-analysis. No runtime HEAP snapshot, ABL1 execution, callback execution, address-space mapping, physical clock readback, frequency unit, voltage, training, synchronization, or hardware behavior is established. The callback+0x660 target and FCLK SP+0x0C type value remain unresolved. No clock mode is known; MCLK=UCLK=FCLK remains unproven. Phase 2 remains PARTIAL and no plan gate is promoted.

## Verification artifacts

- Report: /home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl1-integration-review.md
- Machine result: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-integration-review/review-result.json (SHA-256 f7487eb93caa99f2d7d9327769be46625011e487297e866891a4df208b1bdaaf)
- Action log: /home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-abl1-integration-review.md
- Manifest: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-integration-review/SHA256SUMS.final
- DIFF_FILE reconstruction: patch exit 0; reconstructed file byte-equals MODIFIED_FILE.
- Four transaction roles: MODIFIED_FILE=/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-integration-review/MODIFIED_FILE.md; DIFF_FILE=/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-integration-review/DIFF_FILE.patch; VERIFICATION.txt=/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-integration-review/VERIFICATION.txt; executable ROLLBACK.sh=/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-integration-review/ROLLBACK.sh.
