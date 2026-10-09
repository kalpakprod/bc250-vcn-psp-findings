# D11 early-DXE VCN gasket action log

## Build and hardware-cycle intent (2026-09-12, Asia/Almaty; before writes)

- Actor: root agent; operator direction: `прошивай`, referring to the proposed D11 step.
- Target: authorized board `BC250-01`, expected fully unpowered with CH347T clip attached before SPI access.
- Change: D10R early SMU unlock plus only the 56-write VCN bank-12 gasket sequence. No power/clock thunk, donor dataplane, dom14 request, VCN MMIO, or mode2 action.
- Procedure: build the same-size PE; capture current D10R state; reconcile/rebase NVRAM; validate exact candidate; write with flashrom Verify; independent readback; parser and PE extraction.
- Expected effect: early boot programs/commits bank 12 while retaining a normal mode1 boot.
- Failure path: no initialization means the early-DXE gasket stage is unsafe or unavailable; restore the fresh D10R capture.
- Rollback: fresh pre-write D10R capture and prior verified D10R image.
- Stop conditions: wrong chip/size, unexpected firmware drift, build invariant failure, flash/readback mismatch, parser/extraction failure.

## Fresh capture and D11R build result (2026-09-12, Asia/Almaty)

- PASS: fresh D10R capture `evidence/programmer/reads/20260912/d11/prewrite-d11.bin`, SHA-256 `addef28800ce0102df4e207a28f0f671fa8c2b91e7d2c8864beb08dd1b6d85cd`.
- PASS: versus the D10R post-write readback, only 28 NVRAM bytes in three ranges `0x1A83..0x1AD7` changed; all below `0x20000`; PSP and DXE regions remain byte-identical.
- PASS: built `candidates/d11-early-dxe-gasket/BC250_D11R_EARLY_DXE_GASKET_from_fresh-d10r.bin`, size 16 MiB, SHA-256 `d39973744aa71efdccbb925639822080ed933b6cc7f70c6ea313a399f34ae305`.
- PASS: explicit-size LZMA header, decompressed bytes outside the replacement PE, signed-region identity, PSP/BHD/APCB checksums, four FVs, and extracted PE identity.
- STOP before erase: report the newly generated exact D11R hash for explicit operator confirmation.

## D11R exact write approval (2026-09-12, Asia/Almaty; before write)

- Operator response: `подтверждаю`, approving D11R SHA-256 `d39973744aa71efdccbb925639822080ed933b6cc7f70c6ea313a399f34ae305`.
- Exact rollback: fresh hardware-booted D10R capture `evidence/programmer/reads/20260912/d11/prewrite-d11.bin`, SHA-256 `addef28800ce0102df4e207a28f0f671fa8c2b91e7d2c8864beb08dd1b6d85cd`.
- Proceed with target detection, full write, built-in Verify, independent readback, parsers, and PE extraction.

## D11R hardware write and readback result (2026-09-12, Asia/Almaty)

- PASS: CH347T and Winbond `W25Q128.V` 16 MiB detected.
- PASS: flashrom wrote the full image and reported `VERIFIED`.
- PASS: independent readback `evidence/programmer/reads/20260912/d11/postwrite-d11r.bin` is byte-identical to D11R, SHA-256 `d39973744aa71efdccbb925639822080ed933b6cc7f70c6ea313a399f34ae305`.
- PASS: readback reports four FVs and matching PSP/BHD/APCB checksums.
- PASS: existing-slot PE extracted from readback has SHA-256 `978d4a4ac7f40409c7ceaf29b008974ae8e3537cae37dd28de5b9a6f740ad54e`, byte-identical to the intended early-unlock+gasket DXE.
- Evidence class: hardware-verified at SPI write/readback only.
- UNRUN: cold boot, early gasket execution, SMU liveness/secure access, bank-12 commit readback, domain status, and VCN behavior.

## D11R cold-boot result (2026-09-12, operator observation)

- PARTIAL/FAIL: the board powers on and displays the BIOS splash, but does not progress beyond the splash; Linux/network never becomes reachable (`Destination Host Unreachable` / SSH no route).
- Evidence class: operator-observed boot behavior plus root network check. POST/video and part of firmware initialization execute; OS release fails.
- Differential: D10R with the same early SMU unlock boots Linux; D11R adds only the 56-write early-DXE VCN gasket sequence. Therefore the added early gasket stage causes the post-splash boot failure at this timing.
- Inference boundary: without UART/status-code capture, the exact failing write is unknown. The likely classes are an early bank-12 transaction wedging SMU/fabric or a later firmware consumer encountering the partially programmed bank. This is not proof that all 56 writes completed or committed.
- STOP: do not wait indefinitely, boot mode2, read VCN MMIO, or repeat the same boot. Cold-power the board off and restore the fresh pre-D11 D10R capture.
- Rollback target: `evidence/programmer/reads/20260912/d11/prewrite-d11.bin`, SHA-256 `addef28800ce0102df4e207a28f0f671fa8c2b91e7d2c8864beb08dd1b6d85cd`.
- Method change: future BIOS candidate must not apply the full gasket at initial DXE. Bisect timing first (ReadyToBoot versus initial DXE), then bisect the sequence with a persistent progress marker/UART; never combine all 56 writes again without attribution.

## Rollback intent (2026-09-12, Asia/Almaty; before write)

- Operator response: `подклчбил`, confirming the board is unpowered and the programmer clip is attached in response to the explicit D10R restore procedure.
- Target: authorized BC250-01, CH347T/Winbond W25Q128.V expected.
- First capture the current D11R chip and require identity with its post-write readback. Then restore exact fresh pre-D11 D10R state `evidence/programmer/reads/20260912/d11/prewrite-d11.bin`, SHA-256 `addef28800ce0102df4e207a28f0f671fa8c2b91e7d2c8864beb08dd1b6d85cd`.
- Require flashrom Verify, independent full-chip readback, byte/hash comparison, and firmware/APCB parsing.
- Expected effect: return to the hardware-verified booting D10R early-SMU-unlock state.
- Stop conditions: unexpected current bytes, wrong target, write/Verify failure, readback mismatch, or parser failure.

## Rollback result (2026-09-12, Asia/Almaty)

- PASS with attribution: current D11R capture differed from the original D11R readback by 28 bytes in three ranges `0x1ACF..0x1AF3`, all below `0x20000`; PSP and DXE regions were byte-identical. This is boot-attempt NVRAM drift, not payload corruption.
- PASS: restored `evidence/programmer/reads/20260912/d11/prewrite-d11.bin`; flashrom reported `VERIFIED`.
- PASS: independent readback `evidence/programmer/reads/20260912/d11-rollback/post-rollback-d10r.bin` is byte-identical to the rollback image, SHA-256 `addef28800ce0102df4e207a28f0f671fa8c2b91e7d2c8864beb08dd1b6d85cd`.
- PASS: four FVs, PSP/BHD/APCB checksums, and extracted D10R early-unlock PE.
- Evidence class: hardware-verified SPI rollback/readback. Cold boot confirmation remains UNRUN.
