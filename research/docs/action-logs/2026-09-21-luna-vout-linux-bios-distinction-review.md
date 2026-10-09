# Linux callback versus BIOS writer — bounded review log

Timestamp: 2026-09-21T01:28:23+05:00
Actor: subagent /root/amd_guidance_boundary; root verification pending
Target: docs/research/2026-09-21-luna-vout-linux-bios-distinction-review.md and this log

## Intent (written before report)

- **Exact action:** independently reopen `docs/research/2026-09-21-luna-vout-write-callback-verification.md`, its pinned Linux source hashes/paths, the CLV BIOS direct-writer evidence, and the scoped AMD 1.1 VDDCR-SOC/VDDG reports; accept or reject only the requested layer-transfer claims.
- **Scope:** source/provenance review only. Do not rerun the byte scan, fetch more PDFs, edit shared memory, alter firmware/ROM/NVRAM, or perform hardware/BIOS commands.
- **Expected effect:** one short English review report with line-referenced claim decisions and exact source hashes.
- **Rollback:** remove only this report and log if explicitly requested; no source/device rollback is required.

## After-write observation

Timestamp: 2026-09-21T01:28:23+05:00
Report created: `docs/research/2026-09-21-luna-vout-linux-bios-distinction-review.md` (SHA-256 `590c8f6d86d9dd57058da92e99fd7d3b56429a257895dcf66d6b44d9697ba387`). The report and source line references were reopened after writing.

## Observed result and limits

- `A1` accepted: Linux positive return is in the write callback (`PASS`, prior 14/14 source assertions).
- `A2` accepted: static callback-contract anomaly only; no PMBus command/runtime failure claimed.
- `A3` accepted: BIOS PEI/EC mailbox writer is a distinct static route.
- `R1` rejected: no Linux-to-BIOS bug transfer.
- `R2` rejected: no VCORE/GFX/MEMIO-to-SoC relabel.
- `R3` rejected: no generic AMD 1.1 V DDR4 guidance-to-BC250 GDDR6 transfer.
- No byte scan, PDF fetch, firmware/ROM/NVRAM write, BIOS command, bus command, or hardware operation occurred.
- Rollback: remove only this report and log if explicitly requested.

## Intent — qualification edit

Timestamp: 2026-09-21T01:31:50+05:00. Amend the new review report only to distinguish directly re-opened Linux source bytes from prior BIOS/AMD report evidence, and clarify that the repeated name is not a code-path join. This does not repeat the ROM byte scan or edit shared memory.

## Qualification edit result

Timestamp: 2026-09-21T01:31:50+05:00
The report now labels re-opened Linux source as observed/static and prior BIOS/AMD reports as historical-report inputs; it explicitly says BIOS bytes were not re-decoded and that `ISL69247` name identity is not a code-path join. Updated report SHA-256: `aa6e38c9ca83867622be815db09a058d95f1ccc99b6a053ecc47317d7e5415a7`.

## G7 correction — shell quoting in append command

The qualification-edit append command used an unquoted heredoc while containing backtick-marked `ISL69247`, so the shell emitted `ISL69247: command not found` and the first appended intent line lost that literal label. The report body itself was written by a separate quoted Python heredoc and is correct. No source, firmware, ROM, memory, or hardware artifact was changed. The corrected intent is: “clarify that the repeated `ISL69247` name is not a code-path join.”

## Final readback

Timestamp: 2026-09-21T01:32:58+05:00
Report SHA-256: aa6e38c9ca83867622be815db09a058d95f1ccc99b6a053ecc47317d7e5415a7
Action-log SHA-256 before this final append: ed8c9df882e01f73a6a43bbf12c801a8032aa2181b09e4d80d8df3f97b5c30c3
The report and log were reopened after the qualification edit. All claims remain static/provenance-qualified; no byte scan or hardware operation occurred.
