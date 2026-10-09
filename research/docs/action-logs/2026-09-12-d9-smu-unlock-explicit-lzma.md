# D9 SMU unlock with explicit-size LZMA action log

## Build intent (2026-09-12, Asia/Almaty)

- Actor: root agent.
- Trigger: D8 no-op booted and root independently verified Linux over SSH.
- Exact base: known-booted `/tmp/d3a_flash/pre_d3b2_retest.bin`, SHA-256 `e54709e8c3432271ff53501b519f3c5e4d0dd2db9aa2f6c7e63bdd86e9f8cd45`.
- Replacement: D6/D5 SMU-unlock PE32, SHA-256 `f8774ab43ece688da6ef96c28f606a92b43a1927d4abab1397a6c310e4bd76e2`, size 12,288.
- Method: replace the existing CoreUnlock-slot PE only, preserve every other decompressed byte, and encode the exact `0x420010` decompressed size in the LZMA-alone header.
- Expected effect: reproduce D8's accepted container construction while changing only no-op versus SMU-unlock behavior. The driver registers ReadyToBoot, performs the previously proven BIOS-3 SMU debug unlock/fixup, verifies secure SMN read access, then publishes its protocol. It performs no VCN power, gasket, dom14, or MMIO operation.
- Failure path: no initialization would now implicate the SMU unlock/timing implementation rather than the LZMA construction.
- Rollback: D8 readback or the exact known-booted baseline.
- No hardware write is authorized by this build entry.

## Build and verification result (2026-09-12, Asia/Almaty)

- PASS: built `candidates/d9-smu-unlock-explicit-lzma/BC250_D9_SMU_UNLOCK_EXPLICIT_LZMA_from_pre-d3b2-retest.bin`, size 16 MiB, SHA-256 `b0a3cb7a58ff4b87e2197c2f3ed83adbf471b60a39dcb222c3d066844a3331cb`.
- PASS: LZMA header exactly matches D8's hardware-accepted header `5d000000011000420000000000`, with explicit decoded length `0x420010`.
- PASS: decompressed FV size is unchanged; every byte outside the existing 12,288-byte CoreUnlock-slot PE is identical to the known-booted base.
- PASS: PSP/BHD/APCB checksums, four FVs, signed-region identity, existing-slot metadata, and independent extraction of the intended SMU-unlock PE.
- UNRUN: SPI write/readback, cold boot, ReadyToBoot callback, secure-SMN readback, and VCN behavior.

## Hardware write intent (2026-09-12, Asia/Almaty; before write)

- Actor: root agent; operator approval: `прошивай`, referring to the immediately preceding exact D9 artifact and hash.
- Target: authorized board `BC250-01`; CH347T USB `1a86:55db` and Winbond `W25Q128.V` 16 MiB detected; board expected fully unpowered with clip attached.
- Candidate: `candidates/d9-smu-unlock-explicit-lzma/BC250_D9_SMU_UNLOCK_EXPLICIT_LZMA_from_pre-d3b2-retest.bin`, SHA-256 `b0a3cb7a58ff4b87e2197c2f3ed83adbf471b60a39dcb222c3d066844a3331cb`, size 16,777,216.
- Procedure: capture current chip and require identity with D8; write D9; require flashrom Verify; independent full readback/byte comparison; parser/checksum/PE extraction checks.
- Expected effect: retain D8's hardware-accepted LZMA envelope and execute the SMU debug unlock at ReadyToBoot without any VCN power, gasket, dom14, or MMIO action.
- Rollback: fresh D8 capture and known-booted `/tmp/d3a_flash/pre_d3b2_retest.bin`.
- Stop conditions: starting-state mismatch, wrong target, write/Verify failure, readback mismatch, parser failure, or extracted-PE mismatch.

## Pre-write stop and fresh rebase (2026-09-12, Asia/Almaty)

- STOP before write: fresh capture `evidence/programmer/reads/20260912/d9/prewrite-d9.bin` has SHA-256 `e9cad60d58738d2595e749afe353d35ada8912e4b3e233a4724266df1a198e7d`, not the earlier D8 readback hash.
- Attribution PASS: exactly 131 bytes in 7 ranges changed, all within `0x191D..0x1ABB` below `0x20000`; PSP `0x8E0000..0xAE0000` and DXE `0xAE0000..0xE00000` are byte-identical to D8. This is normal post-boot NVRAM drift, not an unexpected firmware payload.
- Decision: do not overwrite the fresh board NVRAM with the older D9 base. Rebuild D9 from this fresh capture while preserving its NVRAM and changing only the existing CoreUnlock-slot PE inside the accepted explicit-size LZMA envelope.
- The operator's prior approval identified the older D9 hash. The freshly rebased candidate requires reporting its new exact hash before write.

## D9R exact write approval (2026-09-12, Asia/Almaty; before write)

- Operator response: `подтверждаю`, approving the immediately preceding D9R artifact and exact SHA-256.
- Approved candidate: `candidates/d9-smu-unlock-explicit-lzma/BC250_D9R_SMU_UNLOCK_EXPLICIT_LZMA_from_fresh-d8.bin`, SHA-256 `c46392ceca989f0bd558077bf07bc40490645710710d6c48c7d42e8eb328834d`, size 16,777,216.
- Exact source/rollback capture: `evidence/programmer/reads/20260912/d9/prewrite-d9.bin`, SHA-256 `e9cad60d58738d2595e749afe353d35ada8912e4b3e233a4724266df1a198e7d`; this is the D8 hardware-booted state plus its fresh NVRAM drift.
- Procedure and stop conditions remain those above: detect exact 16 MiB Winbond target, write, built-in Verify, independent readback, byte comparison, parser/checksum/PE extraction.

## D9R hardware write and readback result (2026-09-12, Asia/Almaty)

- PASS: CH347T and Winbond `W25Q128.V` 16 MiB detected.
- PASS: flashrom wrote the full image and reported `VERIFIED`.
- PASS: independent readback `evidence/programmer/reads/20260912/d9/postwrite-d9r.bin` is byte-identical to the approved D9R candidate; SHA-256 `c46392ceca989f0bd558077bf07bc40490645710710d6c48c7d42e8eb328834d`.
- PASS: hardware readback reparses with four FVs and matching PSP/BHD/APCB checksums.
- PASS: CoreUnlock-slot PE extracted from the readback has SHA-256 `f8774ab43ece688da6ef96c28f606a92b43a1927d4abab1397a6c310e4bd76e2`, byte-identical to the intended SMU-unlock driver.
- Evidence class: hardware-verified at SPI write/readback only.
- UNRUN: cold boot, x86 release, DXE dispatch, ReadyToBoot callback, secure-SMN readback, and VCN behavior.

## D9R cold boot and SMU-unlock result (2026-09-12 19:05 PKT)

- PASS: operator cold-booted mode1 and reported the board loaded.
- PASS: root independently reached Linux over SSH with uptime 0 minutes, kernel `7.2.0-1.92-cachyos-vcn-bc250`, and `amdgpu.bc250_vcn_mode=1` on the active command line.
- PASS: bounded read-only mailbox verification on this exact boot: Q3 test message returned `alive=True`; secure Q3 message `0x2A` read SMN `0x0005A870` with status `0x01` and value `0x00000077`; Q3 test message remained `alive_after=True`.
- VERDICT: D9R is hardware-verified booting and its BIOS-resident ReadyToBoot SMU debug unlock executes successfully. This is the first verified BIOS image in this campaign that enters Linux with secure SMU access already open.
- Evidence boundary: VCN remains disabled/unverified. No VCN power, gasket, dom14, MMIO, ring, or codec operation was executed during this verification.
