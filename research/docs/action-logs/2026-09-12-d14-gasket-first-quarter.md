# D14 gasket first-quarter action log

## Build intent (2026-09-12, Asia/Almaty)

- Actor: root agent.
- Trigger: D13 proves the wedge lies in records 0..27.
- Baseline: verified D10R rollback SHA-256 `addef28800ce0102df4e207a28f0f671fa8c2b91e7d2c8864beb08dd1b6d85cd`.
- Change: D10R early unlock plus only gasket records 0..13 at ReadyToBoot.
- Exclusions: records 14..55, lock, commit, power/clocks, dataplane, dom14, MMIO.
- Expected signal: live SMU after Linux boot moves culprit to 14..27; dead SMU retains culprit in 0..13.
- Rollback: D10R. No hardware write in this build entry.

## Build result (2026-09-12, Asia/Almaty)

- PASS: RELEASE PE32 is 12,288 bytes, SHA-256 `d16d09df7d469f7194c627360153a728f83eec444de7f01678274160ac248411`.
- PASS: built `candidates/d14-gasket-first-quarter/BC250_D14_GASKET_FIRST_QUARTER_from_d10r.bin`, size 16 MiB, SHA-256 `6c0c23c5ff6fae99e479f8c84b2caa53a7494103c798ca72ce7f0c9d23a6c238`.
- PASS: explicit-size LZMA header, decompressed bytes outside replacement PE, signed-region identity, four FVs, PSP/BHD/APCB checksums, and independent PE extraction.
- Executed prefix is exactly records 0..13; records 14..55, lock and commit excluded.
- Hardware write/readback and cold boot are UNRUN.

## Hardware write intent (2026-09-12, Asia/Almaty; before write)

- Operator response: `прошивай`, approving D14 path and exact SHA-256 `6c0c23c5ff6fae99e479f8c84b2caa53a7494103c798ca72ce7f0c9d23a6c238`.
- Target: authorized BC250-01; CH347T `1a86:55db` and Winbond `W25Q128.V` 16 MiB detected; board expected unpowered with clip attached.
- Procedure: capture current D13 state and reconcile payload regions; write exact D14 (already based on verified D10R); flashrom Verify; independent readback; parser/checksum/PE extraction.
- Expected effect: restore the D10R base and execute only gasket records 0..13 at ReadyToBoot.
- Rollback: fresh D13 capture and verified D10R image.
- Stop conditions: unexpected payload drift, wrong target, write/Verify failure, readback mismatch, parser failure, or extracted-PE mismatch.

## Hardware write and readback result (2026-09-12, Asia/Almaty)

- PASS: fresh D13 capture differed from its post-write readback by only 14 NVRAM bytes in three ranges `0x1ACF..0x1AE5`; PSP and DXE regions remained identical.
- PASS: flashrom detected CH347T/Winbond `W25Q128.V`, wrote D14, and reported `VERIFIED`.
- PASS: independent readback `evidence/programmer/reads/20260912/d14/postwrite-d14.bin` is byte-identical to D14, SHA-256 `6c0c23c5ff6fae99e479f8c84b2caa53a7494103c798ca72ce7f0c9d23a6c238`.
- PASS: four FVs, PSP/BHD/APCB checksums, and independently extracted PE SHA-256 `d16d09df7d469f7194c627360153a728f83eec444de7f01678274160ac248411`.
- Evidence class: hardware-verified at SPI write/readback only.
- UNRUN: cold boot, Linux release, SMU liveness/secure access, and first-quarter gasket effect.

## D14 cold-boot result (2026-09-12 21:13 PKT)

- PARTIAL/FAIL: Linux/SSH boots, but SMU is wedged before amdgpu initialization.
- Direct result: `alive=False`; secure Q3 `0x2A` times out. Kernel repeats SMU hw_init `-62`, fatal GPU init, PSP DESTROY_TMR `0x80000306`, and amdgpu probe `-62`.
- VERDICT: the culprit is within records 0..13. Records 14..55, lock, and commit are excluded.
- STOP: no more mailbox/MMIO on this boot. Next slice is records 0..6 only.
