# 2026-09-23: staged v003 driver identity verified (GUARD); pre-bake ban corrected

Intent: the operator rejected a board-restore proposal he never asked for
(«просил ли я тебя восстанавливать? Какая задача стоит?»). Before answering:
verify which driver the staged v003 package actually carries (guard vs
autonomous), because that decides whether the queue's first flash can double
as the board revive and whether it is safe before the Probe2/bake step.

Verification (read-only; no image, hardware, or candidate file touched):

- Staged ROM re-hashed on disk: `firmware-flash-pkg/20260923-v003-community-vcn/BC250_3.00_MeiMeiDXEv3_vcn_v003.bin`
  = `0fafe2c12bbdecf15cf7e06f474d4f3518d447205a4fbf351bfa097f309f0a36`
  (matches SHA256SUMS and the build report).
- Direct extraction via the injector's own walker
  (`scripts/build_vcn_v002_candidate.py`: decompress_inner + walk_inner_fv):
  inner FV len 0x436000, 194 files; injected FFS at off 0x432000, size
  0x301c, state byte 0xF8, whole-file sha256
  `0a4c997bc352e45c90f6f87b7b17c91892f073f969d5908f7aea1beb2990a20a`.
- Identity: in-image FFS == prep_blob of the preserved guard ffs
  (`bin/Bc250VcnUnlockDxe.ffs.draft-o6`, raw sha256
  `8066400b664b1c0a8dc7eb933a68dcd5761fdd1a2455b5958448fc2e375086cb`, the
  guard build per docs/action-logs/2026-09-23-vcn-driver-v001.md);
  in-image != prep_blob of the current post-edit ffs (raw
  `b9b6f8d381233b8fe5830235a7f2f616095ca96209041510efdbc5c3a4a0e978`,
  normalized `da2f70ccc9de2df5fe530a61197b0f3154ba853b9711e68fe31c7ef76caa9fbe`,
  the autonomous build that went only into withdrawn v004).
- Conclusion: staged v003 carries the GUARD driver (O6 abort on the empty
  clock plan, emulation-validated), NOT the autonomous one. A pre-bake flash
  is boot-safe (the driver aborts before the hang-risk send; the board
  behaves as the bare community base) but does NOT unlock; the unlock rung
  remains Probe2 -> bake -> rebuild -> re-inject (v003b).

Repo writes (this log is the record):

- `.procoder/plans/psp-breach.md` (Re-ranking section): the pre-bake ban
  replaced by the driver-identity verification; the revive folded into the
  queue's first flash; revive-image choice stays the operator's.
- `MISTAKES.md`: new top entry — restore proposal with images outside the
  confirmed queue; prevention rule (every flash proposal names a queue image
  by name + sha256; a rung's pre-step is presented as part of the rung, not
  as a new task).

Gates: `pytest tests/` 83 passed (`~/.local/bin/pytest`, 9.6 s);
`make test` 7/7 OK. Full `procoder check` not re-run this round: its four
blocking findings are pre-existing (old conversation-log secret, PR template),
none in the files this round touched.

Nothing flashed. No image, evidence, or candidate artifact modified.
