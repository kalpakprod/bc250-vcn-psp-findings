# v009-rtb package (2026-09-24, staged ahead, NOTHING flashed)

Target: BC250-01, W25Q128.V via CH347, board fully unpowered.
Image: BC250_vcn-driver-FULL_deferred-to-readyboot_appended-at-end.bin
SHA-256: 56df6244fb8095c9bbcb53e7cbed20d02da4fbc960448aa69c7e66a9d54f839d

What it is: secure-reads route-B code with a ReadyToBoot-deferred entry
(entry only registers a one-shot callback, zero HW touches), APPENDED at
FV end. All 193 base files at identical offsets.

Flash IF v006 boots AND v007-active AND v008 both hang. Preflight 10/10 GO.
OVMF: load Success, entry 0x0 in 6 s (registration only, callback correctly
not fired under shell load), shell alive.
Rollback: evidence/programmer/reads/20260924-v003c/pre-v003c-read-a.bin.
Needs its own explicit approval before any write.
