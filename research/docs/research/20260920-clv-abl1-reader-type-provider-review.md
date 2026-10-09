Current: corrected exact FCLK type-pointer/provider frame; the prior uninitialized-local interpretation is superseded.

# CLV ABL1 FCLK type-pointer/provider boundary review

## Conclusion

The earlier uncertainty was caused by incorrect provider-frame accounting. The real 0x49CC entry pushes 13 registers (R0..R11,LR) = 0x34 bytes, then subtracts 0x6C. Therefore its first incoming stack argument is at current SP+0xA0, not SP+0x9C.

Direct static dataflow:

1. FCLK caller 0x465C passes R3 = SP+0x0C to reader 0x1FB4; it zeroes only caller stack words SP and SP+4.
2. Reader preserves R3 -> R10; at 0x1FD2, its R9 value is written to reader [SP], and 0x1FE0 calls valid Thumb target 0x4800.
3. Explicit-target 0x4800 disassembly confirms STRD R3,R1,[SP]: outgoing provider arg1 is the preserved FCLK type pointer, arg2 is the reader R9 value.
4. Explicit-target 0x49CC disassembly confirms 0x4BF0 loads [SP+0xA0] and 0x4BFA stores a byte through it. With corrected 0x34-byte frame, this is provider arg1: the FCLK type pointer.

Thus provider success can write the returned byte length/type into the FCLK SP+0x0C local before reader type dispatch. The prior report's no-provider-write / actual-type-2-unproven interpretation is too strong and is superseded. What remains unproven is whether this provider path returns success and which returned type byte is produced for the live FCLK request. No physical clock or hardware behavior follows.

## Direct execution

Command: python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-type-provider-review/type_provider_target_verify.py

Observed stdout:

{"status":"PASS","checks":64,"provider_disassembly_exit":0,"provider_type_pointer_arg":"SP+0x9C preserved/unreferenced directly","provider_explicit_byte_store":"through second stack arg SP+0xA0","fclk_type_byte_write":"not established by this provider path"}

Observed stderr: empty. Exit status: 0. Fresh checks: 64/64 PASS.

The verifier also executed llvm-objdump -D --triple=thumbv7m-none-eabi --start-address=0x49cc --stop-address=0x4e4c /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o; exit status 0; stdout /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-type-provider-review/provider-49cc-window.stdout; stderr /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-type-provider-review/provider-49cc-window.stderr.

## Proven versus inferred

- Observed/static: exact FCLK pointer setup, reader preservation, valid helper target 0x4800, valid provider target 0x49CC, helper STRD stack forwarding, provider SP+0xA0 byte store, and corrected frame offsets.
- Inferred: provider arg1 is the FCLK type pointer under direct stack accounting; provider success can initialize the type byte.
- Unrun/unproven: provider runtime success, returned type value for this live request, actual type-2 branch execution, ABL1 runtime, loader/base, physical MCLK/UCLK/FCLK frequencies, synchronization, training, and hardware acceptance.

## Physical completion blocker

The static path does not measure physical clocks. To establish MCLK:UCLK:FCLK = 1:1:1, the next decisive dependency is a booted board plus domain-specific independent counters/readback for all three domains (common reference, calibrated ratios, and valid status), with the same input/settings and a control baseline. Existing software metric aliases and SMU committed-state queries are insufficient. If the board is unavailable, this goal cannot be honestly completed offline; stop at this evidence boundary.

No ROM, firmware, settings, hardware, shared plan, or memory was changed.

## Artifacts

- Report: /home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl1-reader-type-provider-review.md
- Machine result: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-type-provider-review/type-provider-boundary-result.json (SHA-256 587baad7955434520ef900d11f4363c93419a5910580bab41eaf01a658e4744c)
- Action log: /home/OWNER/orca/projects/bc250/docs/action-logs/20260920-clv-abl1-reader-type-provider-review.md
- Manifest: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-type-provider-review/SHA256SUMS.final
- Verifier: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-type-provider-review/type_provider_target_verify.py
