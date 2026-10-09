# t28 donor reconciliation — 2026-09-14, Asia/Almaty

## Intent

Compare the exact early ARM t28 sequence in AMD 4700S C0A and the fresh BC250
readback, with explicit slice offsets and ARM Thumb mode. No image write,
programmer write, or board execution.

## Result

- C0A slice: SPI `0x9F1100`, size `0x1A790`, SHA-256
  `e597065762b4e434c3c08c91a3f1d5c2ad234b583def4dc21fdba4d282ff44e4`.
- BC250 slice: SPI `0x984F00`, size `0x1A770`, SHA-256
  `ebd9a7d279c5ac5751ebcc76fa7380c2da003e8f9bb49c1a419ef4c951e320e1`.
- C0A function at local `0xFC9C` and BC250 function at local `0xFECA` are
  the same algorithm: `svc #0x7C` writes `0x0900C004 <- 1`,
  `0x1F8A4 <- 1`, then iterates five `(address,value)` pairs with zero values,
  stopping on nonzero service status. Tables begin at `0xE188D4` (C0A) and
  `0xE188D8` (BC250), and both contain `0x1F8C4/0x1F8C8/0x1F8CC/0x1F8D0/0x1F8D4`
  followed by zeros.
- This early PSP sequence is functionally equivalent across donor and BC250;
  the 4700S donor does not supply a hidden nonzero VCN unlock table. Neither
  t28 image contains `0x0900C830`, `0x0900C834`, or the 56-entry bank-12 set.

## Interpretation

Scope qualification: the comparison establishes equivalence ONLY of the named
function and five-entry table. It does not close the whole t28 donor path or
prove absence of computed bank-12 programming elsewhere. BC250 entry is local
0xFEC8 (MOVS precedes PUSH), not 0xFECA. The runtime table pointers imply an
apparent base0x00E00000 for these offsets, not0x0E000000. Service implementation
location has not been traced here; 'on-die' below is a historical hypothesis,
not a finding of this comparison.

The donor comparison closes the hypothesis that a 4700S t28 carrier already
contains a usable VCN gasket or alternate nonzero power policy. The interesting
remaining difference is implementation of the `svc #0x7C` on-die handler and
its hardware interpretation, which is not patchable in the image. PS5 material
would only add value if an authorized full firmware image with a comparable
signed carrier becomes available; no such image is present in the bounded
corpus. No unlock claim is made.
