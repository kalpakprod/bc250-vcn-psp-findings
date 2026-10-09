# CLV ABL1 `[R6+0x3C4]` producer trace and callback-object identity boundary

## Current

Exact CLV ABL1 static trace completed one bounded edge: the pointer read by the `0x7378` initializer is loaded from its runtime `arg1+0x3C4` field and copied into the initializer parent at `R5+0x8`. The existing linear listing contains two direct writers to `+0x3C4`, but neither writer base is statically joined to that runtime `arg1/R6` object. The active callback object's identity therefore remains unresolved; the trace stops at that boundary.

## Conclusion

**Acceptance: PARTIAL — runtime object identity unresolved.**

Observed/static dataflow:

```text
0x7378:
  0x737c  R5 = arg0
  0x7384  R6 = arg1
  0x73ae  R4 = [R6 + 0x3c4]
  0x73b2  [R5 + 0x8] = R4
  0x73b6  R0 = [R4 + 0x4]
  0x73b8  [R5 + 0x40] = R0
  0x74de  R0 = R5
  0x74e0  BL 0xaf90

initializer slot evidence:
  0xb0c4  [initializer-body R4 + 0x660] = R0
```

The existing listing's only direct `+0x3C4` stores are:

```text
0xb93c   STR.W R0,[R1,#0x3c4]   ; R0 from PC-relative literal at 0xbcf8
0x10b2e  STR.W R0,[R4,#0x3c4]   ; R0 from [SP,#0x10]
```

No direct `BL 0x7378` row occurs in the existing listing. The linear listing has no decoded entry row at `0xAF90`; only the call target at `0x74E0` and downstream slot store `0xB0C4` are available. Consequently, a static join from either writer's base to `arg1/R6`, and then to the active dispatcher `R0+0x660`, is not established. The values/bases are runtime or indirect at this boundary.

## Fresh bounded execution

Command class: read-only Python check over the existing exact listing and ABL1 byte spans; no disassembly, token rescan, or verifier rerun.

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY' ...
```

Observed corrected execution: exit `0`; stderr empty. The first bounded attempt exited `1` because it incorrectly required a listing row at `0xAF90`; that row is absent. The correction relaxed only that assertion while retaining the exact `BL 0xAF90` and `0xB0C4` checks. The failed stdout/stderr and exit are retained in the evidence directory and action log.

Fresh stdout reported:

```text
rom size=16777216 (0x1000000) sha256=ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8
abl1 size=94624 (0x171a0) sha256=af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a
listing size=2586986 (0x27796a) sha256=b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65
RESULT: PARTIAL_UNRESOLVED_RUNTIME_OBJECT_IDENTITY
```

## Evidence and limits

- Evidence class: `observed-bytes` + `static-analysis`.
- Exact ABL1 body: 94,624 bytes (`0x171A0`), SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203A`.
- Exact CLV ROM: 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Existing listing: 2,586,986 bytes, SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- No runtime execution, HEAP/context capture, SVC#4 translation, physical register mapping, hardware behavior, or clock measurement was performed.
- No ROM, firmware, settings, hardware, candidate, or source input was modified.

## Artifacts

- Report: `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl1-r6-3c4-producer-trace.md`
- Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-r6-3c4-producer-trace/producer-trace-result.json`
- Corrected literal stdout: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-r6-3c4-producer-trace/trace-corrected.stdout`
- Corrected literal stderr: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-r6-3c4-producer-trace/trace-corrected.stderr`
- Corrected exit: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-r6-3c4-producer-trace/trace-corrected.exit`
- First failed exit/error: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-r6-3c4-producer-trace/trace.exit`, `trace.stderr`
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-abl1-r6-3c4-producer-trace.md`
- Correction record: `/home/OWNER/orca/projects/bc250/memory/incidents/2026-09-20-bash-markdown-heredoc-expansion.md`
