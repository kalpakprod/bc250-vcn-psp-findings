# G7 correction: ~/Downloads C0A/C08 are MODS, not vendor stock (2026-09-16)

## Wrong claim (retracted)
Root labeled `~/Downloads/C0A.zip` / `C08.zip` inner images (`e8fa745b...` /
`26863de9...`) as "official/vendor-stock 4700S BIOS" in
`docs/action-logs/2026-09-16-4700s-vendor-bios.md` and the
`memory/firmware-audit.md` intake entry. The donor DeepResearch synthesis
challenged this; root then verified the challenge with its own byte diff.

## Measurement (own run, PASSED)
- `Setup` module, corpus-C0A (`bb2cf51d...`) vs `e8fa745b...`: same length
  (191,424 B), exactly 35 changed bytes, ALL to value `0x47`
  (`45->47` x14, `12->47` x10, `14->47` x8, `46->47` x2, `13->47` x1),
  sparse offsets `0x13717...`. Textbook AMIBCP unhide pattern.
- `AMITSE`: same length (322,496 B), 35 changed bytes (one single + a run at
  `0x43bb0+`).
- All other 243/245 modules byte-identical; PSP/APCB/NVRAM identical
  (from the earlier module-level diff).
- Verdict: `e8fa745b...` is an AMIBCP-unhide MOD of C0A-stock `bb2cf51d...`;
  by symmetry of the pack pair (both images stamped 2022-05-31 ~10:4x, same
  31-minute mod-session window), `26863de9...` is the matching C08 MOD.
  Forum attribution (Maxinator500, bios-mods, tid39055, Drive IDs
  1a6T.../1FtV...) UPGRADED 2026-09-16 to ROOT-VERIFIED: both Drive downloads
  are byte-identical to the ~/Downloads packs (fb01dd67.../a7f2e4b5...).

## Corrected labels (use from now on)
- C0A-STOCK = `bb2cf51d...` (corpus, true stock, 245 modules).
- C0A-MOD = `e8fa745b...` (AMIBCP unhide, REFERENCE only, never a flash base).
- C08-MOD = `26863de9...` (same, REFERENCE only).
- C08-STOCK = `ef32de2f...` (worker hash, bytes NOT in hand, UNVERIFIED).
- C09 = `70429266...`, C07 = `87ce2ebc...`, C06 = `dc62f7b6...` (worker
  hashes, UNVERIFIED). C04 = factory-only, no bytes.
- P5.00-stock `0d6f136c...` (BC250-native, synthesis top base pick) is NOT in
  the repo and NOT downloaded — the highest-value missing byte set.

## Impact
- Any plan that flashes `e8fa745b...`/`26863de9...` as "stock donor" is void;
  mods are reference-only (unknown AMIBCP side effects, forum provenance).
- The 4700S-as-base branch now starts from TRUE stocks (corpus C0A first).
- Standing brief `docs/research/deepresearch-donor-bios-brief.md` §6c and the
  2026-09-16 vendor-bios action log carry correction notes; original entries
  preserved append-only.
