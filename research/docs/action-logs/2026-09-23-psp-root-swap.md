# PSP root-key swap discriminator (lane V3 rung 1) — 2026-09-23

## Intent (before any write)

Attack-track order (no soldering, offline builds allowed). Question: does the on-die PSP ROM
hash-anchor the raw type-0x09 key blob (`ffc8acd4`, SPI `0x93F000`, 0x440 B, unsigned)? It is
the only key outside the KDB and the only root of the carrier chain. Rung 1 swaps ONLY the
256-byte RSA modulus in place (little-endian, layout asserted: version@0x00, cert_id@0x04,
kid@0x14, e u32@0x40, modulus@0x50..0x150), keeping kid/e/tail untouched. One variable.

Target files (new only):

- `candidates/BC250_5.00_clv_ROOTKEY-swap-0x09_v001.bin`
- builder `scripts/build_psp_root_key_swap_candidate.py`
- report `evidence/firmware-audit/20260923-psp-root-swap/build-report.json`
- base `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (untouched)

No flash. Flash needs the operator's exact approval of the candidate hash.

## Result

- Gate PASS: 256 changed bytes confined to `0x93F048..0x93F148` (modulus in place), kid
  unchanged, e unchanged, 64 B tail at +0x400 untouched (purpose unknown, risk recorded).
- Modulus convention: little-endian (original top-bit byte at the end). Our key: RSA-2048,
  e=65537, kid `e298de0371c5de85109f4e4be68b83c7` (sha256(n LE)[:16], same convention as the
  glitch builder).
- The original ffc8acd4 modulus occurs EXACTLY ONCE in the image (no copies in `0x4F` or
  elsewhere) — no consistency edits needed or made.
- Candidate sha256 `46ec00bbcda7a4d0e6fbe6b9a39457395b573f8667141919e58e7f146ca8ecbf`.
- Outcome semantics: boots normally -> ROM does not anchor the blob -> software re-root
  ladder opens (rung 2: re-sign KDB carriers, swap 96ea7cfe, re-sign the locks). Board parks
  -> the blob is anchored -> root-swap lane closed, EMFI target confirmed as this exact check.
- Claim boundary: static discriminator only. Boot behavior UNRUN.
