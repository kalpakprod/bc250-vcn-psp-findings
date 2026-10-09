# Action log: clv + MeiMeiDXE v2.2 + omarchy logo candidate build

Date: 2026-09-17 (UTC). Actor: root (operator request). Offline build only;
no flash, no hardware action, ever, without a separate explicit operator
approval of the exact image.

## Intent (BEFORE writes)
Operator requested: base = P5.00_clv (D25, `ea578104`), graft the
Forbidden-Darkness MeiMeiDXE v2.2 DXE volume (with 8c-unlock ACPI surface
and individual toggles), omarchy boot logo, all onto the clv base.

Known evidence:
- FD v2.2 repo @740546f: 16 variants, all 3.00-family; SMU t8 = 6a3da1ef
  (unchanged); entire diff vs stock 3.00 = 0xAE0088-0xC2654B (UEFI FV
  region). Variants differ only by logo/branding.
- Our clv = BC250_5.00_clv.bin `ea578104`; stock P5.00 = 0d6f136c.
- PSP/SMU/APCB layers must remain byte-identical to clv.

Acceptance criteria for the candidate:
1. New file in candidates/ (never overwrite; never touch baselines).
2. PSP directory, all PSP bodies (incl. t8 6a3da1ef-equivalent for the
   5.00 lineage and t28), APCB incl. CBSG: byte-identical to clv.
3. DXE FV region carries the MeiMeiDXE v2.2 volume from the FD archive
   (FV header valid, _FVH checksums pass), 8c ACPI surface included.
4. Omarchy logo embedded the same way FD variants embed their logos
   (reuse the FD variant logo slot mechanism).
5. Machine-readable build report: source/output SHA-256, changed ranges,
   FV/FFS structural checks, hardware_written=false.
6. Independent structural validation (second parser or re-read) recorded.
Rollback: delete candidate + report; no hardware state exists.

## Result (AFTER writes) — worker build, 2026-09-17 UTC

Status: BUILT, offline, static verification only. hardware_written=false.
No flash. No git commit. No existing file modified; only new files under
candidates/ (see build report JSON for full detail).

Output:
- candidates/BC250_clv_MeiMeiDXEv3_8c_omarchy_v001.bin
  sha256 af53102601bc85027d3b62a9035d2b1767811833ee688d33568fcbaf91dae152
- candidates/BC250_clv_MeiMeiDXEv3_8c_omarchy_v001.build.json

Graft decision (observed bytes): 5.00-lineage and FD 3.00 images both carry
one self-contained DXE FV at 0xAE0000 (len 0x320000, header 0x48, GUID
78E58C8C-..., header bytes identical across clv/5.00/3.00/FD, 0xFF tail).
Whole-FV replace of FD FV into clv. Changed range vs clv: 0xAE0000-0xC26000
(1335296 bytes). Everything outside 0xAE0000-0xE00000 byte-identical to clv.

Structure findings:
- Outer FFS 9E21FD93 wraps LZMA (EE4E5898 GUIDED) section stream =
  RAW section (12 B) + FV_IMAGE section (0x17) with inner FV.
- FD logo isolated to inner FFS 7BB28B99-...; payload format decoded from
  18 samples: [u24=4+len(image)][0x19][JPEG or PNG][UTF-16LE name, NUL-term].
- Omarchy logo: /usr/share/omarchy/icon.png (300x300 PNG,
  edd69e61...) embedded, name 'omarchy.png'. Inner FV grown 0x432000 ->
  0x433000 (one block) because new logo FFS 0x30e > old 0x218 + free tail
  0x2a6; inner FV header 16-bit checksum recomputed (PASS); file count and
  last file unchanged; decompress round-trip from output byte-exact.

Validation (two parsers):
- scripts/firmware_audit.py on clv + candidate: PSP Fletcher32 PASS
  (stored=calc=0x17AA38B9), entry count 19, all entry sizes equal clv;
  APCB (incl. CBSG page) checksum PASS and equal to clv; BHD equal.
- Independent re-scan of output: outer FVs 0x0/0xAE0000/0xE00000/0xE02000
  header checksums PASS; inner FV header checksum PASS.

8c surface (static only): CoreUnlock driver 7A8B9C0D-... present in grafted
FV (edk2 build string 'MeiMeiDXEv3_SMU_Core_Unlock.dll'); absent in clv.
Literal 0x115A870 NOT found as raw bytes in any decompressed section —
address is composed at runtime (open observation). No 8-core ACPI (C00F)
tables in FV; per project docs ACPI update is OS-side.

Not verified (evidence class boundary): hardware acceptance of the
3.00-family FD FV on the 5.00-lineage clv base (PSP/APCB differ between
3.00 and 5.00 lineages), boot behavior, logo rendering, actual unlock.
Rollback: delete the two new candidate files.

## Flash intent (2026-09-17, operator-authorized)
Target: BC250-01, Winbond W25Q128.V @ ch347_spi (identity verified: double
control dump 3e75177e == post-m6-readback). Image:
candidates/BC250_clv_MeiMeiDXEv3_8c_omarchy_v001.bin sha256 af531026...,
independent review GO-conditional (docs/research/2026-09-17-clv-meimeidxe-review.md);
operator explicitly accepted C1 (direct candidate, silence-ambiguity) and C2
(LED/ping oracle, no UART). Rollback: pre-m0 3f836668 / clv ea578104 on disk +
pre-flash-control dumps. Procedure: flashrom -w (erase+write+verify), then
independent -r readback, sha256 must equal af531026; then operator cold boot,
P0 oracle (green blink = boot, static red = halt).

## Flash result (AFTER)
flashrom -p ch347_spi -w: erase/write done 0..0xFFFFFF, VERIFIED.
Independent readback: post-flash-readback.bin sha256 af531026... == candidate.
Chip state = candidate clv+MeiMeiDXEv3+8c+omarchy. Next: operator cold boot,
P0 oracle (green blink = boot; static red = halt; ping check). Remaining
uncertainty: hardware acceptance of 3.00-family DXE FV on 5.00 base (accepted
ambiguity), logo rendering, actual 8c/VCN behavior (not expected this run).

## P0 observation #1 (operator report, 2026-09-17)
Operator: green LED blinked (once), NO LAN indicators, NO video output —
first occurrence of this signature. Root verified: ping 127.0.0.1
(the known board IP) = 100% loss. Signature differs from both known
classes (T1: rhythmic green + LAN up; M6/M5: static red true-silence).
Interpretation (inference only): progress beyond M6's halt point, then
early death; consistent with clv-base or 3.00-FV-graft on 5.00-base
incompatibility. Single-boot observation; power-cycle retry not yet done.
