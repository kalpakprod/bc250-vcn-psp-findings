# Independent clock evidence review — action log

## Intent (recorded before review artifact write)

- Timestamp: 2026-09-21T14:05:00+05:00 (Asia/Almaty)
- Actor: `/root/clock_independent_review`
- Target: exact plain CLV donor `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`; expected SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; owned review report `docs/research/2026-09-21-clock-independent-review.md`.
- Scope: offline, read-only adversarial review of the physical `MCLK:UCLK:FCLK=1:1:1` and CLV `1800MHz` claims, including newly available clock-worker artifacts and the integration overclaim that zero direct UEFI immediate readers proves an ABL1/APOB/SMU handoff.
- Inputs: `memory/INDEX.md`, `memory/oc-recheck.md`, `memory/evidence-model.md`, `docs/knowledge-sources.md`, applicable BC250/firmware/artifact skills, the clock-team registry, exact CLV clock reports and machine results, and current baseline/decision reports.
- Planned checks: reopen source and artifact hashes/manifests; inspect the actual verifier code and byte-backed findings; challenge at least one assumption; classify claims as observed/static/emulated-or-host-tested/hardware-verified or unresolved; preserve contradictions and identify one next executable offline action.
- Safety: no network, board, sysfs, mailbox/MMIO/register action, NVRAM/ROM/candidate write, parser rerun that mutates retained artifacts, or worker-file edits.
- Expected effect: one concise English adversarial decision memo plus this append-only action log; existing reports remain unchanged.
- Rollback: remove only `docs/research/2026-09-21-clock-independent-review.md` and this owned log; no source/evidence artifact is to be altered.

## Observed result (after report write)

- Timestamp: 2026-09-21T14:20:00+05:00 (Asia/Almaty)
- Reopened target hash/size: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`, `16777216` bytes.
- Reopened owned report: `docs/research/2026-09-21-clock-independent-review.md`, SHA-256 `a4401efe792349a802d01c92d697e1709a0a7f64a10e95cfbb99c0d4241bec4b`.
- Reopened action log: this file; final hash recorded after append below.
- Reopened worker results: frequency-unit `6027fd54...`; UCLK discriminator `bb9ed4ea...`; provider/HOB boundary `b20a743a...`; DF consumer `7da3381c...`; observability `504e6761...`; ABL1 precedence `76cf4c68...`; native menu direct check `0d618263...`.
- Fresh manifest checks: clock discriminator `13/13 OK`; provider boundary `4/4 OK`; DF consumer `5/5 OK`; pstate precedence `16/16 OK`; native menu evidence `14/14 OK`; observability `5/5 OK`.
- Correction recorded: direct-immediate zero scans are bounded predicates, not proof of consumer absence or a proven ABL1/APOB/SMU handoff; the provider/HOB negative has the same boundary.
- Result: physical `1:1:1`, applied 1800 MHz, training, voltage, performance, hardware acceptance, and rollback remain unrun/unproven. No ROM, candidate, NVRAM, register, board, network, or worker artifact was modified.
- Remaining uncertainty: final `$INV 0x11ED` consumer/source, units/rate conversion, divider/crossing semantics, and exact caller inputs to ABL1 `0x95FC`.

## 2026-09-21 reachability verifier correction

- Intent: correct the one stale listing predicate at `0x6D20` (`pop.w` -> `pop`) and rerun the existing listing-based reachability verifier.
- Target: `evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/reachability/verify_item17_gate_listing.py`; input evidence stays unchanged.
- Rationale: captured LLVM listing and failed run stderr report `pop` at `0x6D20`; previous expected `pop.w`.
- Expected effect: complete the static verifier while retaining `global_svc6_reachability=UNRESOLVED` for the dynamic callback edge.
- Rollback: restore `evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/reachability/verify_item17_gate_listing.py.pre-correction` over the verifier.
- Observed: command `/usr/bin/python3 evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/reachability/verify_item17_gate_listing.py` exited 1; stdout `evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/reachability/gate-verifier-rerun.stdout` SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; stderr `evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/reachability/gate-verifier-rerun.stderr` SHA-256 `37665456c27663b334ca5cad8378f2fa5ef95e36d813e16fccd5ff2090180860`.
- Verifier pre-change SHA-256 `0def2a0dd045549d3aa87a6e436093fbc1989e2637579fd6f43963adef4e14a3`; corrected SHA-256 `09da86c71bb8e6c08a407c3241ae51094cfc3d899870db92023ee8a20a9a5c2f`.
- Remaining uncertainty: code/data dependent callback table targets are unresolved; this is static listing evidence only and does not establish physical clock writes or application of 1800 MHz.

## 2026-09-21 verifier invocation correction

- Correction: the initial direct Python invocation, after the mnemonic predicate was corrected, failed with `NameError: OUT is not defined` before checks completed; its stdout/stderr are retained as `gate-verifier-rerun.stdout` and `.stderr`.
- Intent: rerun the same listing verifier with its expected output directory explicitly bound as `OUT=BASE` in the execution namespace; do not alter the verifier further. Preserve any prior result JSON before overwrite.
- Expected effect: produce the reachability result JSON and a literal PASS/UNRESOLVED status summary if all byte/listing checks pass.
- Rollback: restore the saved pre-run result JSON if needed; verifier source can be restored from its `.pre-correction` copy.
- Observed: corrected invocation `/usr/bin/python3 -B -c from pathlib import Path; p=Path(sys.argv[1]).resolve(); ns={'__file__':str(p),'__name__':'__main__','OUT':p.parent}; exec(compile(p.read_text(),str(p),'exec'),ns) /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/reachability/verify_item17_gate_listing.py` exited 1; stdout `evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/reachability/gate-verifier-corrected-run.stdout` SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; stderr `evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/reachability/gate-verifier-corrected-run.stderr` SHA-256 `7a8f8c0f27160420075d9894f992d99e71e6d46d6075c59ff969de137f12ef00`.
- The failed direct invocation remains preserved unchanged; no firmware, ROM, or hardware operation.
- Correction: the attempted injected-namespace rerun also failed before entering the verifier because its launcher omitted `import sys` (`NameError: sys is not defined`); preserved in `gate-verifier-corrected-run.stderr`.
- Method change: instead of another launcher wrapper, bind the verifier's output directory explicitly inside the verifier (`OUT=BASE`), preserve the post-mnemonic/pre-output-fix source, and invoke the verifier directly.
- Method-changed direct run: `/usr/bin/python3 -B evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/reachability/verify_item17_gate_listing.py` exited 0; stdout `evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/reachability/gate-verifier-direct-run.stdout` SHA-256 `fbbb48554e7a9b3dfefd0601cf3c10d707c77dba132f1b5b41ae69c34f12cadd`; stderr `evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/reachability/gate-verifier-direct-run.stderr` SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
- Verifier with mnemonic plus output-directory corrections SHA-256 `be4f5e6d30d63c83a2fc5a56c0bd0d6d8007580c1f0e9e0d5505a4d7f043a71c`.
- Result JSON `evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/reachability/reachable-config-result.json` SHA-256 `d1f119e6d84f19291c6e13c31d5bfd1a22c27c8ddda2aef4b49b7bcf2197458b`.

## 2026-09-21T18:47:59+05:00 continuation — item-17 reachability boundary and four-role report update

- Actor: Codex continuation.
- Intent: append the 83/83 listing-verifier result to `docs/research/2026-09-21-clock-independent-review-v2.md` only; regenerate `docs/research/2026-09-21-clock-independent-review-v2.diff`, extend `docs/research/2026-09-21-clock-independent-review-v2-VERIFICATION.txt`, and exercise `docs/research/2026-09-21-clock-independent-review-v2-ROLLBACK.sh` on a separate copy.
- Baseline `docs/research/2026-09-21-clock-independent-review-v2-pristine.md` SHA-256 `aa5d694468f684e8c608fdfe506fc0608a6b9e300f10295eababc54ab1d6e839`; pre-update MODIFIED_FILE SHA-256 `d2e8290ff3b9f19c0aed53dc8ab6c2c91d82ebac154552743e4692ac350c8152`; rollback script SHA-256 `ed15decf2ef8be242754c8fdebb207df1f09d87c0f94a0a02f6f96d2ccb7b085`.
- Expected effect: record selected-branch bypass of three direct callsites and the unresolved data-dependent `BLX R0` boundary; preserve the no-global-SVC6 conclusion. Rollback only the dedicated test copy.
- No guide, firmware image, ROM, NVRAM, register, board, or hardware state is modified.
- Observed: listing verifier PASS 83/83; stdout SHA-256 `fbbb48554e7a9b3dfefd0601cf3c10d707c77dba132f1b5b41ae69c34f12cadd`, stderr empty, exit 0.
- BASELINE/MODIFIED/ROLLBACK marker stdout `item17-reachability=ABSENT` / `item17-reachability=PASS_83_83_UNRESOLVED` / `item17-reachability=ABSENT`; exits 1/0/1; restored hash `aa5d694468f684e8c608fdfe506fc0608a6b9e300f10295eababc54ab1d6e839` equals baseline; reapply exit 0.
- DIFF generation exit 1 (expected 1); patch reconstruction exit 0; reconstructed bytes PASS.
- Reopened roles: MODIFIED_FILE `4a073cee986a18c456442abbab477e81d51fb09d35003c1fefc1aa1b818c81d1`; DIFF_FILE `7867c2224d8fbf4abfa8891ca9e26fc829779bf9d44c64e2a13320922339d393`; VERIFICATION `1dff546c222998e413203a414cb18428acd5844306493f5110c63da89f9c9788`; ROLLBACK.sh `ed15decf2ef8be242754c8fdebb207df1f09d87c0f94a0a02f6f96d2ccb7b085`.
- Reopened G7 correction memory `memory/incidents/2026-09-21-item17-reachability-verifier-launch-correction.md` SHA-256 `c170dfbbf1cbd975e029b434926a75edd59c0bc745bdbf0ea57c78594740b028`.

## 2026-09-21T18:51:14+05:00 final-QA predicate correction

- Observed: a read-only final-QA script exited `1` because it required the literal phrase `global SVC #6 reachability remains unresolved`, while the report's accurate wording is `does **not** prove global SVC #6 unreachability`. The diagnostic showed the only failing predicate was that wording check; no artifact or project output was changed.
- Intent: rerun final readback using the observed report wording, re-execute the identical BASELINE/MODIFIED/ROLLBACK marker predicate, and reopen all four roles.
- Expected effect: confirm report/result consistency and same restored-baseline behavior.
- Rollback: read-only checks only.
- Observed corrected final-QA: verifier summary PASS 83/83; predicate outputs baseline `item17-reachability=ABSENT`/exit `1`, modified `item17-reachability=PASS_83_83_UNRESOLVED`/exit `0`, rollback `item17-reachability=ABSENT`/exit `1`; stderr empty in all three; rollback copy hash equals baseline.
- Final reopened role hashes: MODIFIED_FILE `4a073cee986a18c456442abbab477e81d51fb09d35003c1fefc1aa1b818c81d1`; DIFF_FILE `7867c2224d8fbf4abfa8891ca9e26fc829779bf9d44c64e2a13320922339d393`; VERIFICATION.txt `1dff546c222998e413203a414cb18428acd5844306493f5110c63da89f9c9788`; ROLLBACK.sh `ed15decf2ef8be242754c8fdebb207df1f09d87c0f94a0a02f6f96d2ccb7b085`.
- Reopened G7 memory record `memory/incidents/2026-09-21-item17-reachability-verifier-launch-correction.md` SHA-256 `ca36b8a1caf291881f5c2ae2a36ce911f434b91aad70b82059548f07e954973d`.
