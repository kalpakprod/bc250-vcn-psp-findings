# Flash Package: 20260924-v003c-route-b-vcn (SUPERSEDES v003b — DEFECT FIX)

## Artifacts
- `BC250_3.00_MeiMeiDXEv3_vcn_v003c.bin`: 16,777,216 bytes, SHA-256 `dafb323a5d701f29b9c1b74f0a6bc728572590ced54a8389c01b20c0a4f828b0`
- `SHA256SUMS`: verification hashes

## Why v003c exists (v003b is REJECTED, do not flash)

v003b placed the injected `Bc250VcnUnlockDxe` FFS at inner-FV offset
`0x432000` — AFTER the base image's trailing `0x2A0` of erased (0xFF) free
space. The real DxeCore FV walker (MdeModulePkg/Core/Dxe/FwVol.c,
`FwGetNextFile`: "We have found the free space so we are done") STOPS at the
first erased buffer, so a file placed after a 0xFF gap is never dispatched.
v003b would boot but the driver would never run: a wasted flash cycle and a
false negative for route B. Found by the independent pre-flight pass
(`scripts/verify_candidate_preflight.py`, gate G9) on 2026-09-24.

v003c injects the same driver FFS (same content sha) BEFORE `Bds.ffs`
(offset `0x12940`, contiguous after the previous file, 8-byte aligned) —
the placement pattern proven on hardware by the W9 series, whose injected
driver executed (8-core unlock observed). Builder:
`scripts/build_v003c_bds_prefix.py`; build manifest
`candidates/BC250_3.00_MeiMeiDXEv3_vcn_v003c.build.json`.

## What the image is (unchanged from v003b's design)

Route-B VCN enable candidate on the FD community 3.00 MeiMeiDXEv3 donor
base (sha256 `606a7a7f…`). The injected driver (same GUID
`B6250780-7E00-4203-900C-23443B1413FE`, PE32+ X64 DXE boot-service driver,
12288 B, sha256 `ba1cf214…`) replays the `FUN_0002A184` bring-up tail
(24 steps, `evidence/firmware-audit/20260924-plan-consumers/vcn_replay_writes.json`),
skipping the destructive builder, with secure reads, RMW+readback verify,
timeout-guarded polls, and abort guards. No `0x1B` doorbell send.

Policy word @`0xCCB8` = 0 on this board: SMU bit 6 never authorizes the VCN
tail (probe-measured 2026-09-24). The driver performs the tail itself after
DXE dispatch. Skipped by design (one variable per flash): `0x01D80814 |= 2`,
`0x0220FE00 &= ~4`, the `FUN_0002a344` pump block.

## Independent pre-flight verification (2026-09-24)

`scripts/verify_candidate_preflight.py` — 9/9 gates PASS, VERDICT GO
(`evidence/firmware-audit/20260924-v003c-preflight/result.json`):
G1 diff confined to capsule 0xAE0088-0xC2654B (1,331,254 B);
G8 everything outside byte-identical (PSP dir, APCB untouched);
G2 outer FV headers unchanged; G3 inner FV 193→194 files, all base files
byte-identical, exactly one new; G4 new FFS identity (type 0x07, 0x301C,
state 0xF8); G5 PE machine 0x8664, PE32+ 0x20B, subsystem 0x0B, size 12288,
sha matches the built driver; G6 FV header checksums valid both images;
G7 free tail 0x1280, no overflow; **G9 erased gap before the new file = 0
(dispatch reachable)**. Capsule FFS header checksum valid; tail after
capsule all-0xFF.

## Role in the validation sequence

ONE-VARIABLE image (VCN enable only), on the base class the board runs
right now (P3-family 3.00). The FCLK-1800 image lives on the clv 5.00 base
and is flashed separately. The final combined image is built only after
both variables are proven on hardware.

## Runbook

`docs/guides/bc250-v003c-programmer-flash-runbook.md` (updated from the
v003b runbook: image name/sha replaced, placement note added).

## Evidence

- Defect + fix log: `docs/action-logs/2026-09-24-v003b-route-b.md` (appended)
- Pre-flight result: `evidence/firmware-audit/20260924-v003c-preflight/result.json`
- DxeCore stop rule: `import/.../MdeModulePkg/Core/Dxe/FwVol/FwVol.c` (FwGetNextFile)
- W9 placement precedent: `import/.../bc250-bios/tools/patch-build/build_vcn_bios.py` (insert before Bds)
