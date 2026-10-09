# Flash Package: 20260924-v003b-route-b-vcn

**REJECTED 2026-09-24 — DO NOT FLASH.** The injected driver FFS was placed
at inner-FV offset `0x432000`, AFTER the base's trailing erased (0xFF)
free space. The real DxeCore FV walker stops at the first erased buffer
(`FwVol.c`: "We have found the free space so we are done"), so the driver
would never dispatch: the image boots but does nothing. Superseded by
`firmware-flash-pkg/20260924-v003c-route-b-vcn/` (same driver content,
inserted before `Bds.ffs`, pre-flight 9/9 GO). Evidence:
`evidence/firmware-audit/20260924-v003c-preflight/result.json` and the
appended `docs/action-logs/2026-09-24-v003b-route-b.md`. Kept for
provenance only.

---

## Artifacts
- `BC250_3.00_MeiMeiDXEv3_vcn_v003b.bin`: 16,777,216 bytes, SHA-256 `3a7fcf8507c6ea1a366bc8f8c584f7613e0cfac4ce9fcef47c031ed80f853f4d`
- `SHA256SUMS`: verification hashes

## Description

Route-B VCN enable candidate on the boot-proven community 3.00
MeiMeiDXEv3 donor base (sha256 `606a7a7f…`, inner FV 193 -> 194 files).
The injected `Bc250VcnUnlockDxe` (same GUID
`B6250780-7E00-4203-900C-23443B1413FE`, inner FV offset `0x432000`,
size `0x301c`) is the v003b rewrite:

- No `0x1B` PSP-doorbell send (the v003 wedge hazard is removed).
- Replay of the `FUN_0002A184` bring-up tail (24 steps, artifact
  `evidence/firmware-audit/20260924-plan-consumers/vcn_replay_writes.json`),
  skipping the destructive builder (`FUN_00024594` zeroes
  boot-programmed controller words).
- Secure read (`0x2A`), RMW with readback verify, timeout-guarded polls
  (250 ms), abort guards on every step; driver exits cleanly if the
  board library protocols or SMU answers do not match expectations.
- v1 skips (documented in source): the `0x01D80814 |= 2` write, the
  `0x0220FE00 &= ~4` release, the `FUN_0002a344` pump block.

## Why route B is the only route

Policy word @`0xCCB8` = 0 on this board: SMU bit 6 never authorizes the
VCN tail (probe-measured 2026-09-24). The driver performs the tail
itself after DXE dispatch.

## Role in the validation sequence

This is a ONE-VARIABLE validation image (VCN enable only). The FCLK-1800
image (`firmware-flash-pkg/20260924-clv-fclk1800-apcb/`) lives on the
clv 5.00 base and is flashed separately. The final combined image is
built only after both variables are proven on hardware.

## Runbook

Complete programmer procedure and safety gates:
`docs/guides/bc250-v003b-route-b-programmer-flash-runbook.md`

## Evidence

- Build log: `docs/action-logs/2026-09-24-v003b-route-b.md`
- Driver source: `candidates/vcn-unlock-driver-v000-DRAFT/BC250VCNUnlockDxe.c`
- Replay artifact: `evidence/firmware-audit/20260924-plan-consumers/vcn_replay_writes.json`
- Policy lock: probe `evidence/runtime/20260924-012740-probe4l6-vcnctl.json` (config 0x0E boot-programmed, not enabled)
