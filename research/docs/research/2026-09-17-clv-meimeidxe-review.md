# Independent review: BC250_clv_MeiMeiDXEv3_8c_omarchy_v001.bin

Date: 2026-09-17. Reviewer: independent (not the build author), per review policy.
Scope: read-only re-verification of the candidate plus one new review file. No flash,
no writes to `candidates/`. Reviewer re-ran every check below personally; the build
report (`docs/research/2026-09-17-clv-meimeidxe-build-report.json`) was not trusted
without reproduction.

## Verdict

**GO, conditional** — for a single flash cycle on BC250-01, subject to conditions C1-C4
below. Structurally the candidate is exactly what the build report claims. The residual
risk is behavioral (3.00-family DXE FV on a 5.00-lineage base, and an untested base
itself), not structural; it is bounded by a verified recovery chain.

## Checks re-run by the reviewer (all PASS unless noted)

1. **Hash (PASS).** `sha256sum candidates/BC250_clv_MeiMeiDXEv3_8c_omarchy_v001.bin`
   = `af53102601bc85027d3b62a9035d2b1767811833ee688d33568fcbaf91dae152` (matches).
   Base `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` = `ea578104...` (matches).
2. **Changed-range confinement (PASS).** `cmp -l` candidate vs clv: first diff at
   0xAE008C, last at 0xC25A81, 1,328,487 differing bytes; **zero differing bytes
   outside 0xAE0000-0xE00000** (report's range is the conservative superset).
3. **PSP/APCB identity (PASS).** `scripts/firmware_audit.py` run on both candidate and
   clv: PSP dir @0x8E0000, Fletcher32 stored = calculated = 0x17AA38B9, 19 entries,
   all entry (type, size, body_sha256) tuples equal to clv (covers t8 SMU and t28
   bodies); APCB (offset 0xAB0000-page region incl. CBSG, checksum byte 0xC0) equal;
   BHD equal.
4. **Outer FV structure (PASS).** `_FVH` scan: FVs at 0x0 (0x20000), 0xAE0000
   (0x320000), 0xE00000 (0x200000), 0xE02000 (0x1FE000); all GUID
   8C8CE578-8A3D-4F1C-9935-896185C32DD3, rev 2, 16-bit header checksums PASS. Grafted
   FV tail 0xDF0000-0xE00000 is all 0xFF.
5. **Outer FFS walk (PASS).** Pad file (extended header carrier) at 0xAE0048 + main
   FFS 9E21FD93-9C72-4C15-8C4B-E77F1DB2D792 (type 0x0B) at 0xAE0078; both FFS header
   checksums PASS (sum-to-zero with State and IntegrityCheck.File excluded).
6. **LZMA + inner FV (PASS).** GUIDED section EE4E5898 (LZMA FORMAT_ALONE) decompresses
   to 4,403,216 bytes = RAW section (12 B) + FV_IMAGE section + inner FV 0x433000.
   Inner FV header checksum PASS, GUID identical, hdrlen 0x48.
7. **Inner FV fidelity to the FD donor (PASS — the decisive new check).** Decompressed
   the FD donor variant `BC250_3.00_MeiMeiDXEv3` (still at /tmp/fd-fw) the same way and
   compared FFS inventories: 193 files in both, identical GUID/type sequence, and
   **exactly one differing file** — the logo FFS 7BB28B99 (0x30e vs 0x218). All other
   192 files byte-identical (same type, size, body hash). The graft adds nothing and
   removes nothing relative to the FD variant except the logo slot.
8. **Logo payload (PASS).** Logo FFS header checksum PASS; payload GUIDED section
   98584EEE decompresses to [u24][0x19][PNG][UTF-16LE "omarchy.png"]; embedded image is
   a valid PNG 300x300, sha256 `edd69e61...` = byte-exact match to
   `/usr/share/omarchy/icon.png`.
9. **Recovery chain (PASS).** Pre-m0 read `evidence/programmer/reads/20260916/pre-m0-read-a.bin`
   = `3f836668bc194cfaef23...` (verified by fresh hash); clv `ea578104...` on disk;
   external stock `83c4e420` referenced in the m0-window log. The chip currently holds
   M6 (silent), so the next flash is itself a recovery flash from a known image.

## Cross-lineage analysis (item 4 of the task)

Measured facts (all `static-analysis` / `observed-bytes`):

- The 0xAE0000 FV header is byte-identical across stock 3.00, stock 5.00, clv, and FD.
  The graft does not change any FV-level identity the base firmware relies on.
- SEC FV (0x0-0x20000) differs between 3.00 and 5.00 lineages by 35,523 bytes; PEI
  region (0x20000-0x8E0000) by 44,097 bytes. **PEI/SEC are genuinely different builds.**
- DXE module sets (decompressed inner FVs): clv has 187 FFS GUIDs; FD has 193;
  **all 187 clv GUIDs are present in FD**; FD adds exactly 6 drivers (incl. the
  7A8B9C0D-... MeiMei CoreUnlock). Of the 187 common GUIDs, **174 are byte-identical**
  (type+size+body). Only 13 differ — a handful of version bumps and the logo/setup
  FREEFORM files. This is one EDK II generation, same platform, same toolchain family;
  the two lineages' DXE volumes are close siblings, not foreign objects.

Reasoning on the residual risk:

- **HOB interface:** the DXE Core and PEI Core exchange a generic EDK II HOB list;
  the FV load address (0xAE0000) and FS GUID are identical. No lineage-specific
  DXE->PEI ABI divergence was found in the module-set comparison, though the closed
  AMD PEI/SEC sources prevent proving this exhaustively. The 174/187 byte-identical
  module overlap is the strongest available static evidence of compatibility.
- **NVRAM:** the variable store lives outside the grafted region and remains clv's
  (5.00-lineage). A 3.00-built setup/infrastructure DXE will read 5.00-written
  variables (e.g. AmdSetup). UEFI variable services tolerate size mismatch by falling
  back to defaults, but an AmdSetup layout delta could yield wrong-but-valid
  configuration on first boot. **Unverified; not settled by any check run.**
- **Community provenance:** FD ships its images as whole 3.00-lineage images; there is
  no known community case of this exact FD-FV-on-5.00-base combination. The graft is
  uncharted, but its blast radius is the DXE volume only.
- **8c surface:** the MeiMei CoreUnlock driver (7A8B9C0D, debug string
  `MeiMeiDXEv3_SMU_Core_Unlock.dll`) is present in the grafted FV and absent from clv.
  Whether it produces a working 8-core unlock on the 6C/12T-downcored BC250-01 with
  5.00 PSP/SMU (0.58.6.0) is entirely unverified. Static only; expect nothing at P0/P1.

## Failure path (item 5)

If the grafted FV fails to dispatch on the clv base, the likely observed signature is
the campaign's established **LED static red, no LAN, true-silence class** (M5/M6,
oracle-confirmed 2026-09-17). Critically, this is **indistinguishable** from the
PSP-region kill-locus signature documented for M0-M6: no observation channel (J5 UART,
POST code) was ever established, so a silent result will not localize the failure.
A partial-dispatch variant (DXE core runs, BDS/console fails) could instead present as
"trains, LAN up, no video/logo" — any divergence from pure static-red silence would
itself be informative.

## Unrun checks

- QEMU/emulated DXE dispatch (no BC250 PEI platform model exists to run against).
- AmdSetup NVRAM record layout comparison 3.00 vs 5.00 (task referenced @0x4BB record;
  not re-derived here).
- Hardware acceptance of the whole image, boot, logo rendering, 8-core behavior, VCN.
- Offline signature verification of PSP blobs (tooling unavailable, unchanged from all
  prior campaign candidates).

## Conditions for GO

- **C1 (control, one variable):** the clv base has never been booted on this board.
  A silent result would confound "clv base incompatible" with "graft incompatible".
  Strongly preferred: flash plain clv (`ea578104`) first, observe P0/P1, then flash the
  candidate. If the operator declines a second flash cycle, they must accept that a
  silent outcome carries this ambiguity.
- **C2 (standing anti-G6 rule):** the campaign's promoted rule is instrument-first
  (J5 UART / POST) before any next flash campaign. GO assumes either a working
  observation channel, or an explicit operator acceptance that this run may produce
  another unlocalizable silent failure.
- **C3 (single cycle, rollback on hand):** exactly one flash cycle; rollback images
  `3f836668` (pre-m0) and `ea578104` (clv) stay untouched on disk; full programmer
  readback + sha256 match immediately after the write, before any boot attempt.
- **C4 (no expectations of 8c/VCN):** this run may only ever prove boot + logo +
  dispatch. No VCN, no 8-core, no OC conclusions from this candidate.

## Scope statement

Checked: hashes, byte-level changed ranges, PSP/APCB/BHD identity (two-parser), FV/FFS
structure at all four levels, LZMA integrity, inner-FV fidelity to the FD donor
(module-level), logo payload byte-exactness, recovery-image presence. Reviewer ran all
checks independently; the build report's claims were confirmed without exception where
re-run.
