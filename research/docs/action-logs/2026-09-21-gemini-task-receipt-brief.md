# Gemini dispatch transport audit and test brief — action log

## Intent (recorded before writing the project-local brief)

- Timestamp: 2026-09-21 (Asia/Almaty; host timestamp to be added with the result).
- Actor: bounded workflow executor (`workflow_reset`); root retains dispatch and integration ownership.
- Target: new sanitized task brief `docs/research/2026-09-21-gemini-task-receipt-brief.md` and this action log only.
- Scope: inspect the locally documented Astra file-backed Gemini task transport and the version-matched Orca orchestration route; determine what is observed versus suspected for missing Gemini task inputs; create a harmless project-local test-quality brief for a future Gemini task with a unique receipt and an explicit no-checkpoint-substitution clause. Do not launch agents, alter global config/task files, reinstall tooling, access credential values, or inspect firmware/hardware.
- Inputs: `/home/OWNER/.codex/skills/astra-flash-team/SKILL.md`; `/home/OWNER/.codex/agents/gemini-37.toml` and `gemini-38.toml` only for nonsecret model/task-transport instruction fields; project `.agents/skills/orchestration/SKILL.md` stub; version-matched output of `/home/OWNER/.local/bin/orca-ide skills get orchestration --json`; CLI help; prior workflow report and sanitized task/registry references.
- Expected effect: one project-local brief that root can copy verbatim to the required global task mailbox for an explicitly named Gemini test-quality worker, plus this evidence/limits log. This task does not execute the worker or prove a Gemini result.
- Rollback: remove only this brief and this action log. Do not alter global configs, global task mailbox, other agents' outputs, firmware, source, or memory.
- Safety: inspect only task/model/developer-instruction metadata; do not read `.codex/config.toml`, credentials, tokens, secret env files, or raw unrelated project payloads.

## Correction and observed result — 2026-09-21T14:22:00+05:00 (Asia/Almaty)

- The first local brief draft placed its heading before the receipt. The bounded self-check caught this before any dispatch (`AssertionError` on the first non-empty-line check). The receipt line was moved to the first non-empty line. This is a process correction, not a worker failure; no global task file or config was touched.
- Final project-local brief: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-gemini-task-receipt-brief.md`.
- Final brief readback: `51` lines, `354` words, `2749` bytes; SHA-256 `0dd75eb2a7c1eb9d0cc4b5a275c2d3a9e89ec531845f4c76f01bc5e4cfb3bdb6`.
- Brief self-check: `PASS 7/7` for first-line receipt, unique task marker, explicit checkpoint stop, no generic-test substitution, required mailbox path, and no raw-secret markers. No worker was launched.

## Exact supported route for root

The only documented Gemini-safe route in the inspected local stack is the Astra file-backed task transport:

1. Copy the sanitized project brief byte-for-byte to `/home/OWNER/.codex/tasks/gemini_test_quality.md` **before** dispatch. The global mailbox path is required by both the Astra skill and the Gemini 3.7/3.8 role instructions; the project-local copy is the reviewable source and is intentionally not copied by this task.
2. Use the configured role `gemini_37` or `gemini_38` and its corresponding model/effort from the local role file (`agy/gemini-3.7-flash-high` or `agy/gemini-3.8-flash-high`, effort `high`). Do not invent a model alias or use the Orca `worker-start` route for Gemini.
3. Send only the one-line transport message: `Brief at /home/OWNER/.codex/tasks/gemini_test_quality.md — read it first, start your report with its RECEIPT marker.` Do not put the substantive task in the message body; follow-ups update the file first.
4. Accept the worker only if its first report line is the exact receipt and it contains `CHECKPOINT_SUBSTITUTION: NO`, the authoritative brief path/hash, and no unrelated test result. Missing receipt, `BLOCKED: missing-brief`, stale checkpoint output, or generic workspace PASS is a transport failure for this test—not a technical result.
5. If the route errors/returns empty twice, preserve the same brief and use the documented fallback chain once, recording which chain step completed. Do not repeat the same prompt through the same route.

## Evidence versus suspected cause

### Observed

- `/home/OWNER/.codex/agents/gemini-37.toml` and `gemini-38.toml` explicitly require: read `/home/OWNER/.codex/tasks/<task_name>.md` first; if missing/empty return `BLOCKED: missing-brief`; start the first report with the brief receipt; re-read the file on follow-up; message text is not authoritative.
- `/home/OWNER/.codex/skills/astra-flash-team/SKILL.md` independently specifies the same mailbox path, one-line spawn message, unique `RECEIPT`, file-first follow-ups, and receipt verification.
- The task mailbox exists, but bounded metadata search found no `gemini*` task filename and no `GEMINI37-ASSIGNMENT-913` marker. This is evidence that the inspected mailbox snapshot contains no matching brief/marker; it does not prove what a deleted or differently named brief contained.
- The version-matched Orca guide was loaded with `/home/OWNER/.local/bin/orca-ide skills get orchestration --json`. It says `worker-start` is the normal supervised path, but its help states `--model` supports Claude, Codex and Cursor opaque provider IDs; no Gemini route is advertised. `orca-ide status --json` observed `app.running=false`, `runtime.state=not_running`, `reachable=false`; `worker-list --include-remote` returned `runtime_unavailable`. No Orca worker was started.
- Root reported a Gemini 3.7 `fork_none` response missing the requested receipt and returning generic `30 pytest` output, and five Gemini 3.8 follow-ups returning unrelated old checkpoint output. Those reports are accepted here only as root-provided incident evidence, not independently replayed or promoted to model-capability findings.

### Suspected, not proven

- Highest-probability cause: the Gemini dispatch did not bind the exact task name to the expected `/home/OWNER/.codex/tasks/<task_name>.md` file, or the file was not present before launch; the generic workspace output is consistent with a contextless/fallback launch.
- A secondary possibility is a fork/session transport path that bypasses the configured Gemini role's file-first contract or reuses stale context; no runtime receipt or active Orca dispatch was available to distinguish these.
- It is **not proven** that Gemini 3.7/3.8 cannot follow the task, that a model alias is unavailable, or that repository tests were technically relevant.

## Boundary and no-dispatch status

- Read-only checks only; no agent launch, retry, network, global config/task-mailbox write, package installation, firmware, ROM, NVRAM, register or hardware operation occurred.
- This task provides a safe brief and route; it does not claim a Gemini worker result. Root must perform the one controlled test after copying the brief, then reopen and validate the returned receipt before treating it as evidence.

## Scope correction — 2026-09-21T14:23:00+05:00

One initial recursive `rg` discovery command crossed into unrelated `.codex` cache/task metadata and its output was truncated. It did not read `.codex/config.toml`, credential values, environment secrets, or private-key material, and none of the unrelated output was copied into the brief/report. Stop broad home/config-tree searches; subsequent transport verification is limited to the exact `GEMINI37-ASSIGNMENT-913` marker and task filenames in the task mailbox. No further unrelated task contents were opened.

## Intent — file-first Gemini task-mailbox preparation (before copy)

- Timestamp: 2026-09-21 (Asia/Almaty; exact host timestamp recorded with observed result).
- Actor: bounded workflow executor; root retains dispatch ownership.
- Source: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-gemini-task-receipt-brief.md`, expected SHA-256 `0dd75eb2a7c1eb9d0cc4b5a275c2d3a9e89ec531845f4c76f01bc5e4cfb3bdb6`.
- Target: `/home/OWNER/.codex/tasks/gemini_test_quality.md` only (task mailbox; not configuration).
- Intended operation: copy byte-for-byte only if the destination is absent. If the destination already exists, preserve it and compare only after checking it is the same task/receipt; never overwrite an unknown/pre-existing task.
- Expected effect: make the sanitized, receipt-bearing brief available at the exact path required by the Astra/Gemini transport instructions; do not launch an agent.
- Rollback: if this action creates the destination, remove only that exact file if its hash still equals the copied source hash and root requests rollback; never remove a pre-existing file.
- Safety: no `.codex/config.toml`, credentials, secrets, network, hardware, package, or firmware access/write.

## Observed result — 2026-09-21T14:36:30+05:00 (Asia/Almaty)

- Pre-copy inspection found the exact destination absent ().
- Executed , then on source/destination.
- Literal verification output: ; target ; bytes ; SHA-256 ; first line ; sentinel ; .
- The destination is a task mailbox entry only, not global configuration. No dispatch/agent launch occurred.
- Rollback remains removal of this file only if root requests it and its hash still matches the recorded source; no existing file was replaced.

## G7 correction — mailbox-copy log heredoc expansion (2026-09-21T14:37+05:00)

The mailbox copy and its immediate verification succeeded **before** the action-log result addendum. The first addendum used an unquoted `<<EOF` heredoc containing backticks and `$variables`; Bash evaluated command substitutions instead of preserving the intended literal record. The invalid/blank “Observed result” lines above are superseded by this correction and must not be treated as evidence.

Observed errors from that append command:

```text
/usr/bin/bash: line 15: /home/OWNER/.codex/tasks/gemini_test_quality.md: Permission denied
cmp: missing operand after ‘cmp’
cmp: Try 'cmp --help' for more information.
/usr/bin/bash: line 15: /home/OWNER/.codex/tasks/gemini_test_quality.md: Permission denied
/usr/bin/bash: line 15: 2749: command not found
/usr/bin/bash: line 15: 0dd75eb2a7c1eb9d0cc4b5a275c2d3a9e89ec531845f4c76f01bc5e4cfb3bdb6: command not found
/usr/bin/bash: line 15: RECEIPT:: command not found
/usr/bin/bash: line 15: CHECKPOINT_SUBSTITUTION:: command not found
```

The shell command later returned exit `0` because its final read/hash commands succeeded; the inner command-substitution errors are retained above. The no-clobber copy was not overwritten by the later command substitutions. Fresh readback then confirmed:

```text
COPY_RESULT=PASS
TARGET=/home/OWNER/.codex/tasks/gemini_test_quality.md
BYTES=2749
SHA256=0dd75eb2a7c1eb9d0cc4b5a275c2d3a9e89ec531845f4c76f01bc5e4cfb3bdb6
FIRST_LINE=RECEIPT: gemini_test_quality-20260921-g37a4c9e
SENTINEL=CHECKPOINT_SUBSTITUTION: NO
CMP_EXIT=0
```

Correction method: appended this section with a single-quoted heredoc (`<<'EOF'`) so literal backticks and `$` text were not executed. The exact mailbox/source byte comparison remains passed. No file outside the owned action log and requested task mailbox was written by the failed append command.

## Intent — record observed Gemini file-first acceptance failure

- Timestamp: 2026-09-21T14:46:22+05:00 (Asia/Almaty).
- Actor: bounded workflow executor; root owns the worker and run metadata.
- Target: this owned action log only. Keep the project-local brief and global task-mailbox copy unchanged; do not edit or delete the returned worker output.
- Source: root's current message reports that the exact Gemini 3.7 task name and one-line brief path were used after mailbox `cmp` passed.
- Expected record: distinguish the verified file/receipt state from the worker's failed response; do not retry, launch agents, search secret-bearing logs, or infer model incapability.
- Rollback: append-only record; no rollback needed. No configuration, secret, firmware, network or hardware action.

## Observed failed acceptance — root-reported worker result

Root reports the supported file-first dispatch attempt returned generic:

```text
Current: bc250-reverse-engineering / 30 pytest / awaiting instruction
```

The report lacked both `RECEIPT: gemini_test_quality-20260921-g37a4c9e` and the required `CHECKPOINT_SUBSTITUTION: NO` sentinel. Acceptance: **FAIL**. This is not a valid task result and is quarantined; the generic test count is unrelated to the brief.

Fresh local readback after the reported run shows the project brief and `/home/OWNER/.codex/tasks/gemini_test_quality.md` remain byte-identical (`cmp` PASS), each 2,749 bytes, SHA-256 `0dd75eb2a7c1eb9d0cc4b5a275c2d3a9e89ec531845f4c76f01bc5e4cfb3bdb6`; the mailbox still begins with the expected receipt and contains the sentinel. Therefore “the mailbox file was absent” cannot explain this **verified file-first attempt**. The worker did not demonstrate it read the brief; the reason remains unresolved.

No safe invocation receipt, dispatched-task name/header, effective-agent runtime metadata, terminal/transcript path, or copy of the exact launch envelope was provided to this executor. Do not inspect broad or secret-bearing session/config logs to guess. Root's observed result is recorded as root-provided evidence; no direct transcript was independently reopened.

Disposition: stop all Gemini retries for this task. Preserve both briefs and quarantine the generic response. Do not claim task completion, stale-checkpoint origin, or model incapability. Runtime input delivery/task-name association remains unresolved unless root can supply a safe, exact invocation receipt/transcript path.
