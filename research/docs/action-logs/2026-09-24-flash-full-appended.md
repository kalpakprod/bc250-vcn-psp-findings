# 2026-09-24 — FLASH FULL-appended on BC250-01

## FLASH INTENT (operator-approved, BEFORE any write)

- Operator approval: «прошивай» (2026-09-24) following the exact-image
  proposal: `BC250_vcn-driver-FULL_lzma-FIXED_appended-at-end.bin` on BC250-01.
- Image: `firmware-flash-pkg/20260924-vcn-driver-FULL_lzma-FIXED_appended-at-end/BC250_vcn-driver-FULL_lzma-FIXED_appended-at-end.bin`
  SHA-256: `9d2493975b870810fd31481cf3ded36cc964aa201181ad0ea4949f3cf5afad17`
  (alias v007-active; package `SHA256SUMS` re-verified OK 2026-09-24).
- What it is: the board's own booted BIOS + the FULL route-B VCN driver
  APPENDED at the FV end; all 193 base files at identical offsets; explicit
  LZMA; preflight 10/10 GO.
- Why: STUB early-slot BOOTS (verdict 2026-09-24) → insertion surgery
  innocent, driver code guilty. Dispatch position is the next variable.
- Target: BC250-01, Winbond W25Q128.V via CH347 (`flashrom ch347_spi`,
  1.875M), board fully unpowered + clip by the operator.
- Procedure: chip identity → DOUBLE read a/b (`pre-full-appended-read-*`,
  cmp must match) → drift check vs pre-STUB chip → package sha → write
  (erase+write+verify) → INDEPENDENT readback + cmp + sha → result here.
- Rollback (primary): fresh pre-write dump. Secondary: STUB pre-reads
  (`evidence/programmer/reads/20260924-v006r/`), stock recovery.
- STOP: any mismatch at any step (identity, double-read cmp, package sha,
  write verify, readback cmp).
- Post-flash: operator restores the bench circuit (clip off, programmer USB
  out, battery in, 12V confirmed) → cold boot → signs (blinks/video/LAN/SSH)
  → verdict here.

## FLASH RESULT (AFTER)

- Chip identity: Winbond W25Q128.V, 16 MiB on ch347_spi @1.875M. (First probe
  found nothing — operator reseated the clip / cut power, second probe OK.)
- Double read: `pre-full-appended-read-a/b.bin` CMP-MATCH, sha256
  `aa5727d40daae52259a98b7935ed057d5c68c668963e4d74b7f8852088eec671` —
  primary rollback. Drift vs STUB readback: 176 B in 0xdb3–0x3d53 (NVRAM
  store after the STUB boot), zero bytes above 0x100000. Chip was STUB +
  normal live NVRAM drift.
- Package sha: OK. WRITE erase 0..0xFFFFFF + verify: VERIFIED, rc=0.
- INDEPENDENT readback `post-full-appended-readback.bin` sha256
  `9d2493975b870810fd31481cf3ded36cc964aa201181ad0ea4949f3cf5afad17`,
  cmp vs candidate = FLASH VERIFIED EXACT.
- Dumps: `evidence/programmer/reads/20260924-full-appended/` (pre a/b + post).
- Chip now = FULL-appended. NEXT: operator restores bench circuit (clip off,
  programmer USB out, battery in, 12V confirmed) → cold boot → signs
  (blinks/video/LAN/SSH) → verdict here.

## COLD-BOOT VERDICT (2026-09-24, operator-observed)

- Signs: ONE blink, then nothing. No LAN, no video. = pre-dispatch signature
  (same class as the v004 LZMA hang, NOT the 2-blink DXE wedge of FIXED-early).
- Static evidence (repo parser, `fv_evidence.py`): FULL-appended FV walks
  clean — 194 files, FV + all FFS checksums OK, our file last at 0x43c018
  (8-aligned, size 0x3022), pad all-0xFF, stock bytes untouched below it.
  LZMA explicit (preflight G10). The builder produced a valid volume; the
  board rejects something our parser accepts — or the hang is dynamic.
- Two surviving hypotheses: H1 the board rejects the append structure (our
  file last — the only structural novelty vs loading volumes); H19 the FULL
  code hard-wedges only against initialized SMU (late position; precedent:
  D10R early touch boots). STUB-appended (`0133a34b…`, same surgery, inert
  code) discriminates perfectly: 1 blink → H1, boots → H19.
- Registry: FULL-appended `FLASHED-HUNG`. NEXT: flash STUB-appended (needs
  exact operator approval).
