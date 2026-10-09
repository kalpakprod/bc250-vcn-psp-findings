# G7 correction: unquoted Markdown heredoc executed backticks

Date: 2026-09-20. Scope: bounded CLV ABL1 static-analysis action-log creation.

## Failed procedure and measurement

An unquoted Bash heredoc contained Markdown inline-code backticks. Bash treated text in backticks—including hexadecimal labels and artifact paths—as command substitutions. The shell emitted `command not found` and `Permission denied` errors while the outer compound command still returned status `0`. This did not validate the intended action-log contents; the generated file was incomplete.

## Correction

The action log was rewritten with a Python literal string, safely preserving Markdown backticks. No firmware, ROM, source input, or evidence input changed. The failed shell errors and misleading outer exit status are retained in `docs/action-logs/2026-09-20-clv-abl1-r6-3c4-producer-trace.md`.

## Reusable rule

For Markdown or code containing backticks, use a quoted heredoc (`<<'EOF'`) or a language-level literal; do not rely on an unquoted heredoc. Verify the written file by reopening it and hashing it; a shell exit of `0` is not sufficient if command substitutions emitted errors.

## G7 correction: quoted Markdown heredoc requirement re-applied (2026-09-21T16:38+05:00)

- Current task's continuation-intent append used an unquoted `<<EOF` body containing Markdown backticks. Bash attempted command substitutions and emitted repeated `Permission denied`, `command not found`, and `No such file or directory` diagnostics while the compound shell command returned status `0`.
- Readback proved the appended section lost its backtick-delimited paths, offsets, expected values, and predicate output. No source firmware, payload, guide, or evidence input was changed; only the action-log continuation section is malformed.
- Correction method: replace that malformed section from an explicitly single-quoted heredoc/Python literal, reopen and hash the log, and retain this failure record. Use `<<'EOF'` or Python literal for Markdown containing backticks; never trust the outer exit code without reopening the artifact.

## G7 correction: ABL1 hash transcription corrected (2026-09-21T16:40+05:00)

- The repaired continuation-intent block transcribed the decompressed ABL1 hash incompletely as `af8cf5626a113afe72bc0687ca4f0119df3be2356a74203a`.
- Direct `sha256sum evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin` returned `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a` (94,624 bytes). The artifact identity/hash was not changed; only the transcription was wrong.
- Correct the action-log string to the measured full hash and verify the log readback before any further output write.
