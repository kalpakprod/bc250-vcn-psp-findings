# Safe-reads flash package (2026-09-24, diagnostic, NOT a VCN unlock)

Target: BC250-01, W25Q128.V via CH347, board fully unpowered.
Image: BC250_vcn-driver-FULL_safe-reads-only_appended-at-end.bin
SHA-256: c935e3ec4c0faee88fbe0600f003b4d0d16ac13f587ab8fb6943382e28025c6f

What it is: the board's own booted BIOS + the FULL route-B driver with
SECURE READS ONLY (bitmap via Q3 mailbox, raw debug reads deleted),
APPENDED at the FV end. Preflight 10/10 GO.

Why now: H19 won (FULL code wedges only against initialized SMU). Raw
reads are the prime stuck suspect (probe3: raw reads wedge even after
full init). If this boots, raw reads were the wedge. If it hangs, the
wedge is in the writes (gasket suspects next, D12–D19 precedent).

Rollback: the fresh pre-write double-read dump (primary); STUB-appended
pre-reads in evidence/programmer/reads/20260924-stub-appended/ (secondary).
Procedure: chip identity -> DOUBLE read a/b -> sha -c -> write 1.875M ->
INDEPENDENT readback + cmp + sha. Then operator restores the bench
circuit (clip off, programmer USB out, battery in, 12V) and cold boots.
Needs explicit operator approval for this exact image before any write.
