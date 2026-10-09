# D15 gasket records 0..6 action log

## Build intent (2026-09-12, Asia/Almaty)

- Actor: root agent.
- Trigger: D14 narrows the SMU wedge to records 0..13.
- Baseline: verified D10R rollback SHA-256 `addef28800ce0102df4e207a28f0f671fa8c2b91e7d2c8864beb08dd1b6d85cd`.
- Change: early D10R unlock plus only gasket records 0..6 at ReadyToBoot: `C234`, `C830`, `C834`, `C838`, `C920`, `C92C`, `C930`.
- Exclusions: records 7..55, lock, commit, power/clocks, dataplane, dom14, MMIO.
- Expected signal: live SMU moves culprit to records 7..13; dead SMU retains it in 0..6.
- Rollback: D10R. No hardware write in this build entry.

## Build result (2026-09-12, Asia/Almaty)

- PASS: RELEASE PE32 size 12,288, SHA-256 `a14bdadcb6138139e6774ea97617d870809eb73ed9aa347367c46f93c02351b7`.
- PASS: built `candidates/d15-gasket-first-seven/BC250_D15_GASKET_FIRST_SEVEN_from_d10r.bin`, 16 MiB, SHA-256 `42262d1ca995cdb9309f246aa289848a4a53dcedbbae896e5da213129b991b95`.
- PASS: explicit-size LZMA header, decompressed invariants, signed-region identity, four FVs, PSP/BHD/APCB checksums, and PE extraction.
- Executed prefix exactly records 0..6. Hardware UNRUN.

## Hardware write intent (2026-09-12, Asia/Almaty; before write)

- Operator response: `подключил`, confirming the requested power-off/clip step for the immediately preceding D15 flash procedure.
- Target: authorized BC250-01; require CH347T `1a86:55db` and Winbond `W25Q128.V` 16 MiB.
- Exact D15: SHA-256 `42262d1ca995cdb9309f246aa289848a4a53dcedbbae896e5da213129b991b95`.
- Procedure: capture/reconcile D14; write D15 (D10R-based); flashrom Verify; independent readback; parsers and PE extraction.
- Expected effect: execute only gasket records 0..6 at ReadyToBoot after early unlock.
- Rollback: fresh D14 capture and verified D10R.
- Stop conditions: unexpected payload drift, wrong target, write/Verify failure, readback mismatch, parser or extraction failure.

## Hardware write and readback result (2026-09-12, Asia/Almaty)

- PASS: fresh D14 capture showed only 14 NVRAM bytes of drift in three ranges `0x1ACF..0x1AE5`; PSP and DXE regions remained identical.
- PASS: flashrom detected CH347T/Winbond `W25Q128.V`, wrote D15, and reported `VERIFIED`.
- PASS: independent readback `evidence/programmer/reads/20260912/d15/postwrite-d15.bin` is byte-identical to D15, SHA-256 `42262d1ca995cdb9309f246aa289848a4a53dcedbbae896e5da213129b991b95`.
- PASS: four FVs, PSP/BHD/APCB checksums, and independently extracted PE SHA-256 `a14bdadcb6138139e6774ea97617d870809eb73ed9aa347367c46f93c02351b7`.
- Evidence class: hardware-verified at SPI write/readback only. Cold boot and SMU effect remain UNRUN.

## D15 cold-boot result (2026-09-12 21:31 PKT)

- PARTIAL/FAIL: Linux/SSH boots, but SMU is wedged (`alive=False`, secure Q3 timeout) and amdgpu SMU hw_init fails `-62` with fatal GPU init.
- VERDICT: culprit is within records 0..6. Records 7..55, lock, and commit are excluded.
- Next slice: records 0..2 only (`C234<-0`, `C830`, `C834`). No further mailbox/MMIO operations on this boot.
