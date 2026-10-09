# Action log — BC-250 board voltage sources: independent recheck + minimal verifier correction

Topic: continuation of `docs/action-logs/2026-09-20-bc250-board-voltage-sources.md`.
Scope: read-only static analysis of immutable inputs. No ROM, NVRAM, register, candidate,
board or network action. All writes are new files under
`evidence/firmware-audit/20260920-bc250-board-voltage-sources-recheck/` and two new
`docs/` files; no existing artifact was modified.

Ordering note (honest record): the sibling task directory was being written by another actor
while this recheck ran, so the recheck was moved into a new directory to avoid two writers on
one artifact. The writes below began at 2026-09-20T23:35+05:00; this journal entry was written
after them at 2026-09-20T23:47+05:00. There is no pre-write intent line for those writes; the
intent is reconstructed from the sibling log's stated expectation (scanner + independent
verifier + machine result + literal captures + SHA256SUMS.final + ROLLBACK.sh + one report).

## Observed state at 23:35 (before this recheck's writes)

- `20260920-bc250-board-voltage-sources/`: scanner PASS 31/31, result JSON present, verifier
  revision `a1551700…` present, its input capture `verifier.stdout` deleted by the concurrent
  actor, independent-verify run failing with `FileNotFoundError`.
- Inputs re-hashed and unchanged: donor ROM `ea5781…4cb8` (16 777 216 B), corpus
  `census.json` `506b8e…0d39` (233 modules).

## Actions

A1 23:35–23:36 Snapshotted `scan_vr_mailbox_writers.py` (`63ae081c…`) and
`verify_board_voltage_sources.py` (`a1551700…`) plus the two objdump captures into the new
recheck directory. No sibling file touched.
A2 23:36 Ran the scanner: exit 0, `checks=31 failed=0 status=PASS`, writer set
`{ISL69247-3e1f753a6279, ISL95712-c0cc17d2d54f}`, 28 EC-window-only modules; result JSON
sha256 `852ffd0d…8381`, byte-identical to the sibling directory's result.
A3 23:36–23:37 Ran the snapshot verifier unchanged: exit 1, `FAIL checks 604 failed 57`
(53 anchor-offset re-reads + 4 owned EC-window immediates). Root cause measured on the module
image and the asm text: the scanner reports the offset of the matched pattern bytes, which for
operand-fragment anchors (`imm_ec_window_a20 = 200a0000`) is mid-instruction; the verifier
keyed the re-read by instruction start. Second class: 17 sites where the pinned objdump text
lists no covering instruction (decode gaps).
A4 23:38–23:39 Applied one minimal correction in the recheck copy only (`changes.patch`: new
module-level `site_bytes()`, used by the two offset re-read sites, plus the verdict key
`per_site_readback_sources`). Result: exit 0, `PASS checks 604 failed 0`,
`anchor_offset_entries_verified 200`, readback sources `{"asm": 185, "image": 19}`.
A5 23:39 Tested `ROLLBACK.sh` on a separate copy in a temporary directory at the same depth:
restored sha256 `a1551700…` (equals pristine) and the restored copy reproduced the baseline
`FAIL 604/57` with the same first failure. Working copy left corrected and re-running PASS.
Temporary test directory removed afterwards.
A6 23:41 Independent reproduction of the sibling package's final revision
(`3a207fac…`) from a relocated path: exit 0, `PASS checks 604 failed 0`,
`anchor_offset_alignment {"aligned":181,"cross-instruction":2,"decode-gap":0,
   "outside-code-section":17}`. Both fixes agree on 181 aligned sites and on the bytes at all 200
sites; only the label boundary for 2 cross-instruction sites differs. Temporary directory
removed afterwards.
A7 23:42–23:47 Wrote `VERIFICATION.txt`, `SHA256SUMS.final` (24 files, `sha256sum -c` all OK),
`docs/research/20260920-bc250-board-voltage-sources-recheck.md`, and this log.

## Result

The sibling inventory conclusion is independently reproduced: only `ISL69247` and `ISL95712`
implement the EC-window VR mailbox writer transport in the 233-module CLV 5.00 corpus. The
per-site offset re-read defect in the intermediate verifier revision is root-caused, minimally
corrected in this package, and independently converged upon by the sibling's final revision.

## Remaining uncertainty

- Static analysis only; no hardware readback or register access.
- The 17 decode-gap sites are re-read from the module image (labelled per site), not from asm text.
- Whether those anchors are code or data at run time is unresolved.
- No independent review by a different model family for this recheck.

## Rollback

`evidence/firmware-audit/20260920-bc250-board-voltage-sources-recheck/ROLLBACK.sh` restores the
pristine verifier bytes from the sibling baseline, or with `--remove` deletes only this recheck's
evidence directory. The two `docs/` files added by this recheck are deleted by hand; no sibling
artifact is affected either way.
