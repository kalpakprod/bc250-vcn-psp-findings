# D10 early-DXE SMU unlock action log

## Build intent (2026-09-12, Asia/Almaty)

- Actor: root agent.
- Operator direction: `давай`, accepting the proposed D10 early-DXE step.
- Baseline for construction: hardware-verified D9R image
  `candidates/d9-smu-unlock-explicit-lzma/BC250_D9R_SMU_UNLOCK_EXPLICIT_LZMA_from_fresh-d8.bin`, SHA-256 `c46392ceca989f0bd558077bf07bc40490645710710d6c48c7d42e8eb328834d`.
- Change: replace only the existing 12,288-byte CoreUnlock-slot PE with a
  driver that calls the same D9R unlock/fixup immediately at DXE entry instead
  of registering `ReadyToBoot`.
- Expected effect: secure Q3 access becomes available earlier in DXE while the
  board otherwise boots identically to D9R.
- Failure path: initialization failure means this unlock is unsafe at initial
  dispatch; restore D9R and keep ReadyToBoot timing.
- Rollback: exact D9R candidate/readback and known-booted D8 capture.
- No hardware write is authorized by this build entry.

## Build and verification result (2026-09-12, Asia/Almaty)

- PASS: RELEASE X64 build produced a 12,288-byte early-unlock PE32, SHA-256 `1f921f07d9a785a6d357b997f97f2c57fed385f5dcfd91c03fc2499089d2ec21`.
- PASS: built `candidates/d10-early-dxe-smu-unlock/BC250_D10_EARLY_DXE_SMU_UNLOCK_from_d9r.bin`, size 16 MiB, SHA-256 `f9bf499d94c3da9ce9a3cb140519e3f73ca959296fed394090d1b649872b3f7d`.
- PASS: LZMA header is the D8/D9R hardware-accepted `5d000000011000420000000000`; decoded size `0x420010`.
- PASS: decompressed FV size unchanged and every decompressed byte outside the existing 12,288-byte CoreUnlock-slot PE is identical to D9R.
- PASS: four FVs, PSP/BHD/APCB checksums, signed-region identity, existing-slot metadata, and independent PE extraction.
- UNRUN: fresh post-D9R NVRAM rebase, SPI write/readback, cold boot, early-DXE unlock, secure-SMN readback, and VCN behavior.
- Before any write, take a fresh chip capture and rebase D10 if only NVRAM drift is present, as done for D9R.

## Hardware-cycle intent (2026-09-12, Asia/Almaty; before capture/write)

- Actor: root agent; operator approval: `прошивай`, referring to D10 and the explicitly stated fresh-NVRAM rebase procedure.
- Target: authorized board `BC250-01`; CH347T `1a86:55db` and Winbond `W25Q128.V` 16 MiB detected; board expected fully unpowered with clip attached.
- Procedure: capture the current D9R chip state; reconcile changes; rebuild D10R from that exact capture while changing only the CoreUnlock-slot PE; report and verify its deterministic hash; write it; flashrom Verify; independent readback; parser/checksum/PE extraction.
- Expected effect: move the already hardware-verified SMU unlock from ReadyToBoot to initial DXE dispatch, without any VCN/gasket/dom14/MMIO action.
- Rollback: fresh D9R capture and the existing byte-exact D9R readback.
- Stop conditions: payload-region drift outside expected NVRAM, wrong target, build invariant failure, write/Verify failure, readback mismatch, parser failure, or PE extraction mismatch.

## Fresh capture and D10R rebase result (2026-09-12, Asia/Almaty)

- PASS: fresh D9R capture `evidence/programmer/reads/20260912/d10/prewrite-d10.bin`, SHA-256 `a599bb6d1df994619f059c3c091fc3d2bf1677008278257633ccdb43a1a19f01`.
- PASS: versus the pre-boot D9R readback, exactly 32 bytes in one range `0x1A5D..0x1A7D` changed; all are below `0x20000`; PSP and DXE payload regions are byte-identical. Classified as expected NVRAM drift.
- PASS: built fresh D10R `candidates/d10-early-dxe-smu-unlock/BC250_D10R_EARLY_DXE_SMU_UNLOCK_from_fresh-d9r.bin`, SHA-256 `91340dad8f1a6ac57deb9d8cd749e0a2c0bd8ec62c1051aab476c3cd61bdbaf8`, size 16 MiB.
- PASS: explicit-size LZMA header, decompressed invariants, signed-region identity, four FVs, PSP/BHD/APCB checksums, and extracted early-unlock PE identity.
- STOP before write: the fresh rebase generated a new exact artifact hash. Per the firmware gate, this hash is reported for explicit confirmation before erasing the chip.

## D10R exact write approval (2026-09-12, Asia/Almaty; before write)

- Operator response: `прошивай`, approving the immediately preceding D10R path and SHA-256 `91340dad8f1a6ac57deb9d8cd749e0a2c0bd8ec62c1051aab476c3cd61bdbaf8`.
- Exact rollback: fresh hardware-booted D9R capture `evidence/programmer/reads/20260912/d10/prewrite-d10.bin`, SHA-256 `a599bb6d1df994619f059c3c091fc3d2bf1677008278257633ccdb43a1a19f01`.
- Proceed with full-chip write, built-in Verify, independent readback, byte comparison, parsers, and PE extraction.

## D10R hardware write and readback result (2026-09-12, Asia/Almaty)

- PASS: CH347T and Winbond `W25Q128.V` 16 MiB detected.
- PASS: flashrom wrote the complete image and reported `VERIFIED`.
- PASS: independent readback `evidence/programmer/reads/20260912/d10/postwrite-d10r.bin` is byte-identical to D10R, SHA-256 `91340dad8f1a6ac57deb9d8cd749e0a2c0bd8ec62c1051aab476c3cd61bdbaf8`.
- PASS: readback parser reports four FVs and matching PSP/BHD/APCB checksums.
- PASS: existing-slot PE extracted from readback has SHA-256 `1f921f07d9a785a6d357b997f97f2c57fed385f5dcfd91c03fc2499089d2ec21`, byte-identical to the intended early-unlock DXE.
- Evidence class: hardware-verified at SPI write/readback only.
- UNRUN: cold boot, initial-DXE unlock execution, secure-SMN readback, and VCN behavior.

## D10R cold boot and early-unlock result (2026-09-12 20:06 PKT)

- PASS: root independently reached a fresh mode1 Linux boot over SSH; uptime 0 minutes and active command line contains `amdgpu.bc250_vcn_mode=1`.
- PASS: Q3 test message returned `alive=True`; secure Q3 `0x2A` read SMN `0x0005A870` with status `0x01`, value `0x77`; Q3 remained `alive_after=True`.
- VERDICT: the immediate first-DXE SMU unlock is hardware-verified boot-safe and persists into Linux. D10R advances the unlock window earlier than D9R ReadyToBoot.
- Evidence boundary: no VCN gasket, isolation/reset, dom14, MMIO, ring, or codec operation was executed.
- Next experiment: D11 should retain D10R and add only the 56-write VCN bank-12 gasket program during early DXE, with no dom14 request or VCN MMIO. Boot plus Linux-side commit/liveness readback is the discriminator.
