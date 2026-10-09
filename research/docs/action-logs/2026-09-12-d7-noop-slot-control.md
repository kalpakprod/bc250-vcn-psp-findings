# D7 no-op existing-slot control action log

## Build intent (2026-09-12, Asia/Almaty)

- Actor: root agent.
- Goal: attribute D6 no-initialization between LZMA/FV reconstruction and SMU-unlock execution.
- Base: `/tmp/d3a_flash/pre_d3b2_retest.bin`, SHA-256 `e54709e8c3432271ff53501b519f3c5e4d0dd2db9aa2f6c7e63bdd86e9f8cd45`.
- Target: existing CoreUnlock FFS PE32 payload; preserve GUID, Depex, UI, topology, sizes, and all other decompressed bytes.
- Expected effect: no-op DXE returns success and otherwise behaves like the known-booted baseline.
- Rollback: the exact base image via full write, Verify, and independent readback.
- No hardware write is authorized by this build entry.

## Hardware write intent (2026-09-12, Asia/Almaty; before write)

- Actor: root agent; operator approval: `прошивай`, referring to the immediately preceding D7 artifact and hash.
- Target: authorized board `BC250-01`; CH347T `1a86:55db` and Winbond `W25Q128.V` 16 MiB detected; board expected fully unpowered with SOIC8 clip attached.
- Exact candidate: `candidates/d7-noop-slot-control/BC250_D7_NOOP_CORE_SLOT_CONTROL_from_pre-d3b2-retest.bin`, SHA-256 `dccd89144aea31408bca9519937382a838eb4c4c58b59a11272e207cf473aac1`, size 16,777,216.
- Procedure: fresh full-chip capture and reconciliation with D6; full write using `/tmp/flashrom-src/build/flashrom -p ch347_spi`; built-in Verify; independent 16 MiB readback; byte/hash comparison; firmware/APCB reparse and PE extraction.
- Expected effect: no-op replacement returns `EFI_SUCCESS`; cold boot distinguishes LZMA/FV reconstruction rejection from D6 SMU-unlock execution failure.
- Rollback: fresh capture plus known booted `/tmp/d3a_flash/pre_d3b2_retest.bin`, SHA-256 `e54709e8c3432271ff53501b519f3c5e4d0dd2db9aa2f6c7e63bdd86e9f8cd45`.
- Stop conditions: unexpected starting bytes, wrong chip/size, write/Verify failure, independent readback mismatch, parser failure, or PE extraction mismatch.
- Cold boot remains unrun after SPI verification.

## Hardware write and readback result (2026-09-12, Asia/Almaty)

- PASS: fresh pre-write capture `evidence/programmer/reads/20260912/d7/prewrite-d7.bin`, 16 MiB, SHA-256 `bd7689d6e2da32079878c507c472d5fc6d7208bc8f7dca208be4115c83d2db07`, is byte-identical to the independently verified D6 readback.
- PASS: flashrom detected Winbond `W25Q128.V`, wrote `0x000000..0xFFFFFF`, and reported `VERIFIED`.
- PASS: independent readback `evidence/programmer/reads/20260912/d7/postwrite-d7.bin`, SHA-256 `dccd89144aea31408bca9519937382a838eb4c4c58b59a11272e207cf473aac1`, is byte-identical to the exact D7 candidate.
- PASS: readback reparses with four FVs and matching PSP/BHD/APCB checksums. The existing CoreUnlock-slot FFS GUID/type remain unchanged.
- PASS: its PE32 payload extracted from the hardware readback has SHA-256 `074b361d48e1d395ec3810b3b34fc96a469b736ed04155321b52fec0507c61f1`, byte-identical to the intended no-op DXE.
- Evidence class: hardware-verified at SPI write/readback only.
- UNRUN: cold boot and x86 release. This result does not yet select between the reconstruction and D6-code hypotheses.
