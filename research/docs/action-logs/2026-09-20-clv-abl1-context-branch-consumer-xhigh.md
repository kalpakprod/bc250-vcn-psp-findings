# Exact CLV ABL1 context+0x78 consequent branches — intent

Timestamp: 2026-09-20, Asia/Almaty.
Actor: bounded executor luna-xhigh.
Target: exact ABL1 function branch after `0x107E4` and closest callee `0x10958`, continuing from the completed reader-output checkpoint.

Bounded hypothesis: the field comparisons at `0x107EC`/`0x107F2` select policy/timing values and dispatch them through a callback, rather than directly programming a hardware register. Discriminate with raw exact bytes, all three consequent paths, and the first callee instruction effect. Do not infer units/domain from numeric constants; do not repeat the previous 59-check reader verifier.

Pinned inputs:

- exact ABL1 `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, expected SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- exact Thumb listing `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`, expected SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- completed reader-output result is reused by hash only: `evidence/firmware-audit/20260920-clv-abl1-reader-output-context-xhigh/abl1-reader-output-context-result.json`, expected SHA-256 `6abae87817c9aa5baf8565524b071f5fae6d19ad5e478d140e22fdea0da42c21`.

Next executable action: create and execute the uniquely owned verifier under `evidence/firmware-audit/20260920-clv-abl1-context-branch-consumer-xhigh/`. It will assert the raw branch consequences, `R9=0x618` token handoff, three convergent `0x10958` calls, and `0x10958` indirect callback dispatch `[R0+0x660]` with no direct MMIO/register write in that callee.

Expected effect: only this evidence directory, one report, and this action log. No firmware, hardware, settings, memory, shared plan, MCP/Cutter, install, global configuration, candidate, source or commit changes.

Rollback: remove only this uniquely named evidence directory, report and action log.

## Corrections during verifier execution

The verifier was executed against unchanged pinned inputs. Initial raw-byte expectations for Thumb-2 display-order words were corrected to the observed little-endian bytes only; no input/disassembly bytes changed. Captured failed attempts remain in `verifier.stderr` only for the latest run; the assertion details were: `0x10496` expected display-order `f2406918` versus raw `40f21869`, then subsequent display-order mismatches at `0x107EC`, `0x10804`, `0x10812`, `0x10824`, `0x10826`, `0x1083C`, and call-site slices. Corrections changed only verifier expected literals and listing parser.

## Observed result

Command: `python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context-branch-consumer-xhigh/abl1_context_branch_consumer_verify.py`.
Observed exit status: `0`; checks `79/79 PASS`; captured stderr empty. Literal stdout is in `verifier.stdout`; machine result is `abl1-context-branch-consumer-result.json`.

Observed branch result: the `0x107EC` compare-to-`0x3E8` path reaches `0x107FA -> 0x107FE -> 0x10802 -> 0x1081E` and selects `R2=0x264` or `0x464` based on R5/R6/R7 comparisons. The `0x107F2` compare-to-`0x4B0` path reaches `0x1080E -> 0x10816 -> 0x1081E` and selects `R2=0x260` when R5 matches R7 or R6. The default path `0x107F8 -> 0x1081C -> 0x1081E` selects `R2=0`. All paths converge on indirect dispatcher calls.

The consequent body writes context-child data at `[R4+0x2C4]+0x06/+0x44/+0x46/+0x4C` and issues more indirect dispatcher calls with observed tokens `0x205`, `0x1F7`, `0x21E`, `0x622`, `0x2BA..0x2BD`, derived `0x2BE`, and later derived values. The closest callee `0x10958` loads `[R0+0x660]` into R12, maps incoming R1->R2 and R2->R3, sets R1=1, and executes `BX R12`; its body contains no direct MMIO/register store. The callback target/effect is not bound to a direct in-image executable target for this context, so hardware-register programming is unproven.

## Correction intent: distinguish child structure stores from hardware registers

Timestamp: 2026-09-20T09:34:55.425740+05:00

Review of the raw sequence shows 0x10854 advances R4 to context+0x2C4 and 0x1085A loads the child pointer from [R4]; the later STRH instructions target that child pointer, not [R4+0x2C4]+offset and not an MMIO address. The prior result/report wording therefore needs correction before the claim is used.

Correction action: add raw assertions for child-pointer load sites 0x1085A/0x10862/0x1086C/0x10876; revise the machine result and report to state writes through R1=[context+0x2C4] into child offsets +0x06/+0x44/+0x46/+0x4C; state these are in-memory structure stores with unknown semantics, not direct hardware programming. Then run a fresh verifier and reopen the result/report/log. Pinned inputs remain unchanged.

## Correction after expanded pointer-store verifier

Timestamp: 2026-09-20T09:39:30.607974+05:00
Observed command: `python3 -B evidence/firmware-audit/20260920-clv-abl1-context-branch-consumer-xhigh/abl1_context_branch_consumer_verify.py`.
Observed exit status: `1`. Captured stderr: `AssertionError: listing instruction at 0x1095e: got False, expected True`. The listing shows 0x1095E is `MOV R3,R2`; the `MOV R2,R1` is 0x10960. The raw pair check was already correct; only the semantic listing address assertion was mislabeled.

Correction intent: change only the listing assertion addresses/operands (0x1095E=>MOV R3,R2; 0x10960=>MOV R2,R1), then rerun the branch verifier. Keep all pinned bytes and previous 79-check execution inputs unchanged.
\n## Corrected child-pointer interpretation and final verifier result\n\nTimestamp: 2026-09-20T09:41:58.370608+05:00\nThe previous result/report worded the child structure stores as if they were at `[R4+0x2C4]+offset`; this was too coarse. Raw `0x10854` adds `0x2C4` to R4, `0x1085A` loads R1 from `[R4]`, and the subsequent halfword stores use R1+`0x06/0x44/0x46/0x4C`; R4 is restored at `0x1087E`. They are indirect in-memory child-data writes; not direct MMIO evidence. The report and machine result were corrected accordingly.\n\nFresh command `python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context-branch-consumer-xhigh/abl1_context_branch_consumer_verify.py` exited `0`: `89/89 PASS`; stderr empty. Branch-selected prior R2 values `{0,0x260,0x264,0x464}` reach dispatcher with incoming R1=`0x61E`; 0x10958 maps the callback arguments as R1=1, R2=0x61E, R3=selected value before BX R12. No callback effect or hardware clock programming is proven.\n

## Authoritative corrected child-pointer result

Timestamp: 2026-09-20T09:44:20.809911+05:00
The prior child-pointer correction paragraph was appended with literal backslash-n escapes, so it did not render as normal Markdown. This section is the authoritative correction and supersedes that malformed tail. It records the checked raw dataflow: at `0x10854`, `R4` advances by `0x2C4`; at `0x1085A`, `R1=[R4]`; stores at `0x1085C/0x10864/0x1086E/0x10878` target `[R1+0x06/+0x44/+0x46/+0x4C]`; and `0x1087E` restores `R4`. These are indirect child-object stores, not direct MMIO evidence.

Fresh verifier command: `python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context-branch-consumer-xhigh/abl1_context_branch_consumer_verify.py`.
Observed exit status: `0`; checks `89/89 PASS`; stdout and stderr are retained in `verifier.stdout`/`verifier.stderr`, with stderr empty. The first callback dispatcher call at `0x10820` carries `R0=context`, incoming `R1=0x61E`, and branch-selected `R2 ∈ {0,0x260,0x264,0x464}`; `0x10958` forwards as `R1=1`, `R2=0x61E`, `R3=selected value`, then `BX R12`. The callback target/effect remains unknown for this context, so direct hardware clock programming is not proven.

Corrected research report: `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl1-context-branch-consumer-xhigh.md`. Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context-branch-consumer-xhigh/abl1-context-branch-consumer-result.json`. No source inputs changed.

## Final scoped code check and role readback

`procoder check /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context-branch-consumer-xhigh/abl1_context_branch_consumer_verify.py` exited `0`: 0 unformatted, 0 unchecked, 0 out-of-scope, 0 blocking; the broad repository scan reported 155 non-blocking hygiene findings. Python tests were not collected (`0 passed, 0 failed`), which is recorded as unrun, not green.

Reopened the verifier, machine result, stdout/stderr, report, and this log. The verifier result is 89/89 PASS; stdout is the direct command output; stderr is empty. Input hashes remain pinned as specified above. No firmware, hardware, settings, source inputs, memory, or shared project plan changed in this bounded execution.
