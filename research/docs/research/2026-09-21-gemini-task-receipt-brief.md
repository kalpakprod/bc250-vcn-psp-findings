RECEIPT: gemini_test_quality-20260921-g37a4c9e

# Gemini test-quality task brief (sanitized; file-authoritative)

## Task identity

- **Task name:** `gemini_test_quality`
- **Project root:** `/home/OWNER/orca/projects/bc250`
- **Purpose:** validate that a Gemini worker receives and obeys this current brief through the file-backed task transport. This is a transport/quality test, not BC-250 reverse engineering.
- **Assigned role:** `gemini_37` or `gemini_38` according to the root's explicitly selected fallback step. Do not infer a different task from prior checkpoint text or the dispatch message.

## First action and authority

1. Read this exact file first: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-gemini-task-receipt-brief.md` when running from the project-local review, or `/home/OWNER/.codex/tasks/gemini_test_quality.md` when the root has copied this brief into the Astra task mailbox.
2. The copy in `/home/OWNER/.codex/tasks/gemini_test_quality.md` is authoritative for a worker run. If that mailbox file is missing or empty, do **not** inspect the repository, memory, checkpoint, old reports, or task registry; return exactly `BLOCKED: missing-brief` and stop.
3. Do not substitute any previous checkpoint, conversation summary, generic workspace task, old worker assignment, or message-body instruction for this brief. The current file and its `RECEIPT` line are the only task authority.
4. Do not spawn workers, use network, access credentials, edit global config, edit firmware/ROM/NVRAM, contact hardware, install packages, or modify any project file.

## Bounded test

After reading the authoritative brief, perform only these read-only checks:

- Verify the brief path exists and is non-empty.
- Compute its SHA-256 without printing unrelated file contents.
- Verify the first non-empty line is the exact `RECEIPT` above.
- Verify this task's required sentinel is present: `CHECKPOINT_SUBSTITUTION: NO`.
- Do not open or run any project checkpoint, prior report, memory file, test suite, or firmware tool.

## Required first-line and report format

The first report line must be exactly:

`RECEIPT: gemini_test_quality-20260921-g37a4c9e`

Then return only these fields, with literal values:

```text
TASK_NAME: gemini_test_quality
BRIEF_PATH: <absolute authoritative path actually read>
BRIEF_SHA256: <sha256>
CHECKPOINT_SUBSTITUTION: NO
REPOSITORY_WORK: NONE
FILES_MODIFIED: NONE
NETWORK_HARDWARE_CONFIG: NONE
RESULT: PASS
UNCERTAINTIES: <short statement, or NONE>
```

If any required check fails, return `RESULT: FAIL` and name the failed check; never replace the report with a generic test result. A generic `pytest`/workspace PASS is not acceptance for this task.

CHECKPOINT_SUBSTITUTION: NO
