# v006r-noop control package (2026-09-24, diagnostic, NOT a VCN unlock)

Target: BC250-01, W25Q128.V via CH347, board fully unpowered.
Image: BC250_vcn-driver-STUB_no-hw-ops_early-slot.bin
SHA-256: 6500bea5b01ea1dcc540939d65faa9cc0ec0f2505a5fcb3e358622803b85bb27

What it is: v006 rebuilt with the FFS File-checksum refreshed after the
entry stub (audit F1) + DEPEX payload asserted TRUE (F3). Same slot/size/
layout/explicit LZMA. The driver loads but executes zero HW operations.

Supersedes 20260924-v006-noop-ctrl (80c21dbc, stale File-checksum) — do not flash.
Preflight: 10/10 GO vs the booted pre-dump.
Rollback: evidence/programmer/reads/20260924-v003c/pre-v003c-read-a.bin.
Procedure: chip identity -> DOUBLE read a/b -> sha -c -> write 1.875M ->
INDEPENDENT readback + cmp + sha. Then operator cold boot, P0 signs.
Needs explicit operator approval for this exact image before any write.
