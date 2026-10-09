# ABL1 P-state input/dataflow follow-up — intent

- Timestamp: 2026-09-21T13:45:00+05:00 (+05:00)
- Actor: `/root/pstate_precedence` (bounded executor)
- Target: exact CLV 5.00 ABL1 payload only; read-only offline analysis.
- Scope: trace the producers of the `0x95FC` function's stack fields `[SP+0x164]` and `[SP+0x174]`, and the callback that derives `context+0x0C` consumed as `channel+0x20`. Do not repeat the previous 47-check branch/min verifier and do not overlap the parallel APOB/APCB handoff track; this slice stays within ABL1 local helper/dataflow windows `0x6C20..0x6D20`, `0x95FC..0x98AA`, and `0x109BC..0x10A2C`.
- Baseline: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; exact ABL1 `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-sync-stage2-abl-memory/ABL1-clv-decompressed.bin`, 94,624 bytes, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Existing route: reuse the exact ABL1 Thumb disassembly and existing static producer reports. The prior report left `[SP+0x164]`/`[SP+0x174]` semantically unresolved and did not decode the full `0x6C20` initializer or `0x109BC` channel-pointer writer. No ROM/APOB/APCB rewrite, hardware, network, installation, or new dependency.
- Hypothesis: `0x95FC` receives a local status block from `0x6C20`; its `+0x4` and `+0x14` fields are locally produced before the gates. The `+0x52C` callback at `0x109BC` normalizes the channel index and derives `context+0x0C` from the context's `+0x8/+0x70` table, which is the pointer later read at `0x9672`/`0x9758`/`0x983C`.
- Next executable action: fresh `llvm-objcopy`/`llvm-objdump` windows and a byte-backed verifier over exact address/branch/store relationships; preserve stdout, stderr, statuses, and hashes in `evidence/firmware-audit/20260921-abl1-pstate-inputs/`.
- Acceptance: one new producer/dataflow edge toward the known clock/memory-policy inputs, or a concrete missing-code boundary. Do not label either stack field `MemoryPstate`/`FclkDpm` without a direct join. Preserve `AmdSetup+0x316=0x24` (1800-labelled request) as an unchanged read-only baseline.
- Stop condition: helper field writers and channel-pointer derivation are byte-backed, or the exact ABL1 window ends at an opaque call/indirect pointer. No runtime or physical-clock claims.
- Rollback: remove only this report, action log, and unique evidence directory; prior CLV inputs and evidence remain unchanged.

## Verifier attempt 1 and correction intent

- Timestamp: 2026-09-21T13:49:00+05:00
- Command: `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260921-abl1-pstate-inputs/abl1_pstate_inputs_verify.py > evidence/firmware-audit/20260921-abl1-pstate-inputs/verifier.stdout 2> evidence/firmware-audit/20260921-abl1-pstate-inputs/verifier.stderr; printf '%s\\n' "$?" > evidence/firmware-audit/20260921-abl1-pstate-inputs/verifier.exit`
- Observed exit: `1`; stderr contains `NameError: name 'r1' is not defined` in the checker tuple for instruction `0x109F2`; no JSON result was emitted. This is a verifier source typo, not a disassembler/input failure.
- Correction intent: preserve attempt-1 verifier/source/stdout/stderr/exit in this task's `attempt1/`, correct the tuple to pass mnemonic `ldr` as a string, and rerun unchanged input/disassembly checks. No source/image or analysis scope change.

## Verifier attempt 2 and diagnostic intent

- Timestamp: 2026-09-21T13:51:00+05:00
- The syntax correction removed the NameError, but the verifier still returned exit `1`, `51/54 PASS`, with stderr empty. The raw dumps and source hashes are valid; the failed assertion identities were not included in the first result schema.
- Diagnostic intent: preserve this attempt under `attempt2/`, add `checks_detail` to the task-owned machine result and print only failed check labels in a changed command, then fix only a demonstrably incorrect matcher/assertion. No new payload scan, baseline change, or firmware action.

## Verifier attempt 3 and serialization correction intent

- Timestamp: 2026-09-21T13:52:00+05:00
- Diagnostic run exited `1` while serializing its result: `TypeError: Object of type bytes is not JSON serializable` from the empty-stderr hash check's raw-byte value. It did not execute additional disassembly or change the previous `51/54` findings.
- Correction intent: preserve attempt-3 stdout/stderr/exit and verifier source under `attempt3/`; keep checks unchanged and convert byte values to a JSON-safe representation in the task-owned verifier before rerun.

## Verifier attempt 4 and operand-notation correction intent

The diagnostic result schema now serializes and reports check identities. The unchanged checks produced exit `1`, `51/54 PASS`; failures are only the three `0x109F8/0x109FC/0x10A00` operand matchers. Fresh objdump prints Thumb shifts as decimal `#3/#4`, while the expected regex used `#0x3/#0x4`. The code bytes/listing are valid and no source or input changed. Preserve this attempt under `attempt4/`; correct only these operand regexes to accept LLVM's exact decimal notation, then rerun the same checks.

## Final observed result

- Timestamp: 2026-09-21T13:55:00+05:00 (+05:00)
- Fresh window commands: six `llvm-objdump -D --triple=thumbv7` runs against the existing exact CLV object; all exit `0`, all stderr files empty. LLVM `22.1.8`.
- Final verifier command: `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260921-abl1-pstate-inputs/abl1_pstate_inputs_verify.py > evidence/firmware-audit/20260921-abl1-pstate-inputs/verifier.stdout 2> evidence/firmware-audit/20260921-abl1-pstate-inputs/verifier.stderr`; exit `0`, literal stdout `PASS`, `54/54` checks, stderr empty.
- Machine result: `evidence/firmware-audit/20260921-abl1-pstate-inputs/abl1-pstate-inputs-result.json`; current status `PASS`, `failed=0`, `passed=54`.
- New edge 1: direct `0x95FC -> 0x6C20 -> 0x6D10` local status producer makes `[SP+0x164] == 1` if the call returns, forcing the `BLS 0x9744` branch at `0x9646`; the multi-channel path is not reached on this direct path.
- New edge 2: `0x6C20` locally prepares `[SP+0x174] == 1` through `0x6CA0=0`, `0x6CD8=0`, and `0x6C46 -> 0x6C54 -> 0x6C4A`; this gate is downstream of the first bypass gate.
- New edge 3: `0x109BC` derives `[context+0x0C] = [context+0x8]+0x70 + 0x170*normalized_index`; `0x95FC` accesses this pointer's `+0x20` field.
- Failed attempts 1-4 are preserved under `attempt1/` through `attempt4/`: NameError, missing failure-detail schema, JSON bytes serialization, and decimal-vs-hex operand matcher. These were verifier-only corrections; source hashes and fresh disassembly inputs did not change.
- No ROM, firmware, NVRAM, register, candidate, hardware, network, installation, or shared memory write occurred.
- Unresolved: outer-context/table producer, optional `+0x3B0` callback, runtime invocation, direct native P-state/APOB/APCB/INV join, units, training, 1800 application, 1:1:1, and hardware acceptance.
