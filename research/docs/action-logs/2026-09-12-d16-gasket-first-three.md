# D16 gasket records 0..2 action log

## Build intent (2026-09-12, Asia/Almaty)

- Trigger: D15 narrows the SMU wedge to records 0..6.
- Baseline: verified D10R rollback SHA-256 `addef28800ce0102df4e207a28f0f671fa8c2b91e7d2c8864beb08dd1b6d85cd`.
- Change: early unlock plus only `0x0900C234<-0`, `0x0900C830<-0x00FFFFFB`, and `0x0900C834<-0x00FFFFFF` at ReadyToBoot.
- Exclusions: records 3..55, lock, commit, power/clocks, dataplane, dom14, MMIO.
- Expected signal: live SMU moves culprit to records 3..6; dead SMU retains it in 0..2.
- No hardware write in this build entry.

## Build result (2026-09-12, Asia/Almaty)

- PASS: 12,288-byte PE SHA-256 `2d1422c916a4df31cdae1132f9ac9e5fcd479398d0dfb47bfe0ff484c3548954`.
- PASS: built `candidates/d16-gasket-first-three/BC250_D16_GASKET_FIRST_THREE_from_d10r.bin`, SHA-256 `8ce1bcf0082816a62578a78c72731c1c36bc66b35c9bef06ff06cee5f49cbe71`.
- PASS: explicit-size LZMA, decompressed/signed invariants, four FVs, checksums, and PE extraction.
- Hardware UNRUN.

## Hardware write intent (2026-09-12, Asia/Almaty; before write)

- Operator response: `прошивай`, approving D16 SHA-256 `8ce1bcf0082816a62578a78c72731c1c36bc66b35c9bef06ff06cee5f49cbe71`.
- Target: authorized BC250-01; CH347T `1a86:55db` and Winbond `W25Q128.V` detected; board expected unpowered with clip attached.
- Procedure: capture/reconcile D15; write D16; Verify; independent readback; parsers/checksums/PE extraction.
- Expected effect: D10R base plus only records 0..2 at ReadyToBoot.
- Rollback: fresh D15 capture and verified D10R.
- Stop conditions: unexpected payload drift, target/write/readback/parser/extraction failure.

## Hardware write and readback result (2026-09-12, Asia/Almaty)

- PASS: fresh D15 capture showed only 14 NVRAM bytes of drift in three ranges `0x1ACF..0x1AE5`; PSP/DXE regions identical.
- PASS: CH347T/Winbond detected; flashrom wrote D16 and reported `VERIFIED`.
- PASS: independent readback byte-identical, SHA-256 `8ce1bcf0082816a62578a78c72731c1c36bc66b35c9bef06ff06cee5f49cbe71`.
- PASS: four FVs, PSP/BHD/APCB checksums, and extracted PE SHA-256 `2d1422c916a4df31cdae1132f9ac9e5fcd479398d0dfb47bfe0ff484c3548954`.
- Evidence class: hardware-verified SPI write/readback. Cold boot and SMU effect UNRUN.

## D16 cold-boot result (2026-09-12 21:40 PKT)

- PARTIAL/FAIL: Linux/SSH boots, but SMU `alive=False`; secure Q3 times out and amdgpu SMU hw_init fails `-62`.
- VERDICT: culprit is within records 0..2: `C234<-0`, `C830<-0x00FFFFFB`, or `C834<-0x00FFFFFF`.
- Next slice: record 0 only (`0x0900C234<-0`). This directly distinguishes the program-enable/control write from the two mask writes.
