# D8 LZMA explicit-size control action log

## Build intent (2026-09-12, Asia/Almaty)

- Actor: root agent.
- Trigger: D7 no-op failed initialization; apply the newly installed
  deobfuscation and symbolic-analysis routing skills.
- Finding: accepted baseline LZMA-alone header bytes are
  `5d000000011000420000000000`, declaring the exact decompressed length
  `0x420010`; D5-D7 used `5d00000001ffffffffffffffff` (unknown length).
- Target: rebuild the D7 no-op control from the known-booted baseline while
  explicitly writing the exact decompressed size into LZMA header bytes 5..12.
- Expected effect: restore compatibility with the firmware's bounded LZMA
  decoder without introducing any SMU/PCI/MMIO operation.
- Rollback: known-booted `/tmp/d3a_flash/pre_d3b2_retest.bin`.
- No hardware write is authorized by this build entry.

## Build and verification result (2026-09-12, Asia/Almaty)

- PASS: built `candidates/d8-lzma-size-control/BC250_D8_NOOP_LZMA_EXPLICIT_SIZE_from_pre-d3b2-retest.bin`, size 16 MiB, SHA-256 `e7c8223b56380c8aba1ed04a26cb04306f8ba331fac82121bedf70ff8a62099a`.
- PASS: LZMA header is exactly `5d000000011000420000000000`, including explicit size `0x420010`, matching the accepted baseline header.
- PASS: decompressed FV size unchanged and every decompressed byte outside the 12,288-byte no-op replacement PE is byte-identical to the booted baseline.
- PASS: four FVs, PSP/BHD/APCB checksums, signed-region identity, existing-slot metadata, and independently extracted PE payload.
- UNRUN: SPI write/readback and cold boot. D8 is a construction discriminator, not an unlock image.

## Hardware write intent (2026-09-12, Asia/Almaty; before write)

- Actor: root agent; operator approval: `прошивай`, referring to the immediately preceding exact D8 artifact and hash.
- Target: authorized board `BC250-01`; CH347T USB `1a86:55db` and Winbond `W25Q128.V` 16 MiB detected; board expected fully unpowered with clip attached.
- Candidate: `candidates/d8-lzma-size-control/BC250_D8_NOOP_LZMA_EXPLICIT_SIZE_from_pre-d3b2-retest.bin`, SHA-256 `e7c8223b56380c8aba1ed04a26cb04306f8ba331fac82121bedf70ff8a62099a`, size 16,777,216.
- Procedure: capture current full chip and require identity with D7 readback; write D8; require flashrom Verify; independent full readback and byte comparison; parser/checksum/PE extraction checks.
- Expected effect: no-op DXE with the accepted explicit-size LZMA header. Boot success would validate the corrected reconstruction method; it does not enable VCN.
- Rollback: fresh D7 capture and known-booted `/tmp/d3a_flash/pre_d3b2_retest.bin`, SHA-256 `e54709e8c3432271ff53501b519f3c5e4d0dd2db9aa2f6c7e63bdd86e9f8cd45`.
- Stop conditions: unexpected starting bytes, wrong target, write/Verify failure, readback mismatch, parser failure, or PE extraction mismatch.

## Hardware write and readback result (2026-09-12, Asia/Almaty)

- PASS: fresh pre-write capture `evidence/programmer/reads/20260912/d8/prewrite-d8.bin` is byte-identical to the D7 readback, SHA-256 `dccd89144aea31408bca9519937382a838eb4c4c58b59a11272e207cf473aac1`.
- PASS: flashrom detected Winbond `W25Q128.V`, wrote the full image, and reported `VERIFIED`.
- PASS: independent readback `evidence/programmer/reads/20260912/d8/postwrite-d8.bin` is byte-identical to D8, SHA-256 `e7c8223b56380c8aba1ed04a26cb04306f8ba331fac82121bedf70ff8a62099a`.
- PASS: readback parser reports four FVs and matching PSP/BHD/APCB checksums; extracted no-op PE SHA-256 `074b361d48e1d395ec3810b3b34fc96a469b736ed04155321b52fec0507c61f1` matches the intended payload.
- Evidence class: hardware-verified at SPI write/readback only.
- UNRUN: cold boot. The LZMA explicit-size hypothesis is not resolved until the operator powers on after removing the clip.

## Cold-boot result (2026-09-12 17:59 PKT)

- PASS: operator reports that D8 initialized and powered the board normally.
- PASS: root independently reached the board over SSH at `127.0.0.1`; uptime was 0 minutes, kernel `7.2.0-1.92-cachyos-vcn-bc250`, and the active command line contained `amdgpu.bc250_vcn_mode=1`.
- VERDICT: the D5-D7 BIOS construction defect was the LZMA-alone unknown-size header (`0xffffffffffffffff`). Restoring the accepted explicit decoded length `0x420010` makes the same-slot no-op candidate boot.
- Evidence class: hardware-verified for firmware-decoder acceptance, x86 release, and Linux boot. The no-op control intentionally makes no SMU-unlock or VCN claim.
- Next discriminating candidate: rebuild the D6 same-slot SMU-unlock payload using the D8 explicit-size LZMA envelope. This isolates unlock execution with the construction defect removed.
