# D3-A flash decision brief (2026-09-12, loop run)

## The decision
Flash `D3-A_APCB-DFG-i-only_CONTROL_expected-false-negative.bin`
(md5 bd2605e5869b21ec7426e3084d69aec8) — or do not flash at all.

## Why this image, why now
Five hardware-verified experiments (S2-L5b/L6/L7/L8/L9/L10) established:
the dom14-cluster power transaction never completes, in EVERY runtime
configuration (mode0/mode1/mode2, fw path and direct path, with and
without the driver table, the gasket aperture fully programmed 56/56,
the dataplane routes 15/15). The only mechanism that can deny a power
transaction below the runtime register reach is the boot-time DFG
permission policy (the APCB DFG table): the VCN master sits under the
wildcard baseline perm 0x1f, which lacks the power/reset grant bits 5/6
(the explicit rows sub 06 -> 0x63 / sub 08 -> 0x23 have them).

D3-A = that patch, and nothing else:
- 3 bytes changed vs the board dump base (the wildcard baseline
  `00 ff 1f 00` -> `00 ff 7f 00` in the DFG types 5/6 + the u8 checksum
  recompute @APCB+0x10);
- NO PSP-directory changes, NO blob relocation, NO signed-region edits;
- built and verified 26/26 (d3_verify.py), the manifest + the verifier
  shipped in recon/d3/package/.

## What each outcome means
- Boot OK (expected: the APCB-only edit class is proven bootable) ->
  run the full runbook + S2-L10 -> the ack asserts -> THE UNLOCK (then
  the BAR5 arbiter + the driver checklist).
- Boot OK, the ack still wedges -> the DFG grant theory is dead; the
  remaining candidates are the hardware/fuse class and the PSP-context
  aperture (the D3-B2/C carrier path, blocked by the signature
  acceptance) — the honest end of the current road; register and stop.
- No boot -> the APCB edit is rejected in a way not seen before
  (contradicts the field-proven APCB-only class) — revert with the
  programmer, investigate the UART.

## Prerequisites (firmware-safety gate)
1. The explicit operator approval of THIS image (by md5).
2. The programmer (3.3 V, SOIC8/WSON8 per the package README).
3. The full 16 MB dump backup taken and md5-checked BEFORE the write
   (the reference: 7607a34caeca1ffb95e1f7c52ca227d5 — re-verify against
   the chip, not the archive).
4. The rollback = the verified dump re-flash + Verify.
5. The post-flash checks: the cold boot, linux_check.sh, the domain
   statuses, S2-L10, the arbiter.

## Status
PENDING OPERATOR DECISION. Nothing is flashed without the approval.
