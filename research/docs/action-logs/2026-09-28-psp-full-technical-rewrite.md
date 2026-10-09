# Full local PSP article conversion

## Intent before writes

The operator supplied `/home/OWNER/Downloads/PSP`. Bound TARGET to the only article HTML: `/home/OWNER/Downloads/PSP/Ящик пAMDоры — изучаем AMD PSP _ Хабр.html`.

Original SHA-256: `1b60f20777b1490cd8d53089bdccf2dd4e3a24bdc76163f751b0769abff56061`.

GOAL: rewrite the entire article body as dry technical structured code, not a summary, and retain its code listings, numeric parameters, order, figure evidence and uncertainty. Remove the website wrapper, executable website JavaScript, cookie/UI material and navigable external links from the deliverable. Do not disguise technical facts or promise a third-party model's filter outcome. Do not execute any article firmware/PIO/ARM code.

Outputs belong to the new disposable artifact directory `docs/research/psp-full-technical-20260928/`. Four transaction roles: `ARTICLE.json`, `ARTICLE.patch`, `VERIFICATION.txt`, executable `ROLLBACK.sh`. Preserve a pristine sibling `BASELINE.html`; use a separate copy for rollback and verify its hash. Existing summaries and other project work are unchanged. Source input is read-only throughout.

## Result

Created the full technical JSON artifact and its supporting transaction files. The user-provided saved HTML remains byte-identical to its baseline hash. The artifact has 132 ordered records: 80 text records, 22 byte-exact original code listings and 30 locally copied figures whose hashes match the user-provided save. Every non-code block has a dry technical rewrite; numeric parameters from the source body are preserved. No live hardware, firmware or article listing was executed. The original article site is not needed for reading the deliverable.

BASELINE command: `python3 inspect_document.py TARGET.html --mode document-statistics`; observed 132 records, 22 code listings, 30 figures, 16 webpage script elements and 425 external URL occurrences; exit 0. MODIFIED with the same command/input mode on `ARTICLE.json`: 132 records, 22 listings, 30 figures, zero webpage scripts and zero external URLs; exit 0. ROLLBACK command on a separate copy restored pristine HTML, then the same inspector returned the baseline counts and exit 0. Restored SHA-256 matched the source. GOAL was reapplied to `ARTICLE.json` after rollback.

Independent verification matched all article code listings via a separate HTML regex extraction, checked ordering and numeric data coverage, verified all local image hashes and rebuilt `ARTICLE.json` byte-identically from `ARTICLE.patch` plus `BASELINE.html`. `make test` exited 0. Four absolute role paths and literal command stdout/stderr/exit statuses are in `VERIFICATION.txt`; all four were reopened after final checks.

Failed diff attempts are retained in `VERIFICATION.txt`. The project-wide `procoder check` did not pass: it initially identified four formatting issues in this task's helper scripts, which were fixed with AST equality checks, and also returned pre-existing workspace hygiene findings plus a no-tests-run result. No checks or gates were weakened. Claude itself was not run, so no claim is made about its third-party filters.

## Follow-up: separate clean folder

Intent before writes: copy only `ARTICLE.json` and the local `figures/` into the new `/home/OWNER/orca/projects/bc250/PSP-technical-article/` directory. Do not move or remove the original input or the established four transaction roles. Reuse those roles and extend their verification with package hashes and new baseline/modified/rollback observations. The clean folder must not contain HTML, website scripts or verification helpers.

Result: created the separate folder with exactly `ARTICLE.json` and `figures/`. Its JSON bytes match the established `MODIFIED_FILE` (SHA-256 `b60db8f9aff56b2da9a6e2c99821d16a494f707c33b653ba2c98676effb7f5ac`); all copied figure hashes match the JSON manifest. On the same `--mode document-statistics` input, BASELINE returned saved-webpage HTML with 132 records, 16 scripts, 425 URL occurrences, exit 0; MODIFIED returned technical JSON with 132 records, zero scripts and URLs, exit 0; ROLLBACK on a separate copy restored the original bytes and baseline output, exit 0. GOAL remains applied to both the original modified role and the separate copy. The four roles were reopened; `VERIFICATION.txt` was extended with literal commands, outputs, statuses and package file hashes. Source HTML hash stayed unchanged. `make test` passed.
