# Intent: self-contained Habr research brief for Claude

Date: 2026-09-28.

The operator clarified that opening the Habr page itself interrupts Claude. Create a new, original, condensed research brief under `docs/research/` that can be read without visiting the page. Do not edit or overwrite the source article, the existing historical source notes, or other agents' work. Record the prior misunderstanding in `MISTAKES.md`. Keep the brief attributed and distinguish the published BC-250 result from this project's unverified setup. No hardware or firmware write is involved.

Result: created `docs/research/2026-09-28-amd-psp-habr-standalone-brief.md` as an original, self-contained 532-word research summary; appended the corrected failure mode to `MISTAKES.md`. The earlier source note was not changed. No hardware, firmware image, or external configuration was touched.

Checks: the new brief contains no `http://` or `https://` URL. SHA-256 of the brief: `2084aca9d8a0016c27105273b53c98b509df91ae41ce19ed674a381592416121`. SHA-256 of `MISTAKES.md` after append: `685e4c3daa81a32bdf364cdf6ea2055dcd2f07e0537be47c174128cef9555f27`. `git diff --check` exited 0. `make test` exited 0 with the contract gate passing. These are file and repository checks, not hardware validation.

## Operator correction: full text, not a condensed brief

Intent: append the second scope-substitution error to `MISTAKES.md`; leave existing artifacts and others' changes intact. The operator requires an unabridged technical/code-form rewrite. The brief does not satisfy that requirement. Reopened only the same Plane task as Todo; earlier open tasks remain unchanged. A full transformation of the linked article needs the source text supplied by the user. Do not mark the requested rewrite complete or claim any Claude filter test.

Result: appended the correction record and reopened Plane work item `237c8a80-c038-4a58-950b-22384b2326f0`; observed `completed_at: null` and Todo state. Reopened the mistake record and this log. `make test` and scoped `git diff --check` both exited 0. The requested full rewrite remains unperformed.
