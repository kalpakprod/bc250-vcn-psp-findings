# STUB-appended flash package (2026-09-24, diagnostic, NOT a VCN unlock)

Target: BC250-01, W25Q128.V via CH347, board fully unpowered.
Image: BC250_vcn-driver-STUB_no-hw-ops_appended-at-end.bin
SHA-256: 0133a34b3f6744b3517f7d01abfc2c2b78d0784cd6fcb8e09e3817a670e36ae3

What it is: the board's own booted BIOS + the STUB driver (entry returns 0,
zero HW ops) APPENDED at the FV end. Same append surgery as the FULL-appended
image, inert code. Preflight 10/10 GO.

Why now: FULL-appended hung after 1 blink with a statically valid FV.
This control discriminates H1 (board rejects the append structure → STUB
also 1-blinks, fix the builder) vs H19 (FULL code wedges only against
initialized SMU → STUB boots, pursue secure-reads).

Rollback: the fresh pre-write double-read dump (primary); FULL-appended
pre-reads in evidence/programmer/reads/20260924-full-appended/ (secondary).
Procedure: chip identity -> DOUBLE read a/b -> sha -c -> write 1.875M ->
INDEPENDENT readback + cmp + sha. Then operator restores the bench
circuit (clip off, programmer USB out, battery in, 12V) and cold boots.
Needs explicit operator approval for this exact image before any write.
