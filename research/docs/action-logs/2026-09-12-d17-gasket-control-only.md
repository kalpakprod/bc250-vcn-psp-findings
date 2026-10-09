# D17 gasket control-only action log

## Build intent (2026-09-12, Asia/Almaty)

- Trigger: D16 narrows the SMU wedge to records 0..2.
- Baseline: verified D10R rollback SHA-256 `addef28800ce0102df4e207a28f0f671fa8c2b91e7d2c8864beb08dd1b6d85cd`.
- Change: early unlock plus only record 0, `0x0900C234<-0`, at ReadyToBoot.
- Exclusions: records 1..55, masks, lock, commit, power/clocks, dataplane, dom14, MMIO.
- Expected signal: dead SMU identifies C234 program-open itself as the wedge; live SMU moves culprit to C830/C834.
- No hardware write in this build entry.

## Build result (2026-09-12, Asia/Almaty)

- PASS: 12,288-byte PE SHA-256 `1cbb3912f3b27aa2712099b4a9acdff37158ea99c5e4ffc1e758fd340a7bcd09`.
- PASS: built `candidates/d17-gasket-control-only/BC250_D17_GASKET_CONTROL_ONLY_from_d10r.bin`, SHA-256 `d900e2ac87815a47520cb68c266bd308eb6375f39a98df6bd69b43cfd6ca4f82`.
- PASS: explicit-size LZMA, decompressed/signed invariants, four FVs, checksums, and PE extraction.
- Hardware UNRUN.

## Hardware write intent (2026-09-12, Asia/Almaty; before write)

- Operator response: `прошивай`, approving D17 SHA-256 `d900e2ac87815a47520cb68c266bd308eb6375f39a98df6bd69b43cfd6ca4f82`.
- Target: authorized BC250-01; CH347T `1a86:55db` and Winbond `W25Q128.V` detected.
- Procedure: capture/reconcile D16; write exact D17; Verify; independent readback; parsers/checksums/PE extraction.
- Expected effect: D10R base plus only `0x0900C234<-0` at ReadyToBoot.
- Rollback: fresh D16 capture and verified D10R.
- Stop conditions: unexpected payload drift or target/write/readback/parser/extraction failure.

## Hardware write and readback result (2026-09-12, Asia/Almaty)

- PASS: fresh D16 capture showed only 14 NVRAM bytes of drift; PSP and DXE regions remained identical.
- PASS: flashrom detected CH347T/Winbond `W25Q128.V`, wrote D17, and reported `VERIFIED`.
- PASS: independent readback is byte-identical to D17, SHA-256 `d900e2ac87815a47520cb68c266bd308eb6375f39a98df6bd69b43cfd6ca4f82`.
- PASS: four FVs, PSP/BHD/APCB checksums, and independently extracted PE SHA-256 `1cbb3912f3b27aa2712099b4a9acdff37158ea99c5e4ffc1e758fd340a7bcd09`.
- Evidence class: hardware-verified SPI write/readback only. Cold boot/SMU effect UNRUN.

## D17 cold-boot result (2026-09-12 22:05-22:07 PKT)

- PARTIAL/FAIL: Linux/SSH boots, but the operator selected the stock/default kernel `7.2.0-1.1-cachyos-bc250` rather than mode1; the command line has no `amdgpu.bc250_vcn_mode` parameter.
- Direct invariant result is nevertheless decisive: SMU `alive=False`; secure Q3 `0x2A` times out. Kernel reports SMU hw_init `-62`, fatal GPU init, PSP DESTROY_TMR `0x80000306`, and amdgpu probe `-62`.
- VERDICT: the single ReadyToBoot write `0x0900C234<-0` is sufficient to wedge the SMU. C830/C834 and every other gasket record are excluded as necessary causes.
- Kernel-mode caveat: this run does not compare VCN mode1 behavior, but SMU death occurs before and independently of a VCN hardware probe, so it does not weaken the C234 attribution.
- Next method-class change: never issue C234 program-open at ReadyToBoot. Test whether C830/C834 writes without opening program mode are safely ignored, latched, or independently wedging.
