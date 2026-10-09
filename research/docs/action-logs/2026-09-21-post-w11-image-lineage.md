# Action log: post-W11 programmer-readback and candidate lineage audit

## Intent (before report write)

- Timestamp: 2026-09-21T08:01:52+05:00 (Asia/Almaty; host clock observation).
- Actor: delegated project executor, bounded read-only task from root.
- Scope: compare only the saved programmer captures in `evidence/programmer/reads/20260919/`, candidate ROM files dated from 2026-09-19 onward, and the explicitly documented RetroWeb `5.00_clv` donor needed for ancestry. No programmer access, board query, flash, NVRAM/register action, boot, or external search.
- Target write: new summary `docs/research/2026-09-21-post-w11-image-lineage.md`; this log records its intent/result. Existing reports and binary inputs remain unchanged.
- Existing route: reuse `scripts/firmware_audit.py` (version `1.0-readonly`, SHA-256 `5ead8605678fc5a13eb0cf49c01b43037560ddc485d8ad2686abf0e9c34d9593`) for structural checks; use targeted hashes, `cmp`, and bounded byte-region comparisons for lineage. Its outer parser is not a current-board identity test, so the result will separate saved readback from present state.
- Expected result: identify the exact latest saved readback, candidate-to-readback identity matches, the newer unflashed candidate lineage, source hashes, board-identity limit, and unknown current state.
- Rollback: no binary or candidate bytes are changed. If the report is wrong, append a correction or superseding note; remove only the new report if the operator requests its withdrawal. Keep this action log as provenance.
- Safety: inputs were read-only; no secrets, credentials, raw keys, or security exports were opened or copied.

## Observed result (after report write)

- Timestamp: 2026-09-21, Asia/Almaty (+05:00). Reopened the full report and this log after creating the report; corrected one phrasing to state the exact mtime cutoff.
- Bounded inventory: four 16 MiB programmer files under `evidence/programmer/reads/20260919/`; 14 candidate `.bin` files in `candidates/` with mtime after the 2026-09-18 23:59:59 cutoff; one explicit CLV-donor comparator. `find evidence/programmer/reads -type f -newermt '2026-09-19 23:59:59'` emitted no paths.
- Parser command used the above 19 paths with `python3 scripts/firmware_audit.py --output /tmp/bc250-post-w11-image-lineage-final.json ...`; observed stdout `{"output": "/tmp/bc250-post-w11-image-lineage-final.json", "images": 19, "extracted": 0}`, process exit `0`. Follow-up assertions: `LINEAGE_INPUTS=19;STRUCTURE_CHECKS=19/19 PASS;tool=scripts/firmware_audit.py;version=1.0-readonly`; JSON SHA-256 `efe85565531557712883a0c31124279024c8f76309d839a07fdc85eba659ead4`.
- Direct whole-image comparison: `cmp -s evidence/programmer/reads/20260919/postwrite-vcn-unlock-w11-v001.bin candidates/BC250_5.00_clv_VcnUnlock_W9_v001.bin` exited `0`. Both freshly hash to `3c50bc9a65194b75ca805e6ed31c5778369de1fe8eca4600f44e15fae3b40fc3`.
- Readback hashes re-opened: W9-deferred `749e4c53a05bde7307e37082ad9842cd6d791f98bc2cf805106eb8da1177b224`; W9-S9 `d94435add3a3c0d9d9881c77cf1dac172b9c4f8137ca12311caf5ff30b1cf428`; W10 `136707db95e07faab56f497e0ba4fede708cd5f893bfd0a0f52e7031135d41a5`; W11 `3c50bc9a65194b75ca805e6ed31c5778369de1fe8eca4600f44e15fae3b40fc3`.
- Direct byte comparison W11 vs CLV donor: equal regions `[0x000000,0x020000)`, `[0x8E0000,0xAB0000)`, `[0xAB0000,0xAE0000)`, `[0xE00000,0x1000000)`; only `[0xAE0000,0xE00000)` differs, 1,326,833 byte positions, first `0xAE0088`, last `0xC25586`.
- Latest candidate path/hash reopened: `candidates/BC250_5.00_clv_MeiMeiDXEv3-drivers-only_v001.bin`, `0968a70c4d6fbb51f43d3e0fb5e4b3783dec41e881246356a75c66dc5f19c554`; its `.build.json` hash `ca73b5888850fe3f7a588a34ee049778457400d76c25b096b301554040ac7ba9`. Its source `BC250_5.00_clv.bin` re-hashes to `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`. The referenced build action log SHA-256 is `02b3eca7454380e01528356a8424c01d12f0772ae905e9b7fd7615905ca7f383` and records no flash / `hardware_written=false`.
- Report readback SHA-256 `c9165b2e6962ccba84b9e48e51e5e12935167e35cfd13bfa1fb9115c8a6dc020`. No source image or candidate was changed. No hardware/programmer transaction was performed.
- Evidence classification: `observed-bytes` for sizes, hashes, comparisons, candidate matches and parsed structure; historical programmer attribution is limited by missing same-date W11 raw transcript/manifest. Current board/chip/boot state remains unknown. Rollback: preserve this action log; withdraw the new research report only by operator request, with no effect on source images or earlier ledgers.

## G7 correction — report hash typo

The Observed result above recorded the report SHA-256 as `c9165b2e6962ccba84b9e48e51e5e12935167e35cfd13bfa1fb9115c8a6dc020`; that value was not supported by the immediately preceding `sha256sum` output and is withdrawn. Fresh `sha256sum docs/research/2026-09-21-post-w11-image-lineage.md` measured `58a1d952a84f13ae4302abf779e111150ce8e286e9c56c7336f4c26d9b5570f2`. This is the authoritative report hash; the report itself was reopened, and its final mtime-cutoff wording is the 2026-09-19 23:59:59+05 statement. No input image or candidate changed.
