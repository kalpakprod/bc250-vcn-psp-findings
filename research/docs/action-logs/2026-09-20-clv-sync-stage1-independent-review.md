# Independent review — CLV SYNC stage 1 reconciliation

Timestamp: 2026-09-20T04:23:14+05:00 (+05:00)
Actor: verify_uclk_luna executor
Target: read-only review of `evidence/firmware-audit/20260920-clv-sync-stage1/stage1-report.json`, `stage1-report.md`, `SHA256SUMS.final`, and `docs/action-logs/2026-09-20-clv-sync-stage1.md`.
Procedure planned: verify the cheapest decisive claims directly from the staged image bytes and existing machine reports: three loose SYNC changed ranges; extracted executable-body identity; later archive revision deltas; ULTIMATE AmdSetup field provenance; APCB checksum-fix byte; report/plan status semantics and archive-to-flash ambiguity.
Rationale: independent factual review requested by the operator; no broad duplicate extraction, no firmware/source/shared-memory modification, no installation, and no release or flash approval.
Expected effect: one bounded review record with PASS/qualification findings and any wording corrections.
Rollback: delete only this uniquely named review log; all checks read existing artifacts or write only `/tmp` command output.

## Observed verification

Timestamp: 2026-09-20T04:24:00+05:00 (+05:00).

Reopened absolute main artifacts:

- `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-sync-stage1/stage1-report.json` — SHA-256 `2a0cb0cd4133ec9671eb59b8645d51b6d566bfc4468691f3a22ce63025cd12a6`;
- `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-sync-stage1/stage1-report.md` — SHA-256 `17af4d62817591a9584254849953de1b46b7c8d65fa559e5368152d34f126cea`;
- `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-sync-stage1/SHA256SUMS.final` — 836 entries, SHA-256 `0a64ae0f804b53703dfe115e116214c0f1d4f2288fbe9a61ca14f88c3746bec5`;
- `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-sync-stage1.md` — SHA-256 `3b0e828a61b4c0b91fa177fed13a9a1857e365589027d67f19014d9d54d744c8`.

`sha256sum -c /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-sync-stage1/SHA256SUMS.final` exited `0`: 836/836 entries `OK`, no failures, no stderr.

Pinned baseline `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` remained 16 MiB, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.

### Decisive claims independently checked

- The three loose SYNC images match the staged hashes and have respectively 3019, 3018, and 3020 differing bytes versus clv. Direct byte comparison found every difference below `0x20000` (highest differing offset `0x1FE8F`) and identical tails from `0x20000` onward.
- Existing staged extraction directories contain exactly 233 modules each for donor, SYNC03, and ULTIMATE. Ordered `(filename, SHA-256, size)` tuples are byte-identical across all three sets. This is executable-body coverage, not clock/application proof.
- Each `oc_profiles (1).rar` late revision differs from its same-name loose profile at exactly two bytes: absolute `0x7E6` (Tcl -> `0xFF`) and `0x7FE` (DRAM Timing Control -> `0xFF`).
- Direct decoding from ULTIMATE `AmdSetup` body base `0x4CF` matches the report: `UclkDiv1M0=0`, `PhyPowerSaving=0`, `MemoryPstate=0`, `VDD offset=100`, `DF override=1400`, `VrmCurrent=95000`, `Tcl=0xFF`, and `DramTimingControl=0xFF`. These are persisted NVRAM/default-store bytes, not physical clocks or a recipe.
- Direct APCB bytes show the ckfix transformation `0xAB1014: 0x00 -> 0x1E`; independent additive checksum calculation gives uncorrected idx08-down `0xDE` versus stored `0xC0`, and ckfix `0xC0` versus stored `0xC0`. The `+0x14` semantic and PSP acceptance remain unknown.
- The plan has exactly three `[x]` checks, all under phase-1 offline reconciliation; phase-2 consumer work remains `[ ]`. Report acceptance explicitly leaves hardware clock sync, boot/training, physical voltage, modified-APCB PSP acceptance, and independent clock observation `UNRUN`. Archive-to-flash association is explicitly retained as ambiguous. Therefore the phase-1 checkmarks are justified as offline deliverable completion, not flash/boot acceptance.

## Qualifications / corrections

- **Q1 — count wording:** the report processed 14 image entries, but they collapse to 13 unique SHA-256 contents because the two ckfix files are byte-identical. `stage1-report.md` and the stage-1 action log say “14 unique contents”; that wording is inaccurate. It does not change any structural conclusion; use “14 image entries / 13 unique contents” in downstream summaries.
- **Q2 — checksum status:** “checksum passes” means the local additive APCB calculation only. It is not PSP acceptance, bootability, or flash approval; the report’s qualification is correct.
- **Q3 — archive-to-flash:** message IDs and prior photo review support historical attribution only. The report correctly preserves the ambiguity and does not convert filenames/IDs into a board readback claim.

## Review verdict

**PASS with Q1 wording correction.** The three loose-SYNC confinement, 233-module identity, late-revision byte attribution, ULTIMATE field provenance, checksum-fix byte, and offline-plan status claims are factually supported. No source, ROM, shared memory, or hardware state was changed. This is not release approval and provides no hardware clock, training, PSP-acceptance, or flash result.
