# Baseline NVRAM ledger — intent and execution

## Intent — 2026-09-21T23:35:00+05:00 Asia/Almaty

Actor: `/root/baseline_nvram` worker. Scope: read-only audit of saved programmer readbacks and preserved menu/IFR records for the six requested clock controls plus voltage fields. Target remains saved BC-250 SPI captures; no board contact, NVRAM write, ROM write, candidate build, or source-image modification.

Existing route reused: `scripts/nvar_audit.py` (bounded AMI NVAR parser; source SHA-256 recorded in the ledger) plus the already-reviewed exact-CLV HII/IFR evidence. No new generic scanner or parser is introduced. The parser outputs metadata/selected fields and deliberately excludes raw variable bodies. A temporary summary reads only named AmdSetup/Setup offsets and is not retained as a project artifact.

Expected result: identify primary AmdSetup/Setup records in saved actual-board readbacks, list exact hashes/timestamps and six clock/voltage fields, and separate board readback history from donor CLV/participant/menu evidence. Rollback: delete only this ledger/log and temporary outputs; original captures remain untouched.

## Procedure

1. Enumerate saved programmer captures; hash selected images with `sha256sum`.
2. Run the existing `scripts/nvar_audit.py` against selected saved readbacks using a bounded store beginning at offset `0x0`; retain only selected metadata and named fields in the ledger.
3. Reopen exact source files and verify hashes/field summaries before reporting.
4. Cross-reference already-existing static HII/menu reports and historical participant evidence without promoting them to live board state.

## Recorded execution error and method correction

The first temporary-run command included `rm -rf /tmp/bc250-baseline-nvram-work/reports`; the command runner rejected it before process creation (`Rejected("rm -f style commands are not permitted. Use a safer approach")`). No shell command ran and no repository/capture files were touched. Method changed: retain uniquely named scratch paths, create missing directories with `mkdir -p`, and do not request recursive deletion.

The first selected-field Python run exited `1` with `SyntaxError: unterminated string literal (detected at line 20)` in the temporary wrapper (`evidence/programmer/reads/20260919/postwrite-vcn-unlock-w11-v001.bin` line lacked its opening quote). No image was modified and no result was produced. The command will be corrected at that line and rerun once.

## Intent — ledger evidence qualification before final readback

Update only this worker-owned ledger to make two distinctions explicit: (a) the separate Setup VarStore values are not SoC measurements and VDDCR_VDD cannot be relabelled SoC; (b) `post-flash-readback-sync1to1.bin` is a preserved programmer-directory artifact whose hash matches its named candidate, but the current docs do not contain a primary action-log chain establishing its exact board/boot history. No input, ROM, candidate, board or shared memory file is changed.

## Observed results and verification

Read-only selected captures and exact report values are in `docs/research/2026-09-21-baseline-nvram-ledger.md`. The latest W11 readback's `AmdSetup` record is `0x4BB`, record size `0x8C9`, body length `0x8B5`, body SHA-256 `cd91fa93d8492c3af7882425d7317dc9c50bf615e980feab9387a04ae03244a6`; the `Setup` record is `0xD84`, record size `0x1E4`, body length `0x1D3`, body SHA-256 `4de2a37fd8907979790f5ebda61a4316ae0ae4bb57671b25c1d8073b542e7a5f`.

Exact direct parser tests (`scripts/nvar_audit.py` SHA-256 `16d35db736f5ca0e4423c444ff892b9d2b583bd8efcafda1a5e752ff04cb1160`):

- `python3 -B scripts/nvar_audit.py evidence/programmer/reads/20260919/postwrite-vcn-unlock-w11-v001.bin --store-offset 0 --store-length 0x20000 --variable AmdSetup --output /tmp/bc250-baseline-nvram-work/nvar-w11.json` — exit `0`; literal stdout `{"output": "/tmp/bc250-baseline-nvram-work/nvar-w11.json", "records": 53, "selected": 1, "errors": 0}`; stderr empty.
- Same command on `evidence/programmer/reads/20260917/post-flash-readback-sync1to1.bin` with output `/tmp/bc250-baseline-nvram-work/nvar-sync-readback.json` — exit `0`; stdout `{"output": "/tmp/bc250-baseline-nvram-work/nvar-sync-readback.json", "records": 52, "selected": 1, "errors": 3}`; stderr empty. Three parser errors are NVAR-tail unterminated names; the complete selected `AmdSetup` record was found and fields decoded. The tail caveat is retained; this readback is not used as current state.
- Hash readbacks: latest W11 `3c50bc9a65194b75ca805e6ed31c5778369de1fe8eca4600f44e15fae3b40fc3`; W9 sync-named capture `ec91aaa202905354433473c2f7eaea9c40ec96fd275f2d4e7337c7066a3c34d9`; stock baseline `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`; every listed SPI file size `16777216` bytes.

Final readback: both files were reopened with `cat`, report sections/field table and action-log result were read back, required strings and exact current W11 values checked, and `sha256sum` recomputed for report, log, and selected source binaries. No original/candidate/readback file or shared memory was changed. Remaining uncertainty: the board's state after the 2026-09-19 readback, live menu visibility, physical clocks, physical rail voltage, and whether historic image `ec91...` was booted are not established. Rollback: delete only the two worker-owned text files and `/tmp/bc250-baseline-nvram-work/` scratch outputs; source readbacks remain untouched.

## G7 timestamp correction — 2026-09-21T03:47:27+05:00 Asia/Almaty

The initially typed `Intent` timestamp `2026-09-21T23:35:00+05:00` was not read from the host clock and is superseded. Read-only filesystem birth-time evidence (`stat -c '%w'`) records this log's first creation at `2026-09-21 03:30:34.099404565 +0500` and the report's first creation at `2026-09-21 03:42:32.028957471 +0500`; host `date --iso-8601=seconds` at correction was `2026-09-21T03:47:27+05:00`. The original timestamp line is preserved as historical text, not a valid action time. The corrected start evidence is the observed log creation time above; no finding or input hash changed.
