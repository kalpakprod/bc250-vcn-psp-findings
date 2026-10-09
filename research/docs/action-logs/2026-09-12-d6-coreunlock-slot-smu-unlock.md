# D6 CoreUnlock-slot SMU-unlock BIOS action log

## Build intent (2026-09-12, Asia/Almaty)

- Actor: root agent.
- Operator direction: continue searching specifically for a BIOS-resident
  unlock platform; do not stop at restoring stock.
- Source: `/tmp/d3a_flash/pre_d3b2_retest.bin`, size 16,777,216, SHA-256
  `e54709e8c3432271ff53501b519f3c5e4d0dd2db9aa2f6c7e63bdd86e9f8cd45`.
- Replacement PE32: `candidates/d5-smu-unlock-lab/Bc250SmuUnlockDxe.efi`,
  size 12,288, SHA-256
  `f8774ab43ece688da6ef96c28f606a92b43a1927d4abab1397a6c310e4bd76e2`.
- Existing target: the 12,288-byte PE32 section inside the already present
  `Bc250CoreUnlockDxe` FFS, GUID
  `2F3D426D-6A54-4A6B-82D0-1207CC5B6D92`, type 7.
- Procedure: replace the PE32 section byte-for-byte without changing FFS
  length, GUID, Depex, UI, order, inner-FV length, or any other decompressed
  byte; rebuild the enclosing LZMA container; parse and independently extract.
- Expected effect: use an existing dispatched DXE slot to register the
  ReadyToBoot SMU debug unlock while avoiding D5's extra-FFS/layout variable.
- Rollback: `/tmp/d3a_flash/pre_d3b2_retest.bin` via verified full-chip write
  and independent readback.
- Stop conditions: target ambiguity, payload-size mismatch, any decompressed
  change outside the one PE section, signed-region difference, checksum or FV
  parse failure, or extraction mismatch.
- No hardware write is authorized by this build entry.

## Build and verification result (2026-09-12, Asia/Almaty)

- RESULT: D6 offline candidate built; no hardware write occurred.
- Output: `candidates/d6-coreunlock-slot-smu-unlock/BC250_D6_CORE_SLOT_SMU_UNLOCK_from_pre-d3b2-retest.bin`, size 16,777,216, SHA-256 `bd7689d6e2da32079878c507c472d5fc6d7208bc8f7dca208be4115c83d2db07`.
- PASS: exact existing FFS located once at decompressed-FV offset `0x88`; its PE32 section begins at `0xA4` and is exactly 12,288 bytes.
- PASS: replacement size equals the original CoreUnlock PE32 size exactly.
- PASS: after independent decompression of the final image, every decompressed FV byte outside `0xA4..0x30A4` is byte-identical to the booted baseline. Inner-FV size, existing FFS GUID, header, Depex, UI, order, and all following module offsets are unchanged.
- PASS: the replacement extracted from the final image has SHA-256 `f8774ab43ece688da6ef96c28f606a92b43a1927d4abab1397a6c310e4bd76e2`, byte-identical to the built SMU-unlock EFI.
- PASS: four FVs parse; PSP Fletcher32, BHD Fletcher32, and APCB checksum match; the entire signed/PSP area `0x8E0000..0xAE0000` is byte-identical to the selected baseline.
- Design consequence: D6 removes D5's new-FFS, shifted-module, resized-inner-FV, and new-dispatch-order variables. The only semantic change inside the decompressed DXE FV is replacement of an existing DXE PE payload.
- UNRUN: cold boot, DXE dispatch, ReadyToBoot callback, SMU unlock readback, VCN MMIO/rings/codecs.
- Hardware state remains D5 (boot-failed) until a separately logged and approved write.

## Hardware write intent (2026-09-12, Asia/Almaty; before write)

- Actor: root agent; operator approval: `прошивай`, referring to the immediately preceding exact D6 artifact and hash.
- Physical target: authorized board `BC250-01`; CH347T USB `1a86:55db` detected; Winbond `W25Q128.V` 16 MiB detected; the board is expected fully unpowered with the SOIC8 clip attached.
- Exact candidate: `candidates/d6-coreunlock-slot-smu-unlock/BC250_D6_CORE_SLOT_SMU_UNLOCK_from_pre-d3b2-retest.bin`, SHA-256 `bd7689d6e2da32079878c507c472d5fc6d7208bc8f7dca208be4115c83d2db07`, size 16,777,216.
- Tool: `/tmp/flashrom-src/build/flashrom`, `flashrom v2.0.0-devel`, programmer `ch347_spi` at its reported 15 MHz clock.
- Procedure: capture and hash the current full chip; require byte identity with the independently verified D5 readback; write the exact D6 image; require flashrom built-in verify; independently read all 16 MiB; require hash and byte identity; rerun firmware/APCB parsers and extract the replaced DXE payload.
- Expected effect: use the existing CoreUnlock FFS dispatch slot to register the SMU unlock at ReadyToBoot without changing DXE FV topology.
- Rollback: fresh pre-write capture plus the known booted `/tmp/d3a_flash/pre_d3b2_retest.bin`, SHA-256 `e54709e8c3432271ff53501b519f3c5e4d0dd2db9aa2f6c7e63bdd86e9f8cd45`.
- Stop conditions: unexpected current-chip bytes, wrong chip/size, flashrom failure, readback mismatch, parser failure, or replacement-extraction mismatch.
- Cold boot and SMU unlock remain unrun after the SPI write and require separate verification.

## Hardware write and readback result (2026-09-12, Asia/Almaty)

- PASS: fresh pre-write capture `evidence/programmer/reads/20260912/d6/prewrite-d6.bin` is 16 MiB, SHA-256 `dec17ca81f513c28fa5a3227b3745c4c6ceb6aba68fe3d24fce8110df54ae3f1`, and byte-identical to the independently verified D5 readback. The starting state was reconciled.
- PASS: flashrom detected Winbond `W25Q128.V`, wrote the full `0x000000..0xFFFFFF` range, and reported `VERIFIED`.
- PASS: independent full-chip readback `evidence/programmer/reads/20260912/d6/postwrite-d6.bin` has SHA-256 `bd7689d6e2da32079878c507c472d5fc6d7208bc8f7dca208be4115c83d2db07` and is byte-identical to the exact D6 candidate.
- PASS: hardware readback reparses with four FVs and matching PSP/BHD/APCB checksums. The existing CoreUnlock-slot FFS remains GUID `2F3D426D-6A54-4A6B-82D0-1207CC5B6D92`, type 7.
- PASS: its PE32 payload independently extracted from the hardware readback has SHA-256 `f8774ab43ece688da6ef96c28f606a92b43a1927d4abab1397a6c310e4bd76e2`, byte-identical to the intended SMU-unlock DXE.
- Evidence class: hardware-verified at SPI write/readback layer only.
- UNRUN: cold boot, x86 release, DXE dispatch, ReadyToBoot callback, SMU unlock readback, VCN MMIO/rings/codecs.
- Recovery: fresh D5 capture plus known booted `pre_d3b2_retest.bin` remain preserved; use the latter for recovery if D6 does not boot.

## Cold-boot result (2026-09-12, operator observation)

- FAIL: the operator reports `нет инициализации` after the verified D6 write and cold-power attempt.
- The SPI contents and replacement PE extraction were byte-exact before boot, so an incomplete write is excluded.
- D6 preserved the decompressed FV topology and every decompressed byte outside the existing 12,288-byte CoreUnlock PE payload. This rules out D5's added-FFS, shifted-module, resized-inner-FV, and changed-dispatch-order mechanisms.
- Remaining attribution is two-way: (A) the rebuilt LZMA transport/capsule is not accepted despite parsing correctly; or (B) the replacement DXE dispatches and the SMU unlock/ReadyToBoot path hangs before observable initialization.
- Next discriminator: D7 replaces the same PE32 payload with a same-size no-op DXE that performs no hardware or mailbox access. D7 boot success selects (B); D7 failure selects (A) and closes this recompression-based BIOS construction method.
- D6 must not be described as bootable or as proof that the SMU unlock executed.
