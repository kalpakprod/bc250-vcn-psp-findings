# v005 flash package (2026-09-24)

Target: BC250-01, W25Q128.V via CH347, board fully unpowered.
Image: BC250_vcn-driver-FULL_lzma-FIXED_early-slot.bin
SHA-256: 2fadb173251eb4a44aa9da371f37207efb0f276f8d509926083bfa5a64c03406

What it is: v004 bytes plus an 8-byte fix. The capsule LZMA-alone header
now carries the explicit decoded size (0x441010). Nothing else changed:
same driver, same placement before Bds, same FV, same capsule lengths.

Why: v004 carried an unknown LZMA size (0xFF..FF). The board hangs in PEI
before any DXE driver runs. First blink only, no LAN. This repeats the
hardware-proven D5-D7 defect, fixed the same way D8 fixed it.

Preflight: 10/10 GO vs the booted pre-dump (evidence/firmware-audit/20260924-v005-lzma/).
Rollback: evidence/programmer/reads/20260924-v003c/pre-v003c-read-a.bin (64973ba364...).

Procedure: chip identity -> fresh DOUBLE read a/b (cmp) -> sha -c ->
flashrom write + verify -> INDEPENDENT readback + cmp + sha.
Then: operator cold boot -> P0 signs -> postflash_vcn_check.py.
Needs explicit operator approval for this exact image before any write.
