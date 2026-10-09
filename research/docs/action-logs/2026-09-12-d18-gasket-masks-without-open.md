# D18 gasket masks without program-open action log

## Build intent (2026-09-12, Asia/Almaty)

- Trigger: D17 proves `0x0900C234<-0` alone wedges SMU at ReadyToBoot.
- Baseline: verified D10R rollback SHA-256 `addef28800ce0102df4e207a28f0f671fa8c2b91e7d2c8864beb08dd1b6d85cd`.
- Change: early unlock, then at ReadyToBoot write only `0x0900C830<-0x00FFFFFB` and `0x0900C834<-0x00FFFFFF`; omit C234 entirely.
- Exclusions: every other gasket record, program-open, commit, lock, power/clocks, dataplane, dom14, MMIO.
- Expected signal: live SMU means the mask writes are safe without program-open; dead SMU means C830/C834 are independently inaccessible.
- No hardware write in this build entry.

## Build result (2026-09-12, Asia/Almaty)

- PASS: 12,288-byte PE SHA-256 `1d1edfb7ab0764ba39f05fff7da180744c0efc1ac56795e16b5bc24155d078b0`.
- PASS: built `candidates/d18-gasket-masks-without-open/BC250_D18_GASKET_MASKS_WITHOUT_OPEN_from_d10r.bin`, SHA-256 `3111d97702867cb8c32d10804b4ac87fa17c70bf255cbed33fcf1d85e45ce7a0`.
- PASS: explicit-size LZMA, decompressed/signed invariants, four FVs, checksums, and PE extraction.
- Hardware UNRUN.

## Hardware write intent (2026-09-12, Asia/Almaty; before write)

- Operator response: `подключил`, confirming power-off/clip attachment for the immediately preceding D18 procedure.
- Target: authorized BC250-01; require CH347T `1a86:55db` and Winbond `W25Q128.V`.
- Exact D18 SHA-256: `3111d97702867cb8c32d10804b4ac87fa17c70bf255cbed33fcf1d85e45ce7a0`.
- Procedure: capture/reconcile D17; write D18; Verify; independent readback; parsers/checksums/PE extraction.
- Expected effect: D10R plus C830/C834 writes without C234.
- Rollback: fresh D17 capture and verified D10R.
- Stop conditions: unexpected payload drift or target/write/readback/parser/extraction failure.

## Hardware write and readback result (2026-09-12, Asia/Almaty)

- PASS: fresh D17 capture showed 52 bytes of NVRAM drift in five ranges below `0x20000`; PSP and DXE regions remained identical.
- PASS: flashrom detected CH347T/Winbond, wrote D18, and reported `VERIFIED`.
- PASS: independent readback is byte-identical to D18, SHA-256 `3111d97702867cb8c32d10804b4ac87fa17c70bf255cbed33fcf1d85e45ce7a0`.
- PASS: four FVs, PSP/BHD/APCB checksums, and extracted PE SHA-256 `1d1edfb7ab0764ba39f05fff7da180744c0efc1ac56795e16b5bc24155d078b0`.
- Evidence class: hardware-verified SPI write/readback only. Cold boot/SMU effect UNRUN.

## D18 cold-boot result (2026-09-12 22:14 PKT)

- PARTIAL/FAIL: mode1 Linux/SSH boots, but SMU is dead (`alive=False`, secure Q3 timeout); amdgpu SMU hw_init fails `-62`.
- VERDICT: omitting C234 does not avoid the wedge. At least one of `C830<-0x00FFFFFB` or `C834<-0x00FFFFFF` independently or jointly causes it.
- Next discriminator: D19 writes C830 only. D20 (prepared separately) writes C834 only if required.
