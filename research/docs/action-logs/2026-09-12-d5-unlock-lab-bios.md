# D5 SMU-Unlock Lab BIOS action log

## Build intent (2026-09-12, Asia/Almaty)

- Actor: root agent.
- Operator request: build a BIOS with the highest reasonable probability of
  booting while retaining an unlock substrate for new VCN research vectors.
- Exact source target: `/tmp/d3a_flash/pre_d3b2_retest.bin`, size 16,777,216,
  MD5 `5ccde448e90c67e2afde0478da9756e8`, SHA-256
  `e54709e8c3432271ff53501b519f3c5e4d0dd2db9aa2f6c7e63bdd86e9f8cd45`.
- Planned output: `candidates/d5-smu-unlock-lab/BC250_D5_SMU_UNLOCK_LAB_from_pre-d3b2-retest.bin`.
- Procedure: copy the exact source; build an X64 RELEASE DXE driver that runs
  only the previously hardware-verified BIOS-3 SMU debug unlock and fixup;
  insert one FFS into the unsigned x86 DXE FV; parse and independently compare
  the result.
- Reason: signed-policy D3-B2 and signed-SMU D4 hard-failed. A DXE-only change
  avoids all signed PSP bodies and removes known boot-time VCN wedge actions.
- Expected effect: normal PSP/ABL/SMU/TOS initialization, then a bounded SMU
  unlock during DXE, followed by ordinary OS boot. VCN is not expected to be
  enabled automatically.
- Rollback: full-chip writeback of `/tmp/d3a_flash/pre_d3b2_retest.bin`, with
  flashrom verify and an independent 16 MiB readback comparison.
- Stop conditions: any change outside the intended x86 FV, any PSP/APCB/SMU
  difference, malformed PE/FFS/FV, build failure, or inability to recover the
  injected FFS independently.
- Hardware write is not part of this action. Bootability, DXE dispatch, unlock
  persistence, VCN MMIO, rings, and codecs remain unrun.

## Build and verification result (2026-09-12, Asia/Almaty)

- RESULT: D5 was built as an offline candidate. No flash or hardware action occurred.
- Output: `candidates/d5-smu-unlock-lab/BC250_D5_SMU_UNLOCK_LAB_from_pre-d3b2-retest.bin`, size 16,777,216, SHA-256 `dec17ca81f513c28fa5a3227b3745c4c6ceb6aba68fe3d24fce8110df54ae3f1`.
- DXE payload: `Bc250SmuUnlockDxe.efi`, size 12,288, SHA-256 `f8774ab43ece688da6ef96c28f606a92b43a1927d4abab1397a6c310e4bd76e2`; FFS SHA-256 `daaa4fc102fb512b4af7b1646d82686c3f1f02e1eb561804dd9949d88f732a1a`.
- Implementation: the DXE entry point registers a `ReadyToBoot` callback. The callback runs only `PerformSmuUnlockDxe()` and publishes the existing protocol on success. Automatic power, clock, gasket, donor dataplane, dom14, PCI-command, and VCN-MMIO operations are disabled. Dormant routines remain linked behind a volatile false gate for future single-variable lab variants.
- Build command: `build -a X64 -t GCC -b RELEASE -p Bc250VcnUnlockPkg/Bc250VcnUnlockPkg.dsc -m Bc250VcnUnlockPkg/Bc250VcnUnlockDxe/Bc250VcnUnlockDxe.inf`; GCC 16.2.1, Python 3.14.7, EDK II `GenFw 0.2 Developer Build`, NASM 3.02. NASM package SHA-256: `3a749b14839e1ea665e42b991fa15dfb6e9fc871b8bf4f8a48a40b789edcf579`.
- PASS: EDK II RELEASE build; PE32+ X64 EFI boot-service driver; FFS type 7, GUID `B6250780-7E00-4203-900C-23443B1413FE`, TRUE/END Depex, UI `Bc250SmuUnlockDxe`.
- PASS: independent output reparse found four FVs and extracted exactly one byte-identical DXE payload.
- PASS: PSP Fletcher32 `0x63FFFCC8`, BHD Fletcher32 `0xECE7B2E6`, and APCB checksum `0x32` all match.
- PASS: the entire `0x8E0000..0xAE0000` PSP/BHD/APCB area is byte-identical to the selected booted baseline. No signed PSP, SMU, ABL, TOS, gasket, or policy byte changed.
- PASS: all 1,333,688 changed bytes in 5,267 ranges are confined to the recompressed x86 DXE FV at `0xAE0088..0xC26F0C`. Recompression explains the broad byte diff; the semantic payload delta is one inserted FFS.
- Reports: `build-manifest.json`, `changed-ranges.json`, `firmware-audit.json`, `apcb-detail.json`, `pe-objdump.txt`, and `edk2-build.log` in the candidate directory.
- UNRUN: BC-250 cold boot, DXE dispatch, ReadyToBoot completion, SMU unlock readback, VCN MMIO, rings, and codec behavior. QEMU cannot model the BC-250 SMU exploit or SMN mailboxes.
- Remaining uncertainty: DXE FV reconstruction has not been cold-booted with corrected display wiring. The historical E1 result was confounded by incorrect display wiring and does not settle D5.

## Hardware write intent (2026-09-12, Asia/Almaty; before write)

- Actor: root agent; operator approval: `прошивай`, referring to the immediately preceding exact D5 artifact and hash.
- Physical target: authorized board `BC250-01`; detected programmer CH347T USB `1a86:55db`; detected flash chip Winbond `W25Q128.V`, 16 MiB; board is expected fully unpowered with the SOIC8 clip attached.
- Exact candidate: `candidates/d5-smu-unlock-lab/BC250_D5_SMU_UNLOCK_LAB_from_pre-d3b2-retest.bin`, SHA-256 `dec17ca81f513c28fa5a3227b3745c4c6ceb6aba68fe3d24fce8110df54ae3f1`, size 16,777,216.
- Tool: `/tmp/flashrom-src/build/flashrom`, `flashrom v2.0.0-devel`, programmer `ch347_spi` at its reported 15 MHz clock.
- Procedure: capture the current full chip into a new file; hash and reconcile it with the expected D4 state; write the exact D5 image; require flashrom built-in verify; perform a second independent full-chip readback; compare its SHA-256 and bytes against D5.
- Expected effect: restore the previously booted PSP/APCB/NVRAM baseline and dispatch the unlock-only DXE at ReadyToBoot. No automatic VCN activation is expected.
- Rollback: the fresh pre-write capture plus `/tmp/d3a_flash/pre_d3b2_retest.bin` (SHA-256 `e54709e8c3432271ff53501b519f3c5e4d0dd2db9aa2f6c7e63bdd86e9f8cd45`).
- Stop conditions: wrong chip/size, current-chip capture cannot be reconciled, write or built-in verify failure, independent readback mismatch, or structural parser failure.
- Post-write cold boot remains an operator action after removing the clip. Bootability and SMU unlock are not established by the SPI write/readback.

## Hardware write and readback result (2026-09-12, Asia/Almaty)

- PASS: fresh pre-write capture completed: `evidence/programmer/reads/20260912/d5/prewrite-d5.bin`, size 16,777,216, SHA-256 `7d76aebda1cf9fe24810a4fc2794575186743015a9894bf6a03c5dbe3a741005`.
- PASS: the fresh capture is byte-identical to `/tmp/d3a_flash/readback_d4.bin`; the expected non-booting D4 state was therefore reconciled before writing.
- PASS: flashrom detected Winbond `W25Q128.V` 16 MiB, erased/wrote `0x000000..0xFFFFFF`, and reported `VERIFIED`.
- PASS: independent full-chip readback `evidence/programmer/reads/20260912/d5/postwrite-d5.bin` has SHA-256 `dec17ca81f513c28fa5a3227b3745c4c6ceb6aba68fe3d24fce8110df54ae3f1` and is byte-identical to the exact D5 candidate.
- PASS: parser on the hardware readback reports four FVs; PSP/BHD/APCB checksums all match; the injected FFS is type 7 with GUID `B6250780-7E00-4203-900C-23443B1413FE`.
- PASS: the DXE payload independently extracted from the hardware readback has SHA-256 `f8774ab43ece688da6ef96c28f606a92b43a1927d4abab1397a6c310e4bd76e2`, byte-identical to the built EFI.
- Evidence class: hardware-verified at SPI write/readback layer only.
- UNRUN: cold boot, x86 release, DXE dispatch, ReadyToBoot callback, SMU unlock readback, VCN MMIO, rings, and codecs.
- Recovery: both the fresh D4 capture and the known booted `pre_d3b2_retest.bin` remain preserved. The intended rollback target after a D5 boot failure is `pre_d3b2_retest.bin`, not D4.

## Cold-boot result (2026-09-12, operator observation)

- FAIL: after removing the programmer clip, assembling, and powering the board,
  the operator reports `нет инициализации, индикаторы статичны`.
- The exact D5 bytes on SPI were independently verified before this boot, so
  an incomplete flash write is excluded for this attempt.
- The claimed layer is limited: x86/OS boot failed by external observation.
  Without UART/status-code capture, this does not distinguish failure while
  parsing/dispatching the reconstructed DXE FV from a hang inside the
  ReadyToBoot SMU unlock callback.
- CORRECTION: D5 must not be described as a higher-probability booting image
  after this measurement. The broad LZMA FV reconstruction remains a shared
  unverified mechanism with historical E1; the unlock callback is a second
  changed variable. This candidate therefore cannot attribute the failure.
- Decision: do not repeat this bulk-FV/automatic-DXE class. Restore the known
  booted `pre_d3b2_retest.bin` first. Any next unlock vector must use a
  different method class: an externally loaded UEFI application or a
  byte-local/in-place FFS replacement that avoids rebuilding 1.33 MiB of the
  compressed FV, with UART/status evidence if automatic execution is retried.
- Rollback target: `/tmp/d3a_flash/pre_d3b2_retest.bin`, SHA-256
  `e54709e8c3432271ff53501b519f3c5e4d0dd2db9aa2f6c7e63bdd86e9f8cd45`.
- Rollback remains UNRUN pending the board being fully unpowered and CH347T
  `1a86:55db` visible with the clip attached.
