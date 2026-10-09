# D8 LZMA Explicit-Size No-op Control

## Title and scope

Rebuild the D7 no-op same-slot control while preserving the accepted AMD/AMI
LZMA-alone header's explicit uncompressed-size field.

## Planning anchor

- Accepted baseline LZMA header: `5d000000011000420000000000`; decoded size
  `0x420010` equals the actual decompressed stream length.
- D5/D6/D7 LZMA headers: `5d00000001ffffffffffffffff`; Python emitted an
  unknown-size marker despite otherwise valid decompression.
- D7 no-op failed initialization, so the header difference is now the smallest
  concrete unexplained outer-envelope variable.

## Connected groups or observed existing logic

- Use the D7 same-size replacement and preserve every decompressed byte outside
  the 12,288-byte PE payload.
- After LZMA compression, replace header bytes `5..12` with the exact
  little-endian decompressed-stream length, matching the accepted baseline
  convention.
- Keep all signed PSP-side material and APCB byte-identical.

## Use cases

1. D8 boots: explicit LZMA size was the D5-D7 construction defect; rebuild the
   D6 SMU-unlock candidate with the same fix.
2. D8 fails: investigate compressor stream compatibility or another outer FFS
   metadata difference before any more unlock payload testing.

## Implementation checklist

- [ ] Patch only the generated LZMA header size field after compression.
- [ ] Verify decompression and exact inner-FV invariants.
- [ ] Reparse four FVs, checksums, target slot, and extracted payload.
- [ ] Compare the complete 13-byte LZMA header against the accepted baseline.
- [ ] Record cold boot as unrun until separately approved and flashed.

## Open questions

- Blocking: whether the firmware decompressor also requires the vendor's exact
  LZMA encoder stream, beyond the explicit-size header.

## Decision log

- 2026-09-12: the installed deobfuscation skill's layered-envelope method
  exposed the missing explicit size; change the construction method before
  any new unlock logic.
