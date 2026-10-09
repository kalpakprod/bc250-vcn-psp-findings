# AMD guidance boundary — action log

Timestamp: 2026-09-21T01:03:28+05:00
Actor: subagent /root/amd_guidance_boundary; root verification pending
Target: docs/research/2026-09-21-amd-guidance-boundary.md and this log

## Intent (written before the report)

- **Exact action:** create one bounded source-comparison report from only the official AMD Ryzen Master 2.9 Reference Guide and the pinned BC250 community `bc250_smu_oc` README; do not touch memory, firmware, candidates, or other source trees.
- **Reason:** decide whether the checked AMD material publishes a universal/manual SoC `1.15 V` recommendation for a custom BC-250 and separate recommendation, maximum, and community CPU examples.
- **Expected effect:** one sanitized English report with precise source scope, short quotations, URLs, commit/file hashes, and retrieval limitations.
- **Rollback:** if explicitly requested, remove only this task report and this task log; no original or project source is modified.

## Read-only retrieval and result

- Confirmed project root with `pwd` and `git rev-parse --show-toplevel`: `/home/OWNER/orca/projects/bc250`.
- `agent-reach doctor --json`: `web` backend `Jina Reader`, status `ok`; GitHub `active_backend` was `null`. OpenCLI was inspected for read-only routes. An OpenCLI browser read of the AMD user-guide portal returned `Navigation rejected` (`exitCode: 1`); an earlier option-order attempt returned `error: unknown option '--profile'` (that first parse-error exit status was not captured). A targeted Jina/Google lookup returned a CAPTCHA warning and was not used as evidence; retrieval pivoted to AMD's own product-page link and Jina Reader.
- AMD product page (redirect provenance only): `https://www.amd.com/en/products/software/ryzen-master.html`; Jina retrieval snapshot SHA-256 `ccef022996836613d390968c88293a5ed08504471cd761f5a18a6e6f94c1b0fb`. The page links the current User Guide `https://docs.amd.com/r/en-US/68886-ryzen-master-user-guide` and the official Quick Reference Guide PDF below.
- Current User Guide page: Jina returned only the portal shell/title (“Before You Begin • Ryzen Master User Guide (68886) • AMD Technical Information Portal”), not the guide body. Snapshot SHA-256 `64ab959963b44ed3beb666898b064873264c7e990b7e06c79cec991042ee71fe`. This is the exact missing source body; it is not cited for substantive claims.
- Official AMD Quick Reference Guide PDF URL: `https://www.amd.com/content/dam/amd/en/documents/products/software-tools/ryzen-master-quick-reference-guide.pdf`. Jina Reader extracted 51 pages into a 45,037-byte Markdown snapshot, SHA-256 `d850b95da8f0b48151ac9571f898300d741a48f495d1323fa8195c0cdaff1623`. The extraction's metadata title says “2.1 Reference Guide - Feb 2020,” but the document body says “2.9 – Reference Guide [Public]” and “AMD Ryzen Master 2.9 Reference Guide | April 2022”; the report follows the body and retains this metadata discrepancy. A direct raw-PDF curl failed with `curl: (92) HTTP/2 stream 1 reset by server (error 0x2 INTERNAL_ERROR)`; therefore no original-PDF SHA-256 is claimed. The recorded AMD hash is explicitly the Jina extraction snapshot hash.
- GitHub latest-main commit metadata was read at `https://api.github.com/repos/bc250-collective/bc250_smu_oc/commits?per_page=1`: observed HEAD commit `43d6b4c6e38c57bc9ec8908c44675ce7d5fd3d2f`, dated `2026-01-26T15:48:57Z`, message `Updated readme to include stability testing`.
- Fetched the raw README at the pinned commit: `https://raw.githubusercontent.com/bc250-collective/bc250_smu_oc/43d6b4c6e38c57bc9ec8908c44675ce7d5fd3d2f/README.md`; exact raw file size `5,792` bytes and SHA-256 `7cd268ec3f7fc98f2fe75682380d09e35079d5238f6ad12fe2396e602a6fe9e3`.
- **No commands copied from the README were executed.** No hardware, firmware, NVRAM, register, candidate, or BIOS action occurred. Only the two requested documentation files were written.

## After-write observation

Timestamp: 2026-09-21T01:03:28+05:00

Report created: `docs/research/2026-09-21-amd-guidance-boundary.md` (SHA-256 `82c1f9198c19842aaebf8bd61752e7283c3a126b8d10401d9e7b7ea9c0ed8873`). The report records the AMD guide as a Jina extraction snapshot—not an original PDF hash—and records the pinned raw README SHA-256. Both task files were subsequently reopened for verification.

## Remaining uncertainty and rollback

- The exact current AMD User Guide body at document ID `68886` and the raw PDF SHA-256 remain unavailable; do not expand the scope without a new task.
- AMD's DDR4/Ryzen 3000-Series starting value is not transferred to BC-250 GDDR6, and README CPU VID values remain anecdotal community content.
- Rollback is deletion of only this task report and this task log, if requested. No device/source/hardware rollback is needed because none was modified.
