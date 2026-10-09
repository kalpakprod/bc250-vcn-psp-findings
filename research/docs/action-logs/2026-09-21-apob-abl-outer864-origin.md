# ABL1 outer+0x864 and HEAP source-argument correction — action log

## Intent (before owned evidence writes)

- Timestamp: 2026-09-21T16:00:00+05:00 (Asia/Almaty)
- Actor: delegated project executor (`gpt-5.6-luna`; offline read-only).
- Target: exact CLV donor `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; exact decompressed ABL1 payload SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- G7 correction scope: the prior owned HEAP report said `0x6B78` copied payload from `R10` and asserted the `0x006CD4D0` outer+0x864 pointer was that HEAP source. Reopen exact call frames/prototype and replace this unsupported join with the static byte-backed result; do not edit the prior report or evidence.
- Question: in the exact CLV ABL1 `$PS1` metadata / existing conditional payload-base map, is absolute pointer `0x006CD4D0` mapped into this payload or outside the ABL1 map? Is outer+0x864 overwritten after constructor `0xC00` and before the selector-0x0F HEAP call? What does the second `0x6238` argument mean at all direct callsites; is `0x6B78` memcpy or memset-like?
- Planned bounded test: fresh LLVM Thumb windows for FCLK caller `0x463C`, reader `0x1FB4`, helper `0x4800`, provider `0x49CC`, `0x6238`, `0x6B78`, constructor callers `0xB84/0xC00`; byte-reconcile decoded instructions to the exact payload. Compute stack argument provenance using raw prologues/outgoing stores. Scan only the exact field displacement/direct store pattern for +0x864; inspect relevant direct `0x6238` caller windows to avoid assigning a generic prototype from one call. Preserve native `$INV 0x11ED` and exact service `0x9E3B14C/message0x61/arg0xFF` as context. No PPI GUID recheck, no `0x1204`, no hardware/ROM/NVRAM/network.
- Existing route: exact CLV decompressed ABL1 plus `ABL1-exact.o` and existing full Thumb listing. Previous `34/34` custom byte verifier is insufficient for semantic argument claims because it matched hard-coded instruction bytes but did not model the ARM calling convention, compare 0x6B78 argument roles, or reconcile same-offset local stack slots across separate frames. Fresh disassembly plus byte reconciliation is required.
- Expected outcome: either a direct source provenance edge or a precise unresolved external/runtime boundary; record correction and evidence class.
- Rollback: remove only `evidence/firmware-audit/20260921-apob-abl-outer864-origin/`, `docs/research/2026-09-21-apob-abl-outer864-origin.md`, and this log.
- Acceptance event: one bounded verifier starts, emits result and exits; exact command, stdout/stderr/status and hashes are reopened.

## Correction to first verifier trial (before rerun)

The first verifier execution exited `1` at its first mnemonic anchor because the disassembly parser preserves tabs between mnemonics/registers while the expected anchor used a space. The instruction bytes had already reconciled; this was only an assertion text-normalization error. The verifier now normalizes whitespace for decoded mnemonic operands. No input artifact or evidence claim changed.

## Continuation-intent append correction and retained shell error

At 2026-09-21T16:38:11+05:00, an unquoted Bash heredoc containing Markdown backticks performed shell command substitutions. The shell emitted repeated `Permission denied`, `command not found`, and `No such file or directory` diagnostics, yet the compound command returned exit status `0`. Readback showed paths, hashes, offsets, and output literals missing from the appended intent section. The error was recorded in `memory/incidents/2026-09-20-bash-markdown-heredoc-expansion.md`; the malformed section is superseded by the literal Python rewrite below. Source ROM, ABL1 payload, guide, and old verifier artifacts were not changed by the failed append.

## Continuation intent — root byte-backed recheck and corrected-copy transaction (before new evidence writes)

- Timestamp: 2026-09-21T16:38:11+05:00 (Asia/Almaty)
- Actor: root project executor; offline and read-only with respect to source firmware.
- Reopened TARGET: exact donor `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; exact ABL1 payload `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`; source object `evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o`, SHA-256 `54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135`.
- Recheck: fresh LLVM 22.1.8 Thumb disassembly at aligned addresses `0x463C`, `0x1FB4`, `0x4800`, `0x49CC`, `0x4B54`, `0x6238`, `0x6316`, `0x6B78`, and constructor callers `0xB84/0xBD2/0xC00`; reconcile call-stack argument slots against raw payload bytes. Do not rerun the previous 34-check verifier.
- Guide transaction: preserve original `docs/guides/bc250-clv-111-evidence-draft.md` (SHA-256 `334d6b879156bb2ba773c2d2d766ddc54cbacd37e33e3eab3bab949d2fe8e065`) bytes; create corrected copy `docs/guides/bc250-clv-111-evidence-draft-corrected.md`, patch `evidence/firmware-audit/20260921-apob-abl-outer864-origin/DIFF_FILE.patch`, verification record `.../VERIFICATION.txt`, portable rollback `.../ROLLBACK.sh`, sibling baseline `.../BASELINE.md`, bounded report `docs/research/2026-09-21-apob-abl-outer864-origin.md`, and byte-backed output under `evidence/firmware-audit/20260921-apob-abl-outer864-origin/`.
- Expected effect: retract the prior `0x6B78` copy claim and the `outer+0x864` source join; retain the prior 34/34 replay as superseded evidence, with no implication of runtime, clock, training, voltage, or hardware behavior. Guide status remains DRAFT / NOT READY.
- Baseline behavior already observed before output writes: `python3 -B -c 'import json,pathlib,sys; p=pathlib.Path(sys.argv[1]); s=p.read_text(); status="withdrawn" if "HEAP claim status: WITHDRAWN" in s else "asserted"; print(json.dumps({"path":str(p.resolve()),"heap_claim_status":status},sort_keys=True)); sys.exit(0 if status==sys.argv[2] else 1)' /home/OWNER/orca/projects/bc250/docs/guides/bc250-clv-111-evidence-draft.md asserted` prints `{"heap_claim_status": "asserted", "path": "/home/OWNER/orca/projects/bc250/docs/guides/bc250-clv-111-evidence-draft.md"}`; stderr empty; exit 0.
- Matching modified and rollback checks will use the same predicate and their respective input role files.
- Rollback: run `ROLLBACK.sh` only against a disposable copy of the modified guide; it restores bytes from sibling `BASELINE.md`. Original guide/ROM/payload remain immutable. Preserve this append-only log and the old verifier artifacts.

## Correction to fourth verifier trial (before rerun)

The fourth run exited `1` on the expected raw byte order for the adjacent Thumb STR instructions. Disassembly halfwords `0x9200,0x9201` are little-endian raw bytes `00 92 01 92`, not `92 00 92 01`. The assertion was corrected. No input or interpretation changed.

## G7 correction: ABL1 hash transcription

The continuation-intent line initially omitted the 12-character substring `6f1a3b44fd6d` from the exact ABL1 SHA-256. Direct `sha256sum` readback on the named 94,624-byte payload gave `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`; only the log transcription was wrong. The measured source hash is now reflected above.

## Correction to fifth verifier trial (before rerun)

The fifth run exited `1` because a listing-format extraction dropped the mnemonic column when comparing the two full-listing `#0x864` references. The fresh constructor window had already byte-reconciled `0xC29E` and `0xC2AE`; the direct-reference census now asserts their addresses, while the independent raw store-byte count identifies the only direct store at `0xC2AE`. No input or interpretation changed.

## Correction to sixth verifier trial (before rerun)

The sixth run exited `1` because the context-caller disassembly window ended at `0xA70`, before the second callsite's `0xA86` argument setup. The direct full listing locates that setup, but the fresh window must cover all four bounded direct callsites; the window was extended to `0xA70..0xAF0` (start retained at `0x9C0`). No claim changed.

## Correction to seventh verifier trial (before rerun)

The seventh run exited `1` because the verifier assigned the ORR instruction to RVA `0xA32`; direct fresh disassembly places it at `0xA30` (`0xA32` is the second halfword). The new window already reconciles bytes; the address assertion was corrected. No input changed.

## Intent — separate root verification after output-directory collision (before new writes)

- Timestamp: 2026-09-21T16:47:00+05:00 (Asia/Almaty).
- The first root-only verifier `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260921-apob-abl-outer864-origin/verify_abl1_arg_flow.py` returned exit `1`; stdout was empty and stderr identified a verifier expectation error: disassembly word `9200` was transcribed as raw bytes `92 00`, while exact payload offset `0x4664` is `00 92`. The correction is recorded in `memory/incidents/2026-09-21-thumb-halfword-byte-order.md`; no firmware mismatch was found.
- Directory-boundary correction: by the time root executed `mkdir -p`, another executor's `outer864_origin_verify.py` plus hyphen-named disassembly outputs had appeared in the same `20260921-apob-abl-outer864-origin` directory. Root will not run that script or overwrite its report/evidence. Root's underscore-named check files are separate. Root did rewrite `llvm-objdump.version` and captured `verifier.stdout/stderr` in the shared directory; no pre-write hashes were available for the former, so treat those shared basenames as replaced/uncertain provenance. No old 34-check verifier was rerun.
- New independent output scope: create the root-owned directory `evidence/firmware-audit/20260921-apob-abl-outer864-root-review/`; run only a bounded exact-byte check there, converting LLVM-displayed Thumb halfwords to raw little-endian bytes, and save stdout/stderr/status/result. Read-only inputs remain the hash-pinned ROM, ABL1 payload, and exact ELF wrapper.
- After that review, create a corrected copy of the guide with the false `0x6B78` source-copy and `outer+0x864` provider-source assertions withdrawn, plus a reconstructive patch, `VERIFICATION.txt`, and executable rollback; keep original guide bytes unchanged. Reuse the observed baseline status predicate and verify BASELINE/MODIFIED/ROLLBACK identically.
- Expected conclusion remains static only: on the bounded selector-0x0F path, `0x4B54` consumes the second stacked argument (zero); `0x6238` sets fill byte R1 to zero and `0x6B78` stores R1 repeatedly. The `outer+0x864` field's producer/dataflow and all hardware clock/training/voltage behavior remain unresolved.
- Rollback for the guide transaction remains a disposable-copy restore from a sibling baseline. No ROM/NVRAM/register/hardware/network/source input write is authorized.

## G6 method-class pivot after repeated verifier assertion failures

The owned correction history contains seven prior verifier attempts that ended on parser/anchor/window/mnemonic assertions; the root-only byte-order assertion trial also exited `1`. Per the circuit breaker, root will not run `outer864_origin_verify.py`, `verify_abl1_arg_flow.py`, or the old 34-check verifier again. The next check changes method class to direct aligned LLVM Thumb disassembly paired with `xxd -g1 -s OFFSET` raw-byte windows and manual AAPCS stack-slot reconstruction. This validates the exact bounded path without another assertion parser or overwrite of the concurrent evidence directory. The correction and measurement are recorded in `memory/incidents/2026-09-21-thumb-halfword-byte-order.md`.

## G7 correction persisted — bounded observed result

- Timestamp: 2026-09-21T16:20:00+05:00 (Asia/Almaty).
- Exact target remained the pinned CLV donor and extracted ABL1 (`ea578104…ca4cb8` / `af8cf562…6a74203a`); no input changed.
- **Correction:** prior report `docs/research/2026-09-21-apob-abl-heap-populator.md` misnamed `0x6B78` as a copy helper and conflated constructor-frame `[SP+0xA4]` with provider-frame `[SP+0xA4]`. Raw instructions show `0x6B78` is `STRB R1,[R0],#1` in a loop; `0x6238` sets `R1=0`, payload destination `R0=R5+0x10`, length `R2=[R5+4]`, and passes `R10` in ignored `R3`. This FCLK miss branch zero-fills; it does not copy R10/outer+0x864.
- **Argument provenance:** FCLK `0x463C` initializes its two reader stack slots to zero (`0x4664/0x4666`); reader `0x1FB4` loads them into R7/R9 and forwards R9; helper `0x4800` forwards the first helper stack arg as provider stack arg two. Provider frame is 52 saved bytes + 108 local bytes, so provider `[SP+0xA4]` is entry-SP+4 (second stack arg), zero for this FCLK path. `0x4B54` loads that zero before call `0x6238`.
- **Load-map result:** exact `$PS1 load_address=0`, payload length `0x171A0`; literal `0x006CD4D0` at ABL1 payload `0xC4B4` is outside payload-relative coordinates. The prior conditional base `0x57100` maps it to `0x6763D0`, also outside; no exact loader/runtime base establishes the target region. The 0x864 displacement has one explicit store site in the full listing (`0xC2AE`); alias writes remain unresolved.
- **Fresh tool event:** LLVM `22.1.8`; 21 stored `llvm-objdump` windows have exit `0`/empty stderr and their decoded bytes were reconciled to the exact ABL1 payload by the verifier before final output assembly. The orchestration command itself exited `1` at result serialization with `NameError: toolver is not defined`; therefore no machine `PASS` result is claimed from that script. This error is retained in `evidence/firmware-audit/20260921-apob-abl-outer864-origin/verifier.stderr`.
- **Owned correction report:** `docs/research/2026-09-21-apob-abl-outer864-origin.md`, SHA-256 `632ce02cca513e6a27c867bb1be91804b5a365f06de31bd33693204baecb5478`.
- **Owned evidence path:** `evidence/firmware-audit/20260921-apob-abl-outer864-origin/` (fresh windows/captures only). No old report, old verifier, prior result, ROM, firmware, NVRAM, hardware, shared plan, or shared memory was edited.
- **Next for root/guide-review owners:** propagate the correction to the goal-continuation and clock-independent review records before any follow-up uses the prior source-copy narrative. Direct inter-agent send capability was not exposed to this subagent; the correction is persisted at the new report path for forwarding.

## Correction — `xxd` unavailable; retain failure and use `od`

The root raw-byte capture command `xxd -g1 -s 0x4664 -l 8 .../ABL1-clv-decompressed.bin` returned shell error `/usr/bin/bash: line 28: xxd: command not found`; the captured `.exit` is `127`. The surrounding shell used `set -e`, so the tool cell ended with exit `1` after the earlier nine direct disassembly windows had all exited `0`; only the first raw-byte window was attempted. No source or guide changed. The raw-byte method class remains the G6 pivot, but use available coreutils `od -An -tx1 -v -j OFFSET -N LENGTH` instead, preserve the xxd command/error, and verify each output/stderr/status.

## Evidence-directory ownership collision and handoff

During readback at 2026-09-21 16:58+05 I found pre-existing root-created artifacts dated 16:46 in the nominal output directory (`verify_abl1_arg_flow.py`, its `*_*.cmd.json` and window captures). My additional uniquely named artifacts are timestamped 16:50/16:58. I did not edit the root-created verifier or its captures. The `SHA256SUMS.final` I generated after discovering those files covers both sets and must not be treated as a single-owner manifest; root must decide how to reconcile/replace it. All findings in this report are independently supported by the fresh `*-*.stdout` windows and byte reconciliation recorded in my verifier, whose final result assembly failed with the NameError above.

Root requested propagation to `read_current_goal` and `clock_independent_review`. Direct inter-agent send capability was not exposed to this subagent; correction is persisted at `docs/research/2026-09-21-apob-abl-outer864-origin.md` for root to forward. No further tracing or writes to the shared evidence directory are performed here.

## Intent — isolated verifier correction rerun (before new evidence writes)

- Timestamp: 2026-09-21T17:15:30+05:00 (Asia/Almaty).
- Actor: current project executor; offline, read-only with respect to source firmware.
- TARGET: prior verifier copy `evidence/firmware-audit/20260921-apob-abl-outer864-origin/outer864_origin_verify.py`, preserved unchanged; source input artifacts remain the pinned CLV ROM, decompressed ABL1 payload, exact ELF object, and existing full listing.
- GOAL: create a fresh uniquely owned evidence directory and apply only two corrections to a copied verifier: retarget `OUT` to that directory and initialize `toolver` with one `llvm-objdump --version` subprocess result. Do not alter instruction expectations, firmware facts, or the mixed-owner directory.
- Planned outputs: corrected copied verifier, exact unified diff against the failed verifier, verifier stdout/stderr/exit, machine result JSON, per-window captures, one independent single-case `0x6B78` `llvm-objdump` stdout/stderr/exit capture, and final hash manifest.
- Expected effect: the previously observed `NameError: name 'toolver' is not defined` is removed while all existing byte/dataflow checks run unchanged in an isolated output scope; the verifier should emit a machine PASS only if every existing check passes.
- Rollback: remove only the fresh isolated evidence directory; leave the prior failed run, mixed-owner directory, source ROM/payload/object/listing, and reports unchanged.
- Acceptance event: corrected verifier process starts and exits with a captured event; all four output roles (modified verifier, diff, verification record, rollback script) are reopened, and the independent `0x6B78` command is captured with literal stdout/stderr/status.
- Safety: no ROM, NVRAM, register, hardware, network, or firmware write.

## Correction to isolated verifier rerun (before next patch/write)

- Timestamp: 2026-09-21T17:16:40+05:00 (Asia/Almaty).
- Observed event: the copied verifier started with the two requested fixes, all 21 LLVM windows again exited `0` with empty stderr, and final result assembly reached JSON serialization; it exited `1` with `TypeError: Object of type bytes is not JSON serializable` because existing `ck()` records retain byte-valued `$PS1` magic (`got`/`expected`).
- This is a verifier serialization defect, not an input or instruction-expectation mismatch. The `toolver` `NameError` did not recur.
- Planned smallest follow-up: preserve the first isolated rerun captures under distinct names, then add only a JSON `default` serializer converting bytes/bytearray to hex; do not change any instruction expectations, checks, source paths, or firmware facts. Recompute the exact diff against the unchanged failed verifier baseline.
- Expected effect: result JSON becomes parseable while retaining byte checks as hex strings; the machine verifier can emit its existing PASS summary.
- Rollback: remove the isolated directory; the failed mixed-owner directory and the preserved first isolated rerun captures remain untouched.

## Observed result — isolated verifier correction rerun (2026-09-21T17:18:00+05:00)

- Fresh output directory: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-outer864-origin-isolated/`; the mixed-owner origin directory was not modified.
- Original failed run retained: exit `1`, `NameError: name 'toolver' is not defined` in `.../outer864_origin_verify.py`; source hash `9e3ae148c72c333a0816e7b90ba70d359691eef297e537d89a2be655fec05241`.
- Corrected verifier command exited `0` with empty stderr. Literal stdout was the JSON PASS summary: `status=PASS`, `checks_passed=102`, `checks_failed=0`; `pointer=0x006CD4D0 ... runtime map unresolved`; `fclk_provider_aux=zero`; `fill_semantics=0x6B78 repeats R1 byte ... not memcpy`.
- A first isolated rerun after OUT/toolver correction reached final JSON assembly and exited `1` with `TypeError: Object of type bytes is not JSON serializable`; captured as `verifier-first-rerun.stdout/.stderr/.exit`. The follow-up bytes-to-hex default changed only serialization and allowed the existing 102 checks to emit their result.
- Independent helper event: `llvm-objdump -D --section=.data --triple=thumbv7 --start-address=0x6b78 --stop-address=0x6b84 .../ABL1-exact.o` exited `0`, stderr empty; it decodes `STRB R1,[R0],#1`, and independent `od` bytes are `01 e0 00 f8 01 1b 52 1e fb d2 70 47`.
- Rollback event: `ROLLBACK.sh` on a separate copy exited `0`, stderr empty; rollback target hash equals baseline `9e3ae148...fec05241`, modified verifier remains distinct.
- Final `sha256sum -c SHA256SUMS.final` exited `0`; 68/68 entries reported `OK`.
- Role paths: modified `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-outer864-origin-isolated/outer864_origin_verify.py`; patch `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-outer864-origin-isolated/DIFF_FILE.patch`; verification `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-outer864-origin-isolated/VERIFICATION.txt`; rollback `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-outer864-origin-isolated/ROLLBACK.sh`.
- Inputs and semantics remain unchanged: exact CLV ROM SHA-256 `ea578104...ca4cb8`, ABL1 payload SHA-256 `af8cf562...6a74203a`; static-only result, no hardware/network/ROM/NVRAM writes.

## G7 correction — isolated window count transcription (2026-09-21T17:19:00+05:00)

The preceding correction-intent section said “all 21 LLVM windows”; direct readback of the copied verifier's `specs` and its machine result shows 13 requested windows/command records in this isolated rerun. The 21 count belongs to the earlier mixed-directory artifact inventory and is not a claim about this fresh run. No evidence or semantic result changes: all 13 isolated window commands exited `0` with empty stderr, and the result remains 102/102 PASS.
