# FULL-appended flash package (2026-09-24, diagnostic, NOT a VCN unlock)

Target: BC250-01, W25Q128.V via CH347, board fully unpowered.
Image: BC250_vcn-driver-FULL_lzma-FIXED_appended-at-end.bin
SHA-256: 9d2493975b870810fd31481cf3ded36cc964aa201181ad0ea4949f3cf5afad17

What it is: the board's own booted BIOS + the FULL route-B VCN driver
APPENDED at the FV end (@0x43c018). All 193 base files at identical
offsets; explicit LZMA. Preflight 10/10 GO.

Why now: the STUB early-slot image BOOTS (verdict 2026-09-24), so the FV
insertion surgery is innocent and the driver code is guilty. Dispatch
position is the next variable this image tests.

Rollback: the fresh pre-write double-read dump (primary); STUB pre-reads
in evidence/programmer/reads/20260924-v006r/ (secondary).
Procedure: chip identity -> DOUBLE read a/b -> sha -c -> write 1.875M ->
INDEPENDENT readback + cmp + sha. Then operator restores the bench
circuit (clip off, programmer USB out, battery in, 12V) and cold boots.
Needs explicit operator approval for this exact image before any write.
