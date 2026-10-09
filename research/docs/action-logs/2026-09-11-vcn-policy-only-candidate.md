# BC-250 VCN policy-only candidate

## Build intent

- Timestamp: 2026-09-11T19:12+05:00.
- Actor: root Codex agent; no delegated writer.
- Goal: remove the common APCB DFG change from the combined D3-B2 candidate while retaining both reviewed VCN policy carriers.
- Existing route: reuse the verified D3-B2 artifact and existing structural verifier. A new small builder is required because the historical tools do not provide a stock-APCB combined-policy variant.
- Inputs: exact stock SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`; exact D3-B2 SHA-256 `439e248141ef6a9c1313bc7815696d570be8fed5471262596186f3da8914747d`.
- Transformation: start from the reviewed D3-B2 candidate and replace the entire APCB range `0xAB1000..0xAB1B6F` with the stock APCB bytes. All PSP directory and policy-carrier bytes remain identical to D3-B2.
- Expected discriminator: a boot would implicate the APCB change and permit direct VCN checks; repeated no-display would implicate the policy relocation/signature branch more strongly. Neither outcome proves VCN function without runtime evidence.
- Output must be a new candidate and manifest; no hardware operation is authorized by this build.
- Rollback: delete only generated offline artifacts. Stock recovery remains preserved.
- Acceptance: deterministic hash, exact diff confinement, stock-identical APCB, D3-B2-identical policy regions, PSP/BHD/APCB parser checks, policy structural checks, negative tests, and independent review.

## Build and root verification result

- Built `candidates/BC250_VCN_policy_only_v001_from_read-a.bin`, 16 MiB, SHA-256 `8cd9d19912ad80d2d6a8c5a1ca1a25379054f80f4c62ff528643e0a8193921b1`.
- Builder: `scripts/build_vcn_policy_only_candidate.py`, SHA-256 `30505bc7467e995d60979902e5d95939bb14bbf8498b2c0a8abefe387af8f331`.
- Exact change versus D3-B2: restore complete stock APCB; this removes only absolute differences `0xAB1010`, `0xAB1132`, and `0xAB116E`. Policy and PSP-directory regions are byte-identical to D3-B2.
- Diff versus stock: 13,733 bytes in 329 contiguous ranges, confined to PSP directory and relocated policy carriers.
- General firmware parser PASS; PSP/BHD/APCB checksums match and four FVs remain valid. Report SHA-256 `f9f3ca1b3f9d9018df947e7aabd6b330b83c188448008316e21fd2b5a5cbab81`.
- APCB parser PASS with stock DFG words `0x001FFF00`. Report SHA-256 `0bcab1b66c1c8d31899455d05fa1581e893b5dbbc65d14e25e7de7d6c97036d7`.
- Policy/D3 structural verifier PASS 26/26 in `stock` APCB mode. Report SHA-256 `6a3f55eaa63ba530d9d2d912dcba5d6fdfdc707507e1b1813bd7aab04af0cc3c`.
- Negative tests PASS: wrong stock hash and wrong D3-B2 input hash were rejected before output creation.
- Candidate is static only. PSP acceptance, boot, display, and VCN behavior are UNRUN.

## Independent review dispatch intent

- Bounded task: review only the policy-only candidate delta, builder, reports, inherited D3-B2 policy/signature risk, and its value as the next hardware discriminator.
- Reviewer: existing Orca Claude Code terminal, Anthropic Claude Opus family; effective model/effort must be disclosed in the return report. Permissions remain bypass at terminal level but task permission is read-only except one review file.
- Acceptance: recompute stock/D3-B2/output hashes; prove complete APCB stock identity; prove policy/directory identity to reviewed D3-B2; validate parsers/checksums/diff; assess whether this is a true one-variable comparison; mark PASS/FAIL/INCONCLUSIVE/UNRUN and return `APPROVE_FOR_HARDWARE_TRIAL` or `REJECT`.
- Return artifact: `evidence/candidates/BC250_VCN_policy_only_v001/independent-review-claude-opus.md`. No hardware access or other file writes.

## Independent review dispatch receipt

- Existing Orca Claude terminal accepted the prompt and started a new turn.
- Terminal handle: `term_4271dcd6-ee99-4458-a765-385e2a9173e3`; request ID `ff69be1f-b11e-4ca3-860c-5b75278719d4`; stages `input_accepted`, `turn_started`.
- Receipt is not a review finding. Hardware gate remains pending until root reads and verifies the completed report.

## Independent review result and root verification

- Review artifact: `evidence/candidates/BC250_VCN_policy_only_v001/independent-review-claude-opus.md`, SHA-256 `07de7fda571bfb8d2d4e3cd4e406cf41a080bd97eaf0171b36c52944467d21af`.
- Reviewer: Anthropic Claude Opus 4.8 (1M context), numeric effort not exposed; different-author/family review gate satisfied.
- Recommendation: `APPROVE_FOR_HARDWARE_TRIAL`, bounded to a controlled programmer-backed experiment only; no safety, bootability, signature, or VCN claim.
- Independent review confirms entire APCB is stock, policy/directory regions equal reviewed D3-B2, candidate-versus-D3-B2 delta is exactly the three APCB bytes, and candidate-versus-stock diff is 13,733 bytes confined to directory/policy regions.
- Root read the report to EOF, recomputed report/candidate/current-chip hashes, and reran the verifier in stock-APCB mode: 26/26 PASS; temporary result SHA-256 `6fc025990157e22f0daefe21a875af41026ebec7fb3c0ac5cb8e952093cd531f`.
- Critical inherited risk remains stale signature material over modified/grown `$PS1` payloads. A repeated no-display result will not prove policy causality; the precommitted next control is fresh-baseline signed-gasket relocation without payload or APCB changes.
- Hardware trial is still blocked on a fresh current-chip capture, exact file/hash/board approval, and explicit physical-isolation confirmation. The operator's general statement `разрешаю прошить` does not name the exact artifact/hash and therefore does not satisfy the exact write gate.

## Exact hardware authorization and pre-write capture intent

- Timestamp: 2026-09-11T19:51:46+05:00.
- Operator explicitly authorizes `/home/OWNER/orca/projects/bc250/candidates/BC250_VCN_policy_only_v001_from_read-a.bin`, SHA-256 `8cd9d19912ad80d2d6a8c5a1ca1a25379054f80f4c62ff528643e0a8193921b1`, for `BC250-01`, conditional on a fresh full dump of the current D3-B2 state.
- Operator also authorizes emergency rollback to `/home/OWNER/orca/projects/bc250/evidence/programmer/reads/20260911/read-a.bin`, SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`, only on write/readback failure.
- Physical confirmation: board fully unpowered, battery removed, clip orientation correct, programmer at 3.3 V.
- Host/tool recheck PASS: CH347T `1a86:55db` present; flashrom binary SHA-256 `5ee0b2e4ea215a81ec08997dad99c469bd9f2335d5237d623388dee29875573c`; candidate/rollback hashes match authorization.
- Probe command: `pkexec /tmp/bc250-flashrom-resume-tDCb0q/prefix/usr/bin/flashrom -p ch347_spi:spispeed=1.875M --flash-name`. Stop unless Winbond `W25Q128.V`, 16 MiB is detected.
- Fresh capture command: `pkexec /tmp/bc250-flashrom-resume-tDCb0q/prefix/usr/bin/flashrom -p ch347_spi:spispeed=1.875M -r /home/OWNER/orca/projects/bc250/evidence/programmer/reads/20260911/read-e-prewrite-policy-only.bin`.
- Required reconciliation: new read must be byte-identical to D3-B2 readback SHA-256 `439e248141ef6a9c1313bc7815696d570be8fed5471262596186f3da8914747d`. Any mismatch is a stop.
- Preserve probe/read logs, rerun policy-only verifier 26/26, then record exact write intent before `-w`.

## Fresh capture result and exact write intent

- Probe PASS: Winbond `W25Q128.V`, 16 MiB, CH347 SPI 1.875 MHz. Probe log SHA-256 `c89588ff0a4889bf03d9ab2f7b12e0c56eb891c5f8746b5793f0664944c7cd1e`.
- Fresh full capture PASS: `evidence/programmer/reads/20260911/read-e-prewrite-policy-only.bin`, 16 MiB, SHA-256 `439e248141ef6a9c1313bc7815696d570be8fed5471262596186f3da8914747d`.
- Current-state reconciliation PASS: byte-identical to the verified D3-B2 candidate/readback; no unexplained chip state.
- Policy-only candidate hash PASS: `8cd9d19912ad80d2d6a8c5a1ca1a25379054f80f4c62ff528643e0a8193921b1`.
- Pre-write structural verification PASS 26/26; temporary result SHA-256 `e9aaea683bb9919e42b6bc39ec3b9ef06f455adba0963a3faf8bef77e3518437`.
- Exact authorized write command: `pkexec /tmp/bc250-flashrom-resume-tDCb0q/prefix/usr/bin/flashrom -p ch347_spi:spispeed=1.875M -w /home/OWNER/orca/projects/bc250/candidates/BC250_VCN_policy_only_v001_from_read-a.bin`.
- Preserve write output at `evidence/programmer/reads/20260911/write-policy-only-v001.flashrom.log`. Keep the board unpowered/programmer attached for an independent full readback; trigger the pre-authorized stock rollback only on write/readback failure.

## Write result and independent readback intent

- Timestamp: 2026-09-11T19:59:06+05:00.
- flashrom write exited 0: Winbond `W25Q128.V` detected, full erase/write completed, built-in verification returned `VERIFIED`.
- Write log SHA-256 `17248ec2e3454a4a8a85ce9821251a26bda1fea9208becd5cd9ca32e5b6474ed`.
- Board remains unpowered and programmer attached. Exact independent readback command: `pkexec /tmp/bc250-flashrom-resume-tDCb0q/prefix/usr/bin/flashrom -p ch347_spi:spispeed=1.875M -r /home/OWNER/orca/projects/bc250/evidence/programmer/reads/20260911/postwrite-policy-only-v001.bin`.
- Preserve read log, compare the entire image with the authorized candidate, and run firmware/APCB/policy verifiers before power-up.


## Independent post-write readback result

- Timestamp: 2026-09-11T20:34:38+05:00.
- Full-chip readback PASS: `evidence/programmer/reads/20260911/postwrite-policy-only-v001.bin`, 16,777,216 bytes, SHA-256 `8cd9d19912ad80d2d6a8c5a1ca1a25379054f80f4c62ff528643e0a8193921b1`.
- Candidate comparison PASS: readback is byte-identical to the exact authorized candidate (`cmp` exit 0 and matching SHA-256).
- General firmware parser PASS: PSP Fletcher32 `0x9F717AB8`, BHD Fletcher32 `0xECE7B2E6`, APCB checksum byte `0xF2`, and four firmware volumes remain valid. Report SHA-256 `68ca6f52ffb032ea317a9b609982a03adefda426d83cd1ae6f9f91fc92ce19be`.
- APCB detail parser PASS: DFG words at `+0x130/+0x16C` are both stock `0x001FFF00`. Report SHA-256 `2c6221c1054157c6c43021e186af45f48d80ae58ad28531800e68700ddbcc270`.
- Policy-only structural verifier PASS 26/26 in `stock` APCB mode on the physical readback, including `apcb_block_stock_identity` and `diff_confinement`. Report SHA-256 `26a52645c6fe746ae9cbdafacada234ea05ac000cfaaa1403d37ee0e542c2810`.
- No emergency rollback was triggered because write and independent readback passed. Stock recovery remains preserved and authorized only for the stated failure condition.
- Result classification: hardware-verified at SPI write/readback layer only. PSP acceptance, boot/video, VCN power/MMIO/rings/codecs, and stability remain UNRUN.

## Hardware-trial evidence synchronization result

- Machine-readable manifest: `evidence/programmer/reads/20260911/policy-only-v001-hardware-trial-manifest.json`, SHA-256 `8078820cb06eee86009d06f29d5fc1c02a1a7f26cd1902e88d56ccb58db4f4b9`.
- Board may now proceed to the authorized cold-boot/video observation; record the exact power-up procedure, indicator pattern, display result, and post-boot readback decision separately.

## Policy-only cold-boot observation and stop decision

- Timestamp: 2026-09-11T20:39+05:00.
- Operator report after disconnecting the programmer and one cold boot: green and blue indicators on; red indicator between USB and Ethernet on; no link/activity LEDs on the Ethernet jack itself; fan spins at normal speed; no display image observed.
- Evidence class: operator-observed hardware behavior. No POST code, UART trace, network reachability, keyboard state, or Linux log is available, so execution stage and root cause are inconclusive.
- User-visible video-output check: FAIL for this boot attempt. Candidate boot/PSP acceptance: INCONCLUSIVE, because LEDs and fan establish power/status activity only and do not prove x86/UEFI execution.
- Comparison: identical outcome to the prior APCB-only and combined D3-B2 attempts (same indicator pattern, no display). The restored stock APCB did not change the video result, so the APCB DFG change is not the discriminating cause at the boot/video layer. Focus shifts to the PSP policy relocation/signature branch shared by D3-B2 and policy-only.
- Stop condition triggered. Operator is instructed to remove normal power and avoid repeated candidate boot cycles.
- No rollback was performed. Restoring the exact preserved stock image is a new firmware write and requires explicit exact operator approval plus reconfirmation that the board is fully unpowered, battery removed, clip orientation correct, and programmer at 3.3 V.

## VCN unlock synthesis (research only, no flash)

- Timestamp: 2026-09-11T20:55+05:00.
- Intent: reread full VCN-lock corpus + 4 worker reports, list real holes/exploits and ranked sequence. No candidate built, no hardware touched.
- Sources: VCN-LOCK-MECHANISM.md (55,977 B), doc 10 runtime recipe (14,404 B), CORRECT-CHAIN (12,164 B), EXPLOIT-SPEC (3,310 B), vuln-1 (4,755 B), vuln-2 (3,328 B), worker1 6,325 B / worker2 10,497 B / worker3 8,241 B / worker4 9,662 B.
- Key correction (G7): historical VULN-002 expectation that APCB-DFG-only edit boots (false-negative, VCN dead) is DISPROVED on BC250-01 — our APCB-only flash gave the same no-video as PSP-touching variants. Cause open (PSP-side APCB consumer vs memory-init break).
- Main finding: 3 identical no-video results point to PSP RSA-2048 halt on relocated/modified $PS1 carriers (stale 0x100 tails). Skipped discriminator: historical ladder prescribed D3-C signed-relocation first; it was never flashed.
- Ranked next: S1 D3-C signed relocation (flash) / S2 C2P runtime 0x100B-0x100C-0x1033 (no flash, needs bootable OS) / S3 Q3 0x98 replay / S4 patched kernel 1.92 / S5 in-place single-value edit.
- Report: `docs/research/2026-09-11-vcn-unlock-synthesis.md`, SHA-256 eac7b372e0216205ae943cf4ee7fe35ee14138cc9db46e1262062e569cd7e6dc.

## Fast VCN-on exploit loop intent (no flash yet)

- Timestamp: 2026-09-11T21:05+05:00.
- Operator order: build VCN-on firmware now, skip kernel builds, fast flash-test loop. No stock restore.
- G6 breaker: 3 same-class unsigned-relocation no-video failures. Next builds change method class, not repeat.
- Track E1 (fastest, bootable): UEFI/DXE-region only VCN unlock from read-a.bin (no PSP/APCB touch, community-proven region 0xAE0088..). If it boots, VCN path attempted in DXE.
- Track E2 (brute VCN-on): maximal donor transplant stage A+B+C in new carriers from read-a.bin (VCN bank + DF + IOHC + NBIO + fabric). Expected no-video risk accepted by operator.
- Both tracks: new output files only, source read-a.bin SHA 83c4e420..., structural hash/parse only (30 sec), no kernel/emulator gate. Flash approval requested separately with exact hash+command.
- No hardware touched by this entry.

## E1 DXE-only candidate built and root-verified (no flash)

- Timestamp: 2026-09-11T21:10+05:00.
- Source: `evidence/programmer/reads/20260911/read-a.bin` SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- Output: `candidates/BC250_VCN_DXE_only_v001_from_read-a.bin` SHA-256 `9d0f7ca14952369833f8f87f9092cad4edd27df62f01d0df28b20d55c49eb497`, 16 MiB.
- Change: 1,333,711 bytes across 5,245 ranges, confined to DXE region 0xAE0088..0xC26F0B. PSP and APCB byte-identical to stock (worker + root checks agree).
- Root direct test (G2): `firmware_audit.py` PASS (PSP 0x63FFFCC8, BHD 0xECE7B2E6, APCB 0xF2, 4 FVs); `apcb_detail.py` PASS (DFG words stock 0x001FFF00). Reports `e33cef4d285ea5be61b2b6b777012e38c1ea3f19ea38d54f08568320c1ea3f19ea38d54f08568320c85b5319` / `5908ff064d721a9a1a1fc5c551e9440150b427966523cfb6a86ffb683ec038b3`.
- Claim boundary: structural only. PSP acceptance N/A (untouched), boot/video/VCN UNRUN. Flash NOT approved; needs exact operator approval with hash+command.

## Correction: E2 fulltransplant duplicates existing D3-B2 (G7)

- E2 output `candidates/BC250_VCN_fulltransplant_v001_from_read-a.bin` SHA-256 `439e248141ef6a9c1313bc7815696d570be8fed5471262596186f3da8914747d` is byte-identical (`cmp`) to the already-flashed `candidates/BC250_VCN_D3B2_combined_v001_from_read-a.bin`.
- It is therefore NOT a new maximal transplant; the A+B+C donor values were not actually added beyond the old D3-B2. Rejected as a separate flash track. A true stage-C build must diff against D3-B2 with new IOHC/NBIO/fabric values, not rebuild it.

## E1 flash pre-write intent (approval received)

- Timestamp: 2026-09-11T21:15+05:00.
- Operator approval: explicit "da" for E1 flash in chat.
- Target: board BC250-01, chip Winbond W25Q128.V, backend ch347_spi 1.875M, binary /tmp/bc250-flashrom-resume-tDCb0q/prefix/usr/bin/flashrom, SHA-256 5ee0b2e4ea215a81ec08997dad99c469bd9f2335d5237d623388dee29875573c.
- Candidate: `candidates/BC250_VCN_DXE_only_v001_from_read-a.bin` SHA-256 `9d0f7ca14952369833f8f87f9092cad4edd27df62f01d0df28b20d55c49eb497`. PSP/APCB untouched, DXE-region only.
- Procedure: 1) board fully unpowered, battery removed, clip attached with orientation check, programmer 3.3V; 2) fresh pre-write full capture to `evidence/programmer/reads/20260911/read-f-prewrite-dxe-only.bin` + hash; 3) write candidate, preserve log to `write-dxe-only-v001.flashrom.log`; 4) independent full readback to `postwrite-dxe-only-v001.bin` + hash/cmp/parsers. No power-up until readback PASS.
- Expected: flashrom exit 0 + VERIFIED, readback byte-identical to candidate, PSP/BHD/APCB checksums match stock values.
- Rollback: preserved `read-a.bin` SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`; rollback is a separate write requiring new exact approval. Trigger rollback only on write/readback failure.
- No hardware touched by this entry. Awaiting operator reconfirmation of power/battery/clip/voltage + pre-write capture result.

## E1 flash write + independent readback result

- Timestamp: 2026-09-11T21:20+05:00.
- Pre-write: `read-f-prewrite-dxe-only.bin` SHA-256 `8cd9d19912ad80d2d6a8c5a1ca1a25379054f80f4c62ff528643e0a8193921b1` (policy-only on chip, as expected).
- Write: flashrom exit 0, `VERIFIED`. Log preserved.
- Readback: `postwrite-dxe-only-v001.bin` SHA-256 `9d0f7ca14952369833f8f87f9092cad4edd27df62f01d0df28b20d55c49eb497`, byte-identical to candidate (`cmp` IDENTICAL).
- Parsers on readback: PSP 0x63FFFCC8 match, BHD 0xECE7B2E6 match, APCB 0xF2 match, 4 FVs, DFG stock words. Reports preserved.
- Claim: hardware-verified at SPI write/readback layer only. Boot/video/VCN UNRUN. Board unpowered, programmer attached.

## E1 DXE-only cold-boot observation and stop decision

- Timestamp: 2026-09-11T21:25+05:00.
- Operator report after disconnecting programmer and one cold boot: same pattern as all prior attempts (green/blue on, red USB/Ethernet on, no Ethernet jack LEDs, fan normal, no display image).
- Evidence class: operator-observed hardware behavior. No POST/UART/network/Linux evidence, so stage and cause INCONCLUSIVE.
- Video: FAIL. Boot/PSP: INCONCLUSIVE.
- Comparison: 4th identical no-video (APCB-only, D3-B2, policy-only, DXE-only). DXE-region edit did not discriminate either — even PSP/APCB-untouched image gives no video on this boot path. Next discriminator: verify stock still boots (needs operator decision), or change method class to runtime-only probes on a booted OS.
- Stop: remove power, no repeated cycles. No rollback performed (operator declined stock restore).

## Stock restore intent (operator: stock boots, build normal BIOS)

- Timestamp: 2026-09-11T21:30+05:00.
- Operator statement: stock boots; task = build normal (bootable) BIOS with VCN.
- Plan: 1) restore stock read-a.bin SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0` to recover video; 2) independent readback + parsers; 3) cold-boot confirm video; 4) build minimal bootable VCN candidates (1-byte NVAR probe first, then proper FFS-insert DXE).
- G6 method change: E1 1.3MB DXE rewrite did not boot despite untouched PSP/APCB — bulk FV rewrite class abandoned; switch to single-variable / single-FFS class.
- No hardware touched by this entry.

## Stock restore write + readback result

- Timestamp: 2026-09-11T21:35+05:00.
- Write: `read-a.bin` SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`, flashrom exit 0, VERIFIED.
- Readback: `postwrite-stock-restore-20260911.bin` SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`, IDENTICAL to stock.
- Claim: stock bytes on SPI hardware-verified. Video/boot UNRUN until operator cold boot.
- Next: operator cold boot to confirm video, then minimal bootable VCN builds.

## Stock restore cold-boot observation (operator: no video)

- Timestamp: 2026-09-11T21:40+05:00.
- Operator report after stock restore (readback IDENTICAL `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`): no video on cold boot.
- Evidence class: operator-observed hardware behavior. No POST/UART/network/Linux evidence, so stage and cause INCONCLUSIVE.
- Video: FAIL on stock bytes. Boot: INCONCLUSIVE.
- Consequence (G7 correction): all 4 prior candidate no-video results are NON-DISCRIMINATING. If stock bytes give the same symptom, the cause is outside the flashed bytes: power/procedure, programmer still attached, battery, display/cable/input, or board state. No candidate may be judged boot-unsafe from this series until stock boots under the same setup.
- Stop: remove power, no repeated cycles. Next: verify boot procedure and display path with unchanged stock on chip.

## APCB-only reflash intent after connector fix (no hardware touched yet)

- Timestamp: 2026-09-11T22:00+05:00.
- Operator correction (G7): all prior no-video results (APCB-only, D3-B2, policy-only, DXE-only, stock restore) are NON-DISCRIMINATING — display connectors were wrongly connected on operator side.
- Operator order: flash from the first BIOS (Codex session first candidate).
- Target: `candidates/BC250_APCB_DFG_only_v001_from_read-a.bin` SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`, 16 MiB. Root re-hashed file just now: MATCH.
- Procedure: 1) pre-write full capture; 2) write candidate with log; 3) independent readback + hash/cmp/parsers; 4) operator reconnects display correctly, cold boot, video observation.
- Expected: flashrom exit 0 + VERIFIED, readback byte-identical to candidate.
- Rollback: stock `read-a.bin` 83c4e420... preserved; separate approval needed.

## APCB-only reflash write + readback result

- Timestamp: 2026-09-11T22:10+05:00.
- Pre-write: `read-g-prewrite-apcb-reflash.bin` SHA-256 `e5a2a8bd36693bc02be96bb08b3470419c1895f78d899d4c752aecb5dec1453c` — NOT stock, NOT any known candidate (operator's own backup flashed earlier from outside this session). Recorded honestly; no claim about its content.
- Write: APCB-only `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`, flashrom exit 0, VERIFIED.
- Readback: `postwrite-apcb-only-reflash-20260911.bin` SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`, IDENTICAL to candidate.
- Claim: SPI write/readback hardware-verified only. Boot/video/VCN UNRUN.
- Next: operator disconnects programmer, returns battery, connects display CORRECTLY, one cold boot, video observation.

## APCB-only v001 runtime audit via SSH (read-only)

- Timestamp: 2026-09-11T22:55+05:00. Access steammachine@127.0.0.1 via ~/.ssh/id_ed25519 (host entry found in config.windows-20260911). No password stored.
- Board boots Linux on APCB-only `6b1fe8ef...`: amdgpu on 1002:13fe, DP-1 connected, card1/renderD128 present, SMU 88.6.0 OK.
- IP blocks: 8 detected, NO vcn/uvd/vce. VCN firmware lines absent. Display IRQ errors present but non-fatal.
- Report: `evidence/runtime/20260911-apcb-only-v001-boot-audit.md`. No writes issued; read-only audit only.

## Firmware audit decision (G3): reuse 1.92 probe kernel, no new build

- Timestamp: 2026-09-11T23:05+05:00.
- Audit (read-only SSH steammachine@127.0.0.1): running kernel 7.2.0-1.1 (stock, no bc250_vcn_mode param).
- Installed: 7.2.0-1.92-cachyos-vcn-bc250 with amdgpu.bc250_vcn_mode 0/1/2 (probe=1, hardware=2). Mode1 boot PASS 2026-08-28 (vcn_v2_0_probe block 8 attached, VCN fw ENC 1.24 DEC 8 found, no user-visible decode yet).
- Firmware present: renoir_vcn.bin -> green_sardine_vcn.bin (404,544 B decompressed, sha 0e9814527ce28983cacd24eaa8a35ffb4b069b8d372f0980a4ede15cf6dc186d). No cyan_skillfish2_vcn exists (expected: empty driver case).
- Decision: existing 1.92 route already addresses both needs (probe block + hardware block + fw declared renoir/green_sardine). New kernel build NOT justified. Next: boot installed mode1 (probe signal) then mode with hardware block; operator reboots via local console (SSH cannot reboot safely while display observed).
- Rollback: default boot stays 7.2.0-1.1 stock; probe entries are extra limine items only.

## Mode2 limine entry created (no reboot yet)

- Timestamp: 2026-09-11T23:15+05:00.
- Added `linux-cachyos-vcn-bc250-mode2` via `limine-entry-tool --add-kernel linux-cachyos-vcn-bc250 <initramfs> <vmlinuz> -mode2 --comment 'BC-250 VCN hardware: mode 2, experimental'`.
- Verified: `--get-cmdline linux-cachyos-vcn-bc250-mode2` ends with `amdgpu.bc250_vcn_mode=2`; tree shows mode0/mode1/mode2.
- Dropin `/etc/limine-entry-tool.d/90-bc250-vcn-probe.conf` also has mode2 KERNEL_CMDLINE line (backup at .bak). First append attempt wrote a broken unquoted line; removed and re-appended via scp exact line.
- Reboot NOT issued via SSH (local display observed by operator). Operator reboots and selects mode2 from menu.
