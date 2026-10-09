# CLV ABL1 bounded integration review — intent

Timestamp: 2026-09-20T10:09:34+05:00 Asia/Almaty
Actor: bounded integration reviewer
Target: append-only integration qualification in /home/OWNER/orca/projects/bc250/memory/oc-recheck.md and /home/OWNER/orca/projects/bc250/specs/2026-09-20-clv-sync-development-plan.md; do not edit source reports, verifier, firmware or ROM.

Bounded task from root: integrate the fresh heap-followup worker result with one independent raw-byte check limited to the node header/lookup versus the HEAP-header initializer. Correct the ordered reader fallback description; record the FCLK type-byte uncertainty; qualify exact-scalar absence as not excluding other ROM representations; retain unknown pointer-space (MMIO remains possible); do not claim a known clock mode or MCLK=UCLK=FCLK. Leave the separate callback target at context+0x660 unresolved while its author result is pending. No additional research track.

Inputs read and pinned before writes:

- Target context report /home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl1-context-branch-consumer-xhigh.md SHA-256 f77b55f179bf70fb0dfb856ae2bf8919ae3ad5eb6664ad222a7848933dc67ca0.
- Heap follow-up report /home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl1-runtime-heap-followup.md SHA-256 0d2046ec0bb5ac829a68e2e803d142ff0d93ca6f6b0c0df8b4244968d2dd6475.
- Heap follow-up result /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-runtime-heap-followup/abl1-runtime-heap-followup-result.json SHA-256 9c94bf1d3b3a4880b32a36d2e6c95b25e56a7e0292aa495c0ff1400c0492a75f; author reports 90 checks PASS.
- Shared memory /home/OWNER/orca/projects/bc250/memory/oc-recheck.md pre-append SHA-256 186009168f9ab552d23652ab1056e16d92ca6d852e62cb264364d1688f3e24d7.
- Shared plan /home/OWNER/orca/projects/bc250/specs/2026-09-20-clv-sync-development-plan.md pre-append SHA-256 0e6691f1a4a9d0b010dfd954187c9fa3490546e443f189dc690a3f1cb5aa98ad.

Expected outputs: own report `docs/research/20260920-clv-abl1-integration-review.md`; machine result, verification record, MODIFIED_FILE/DIFF_FILE/ROLLBACK.sh roles, and manifest under `evidence/firmware-audit/20260920-clv-abl1-integration-review/`; this action log. Append one dated qualification to the shared memory and shared plan; preserve existing text.

Next executable action: run a minimal, read-only checker against the pinned ABL1 payload and full Thumb listing for only the 0x6374 node-field reads, 0x63F8 HEAP-header initialization, and its 0x6F78 caller, then integrate the checked limit. Reuse the existing 90-check result/APCB parse; do not rerun broad analysis.

Expected effect: confirm static lookup/header bytes only; no proof of node population or ROM-to-HEAP conversion. The exact direct-scalar search is not absence-of-representation proof. Parent-provided callback target result remains pending and is not joined.

Rollback: use the created ROLLBACK.sh only on a separate test copy of the modified memory file, then remove only uniquely named review artifacts/appendix if rollback is requested; preserve the original exact firmware inputs and other workers' results.

Baseline hashes: 186009168f9ab552d23652ab1056e16d92ca6d852e62cb264364d1688f3e24d7 (memory); 0e6691f1a4a9d0b010dfd954187c9fa3490546e443f189dc690a3f1cb5aa98ad (plan).

## Bounded-check setup corrections (2026-09-20T10:16:29+05:00 Asia/Almaty)

Two inline-checker attempts failed before producing a result and did not modify inputs: (1) exit 1, `AttributeError: 'list' object has no attribute 'split'` from malformed mnemonic normalization; (2) exit 1, `listing/source byte mismatch at 0x0` because the attempt compared every line in a mixed full listing to payload-relative bytes. Corrective method: bind to the pinned ABL1/listing hashes and compare only the explicitly selected instruction rows around selector 0x4B1A, lookup 0x6374, initializer 0x63F8, and caller 0x6F78. This remains one narrow edge check; no whole-image scan or producer search is added.

Next action: materialize this bounded checker under the uniquely named review evidence directory, execute it once, and preserve its literal stdout/stderr/exit.

## Verifier correction (2026-09-20T10:18:20+05:00 Asia/Almaty)

The first persisted-checker execution exited 1 before assertions because the generated regex was over-escaped and matched literal backslashes rather than whitespace; no input was modified. Correct only the listing-row regex to use `\s` in the Python raw regex and newline serialization to emit a single newline; rerun the same bounded edge check.

## Transaction-check predicate correction (2026-09-20T10:22:04+05:00 Asia/Almaty)

The first modified-state grep check exited 1 because its marker used context+HEAP while the appended heading spells context/HEAP; baseline check still correctly saw no marker, but the comparison predicate was mismatched. No source was changed by the failed isolated check. Correct the exact marker to match the appended heading and rerun baseline, modified, and rollback checks on the same scratch path.

## Exact-marker correction (2026-09-20T10:22:33+05:00 Asia/Almaty)

The first corrected transaction attempt stopped before running grep because the marker omitted the words remains PARTIAL present in the actual heading. No scratch state was modified in that attempt. Use the full literal heading as the predicate for the same baseline/modified/rollback test.

## Result-writer correction (2026-09-20T10:26:16+05:00 Asia/Almaty)

The report writer initially expected review-result.json not to exist; the bounded verifier correctly created it before the writer ran. No artifact was lost or overwritten. The integration writer now reopens and extends that existing verified result instead of treating it as a collision.

## Observed integration result (2026-09-20T10:28:54+05:00 Asia/Almaty)

Independent bounded checker command: python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-integration-review/abl1_heap_node_init_review_verify.py; stdout is retained at /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-integration-review/verifier.stdout; stderr is empty; exit 0; result 64/64 PASS. Exact inputs remained at ABL1 SHA-256 af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a and listing SHA-256 b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65. The bounded result verifies lookup-node field offsets and 0x63F8 HEAP-tag initialization called at 0x6F78; it does not prove a producer for the linked 0xA04E node.

Same-predicate transaction on one scratch target path: BASELINE grep exit 1 (absent); MODIFIED grep exit 0 (present); ROLLBACK.sh exit 0; restored-state grep exit 1 (absent). Restored SHA-256 186009168f9ab552d23652ab1056e16d92ca6d852e62cb264364d1688f3e24d7 equals pristine target SHA-256 186009168f9ab552d23652ab1056e16d92ca6d852e62cb264364d1688f3e24d7. GOAL was reapplied to MODIFIED_FILE after rollback. Shared memory hash changed from 186009168f9ab552d23652ab1056e16d92ca6d852e62cb264364d1688f3e24d7 to 39ea72fca9ded368fc96d3a1d4608626b32b36e08f3befede397b271e5bc89f9; plan hash changed from 0e6691f1a4a9d0b010dfd954187c9fa3490546e443f189dc690a3f1cb5aa98ad to d829ac5331d4c7ee029ab592f93766eb5054409ae119fb45d5138c5dbb2132ca; both changes are append-only.

Correction qualification: the exact raw-ROM search only rejects the searched contiguous little-endian scalar byte strings. It does not reject another ROM encoding; the decoded ABL1 directly contains both 0xA04E and 0x73000. The ABL1 HEAP header initializer is not evidence of the node producer. The CBSG 0x1707 parser result provides no schema link. MMIO remains possible for unknown indirect pointer targets. FCLK type-byte SP+0x0C is uninitialized in the bounded caller; type-2 execution remains unproven. The separate context+0x660 callback target remains pending/unjoined. No clock mode, hardware result, or MCLK=UCLK=FCLK claim is made.

Earlier setup failure note: the first transaction predicate correction wrote context+HEAP instead of the literal context/HEAP heading; the next check failed its assertion, but that tool event did not print the subprocess returncode. Treat the prior phrase claiming a literal grep exit 1 as unverified. The finalized transaction-events.json contains the directly observed same-predicate statuses above.

## Final readback and manifest intent (2026-09-20T10:30:50+05:00 Asia/Almaty)

Current observed statuses: branch-consumer result 89/89 PASS; runtime-HEAP follow-up result 90/90 PASS; reader fallback/type result 64/64 PASS; independent one-edge review result 64/64 PASS, exit 0, stderr empty. The separate context+0x660 author target result remains pending. The report now references integrated result SHA-256 50247ac4dda89ceabf068e9f4f50a98fa0c9cb9725b6c55cf40656c40023e13b; report SHA-256 is d90aedc64e78233decfc1a714432a1528bcd4779cb44c1bb35c58533fe8682c1. Next step is create and verify the checksum manifest, then reopen all four requested paths and all four transaction roles. No further research is undertaken.

## Diff reconstruction tool correction (2026-09-20T10:32:49+05:00 Asia/Almaty)

An exec wrapper rejected a combined patch-test shell command because it included rm -rf; the command did not start, so no shell status/output exists and no files changed. Replaced that cleanup approach with Python TemporaryDirectory and reran the same disposable patch-apply check.

## DIFF_FILE reconstruction and final artifacts (2026-09-20T10:34:02+05:00 Asia/Almaty)

Observed patch command: patch --batch --silent -p0 -i /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-integration-review/DIFF_FILE.patch in a disposable directory with pristine memory/oc-recheck.md; stdout empty; stderr empty; exit 0. Reconstructed SHA-256 39ea72fca9ded368fc96d3a1d4608626b32b36e08f3befede397b271e5bc89f9 equals MODIFIED_FILE SHA-256 39ea72fca9ded368fc96d3a1d4608626b32b36e08f3befede397b271e5bc89f9; cmp status 0.

Final report SHA-256 9fdfb4d7342c82735f70ede946ad156e3ea7e4843a1622e451fd11345e31482c; integrated result SHA-256 f7487eb93caa99f2d7d9327769be46625011e487297e866891a4df208b1bdaaf; VERIFICATION.txt SHA-256 3c896f6e8026d727a390d0f2b956111eb48633e2dc1ceca8361f91c29807044f. Four requested paths and all transaction roles are included in the final manifest. Callback+0x660 target remains pending, not guessed; no completion or clock-mode claim.

## Manifest input-path correction (2026-09-20T10:35:28+05:00 Asia/Almaty)

The first manifest assembly attempt stopped at a mistaken ABL1 result filename before writing SHA256SUMS.final. Report/result/verification/action-log writes had already completed; no evidence was removed. The correct path is evidence/firmware-audit/20260920-clv-abl-memory-review/abl1-memory-review-result.json; rerun manifest generation with existing input paths only.

## Final report formatting correction (2026-09-20T10:37:01+05:00 Asia/Almaty)

The report's DIFF_FILE readback bullet contained literal backslash-n characters from a string-escape error. It was corrected to a normal Markdown line break; no finding or evidence changed. Final report SHA-256: 40bd3fd1c6b03ee39d8870ddfcb0277b62d4d87b4ab6697c674103600dc4585f.
