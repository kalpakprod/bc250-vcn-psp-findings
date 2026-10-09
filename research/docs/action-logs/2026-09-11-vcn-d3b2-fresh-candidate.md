# Fresh-baseline D3-B2 VCN candidate

## Build intent

- Timestamp: 2026-09-11T18:20+05:00.
- Actor: root Codex agent. No worker is delegated; root retains builder adaptation, artifact generation, and deterministic verification because the work is tightly coupled to the current baseline.
- Goal: continue the VCN-unlock investigation after the APCB-only candidate produced no display, without treating stock rollback as the project objective.
- Exact source: `evidence/programmer/reads/20260911/read-a.bin`, 16 MiB, SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- Existing route: historical `d3b2_build.py` plus D3-B2 verifier and package. It addresses the combined SEC_GASKET/TOS/APCB route but is insufficient as-is because paths are Windows-specific, the historical base is SHA-256 `4005b68a70e335581b23e819fd3e52ff74c0f10178bf8563e36220304a12aa67`, and its source APCB checksum byte differs from the current baseline.
- Planned change: create the smallest path-parameterized adapter under `scripts/`, build a new candidate under `candidates/`, and preserve a machine-readable manifest under `evidence/candidates/`.
- Expected effect: modified copies of PSP types `0x24` and `0x45` placed in the verified erased area at `0x9E0000/0x9E4000`, two PSP directory entries repointed with Fletcher32 recomputed, and APCB DFG words changed to `0x007FFF00` with checksum recomputed.
- Signature boundary: the modified policy payloads retain old signature tails but change signed bytes; acceptance is unknown. Do not call the candidate signed, bootable, safe, or VCN-enabled.
- Rollback for offline build: delete only the new generated candidate/reports. Hardware rollback remains the preserved stock image and requires a separately approved write.
- Acceptance: exact input/output SHA-256, strict baseline assertions, bounded changed ranges, valid PSP/BHD/APCB/FV structure, detailed policy group checks, negative baseline tests, and independent review before any flash request.

## Build and root verification result

- Timestamp: 2026-09-11T18:22:10+05:00.
- Added path-parameterized builder `scripts/build_vcn_d3b2_candidate.py`, SHA-256 `0c0d3d6bc22ec6b9d238eb74cfe5047499222984925c28dafa3b6e57f54f254a`.
- Built `candidates/BC250_VCN_D3B2_combined_v001_from_read-a.bin`, 16,777,216 bytes, SHA-256 `439e248141ef6a9c1313bc7815696d570be8fed5471262596186f3da8914747d`.
- Build manifest: `evidence/candidates/BC250_VCN_D3B2_combined_v001/build-manifest.json`, SHA-256 `5ff627ebc4c5749a3c35c2b4399a562a7967adb1a63da1943826bee0ea4928f1`; exact diff contains 13,736 changed bytes in 332 contiguous ranges.
- Added independent-parser-style root verifier `scripts/verify_vcn_d3b2_candidate.py`, SHA-256 `9d831b0ac179434338cae62386808f292171b18c838ccc93a5e652e12ea14618`.
- Structural verification PASS 21/21: PSP/BHD Fletcher32, type-0x24 and type-0x45 directory targets/sizes, both policy group layouts, VCN bank/tail, target values, old carrier preservation, signature boundaries, APCB checksum/DFG words, diff confinement, and erased trailing region. Report SHA-256 `296d93579ee927aa9b64992931a4f8bf3a07160598c2a7bd91c1b85730933ddf`.
- General firmware parser PASS: 16 MiB, PSP/BHD/APCB checksums match and four firmware volumes remain valid. Report SHA-256 `2f95edea6e2399171fa3d081ee6f3a2e91e8bacd64b47cd376a929c310348019`.
- APCB detail parser PASS: both DFG words are `0x007FFF00`. Report SHA-256 `873bbed46f10a7316ed7e035e6132ea5246c14154703e083b48fc46d35b29f85`.
- Historical-delta reconciliation PASS: the fresh candidate applies the historical D3-B2 delta to the current stock where source bytes agree, while recomputing the current APCB checksum (`0x32`; historical image used `0x09`). The historical full image is not reused.
- Negative tests PASS after correcting the fixture: a first attempted source corruption wrote `0x00` over an already-zero byte and therefore did not alter the hash; the fixture was corrected by changing the `$PSP` byte. The corrected source-hash mismatch and a separately corrupted unsigned-body hash were both rejected before output creation.
- Signature status: modified policy payload bytes retain historical 0x100-byte signature tails. Exact PSP acceptance remains unverified; this is not claimed as a valid signature.
- Hardware status: UNRUN. The current board still contains the APCB-only candidate that produced no display. No additional programmer operation occurred during this build.
- Independent reviewer gate: PENDING. Root verification is not a substitute for the required different-author review of the actual artifact and failure path. Do not flash until that review passes and a new exact file/hash/board approval is received.

## Independent reviewer dispatch intent

- Timestamp: 2026-09-11T18:25+05:00.
- Bounded task: independently review the exact fresh-baseline D3-B2 candidate, builder, manifest, verification reports, changed regions, signature-boundary risk, and failure/rollback path; do not modify firmware, hardware, root-owned metadata, or the candidate.
- Reviewer model family: Anthropic Claude; effective model shown by the operator's Claude Code terminal: `Opus 5 (1M context)`. Effort: current/default Claude Code effort is not separately exposed in the terminal UI; prompt requests a thorough consequential-firmware review and requires the reviewer to disclose the effective model/effort information it can observe.
- Permissions: Claude Code terminal shows `bypass permissions on`; reviewer is nevertheless restricted by the task brief to read-only inspection except for one review Markdown artifact.
- Source paths: `evidence/programmer/reads/20260911/read-a.bin`, `candidates/BC250_VCN_D3B2_combined_v001_from_read-a.bin`, `scripts/build_vcn_d3b2_candidate.py`, `scripts/verify_vcn_d3b2_candidate.py`, `evidence/candidates/BC250_VCN_D3B2_combined_v001/`, `specs/2026-09-11-vcn-d3b2-fresh-baseline.md`, and historical D3-B2 references under `import/from-windows/Users/kukuruza/`.
- Acceptance criteria: independently recompute hashes/diff confinement; validate PSP/BHD/APCB checksums; parse types `0x24/0x45`, group counts, VCN values/tails, old-carrier preservation, and signature-tail boundaries; inspect builder/verifier assumptions; identify boot/PSP failure modes; mark each check PASS/FAIL/INCONCLUSIVE/UNRUN; make an explicit `APPROVE_FOR_HARDWARE_TRIAL` or `REJECT` recommendation without claiming safety or VCN enablement.
- Return artifact: `evidence/candidates/BC250_VCN_D3B2_combined_v001/independent-review-claude-opus5.md` in English. No other file may be written.
- Root will re-read the returned artifact and rerun the cheapest decisive checks before relying on it. Dispatch receipt alone is not a finding.

## Independent reviewer dispatch receipt

- Orca terminal: `term_4271dcd6-ee99-4458-a765-385e2a9173e3`, title `Claude Code`, provider `claude`.
- Request ID: `37e6f03f-7164-4f88-8af1-d7fe8da447cd`.
- Send result: `accepted=true`; observed stages: `input_accepted`, `turn_started`.
- The receipt proves that the Claude Code turn started. It is not review evidence and does not satisfy the independent-review gate until the return artifact exists and root verifies it.

## Independent review result and root reconciliation

- Review artifact received: `evidence/candidates/BC250_VCN_D3B2_combined_v001/independent-review-claude-opus5.md`, SHA-256 `5abe1f3f20fe03359d54bd85a71005c0bff3cbbd5213d452fd0bc2954d52a4a1`, 14,590 bytes.
- Effective reviewer disclosure: session began as Anthropic Claude Opus 5 (1M context) and was re-identified mid-session as Opus 4.8 (1M context); no numeric effort was exposed. Different-author/family review condition is satisfied relative to the root Codex builder.
- Reviewer recommendation: `APPROVE_FOR_HARDWARE_TRIAL`, bounded to a controlled programmer-backed experiment only. It does not establish safety, bootability, signature validity, or VCN enablement.
- Root re-read the report to EOF, recomputed the report/candidate/stock hashes, and reran the structural verifier: 21/21 PASS; temporary root result SHA-256 `2477088c7a7bd789398e5878a407ddb0f6f5014a27abd90d28ee76168ca6dd96`.
- Accepted critical risk: modified/grown `$PS1` payloads retain stale signature material; PSP acceptance is the hardware hypothesis and remains unknown.
- Accepted operational risk: the board currently contains the APCB-only candidate that produced no display. Before a D3-B2 write, capture a fresh complete read and prove it matches that known candidate/readback or stop. Stock recovery remains preserved.
- Reviewer F4 accepted: extend the root verifier to assert the leading/+0xD0 signature-material preservation and exact type-0x45 prefix delta before using it as a hardware gate.
- Reviewer F5 correction: the report states that the historical full base and D3-B2 image are absent from `import/`. Direct root filesystem/hash checks disprove this. They exist at `import/from-windows/Users/kukuruza/tmp_bc250/recon/d3/package/00_BASE-reference_stock.bin` (SHA-256 `4005b68a70e335581b23e819fd3e52ff74c0f10178bf8563e36220304a12aa67`, 16 MiB) and `02_D3-B2_MAIN_APCB-DFG-i_gasket+TOSpolicy_A-B-unsigned.bin` (SHA-256 `dec4930e6b322bc60a3954870f728adb08e50018b001ac6c21d318c154036b61`, 16 MiB). Preserve the reviewer report as-authored; root correction governs project conclusions.

## Verifier coverage correction intent

- Update `scripts/verify_vcn_d3b2_candidate.py` to assert that both relocated headers preserve stock bytes at `+0x00..+0x0F` and `+0xD0..+0xEF`, and that the type-0x45 prefix/body shift matches the historical exact-delta expectations.
- Write a new verification report rather than overwrite earlier reports. Candidate bytes remain unchanged; no hardware operation.

## Verifier coverage correction result

- Added explicit checks for preserved `+0x00..+0x0F` and `+0xD0..+0xEF` signature-material ranges in both relocated `$PS1` headers, exact type-0x45 prefix diff offsets `{0x4C,0xBC,0x245,0x246}`, and byte-identical shifted group `0x281`.
- Corrected verifier SHA-256: `7070fb1ac521abbf22587b6def04ffef8dfdfb3b5dccc98fcb489918c9aaad66`.
- New report: `evidence/candidates/BC250_VCN_D3B2_combined_v001/verification-v3.json`, SHA-256 `d0b0b9abc6251c39d8ca9c303be1a927a05c6cc82d9a03986c6e635c15cc999b`; 25/25 checks PASS.
- Candidate remains byte-identical at SHA-256 `439e248141ef6a9c1313bc7815696d570be8fed5471262596186f3da8914747d`.
- Independent-review gate is PASS for a controlled hardware trial, subject to a fresh current-chip capture, exact new approval, programmer readback, and preserved rollback. Hardware write remains unauthorized until the operator supplies the exact approval.

## Exact D3-B2 hardware-trial authorization and pre-write intent

- Timestamp: 2026-09-11T18:47:12+05:00.
- Target: operator-owned board `BC250-01`; operator confirms it is fully unpowered, battery removed, clip oriented correctly, and programmer set to 3.3 V.
- Exact candidate authorization received for `/home/OWNER/orca/projects/bc250/candidates/BC250_VCN_D3B2_combined_v001_from_read-a.bin`, SHA-256 `439e248141ef6a9c1313bc7815696d570be8fed5471262596186f3da8914747d`.
- Exact emergency rollback authorization received for `/home/OWNER/orca/projects/bc250/evidence/programmer/reads/20260911/read-a.bin`, SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`, only on write/readback failure.
- Programmer/tool recheck PASS: CH347T USB `1a86:55db` present; flashrom binary SHA-256 `5ee0b2e4ea215a81ec08997dad99c469bd9f2335d5237d623388dee29875573c`; candidate and rollback hashes match authorization.
- First run read-only probe: `pkexec /tmp/bc250-flashrom-resume-tDCb0q/prefix/usr/bin/flashrom -p ch347_spi:spispeed=1.875M --flash-name`. Stop unless Winbond `W25Q128.V`, 16 MiB is detected.
- Fresh pre-write capture command: `pkexec /tmp/bc250-flashrom-resume-tDCb0q/prefix/usr/bin/flashrom -p ch347_spi:spispeed=1.875M -r /home/OWNER/orca/projects/bc250/evidence/programmer/reads/20260911/read-d-prewrite-d3b2.bin`.
- Preserve logs at `evidence/programmer/probe-d3b2-trial-20260911.log` and `evidence/programmer/reads/20260911/read-d-prewrite-d3b2.flashrom.log`.
- Required current-state reconciliation: the fresh read must be 16 MiB and byte-identical to the previously verified APCB-only readback SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`; relative to stock it must differ at exactly `0xAB1010`, `0xAB1132`, and `0xAB116E`. Any other state is a hard stop.
- After reconciliation, rerun verifier v3 (25/25 expected), hash candidate again, then log the exact write intent before issuing `-w`.
- Keep the programmer attached and board unpowered until an independent complete post-write readback is byte-identical to the candidate and all structural checks pass.

## Fresh current-state capture result and exact write intent

- Probe PASS: Winbond `W25Q128.V`, 16 MiB, CH347 SPI at 1.875 MHz. Probe log SHA-256 `c89588ff0a4889bf03d9ab2f7b12e0c56eb891c5f8746b5793f0664944c7cd1e`.
- Fresh current-chip capture PASS: `evidence/programmer/reads/20260911/read-d-prewrite-d3b2.bin`, 16,777,216 bytes, SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`.
- Current-state reconciliation PASS: byte-identical to the prior APCB-only post-write readback; relative to stock, exactly `0xAB1010`, `0xAB1132`, and `0xAB116E` differ. No unexplained chip-state change exists.
- Fresh read log SHA-256 `bc00e08f69e24c06546757db93932d401622ed6ad558e246b502c6c4a5ae8175`.
- Candidate SHA-256 recheck PASS: `439e248141ef6a9c1313bc7815696d570be8fed5471262596186f3da8914747d`.
- Corrected verifier v3 pre-write run PASS: 25/25; temporary result SHA-256 `b671bb239aae2bd827c8c47c6d9a1c0cecc02d97c8f597f7770cab0fe1c11ec8`.
- Exact authorized write command: `pkexec /tmp/bc250-flashrom-resume-tDCb0q/prefix/usr/bin/flashrom -p ch347_spi:spispeed=1.875M -w /home/OWNER/orca/projects/bc250/candidates/BC250_VCN_D3B2_combined_v001_from_read-a.bin`.
- Preserve output at `evidence/programmer/reads/20260911/write-d3b2-v001.flashrom.log`. Stop and use the pre-authorized stock rollback only if erase/write/built-in verification or the subsequent independent readback fails.

## D3-B2 write result and independent readback intent

- Timestamp: 2026-09-11T18:55:13+05:00.
- Write command exited 0. flashrom detected Winbond `W25Q128.V`, read old contents, reported `Erase/write done from 0 to ffffff`, and returned built-in `VERIFIED`.
- Write log SHA-256 `17248ec2e3454a4a8a85ce9821251a26bda1fea9208becd5cd9ca32e5b6474ed`.
- Built-in verification is not the independent readback. Board remains unpowered and the programmer remains attached.
- Exact readback command: `pkexec /tmp/bc250-flashrom-resume-tDCb0q/prefix/usr/bin/flashrom -p ch347_spi:spispeed=1.875M -r /home/OWNER/orca/projects/bc250/evidence/programmer/reads/20260911/postwrite-d3b2-v001.bin`.
- Preserve output at `evidence/programmer/reads/20260911/postwrite-d3b2-v001.flashrom.log`, compare the entire chip with the authorized candidate, then rerun firmware/APCB/D3-B2 structural verification. Do not power the board until all checks pass.

## Independent post-write readback result

- Timestamp: 2026-09-11T18:57:51+05:00.
- Full-chip readback PASS: `evidence/programmer/reads/20260911/postwrite-d3b2-v001.bin`, 16,777,216 bytes, SHA-256 `439e248141ef6a9c1313bc7815696d570be8fed5471262596186f3da8914747d`.
- Candidate comparison PASS: readback is byte-identical to the exact authorized candidate (`cmp` exit 0 and matching SHA-256).
- General firmware parser PASS: PSP/BHD/APCB checksums match and four firmware volumes remain valid. Report SHA-256 `fac4b689eb685d2504f8df144133c4a44b3c82daf129389741cb1385f04111f2`.
- APCB detail parser PASS: DFG words at `+0x130/+0x16C` are both `0x007FFF00`. Report SHA-256 `170902611009bdcd3c713c7be0fd5a0b3c3c02290fc9565f07fa8a78edb6b910`.
- Corrected D3-B2 structural verifier PASS 25/25 on the physical readback. Report SHA-256 `fa2e048cb739ca17fb3b811edc133092737c2a116600df0d7b19cb5e05df6dfb`.
- No emergency rollback was triggered because write and independent readback passed. Stock recovery remains preserved and authorized only for the stated failure condition.
- Result classification: hardware-verified at SPI write/readback layer only. PSP acceptance, boot/video, VCN power, ring completion, codecs, and stability remain UNRUN.

## Hardware-trial evidence synchronization intent

- Create a machine-readable D3-B2 hardware-trial manifest, update candidate catalog/project memory/completion state, and run final JSON/hash/contour/test/diff checks.
- Metadata/documentation only; no further hardware operation. Keep the board unpowered and programmer attached until the final handoff explicitly permits disconnection.

## Hardware-trial evidence synchronization and closing result

- D3-B2 hardware-trial manifest written and JSON-validated: `evidence/programmer/reads/20260911/d3b2-v001-hardware-trial-manifest.json`, SHA-256 `32fcfddd75f7fbc298d957655fafd93247a77dce5dc7ba2782314e26ffc4ecc8`.
- Completion matrix updated: SHA-256 `0342dcbf65f07178b1d4fbe319922f92e2ee97a37079ed46855114964dfc6df9`; D3-B2 programmer layer PASS, boot/runtime UNRUN.
- Final candidate/readback `cmp`: PASS. Corrected structural verifier on the physical readback: 25/25 PASS; temporary closing result SHA-256 `8b36feab285e8497aa63139bcddf161c4a2629593b2ccd3bd91d71d4909dc95e`.
- Contour validation PASS (`contract_copies=4`, `skills=11`, `instincts=6`); unit tests 4/4 PASS; JSON parsing PASS; `git diff --check` PASS.
- No emergency rollback was performed. Board remains unpowered and programmer attached at handoff.
- Operator may now disconnect CH347T USB and the SPI clip, then perform one cold boot. Report video output and indicator state. If Linux becomes reachable, capture VCN/runtime evidence before any further firmware variant.

## First D3-B2 cold-boot observation

- Timestamp: 2026-09-11T19:03:31+05:00.
- Operator reports the same observable result as the APCB-only trial: board indicators illuminate in the same pattern and no display image appears.
- Video-output criterion: FAIL. PSP acceptance, POST stage, x86/UEFI execution, and VCN state remain INCONCLUSIVE because no POST/UART/network/Linux evidence was captured.
- The write/readback was byte-identical, so the observation is not explained by programmer transfer mismatch.
- Both failed candidates share the APCB DFG `0x007FFF00` change. This makes APCB a suspect but does not prove causality because D3-B2 also adds modified signed-policy carriers.
- Stop repeated boots of this image. The next smallest goal-aligned discriminating variant will retain the combined VCN SEC_GASKET/TOS policy changes but restore the entire APCB block to stock. If it boots, the APCB change is implicated; if it still fails, policy relocation/signature handling becomes the leading branch. No hardware write is authorized by this decision.

