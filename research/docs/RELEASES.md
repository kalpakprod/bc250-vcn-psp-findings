# Release numbering and repo order

> Audit 2026-09-27: this is a dated release-history record. The "Going public" section below predates the explicit curated-repository exception in docs/git-storage-policy.md and is not the current publication policy. No publication is authorized by this audit.

How this project names firmware releases, where they live, and what may go
public. Written 2026-09-24 after a 3-agent audit + critic + primary-source
check (see `docs/action-logs/2026-09-24-v003b-route-b.md`, releng entries).

## How versions were written (honest history)

Ad hoc. One ladder counter `vNNN` shared across different base lines
(`v004` exists in community-3.00 and pre-dump lines; bare `v003` in three
tracks), letter suffixes without formal meaning (`b/c/d/e`), `r` for
rebuilds, campaign dirs (`d5`–`d19`, `s*`) with their own nested scheme.
Result: 63 root images, 32 without manifests, three naming schemes at once.
This document freezes that history and fixes the rules for NEW builds only.

## Rule 0 — published names never change (amended 2026-09-24)

A built or flashed name is immutable (SemVer rule, coreboot/EDK2 practice).
Old chaos stays as history and is mapped — never renamed — in the generated
registry `candidates/VERSIONS.md` (`scripts/gen_versions_registry.py`).

Amendment 2026-09-24, operator decision: the v004–v009 ladder was renamed to
plain-language filenames (the filename says what is inside; see `MISTAKES.md`
2026-09-24). Bytes and sha256 did not change — only names. Old vNN tags
survive as the `alias` field in each `.build.json` and in append-only
action logs. This amendment covers the ladder only; everything else stays
frozen.

## New-build scheme (from the next build on)

`BC250_<track>_<method>_<code>_0.<ladder>.<fix>[-<opt>]+g<sha>[.rbN]`

- `track`: `predump` | `clv500` | `community300` | `dxe` | `s` | `probe`.
  The D-campaign (`d5`–`d19`) is the `dxe` track, NOT a donor board number.
- `method`: `ownfv-insert` | `append` | `slot-swap` | ...
- `code`: `routeb` | `secure` | `rtb` | `noop` | ... (real code variant).
- `0.<ladder>.<fix>`: SemVer-shaped, major stays 0 until a stable release
  (Dasharo rule). `ladder` continues the current counter (next new: `0.10.0`).
  Old letters map to fix numbers (`b`=1, `c`=2, `d`=3, `e`=4) for reference only.
- `-<opt>`: reserved for real orthogonal options (O2/O3 were). Omit otherwise.
- `+g<sha>[.rbN]`: build metadata — short git sha of the build tree, plus
  rebuild counter. Ignored in precedence (SemVer): same version + new `rbN`
  = same content claim, different bytes — compare by sha256.

Every `.build.json` gains `git.sha`, `git.describe`, `toolchain.*` next to
the existing `base/output/blob sha256` (traceability, not renaming).

No `staging/active/stable` renames: promotion is a status change in
`candidates/VERSIONS.md` (`STAGED` → `FLASHED-*`), one sha keeps one name.
(Changelog `YANKED` is reserved for flashed-then-recalled images.)

## Current ladder in both notations (renamed 2026-09-24, bytes unchanged)

| plain filename                                                  | old alias     | canonical reading           | sha12     | status                   |
| --------------------------------------------------------------- | ------------- | --------------------------- | --------- | ------------------------ |
| SUPERSEDED-BC250_pre_dump_vcn_own_fv_v003e.bin                  | v003e (ownfv) | 0.3.4 routeb ownfv-insert   | b67e59d7… | FLASHED-HUNG             |
| BC250_vcn-driver-FULL_lzma-BROKEN_early-slot.bin                | v004 (ownfv)  | 0.4.0 routeb ownfv-insert   | 98b9c2bd… | FLASHED-HUNG             |
| BC250_vcn-driver-FULL_lzma-FIXED_early-slot.bin                 | v005          | 0.5.0 routeb ownfv-insert   | 2fadb173… | FLASHED-HUNG             |
| BC250_vcn-driver-STUB_no-hw-ops_early-slot.bin                  | v006r-noop    | 0.6.0+rb1 noop ownfv-insert | 6500bea5… | FLASHED, verdict pending |
| BC250_vcn-driver-FULL_lzma-FIXED_appended-at-end.bin            | v007-active   | 0.7.0 routeb append         | 9d249397… | STAGED                   |
| BC250_vcn-driver-STUB_no-hw-ops_appended-at-end.bin             | v007r-noop    | 0.7.0+rb1 noop append       | 0133a34b… | STAGED                   |
| BC250_vcn-driver-FULL_safe-reads-only_appended-at-end.bin       | v008-secure   | 0.8.0 secure append         | c935e3ec… | STAGED                   |
| BC250_vcn-driver-FULL_deferred-to-readyboot_appended-at-end.bin | v009-rtb      | 0.9.0 rtb append            | 56df6244… | STAGED                   |

(Not ladder: `BC250_3.00_MeiMeiDXEv3_vcn_v004.bin`, the community-3.00 track,
`2981b252…`, PACKAGED — untouched. The old table also carried a wrong sha12
for v003e (`7b28fd45…`); the file hashes to `b67e59d7…`, fixed above.)

## Flash release checklist (unchanged gate)

Full verified dump, independently confirmed recovery path, explicit approval
for the exact image + target, cold-boot + readback planned. Then: INTENT in
the action log BEFORE any write, chip identity, double read, package sha,
write + verify, independent readback + structural re-parse, RESULT in the log.

## Directory order

Frozen, do not touch: `import/` (31G provenance), `evidence/programmer/`
(originals), pinned tools, pre-migration snapshot zip, `.gitignore` binary rules.

Phase 0 — done 2026-09-24: this doc; generated `candidates/VERSIONS.md`;
`CHANGELOG.md`; `firmware-flash-pkg/` text-in-git + binaries-ignored (hole
closed); `specs/` marked archive (new plans → `.procoder/`).

Phase 1 — needs owner word (recommend: after VCN boots, not mid-campaign):
32 orphan manifests (or move to `candidates/legacy-unsupported/`);
`firmware-flash-pkg/` stop byte-duplicating `candidates/` (reference, not copy);
`evidence/candidates/` retire in favor of per-tree manifests;
`docs/repository-layout.md` + inventory rewrite; root stray
(`Build/`, `dump/`, `scratch/`, session exports) triage;
`evidence/bc250-system-audit-20260923/` (1.1G) disposition.

## Going public (strategy, gated — nothing published)

Current state: no public remote; `docs/git-storage-policy.md` explicitly
forbids publication. Lifting it is an owner decision. Verified facts:
tracked tree is ~3 MB / 437 files (publishes cleanly); GitHub blocks files
≥100 MiB and wants repos <1–5 GB (primary docs); GitHub Releases attachments
have no total size/bandwidth cap — the vehicle for 16 MB images, never the
git tree; LFS free quota is 10/10 GB (primary docs, not 1/1).

Order (only after the ban is lifted + a secret scan): S1 close ignore hole
(done); S2 micro-repo `bc250-tools` (scripts+tests+README, no binaries);
S3 research digest (2–3 self-contained reports + proof JSONs); S4 sources
that build FROM the user's stock image (xdelta + script, never full 16M
vendor blobs). Outreach order: bc250-collective (warmest, issue/PR),
coreboot mailing list (narrow question + log; Gerrit only for clean patches,
no PSP blobs), Win-Raid L1T (NVAR/menu level + tester recruiting), L1T forum

- r/coreboot (announce). Never: `import/`, full SPI dumps, programmer/audit
  evidence as-is, flash-pkg binaries as-is. Every published flashable ships
  with a recovery path and a brick disclaimer.
