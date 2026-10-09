# CLV ABL1 UCLK descriptor runtime-table boundary — intent

Timestamp: 2026-09-20T09:20:00+05:00 (+05:00)
Actor: luna-xhigh bounded executor
Target: exact CLV ABL1 helper path after 0x4800/0x49CC, with exact pinned ROM APCB bytes used only as a raw storage contrast.

Bounded one-chain action: follow Uclk descriptor first token 0x20 into provider selector 0x0F, recover the exact runtime table key and 0x6374/0x6238 storage path, then compare that runtime key against the pinned ROM APCB without assigning an unsupported CBSG schema. Stop at the first storage indirection if no direct flash-row mapping exists.

Pinned inputs:

- ROM SHA-256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8.
- Exact ABL1 SHA-256 af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a.
- Existing 0x4800/0x49CC result SHA-256 3950e5136254db2aa9c96c91caba4d48da4a11c369b38a36703c9f54cef45ee9.
- Existing APCB parser output SHA-256 503e4f525f4372903b23ea9320c77f7b0b39250f310d80a1b7565eb98b39f394.

Next executable action: run unique verifier evidence/firmware-audit/20260920-clv-abl1-runtime-heap-boundary/abl1_runtime_heap_boundary_verify.py.

Expected effect: new evidence/report/action-log artifacts only. No firmware, hardware, settings, shared plan/memory, global config, MCP/Cutter, candidates, source, commits, or subagents.

Rollback: remove only this unique evidence directory, report, and action log.

## Correction after verifier execution

Timestamp: 2026-09-20T09:25:00+05:00 (+05:00)
Observed execution error: verifier exited `1` before checks because the project `scripts` directory was not on `sys.path` when launched by absolute path (`ModuleNotFoundError: No module named 'scripts'`). No input or firmware artifact was involved.

Correction: add the project root to the verifier import path only; retain the terminal error. No shared state changed.

## Correction after second verifier execution

Timestamp: 2026-09-20T09:26:00+05:00 (+05:00)
Observed execution error: exact `movw r6,#0xA04E` expected encoding was written in display rather than little-endian raw order. Measured bytes: `4a f2 4e 06`.

Correction: change that raw-byte expectation only.

## Correction after third verifier execution

Timestamp: 2026-09-20T09:27:00+05:00 (+05:00)
Observed execution error: provider descriptor-store window again used display-order bytes and a shorter expected span. Exact bytes at `0x4B34..0x4B3B` are `09 a8 29 99 09 96 01 f0`.

Correction: update the exact raw window only.

## Correction after fourth verifier execution

Timestamp: 2026-09-20T09:28:00+05:00 (+05:00)
Observed execution error: 0x6374 linked-list signature expected one extra byte beyond the selected slice. The exact selected window ends at the conditional branch bytes `...04 d0`.

Correction: align expected signature length to the selected exact window.

## Correction after fifth verifier execution

Timestamp: 2026-09-20T09:29:00+05:00 (+05:00)
Observed execution error: 0x6374 table-entry comparison window used disassembly display order. Exact raw bytes are `05 68 1c 68 ac 42 04 d0 db 68 5c 1c 0b d0`.

Correction: use the exact raw window.

## Correction after sixth verifier execution

Timestamp: 2026-09-20T09:30:00+05:00 (+05:00)
Observed execution error: 0x6374 match-return window used display-order bytes. Exact raw sequence is `46 b1 59 7a 5a 18 10 32 82 60 5a 68 51 1a 41 60 00 20`.

Correction: update the exact raw window.

## Correction after seventh verifier execution

Timestamp: 2026-09-20T09:31:00+05:00 (+05:00)
Observed execution error: 0x6238 prologue check expected one extra byte beyond the selected 16-byte span.

Correction: align expected bytes to the selected exact span.

## Correction after eighth verifier execution

Timestamp: 2026-09-20T09:32:00+05:00 (+05:00)
Observed execution error: verifier labelled literal `0x73000` as `0x3000`. Direct byte read at payload `0x6360` is `00 30 07 00` -> `0x00073000`; the adjacent word is ASCII `HEAP`.

Correction: update only expected literal and all semantic wording to the exact `0x73000` value. This supersedes the preliminary intent note's generic mention of heap base, which did not specify an address. No input changed.

## Correction after ninth verifier execution

Timestamp: 2026-09-20T09:33:00+05:00 (+05:00)
Observed execution error: 0x6238 cache-search check spanned too many instructions and used display-order bytes. Direct raw windows have been narrowed to separate instructions, starting `38 68 88 42` (load heap head, compare signature).

Correction: narrow the assertion windows to exact direct-read instructions; retain the error.

## Correction after tenth verifier execution

Timestamp: 2026-09-20T09:34:00+05:00 (+05:00)
Observed execution error: entry-scan assertion used display order; direct raw bytes at `0x627C..0x6283` are `d8 f8 00 30 93 42 03 d1`.

Correction: align the expected signature to these exact little-endian bytes.

## Observed result

Timestamp: 2026-09-20T09:40:00+05:00 (+05:00)
Actor: luna-xhigh bounded executor

Command:

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-runtime-heap-boundary/abl1_runtime_heap_boundary_verify.py
```

Observed exit status: `0`; stderr empty; verifier `PASS`; checks `32`.

Literal stdout is preserved at `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-runtime-heap-boundary/verifier.stdout`.

Final hashes:

```text
3614f60bed0058f54f9ac8097ad4dc2e9003f8b3c4fff1eab3a011d44fd83fb2  evidence/firmware-audit/20260920-clv-abl1-runtime-heap-boundary/abl1_runtime_heap_boundary_verify.py
46a126825991b945716fe6cf52b4b68df5054304a16feac086067451a2dc5ce5  evidence/firmware-audit/20260920-clv-abl1-runtime-heap-boundary/abl1-runtime-heap-boundary-result.json
0ffeaa958ea5afc12ad546d1d5fc2dd068042d39eedff377aa2d1c5d702a0158  evidence/firmware-audit/20260920-clv-abl1-runtime-heap-boundary/verifier.stdout
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  evidence/firmware-audit/20260920-clv-abl1-runtime-heap-boundary/verifier.stderr
396338e512931454fc0dd5aae3d369a5697f0de1b84dd922474581fb51b53b8f  docs/research/20260920-clv-abl1-runtime-heap-boundary.md
```

Finding: first UCLK descriptor `0x20` reaches runtime key `0xA04E`; 0x6374/0x6238 read a runtime HEAP-linked table at `0x73000`. The key is absent from pinned ROM; APCB/CBSG-to-runtime conversion is not recovered. No semantic clock claim.

Readback: reopened verifier, result JSON, stdout/stderr, report and this log; JSON parse passed and final hashes match. No firmware/hardware/settings/shared-state change. Rollback is deletion of this unique evidence directory/report/action log.

## Observed result

Timestamp: 2026-09-20T09:42:00+05:00 (+05:00)
Actor: luna-xhigh bounded executor

Command:

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-runtime-heap-boundary/abl1_runtime_heap_boundary_verify.py
```

Observed exit status: `0`; stderr empty; verifier `PASS`; checks `32`.

Final artifact hashes:

```text
3614f60bed0058f54f9ac8097ad4dc2e9003f8b3c4fff1eab3a011d44fd83fb2  evidence/firmware-audit/20260920-clv-abl1-runtime-heap-boundary/abl1_runtime_heap_boundary_verify.py
46a126825991b945716fe6cf52b4b68df5054304a16feac086067451a2dc5ce5  evidence/firmware-audit/20260920-clv-abl1-runtime-heap-boundary/abl1-runtime-heap-boundary-result.json
0ffeaa958ea5afc12ad546d1d5fc2dd068042d39eedff377aa2d1c5d702a0158  evidence/firmware-audit/20260920-clv-abl1-runtime-heap-boundary/verifier.stdout
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  evidence/firmware-audit/20260920-clv-abl1-runtime-heap-boundary/verifier.stderr
396338e512931454fc0dd5aae3d369a5697f0de1b84dd922474581eb51b53b8f  docs/research/20260920-clv-abl1-runtime-heap-boundary.md
```

Readback: verifier, machine result, stdout/stderr, report and action log reopened; JSON parse and role paths pass. No firmware, hardware, settings, shared plan/memory, global config, candidate, source, installation or commit changed.
