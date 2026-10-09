# 2026-09-24 — Flash packages staged for both one-variable candidates

## Intent (before the write)

Goal: complete the operator-approval dossier for both validated
candidates so the flash decision is a single yes/no per package. No
flash happens here; the packages are STAGED copies of already-verified
candidate images plus their runbooks.

Targets (new paths only):

- `firmware-flash-pkg/20260924-v003b-route-b-vcn/`
- `firmware-flash-pkg/20260924-clv-fclk1800-apcb/`
- `docs/guides/bc250-v003b-route-b-programmer-flash-runbook.md`
- `docs/guides/bc250-clv-fclk1800-programmer-flash-runbook.md`

## Result

Package 1 (VCN, route B, on the community 3.00 MeiMeiDXEv3 base):

- `BC250_3.00_MeiMeiDXEv3_vcn_v003b.bin`
  sha256 `3a7fcf8507c6ea1a366bc8f8c584f7613e0cfac4ce9fcef47c031ed80f853f4d`
- README (identity, route-B driver semantics, policy-lock rationale,
  role in the validation sequence) + SHA256SUMS.
- Runbook: inherits the v003 hardware procedure (CH347 + flashrom,
  W25Q128.V, double-read backup, rollback A/B); states the v003b
  differences (no 0x1B send, replay + guards, abort-on-mismatch) and
  the acceptance gates H1-H7 including the probe4l6 before/after pair
  (controller measured alive-but-not-enabled pre-flash).

Package 2 (FCLK 1800, on the clean clv 5.00 base):

- `BC250_5.00_clv_FCLK1800_APCB_v001.bin`
  sha256 `3d6348c65a0c2ee500e13f3b1a5c9e9c64c57e36b570fbd1e85a19b9713871f8`
- README (3-byte change, emulator validation, role/flash-order) +
  SHA256SUMS.
- Runbook: same inherited procedure; C1-C6 gates with the honest
  split (service argument proven, SVC28 transport to physical FCLK
  not); expected outcome 1800:1800:900 (UCLK division unchanged),
  NOT 1:1:1 — stated explicitly so the result is not misread.

## Verification

- `sha256sum -c SHA256SUMS` from inside each package dir: both `OK`.
- `cmp` package copy vs `candidates/` original: byte-identical for
  both.
- Flash order documented in both READMEs: v003b first, evaluate,
  known state, then the FCLK image (different BIOS lineage; one
  variable per flash).

## Status

Both packages STAGED, NOT flashed. Physical execution requires the
operator approval template from each runbook (exact name + SHA-256,
pre-write dump hash, recovery path). The remaining open decisions are
unchanged: flash approval, D1 (SoC voltage), the PSP-breach UCLK track.
