# Fresh-baseline D3-B2 VCN candidate

## Title and scope

Build a new offline VCN-unlock BIOS candidate from the verified `BC250-01` stock read. The candidate combines the existing APCB DFG hypothesis with modified SEC_GASKET (`PSP type 0x24`) and TOS_SECURITY_POLICY (`PSP type 0x45`) records. It is not a release image and is not authorized for hardware write by this specification.

## Planning anchor

- Stock source: `evidence/programmer/reads/20260911/read-a.bin`, 16,777,216 bytes, SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- Failed first hardware hypothesis: APCB DFG-only candidate wrote/read back correctly but produced no display on its first boot; execution stage is unknown.
- Historical transformation reference: `archives/imported/historical-bios-repo/legacy-bc250-bios/tools/patch-build/d3b2_build.py` and the historical D3-B2 package image. The script is not directly reusable because it contains Windows-only absolute paths, MD5-oriented output, and a different baseline checksum byte.
- Unsigned gasket-body reference: `archives/imported/recon-evidence/legacy-tmp-bc250-recon/bc250_sec_gasket_with_vcn_UNSIGNED_DO_NOT_FLASH.bin`, 11,792 bytes, SHA-256 `531d27b386d631ccdad3e8397f916ee4b5f9608d9516317b0d661db92d4a1017`.

## Connected groups and existing logic

- APCB DFG words at `APCB+0x130` and `APCB+0x16C` currently encode `0x001FFF00`; the prior candidate used `0x007FFF00`.
- SEC_GASKET type `0x24` is currently at flash `0x982000`; the historical route builds a modified copy at `0x9E0000` and repoints the PSP directory.
- TOS_SECURITY_POLICY type `0x45` is currently at `0x9CA400`; it is applied after type `0x24`, so a stock type-45 policy can overwrite matching gasket values. The combined route builds a modified copy at `0x9E4000` and repoints the directory.
- Target changes include `0x03E810: 0 -> 6`, DF aperture expansion, and the donor-derived HWID-12 VCN tail in groups `0x201/0x280`.
- Both modified `$PS1` copies retain historical signature tails while changing signed payload bytes. Offline signature acceptance is therefore not established and PSP may reject them.

## Use cases

1. Test whether the combined two-policy-carrier model reaches a later boot/VCN state than APCB-only.
2. Distinguish an APCB-only limitation from PSP rejection of modified `$PS1` policy carriers.
3. Preserve a deterministic stock-derived artifact for independent review and exact per-image approval.

## Implementation checklist

- [x] Create a path-parameterized builder with strict baseline assertions and SHA-256 reporting.
- [x] Write only to a new candidate path; never modify the stock or currently programmed readback.
- [x] Build type `0x24` at `0x9E0000` and type `0x45` at `0x9E4000` from the verified stock baseline.
- [x] Repoint only the two matching PSP directory entries and recompute the observed Fletcher32 directory checksum.
- [x] Apply the two APCB DFG word changes and recompute the APCB byte checksum at `+0x10`.
- [x] Produce exact changed-byte/range reports and source/output hashes.
- [x] Run firmware, APCB, `$PS1`, directory, size, alignment, and independent byte-level checks.
- [x] Verify that all bytes outside the declared regions are unchanged.
- [ ] Obtain an independent review of the actual new artifact and its failure path before requesting hardware-write approval.
- [ ] Require a new exact file/hash/board approval for any flash.

## Open questions

- Blocking: will the target PSP accept, skip, or fail on the modified signed-payload copies?
- Blocking: does the historical policy-body layout match the current board's closed supervisor parser?
- Non-blocking for build: is the APCB-only no-display result caused by PSP/APCB rejection or a separate display state?
- Runtime: if the board boots, will the policy changes power VCN and permit Linux ring completion rather than only expose registers?

## Decision log

- 2026-09-11: keep the preserved stock image as the build source even though the board currently contains the APCB-only candidate.
- 2026-09-11: reuse and adapt the historical D3-B2 algorithm; do not flash the historical image from its mismatched baseline.
- 2026-09-11: classify the output as an unsigned-policy research candidate until independent review and hardware evidence exist.
- 2026-09-11: fresh candidate built at SHA-256 `439e248141ef6a9c1313bc7815696d570be8fed5471262596186f3da8914747d`; root structural checks pass 21/21, independent review remains blocking.
