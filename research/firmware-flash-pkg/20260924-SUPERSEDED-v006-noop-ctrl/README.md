SUPERSEDED — DO NOT FLASH. # v006-noop control package (2026-09-24, diagnostic, NOT a VCN unlock)

Target: BC250-01, W25Q128.V via CH347, board fully unpowered.
Image: SUPERSEDED-BC250_pre_dump_vcn_own_fv_v006_noop.bin
SHA-256: 80c21dbc3ed15c4e4e1743aa8594a382c8c41537b222ca0f33534535cf28b7d4

What it is: v005 with the VCN driver entry stubbed (xor eax,eax; ret).
Same FFS offset/size, same FV layout, explicit LZMA. The driver loads but
executes zero hardware operations.

Question it answers: does DXE complete with a passive driver in this slot?
- Boots to Linux -> the route-B writes wedge DXE; next rung is v007 with
  the sequence deferred to ReadyToBoot.
- Same hang (2 blinks, no LAN/video) -> the insertion surgery itself is at
  fault; next rung is in-slot PE swap (D-technique) or append-at-end (W9).

Preflight: 10/10 GO vs the booted pre-dump (evidence/firmware-audit/20260924-v006-noop/).
Rollback: evidence/programmer/reads/20260924-v003c/pre-v003c-read-a.bin (64973ba364...).
Procedure: chip identity -> DOUBLE read a/b -> sha -c -> write 1.875M ->
INDEPENDENT readback + cmp + sha. Then operator cold boot, P0 signs.
Needs explicit operator approval for this exact image before any write.

# SUPERSEDED 2026-09-24 by 20260924-v006r-noop-ctrl (audit F1: stale FFS
# File-checksum). DO NOT FLASH this package.
