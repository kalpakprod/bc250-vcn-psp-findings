# D13 gasket first-half action log

## Build intent (2026-09-12, Asia/Almaty)

- Actor: root agent; operator direction: prepare the next BIOS/binary slice immediately.
- Baseline: restored D10R image `evidence/programmer/reads/20260912/d11-rollback/post-rollback-d10r.bin`, SHA-256 `addef28800ce0102df4e207a28f0f671fa8c2b91e7d2c8864beb08dd1b6d85cd`.
- Change: immediate D10R unlock plus gasket records 0..27 only at ReadyToBoot.
- Explicit exclusions: records 28..55, every lock/unlock tail and commit, power/clocks, donor dataplane, dom14, PCI-command changes, VCN MMIO, mode2.
- Expected signal: Linux boot plus live SMU means the failure is outside the first half; SMU/boot failure means the first half contains it.
- Rollback: current D12 capture and restored D10R image.
- No hardware write is included in this build action.

## Build and verification result (2026-09-12, Asia/Almaty)

- PASS: RELEASE build produced a 12,288-byte PE, SHA-256 `c1a190710a6dda842b8d269db2463b005f4b9a9073ec297d7357b811ca991e1f`.
- PASS: built `candidates/d13-gasket-first-half/BC250_D13_GASKET_FIRST_HALF_from_d10r.bin`, 16 MiB, SHA-256 `00164ea687b2622b117f779c74c27bc810ef4f8b6f885a8fea6a5fa44f58eaeb`.
- PASS: explicit-size LZMA header `5d000000011000420000000000`; decompressed bytes outside replacement PE identical; signed region identical; PSP/BHD/APCB checksums; four FVs; extracted PE identity.
- The executed prefix is exactly records 0..27. It excludes all records 28..55, lock `0x0900CB80`, and both commit writes `0x0900C234 <- 1`.
- UNRUN: hardware write/readback, cold boot, SMU liveness, and any gasket effect.

## Hardware write intent (2026-09-12, Asia/Almaty; before write)

- Operator response: `прошивай`, approving the immediately preceding D13 path and exact SHA-256 `00164ea687b2622b117f779c74c27bc810ef4f8b6f885a8fea6a5fa44f58eaeb`.
- Target: authorized BC250-01; CH347T `1a86:55db` and Winbond `W25Q128.V` 16 MiB detected; board is expected unpowered with clip attached.
- Procedure: capture current D12 state; reconcile firmware regions; write exact D13; flashrom Verify; independent readback; parser/checksum/PE extraction.
- Expected effect: replace D12 with the D10R-based first-half slice. No separate intermediate D10 flash is needed because D13 itself is built from the exact restored D10R base.
- Rollback: fresh D12 capture and verified D10R image.
- Stop conditions: unexpected payload drift, wrong target, write/Verify failure, readback mismatch, parser failure, or extracted-PE mismatch.

## Hardware write and readback result (2026-09-12, Asia/Almaty)

- PASS: fresh D12 capture differed from its post-write readback by only 14 NVRAM bytes in three ranges `0x1ACF..0x1AE5`; PSP and DXE payload regions remained identical.
- PASS: flashrom detected CH347T/Winbond `W25Q128.V`, wrote the full D13 image, and reported `VERIFIED`.
- PASS: independent readback `evidence/programmer/reads/20260912/d13/postwrite-d13.bin` is byte-identical to D13, SHA-256 `00164ea687b2622b117f779c74c27bc810ef4f8b6f885a8fea6a5fa44f58eaeb`.
- PASS: four FVs, PSP/BHD/APCB checksums, and independently extracted PE SHA-256 `c1a190710a6dda842b8d269db2463b005f4b9a9073ec297d7357b811ca991e1f`.
- Evidence class: hardware-verified at SPI write/readback only.
- UNRUN: cold boot, Linux release, SMU liveness/secure access, and first-half gasket effect.

## D13 cold-boot result (2026-09-12 20:56 PKT)

- PARTIAL/FAIL: Linux and SSH booted, but SMU is wedged before amdgpu initialization.
- Direct checks: `alive=False`; secure Q3 `0x2A` timed out. Kernel reports SMU hw_init `-62`, fatal GPU init, PSP DESTROY_TMR `0x80000306`, and amdgpu probe `-62`.
- VERDICT: the wedging operation is within gasket records 0..27; records 28..55, lock, and commit are excluded as necessary causes.
- STOP: no further mailbox/MMIO operations on this boot. Cold cycle and restore D10R before the next slice.
- Next binary-search slice: records 0..13 only at ReadyToBoot.
