# BC-250 APCB VCN hardware trial

## Scope and authorization

- Timestamp: 2026-09-11T17:52:49+05:00 (Asia/Almaty).
- Actor: root Codex agent; physical operator: user.
- Target: operator-owned board `BC250-01`, SPI flash detected on the host as CH347T USB `1a86:55db`; expected chip Winbond `W25Q128.V`, 16 MiB, 3.3 V.
- Candidate: `/home/OWNER/orca/projects/bc250/candidates/BC250_APCB_DFG_only_v001_from_read-a.bin`, SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`, size 16,777,216 bytes.
- Preserved recovery baselines: `evidence/programmer/reads/20260911/read-a.bin` and `read-b.bin`, both SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`, byte-identical.
- Operator confirmation: board fully unpowered, BIOS battery removed, clip orientation checked, programmer configured for 3.3 V.
- Exact operator approval received: `Подтверждаю запись файла /home/OWNER/orca/projects/bc250/candidates/BC250_APCB_DFG_only_v001_from_read-a.bin SHA-256: 6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70 на плату BC250-01, только если новый полный дамп совпадёт с сохранённой базой. Плата полностью обесточена, клипса ориентирована правильно, программатор настроен на 3,3 В.`

## Pre-write intent

- Reacquire the pinned Arch `flashrom 1.8.0-1` package into `/tmp/bc250-flashrom-resume-tDCb0q/`, verify package SHA-256 `b3804df8cf3a44461deb03bd0ac2edc37d616edc28eb95a9a0d3b3c16cc48316`, detached signature against the Arch keyring, extracted binary SHA-256 `5ee0b2e4ea215a81ec08997dad99c469bd9f2335d5237d623388dee29875573c`, and `flashrom --version`.
- Run a read-only chip probe using `flashrom -p ch347_spi:spispeed=1.875M --flash-name`. Stop unless the result is Winbond `W25Q128.V`, 16 MiB.
- Take a new full pre-write dump to `evidence/programmer/reads/20260911/read-c-prewrite.bin` using `flashrom -p ch347_spi:spispeed=1.875M -r <path>`, preserve the flashrom log, hash it, and compare it byte-for-byte with both preserved recovery reads.
- Hard stop unless the fresh dump is exactly 16,777,216 bytes with SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0` and `cmp` succeeds against both prior reads.
- Re-run the deterministic candidate verifier to a new temporary output before writing. Stop on any failed check or candidate hash mismatch.
- If every gate passes, write exactly the approved candidate with `flashrom -p ch347_spi:spispeed=1.875M -w /home/OWNER/orca/projects/bc250/candidates/BC250_APCB_DFG_only_v001_from_read-a.bin` and preserve the complete output.
- Expected image effect: only absolute offsets `0xAB1010`, `0xAB1132`, and `0xAB116E` differ from stock; APCB checksum `F2 -> 32`; two DFG words `0x001FFF00 -> 0x007FFF00`. PSP, `$PS1`, BHD, FV/FFS, and NVRAM remain unchanged.
- Immediately after the write, take a separate complete readback at `evidence/programmer/reads/20260911/postwrite-apcb-v001.bin`, hash it, compare it byte-for-byte with the approved candidate, and run firmware/APCB parsers. Do not authorize board power-up unless readback and structure checks pass.
- Rollback: while the board remains unpowered and the programmer remains attached, write the preserved stock `read-a.bin`, then perform a complete readback and byte comparison. Stop on any programmer, identity, write, verify, or readback error.
- Claim boundary: a successful programmer verify/readback establishes only that candidate bytes reached the SPI flash. Boot, PSP acceptance, VCN power, rings, codec operation, and stability remain unverified until the operator performs cold boot and runtime checks.

## Tool reacquisition result

- Timestamp: 2026-09-11T17:54+05:00.
- Downloaded `flashrom-1.8.0-1-x86_64.pkg.tar.zst` and its detached signature from the previously recorded Omarchy/Arch mirror into `/tmp/bc250-flashrom-resume-tDCb0q/`.
- Package SHA-256 PASS: `b3804df8cf3a44461deb03bd0ac2edc37d616edc28eb95a9a0d3b3c16cc48316`.
- Signature PASS: `gpgv` reported a good signature under key fingerprint `05C7775A9E8B977407FE08E69D4C5AA15426DA0A`. No secret key material was accessed.
- Extracted binary SHA-256 PASS: `5ee0b2e4ea215a81ec08997dad99c469bd9f2335d5237d623388dee29875573c`.
- Version PASS: `flashrom v1.8.0 (git:v1.8.0)`.
- Host USB enumeration PASS: CH347T `1a86:55db` is present and `/dev/ttyACM0` exists. The earlier apparent absence was caused by the restricted sandbox hiding the device node; the host never lost the programmer.

## Fresh probe and pre-write read intent

- Exact probe command: `pkexec /tmp/bc250-flashrom-resume-tDCb0q/prefix/usr/bin/flashrom -p ch347_spi:spispeed=1.875M --flash-name`.
- If and only if the probe returns Winbond `W25Q128.V`, exact read command: `pkexec /tmp/bc250-flashrom-resume-tDCb0q/prefix/usr/bin/flashrom -p ch347_spi:spispeed=1.875M -r /home/OWNER/orca/projects/bc250/evidence/programmer/reads/20260911/read-c-prewrite.bin`.
- Preserve outputs at `evidence/programmer/probe-apcb-trial-20260911.log` and `evidence/programmer/reads/20260911/read-c-prewrite.flashrom.log`.

## Fresh probe and pre-write read result

- Probe PASS: `flashrom v1.8.0` detected Winbond `W25Q128.V` (16,384 KiB) at CH347 SPI clock 1.875 MHz. Probe log SHA-256 `c89588ff0a4889bf03d9ab2f7b12e0c56eb891c5f8746b5793f0664944c7cd1e`.
- Fresh complete read PASS: `evidence/programmer/reads/20260911/read-c-prewrite.bin`, 16,777,216 bytes, SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- `cmp` PASS against both preserved recovery reads; all three reads are byte-identical.
- Read log SHA-256 `bc00e08f69e24c06546757db93932d401622ed6ad558e246b502c6c4a5ae8175`.
- Candidate SHA-256 recheck PASS: `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`.
- Deterministic pre-write verification PASS: 14/14 checks; temporary result SHA-256 `4f92f2f779232d880419e3a8468f5b933093b4c42e0d7f9475b1f42c2882fc8e`.

## Exact firmware write intent

- Timestamp: 2026-09-11T17:57+05:00.
- All operator conditions and the fresh-baseline equality condition are satisfied.
- Exact command: `pkexec /tmp/bc250-flashrom-resume-tDCb0q/prefix/usr/bin/flashrom -p ch347_spi:spispeed=1.875M -w /home/OWNER/orca/projects/bc250/candidates/BC250_APCB_DFG_only_v001_from_read-a.bin`.
- Preserve full command output at `evidence/programmer/reads/20260911/write-apcb-v001.flashrom.log`.
- Stop on any erase, write, or built-in verification failure. Keep the board unpowered and programmer attached until a separate full-chip readback matches the candidate.

## Firmware write result and independent readback intent

- Timestamp: 2026-09-11T17:58:58+05:00.
- Write command exited 0. Observed sequence: chip detected as Winbond `W25Q128.V`; old contents read; `Erase/write done from 0 to ffffff`; flashrom built-in verify returned `VERIFIED`.
- Write log SHA-256: `17248ec2e3454a4a8a85ce9821251a26bda1fea9208becd5cd9ca32e5b6474ed`.
- Built-in verification is not the independent post-write readback. Board remains unpowered and the programmer remains attached.
- Exact independent readback command: `pkexec /tmp/bc250-flashrom-resume-tDCb0q/prefix/usr/bin/flashrom -p ch347_spi:spispeed=1.875M -r /home/OWNER/orca/projects/bc250/evidence/programmer/reads/20260911/postwrite-apcb-v001.bin`.
- Preserve output at `evidence/programmer/reads/20260911/postwrite-apcb-v001.flashrom.log`; then compare the entire 16 MiB image against the approved candidate, enumerate changed offsets relative to stock, and run the firmware/APCB parsers.

## Independent post-write readback result

- Timestamp: 2026-09-11T18:04:06+05:00.
- Full-chip readback PASS: `evidence/programmer/reads/20260911/postwrite-apcb-v001.bin`, 16,777,216 bytes, SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`.
- Candidate comparison PASS: readback is byte-identical to the approved candidate (`cmp` exit 0 and identical SHA-256).
- Stock comparison PASS for expected scope: exactly three offsets differ from the fresh pre-write dump: `0xAB1010`, `0xAB1132`, `0xAB116E`.
- Fresh pre-write dump remains preserved at SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- Firmware parser PASS: image size 16 MiB, PSP checksum match, BHD checksum match, APCB checksum match, four firmware volumes. Report SHA-256 `f788a8282931f4131a9f3fbab73f734dcce13b42a6c67caa52c1189b9b8b47c7`.
- APCB detail parser PASS: DFG words at APCB `+0x130/+0x16C` are both `0x007FFF00`. Report SHA-256 `e3f4556b47248259566464a076ad5958236f560c444a2a466033ed95e6dd1eb5`.
- Result classification: hardware-verified at programmer write/readback layer only. Boot, PSP acceptance, DXE/runtime state, VCN rings, codec functionality, and stability remain UNRUN.
- Rollback remains available from any of the three byte-identical stock reads while the programmer is attached.

## Evidence synchronization intent

- Preserve a machine-readable hardware-trial manifest under `evidence/programmer/reads/20260911/`, update `candidates/README.md`, and append the durable write/readback result to `memory/firmware-audit.md` and `memory/project-state.md`.
- Metadata/documentation only; no further hardware operation. Do not tell the operator to power the board until synchronization and final hash checks pass.

## Completion-state synchronization intent

- The prior completion matrix and hash-specific report still state that no flash occurred. Update them with the exact APCB write/readback result, mark only the programmer layer PASS, and retain cold-boot/runtime checks as UNRUN.
- Refresh affected artifact hashes and run JSON parsing, candidate/readback comparisons, firmware/APCB parser checks, contour tests, and `git diff --check` before handoff.
- Documentation and metadata only; no further hardware operation.

## Evidence synchronization and closing validation result

- Machine-readable trial manifest written and JSON-validated: `evidence/programmer/reads/20260911/apcb-v001-hardware-trial-manifest.json`, SHA-256 `e0488e8cc0d8d99c25b626ae08dec04db496256d20303fcaa03912b907c3e696`.
- Completion matrix updated: SHA-256 `dbc29323993677598b2f94b3d363bd4a868e6561f706f6fe0bb8e6c32e16cefb`; it marks the exact programmer write/readback PASS and boot/runtime UNRUN.
- Candidate catalog, project memory, firmware memory, report, and derived-artifact inventory were synchronized with the hardware result.
- Independent candidate/readback `cmp`: PASS.
- Deterministic audit-state verifier: 14/14 PASS; temporary result SHA-256 `84d345d0d60967f0adf898b526c322d2b6219733ae5550655ad404c4baf11cbd`.
- Contour validation: PASS (`contract_copies=4`, `skills=11`, `instincts=6`).
- Unit tests: 4/4 PASS. `git diff --check`: PASS. JSON parsing: PASS.
- Final state before operator handoff: the APCB candidate is present on SPI and independently read back byte-identical. The board has not been powered or booted after the write. The programmer/clip must be disconnected before restoring battery or normal board power.
- Next decisive evidence: operator cold boot and video-output observation; if Linux boots, collect VCN discovery, firmware, ring, codec, and error logs without using write-capable SMU helpers.

## First cold-boot observation and stop decision

- Timestamp: 2026-09-11T18:13:25+05:00.
- Operator report after disconnecting the programmer and attempting the first candidate boot: green and blue indicators illuminate; a red indicator between USB and Ethernet is illuminated; no display image is observed.
- Evidence class: operator-observed hardware behavior. No POST code, UART trace, network reachability, keyboard state, or Linux log is available, so execution stage and root cause are inconclusive.
- User-visible video-output check: FAIL for this boot attempt. Candidate boot/PSP acceptance: INCONCLUSIVE, because LEDs establish power-rail/status activity only and do not prove x86/UEFI execution.
- Stop condition triggered. Operator is instructed to remove normal power and avoid repeated candidate boot cycles.
- Recommended next action: restore the exact preserved stock image and independently read it back before another boot. This rollback is a new firmware write and requires explicit exact operator approval plus reconfirmation that the board is fully unpowered, battery removed, clip orientation correct, and programmer at 3.3 V.
- No causal claim is made yet. If stock restores video under the same display setup, the candidate change becomes the discriminating cause at the boot/video layer; if stock also has no video, investigate cabling/output/board state separately.
