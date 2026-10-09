# Post-W11 programmer-readback and candidate lineage

Date: 2026-09-21 (Asia/Almaty, +05:00). Scope: bounded, read-only reconciliation of the four saved programmer images under `evidence/programmer/reads/20260919/`, candidate ROM binaries with saved mtimes from 2026-09-19 onward, and the local `5.00_clv` donor as a source comparator. No current board/programmer access or firmware/NVRAM/register operation occurred.

## Conclusion

The latest saved programmer readback in this bounded inventory is `evidence/programmer/reads/20260919/postwrite-vcn-unlock-w11-v001.bin`, 16 MiB, SHA-256 `3c50bc9a65194b75ca805e6ed31c5778369de1fe8eca4600f44e15fae3b40fc3`. It is byte-for-byte identical (`cmp` exit 0; full-image SHA-256 equal) to `candidates/BC250_5.00_clv_VcnUnlock_W9_v001.bin`. Thus that W9-named candidate is the best-supported image applied at the time represented by the saved W11 readback. “W9” and “W11” are artifact/run labels here, not a verified board BIOS version or current state.

A later candidate exists: `candidates/BC250_5.00_clv_MeiMeiDXEv3-drivers-only_v001.bin`, SHA-256 `0968a70c4d6fbb51f43d3e0fb5e4b3783dec41e881246356a75c66dc5f19c554`, saved 2026-09-20. Its build metadata names the RetroWeb CLV donor as its base; the 2026-09-20 action log says **no flash**, `hardware_written=false`, independent review and hardware acceptance unrun. It matches none of the saved programmer images. It is the newest candidate artifact found, not the newest applied/read-back image.

No programmer-read file with mtime later than 2026-09-19 23:59:59+05 was found. Therefore, the latest saved readback is not proof of the board's present contents. Current board/chip/boot state remains **UNKNOWN**.

## Scope, provenance, and identity boundary

- Bounded saved reads: the four 16 MiB `.bin` files in `evidence/programmer/reads/20260919/` (listed below). A bounded `find evidence/programmer/reads -type f -newermt '2026-09-19 23:59:59'` returned no paths.
- Bounded candidates: 14 ROM `.bin` files in `candidates/` with saved mtime on or after 2026-09-19; all 14 were included in the structural/hash comparison. The comparison also included the donor below. This was not a whole-corpus scan.
- Donor/source comparator: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`. The local manifest records retrieval on 2026-09-16 from RetroWeb board ID 20611, labels it a community redistribution of vendor firmware, says uploader unknown/page disclaimed, and does not supply a license. It is a donor/reference, not a user-board capture.
- Board identity: existing project records associate the W11 capture with the operational label `BC250-01`; this is not a fresh physical serial or PCB-revision identification. The W11-specific directory contains the image but no matching raw flashrom transcript or capture manifest, as also noted in `docs/research/2026-09-21-baseline-rom-ledger.md`. The older CH347T/Winbond probe record is not a contemporaneous identity check for this W11 capture.
- Current state: the latest readback is historical; the 2026-09-20 FD candidate-build log records the board as unreachable at its last check. No fresh current chip/boot query was performed in this task.

## Saved programmer images

Each is 16,777,216 bytes. Files are sorted by recorded mtime; full-image hashes were freshly recomputed.

| Saved path                                                                     | Recorded mtime (+05) | SHA-256                                                            | Differing byte count vs W11; first..last differing offsets |
| ------------------------------------------------------------------------------ | -------------------: | ------------------------------------------------------------------ | ---------------------------------------------------------- |
| `evidence/programmer/reads/20260919/postwrite-vcn-unlock-w9-deferred-v001.bin` |     2026-09-19 01:26 | `749e4c53a05bde7307e37082ad9842cd6d791f98bc2cf805106eb8da1177b224` | 113,641; `0xAE0088..0xC21CE7`                              |
| `evidence/programmer/reads/20260919/postwrite-vcn-unlock-w9-s9-v001.bin`       |     2026-09-19 01:47 | `d94435add3a3c0d9d9881c77cf1dac172b9c4f8137ca12311caf5ff30b1cf428` | 113,583; `0xAE0088..0xC21CE7`                              |
| `evidence/programmer/reads/20260919/postwrite-vcn-unlock-w10-v001.bin`         |     2026-09-19 02:28 | `136707db95e07faab56f497e0ba4fede708cd5f893bfd0a0f52e7031135d41a5` | 113,625; `0xAE0088..0xC21CF7`                              |
| `evidence/programmer/reads/20260919/postwrite-vcn-unlock-w11-v001.bin`         |     2026-09-19 02:42 | `3c50bc9a65194b75ca805e6ed31c5778369de1fe8eca4600f44e15fae3b40fc3` | Reference image                                            |

The four images are distinct; none of the W9-deferred, W9-S9, or W10 captures is byte-identical to W11. The W11 candidate match is decisive at the saved-byte level, independent of its filename. Programmer-capture attribution remains bounded by the missing same-date W11 transcript/manifest.

## Candidate lineage and latest-vs-applied distinction

| Candidate / saved artifact                                    | SHA-256                                                            | Lineage and observed status                                                                                                                                                                                                                                                                        |
| ------------------------------------------------------------- | ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `candidates/BC250_5.00_clv_VcnUnlock_W9_v001.bin`             | `3c50bc9a65194b75ca805e6ed31c5778369de1fe8eca4600f44e15fae3b40fc3` | Exact whole-image match to W11 readback; saved candidate mtime 2026-09-19 02:40, readback mtime 02:42. This is the likely image applied at the latest captured programmer state.                                                                                                                   |
| `candidates/BC250_5.00_clv_VcnUnlock_GlitchSigned_v001.bin`   | `91de01eb7cb8e97014294adc8692eb8be66c3f95ce8481c234805544c0ddd517` | Later offline VCN candidate (saved 2026-09-19); no equal-hash readback in the bounded set. The documented physical key-acceptance step remains outstanding.                                                                                                                                        |
| `candidates/BC250_5.00_clv_OC_sync_v002.bin`                  | `544b3c24d4b969c3b9b5ab7bbcb873b552f2757808a5855806b5324239749b27` | Offline request profile based on the CLV donor; its build metadata says `hardware_written=false`. It does not match a saved programmer image.                                                                                                                                                      |
| `candidates/BC250_5.00_clv_DF1400_REQUEST_ONLY_v003.bin`      | `4811e1bdc95fa96a74fc7d6e688d6d44aa2cc306c52803c89c635d81917df841` | CLV-donor request-only candidate, explicitly marked `EXPERIMENTAL_REQUEST_ONLY_NOT_FLASH_APPROVED` and `hardware_written=false`; no matching readback.                                                                                                                                             |
| `candidates/BC250_5.00_clv_MeiMeiDXEv3-drivers-only_v001.bin` | `0968a70c4d6fbb51f43d3e0fb5e4b3783dec41e881246356a75c66dc5f19c554` | Newest candidate by saved mtime (2026-09-20 17:01). Build JSON pins base `BC250_5.00_clv.bin` at `ea578104…ca4cb8`. `docs/action-logs/2026-09-20-fd-v22-to-clv-port.md` records an offline-only build, `hardware_written=false`, no flash, and review/hardware checks unrun. No matching readback. |

All 14 candidate binaries and four saved programmer images were hashed and parsed for the bounded match check. The only candidate/readback full-image hash match was the W9-labelled candidate and W11 readback above. Two CLV `OC_vdd80` filenames are duplicate bytes (both `3891f8a6240b594bddc393d8ee55c971229414bad08ca17c7d5883e2357a4948`); this does not create another applied revision.

### Direct donor comparison for the W11 bytes

Against the local CLV donor (`ea578104…ca4cb8`), the W11 bytes are identical in `[0x000000,0x020000)`, `[0x8E0000,0xAB0000)`, `[0xAB0000,0xAE0000)`, and `[0xE00000,0x1000000)`. Differences are confined to the parsed FV at `[0xAE0000,0xE00000)`: 1,326,833 differing byte positions, first `0xAE0088`, last `0xC25586`. This is byte-region lineage evidence for a CLV-derived image with a changed DXE FV, not an independently documented build-parent manifest for the W9-named candidate.

The newer FD drivers-only candidate also records CLV donor as its source and has its own changed inner-FV range (`0xAE0088..0xC28F45` per `.build.json`). It is a separate offline candidate, not a continuation proven to have been applied after W11.

## Verification and limits

- **PASS — identity/hash:** `sha256sum` and direct whole-file comparison show W11 readback and the W9-labelled candidate have identical 16 MiB bytes/hash; no other one of the 14 bounded candidates matches a saved programmer image.
- **PASS — bounded parser:** existing `scripts/firmware_audit.py` version `1.0-readonly` (script SHA-256 `5ead8605678fc5a13eb0cf49c01b43037560ddc485d8ad2686abf0e9c34d9593`) ran on 19 files (4 readbacks, 14 candidates, 1 donor), exit `0`. All 19 parsed as 16 MiB, 19 PSP entries with Fletcher checksum match, 4 BHD entries with checksum match, APCB size 2,972 bytes with checksum match, and four FVs. Machine result was temporary `/tmp/bc250-post-w11-image-lineage-final.json` (SHA-256 `efe85565531557712883a0c31124279024c8f76309d839a07fdc85eba659ead4`). Parser structure is not PSP acceptance, signature-validity, boot, or feature proof.
- **PASS — lineage regions:** direct byte comparison against the donor reproduced the equal ranges and the bounded DXE-FV difference above. Direct pairwise reads produced the W11-relative difference counts in the table.
- **PASS — inventory boundary:** no saved programmer-read file with mtime later than the 2026-09-19 local-day cutoff was present in `evidence/programmer/reads/`.
- **INCONCLUSIVE — board/source identity:** project label `BC250-01` and the historical readback name support attribution, but no same-date W11 capture transcript/manifest, physical serial, or PCB revision was present in this scoped set.
- **UNRUN — current state:** no current programmer read, physical board check, boot, BIOS identity, runtime, or performance query was made; the board's present installed image remains unknown.

The next decisive check for **present** chip contents would be an operator-authorized read-only capture that records physical board/chip identity and the full programmer stdout/manifest. This report does not authorize or perform it.
