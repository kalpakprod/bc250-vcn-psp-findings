# BC-250 board voltage sources — independent recheck and minimal verifier correction

Date: 2026-09-20 (Asia/Almaty). Evidence class: `static-analysis` over `observed-bytes`.
No ROM, NVRAM, register, candidate, board or network action occurred; all inputs read-only.

## Conclusion

The inventory result of `docs/research/2026-09-20-bc250-board-voltage-sources.md` reproduces
independently from a relocated copy of the same pinned corpus: of 233 CLV 5.00 modules, only
`ISL69247-3e1f753a6279` and `ISL95712-c0cc17d2d54f` implement the full EC-window VR mailbox
writer transport (config port `0x2E`, data window `0xA20`, staging registers `0x65`/`0x66`/`0x70`/
`0x63`/`0x60`, status poll `test al,0x40`); 28 further modules touch the shared Super-I/O/EC window
without a VR mailbox transaction.

The verification path itself had a defect: the intermediate verifier revision
`a1551700443086d1c097ae44d516eb152c88c9174b277ba0825c982d77b0e5b4` failed 57 of 604 checks. The
defect is a per-site offset-re-read convention error, not a detector error. A one-helper correction
restores the same 604 checks to `PASS 604/0`, and the upstream final revision
`3a207facf42178b101c56650a913c2a48761b51778e11668fdaa5ff27e6d83fa` independently reaches the same
`PASS 604/0` on the same 200 offset sites.

## Reproduction

    cd evidence/firmware-audit/20260920-bc250-board-voltage-sources-recheck
    python3 scan_vr_mailbox_writers.py  > captures/scanner.stdout    # exit 0, PASS 31/31
    python3 verify_board_voltage_sources.py.orig  # (baseline bytes) exit 1, FAIL 604/57
    python3 verify_board_voltage_sources.py       # (corrected)      exit 0, PASS 604/0
    ./ROLLBACK.sh <copy>/verify_board_voltage_sources.py            # restores a1551700…, FAIL 604/57

Immutable inputs: donor ROM `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
(16 777 216 B, sha256 `ea5781…4cb8`) and corpus
`evidence/firmware-audit/20260919-inv-token-consumers/` (`census.json` sha256 `506b8e…0d39`,
233 modules). The scanner result JSON is byte-identical to the one produced in the sibling task
directory (sha256 `852ffd0d…8381`), so the detector is deterministic across directories.

## Defect

The scanner reports the offset of the _matched pattern bytes_, not of the enclosing instruction.
Anchors such as `imm_ec_window_a20 = 200a0000` and `test_al_40 = a840` are operand fragments, so
their offset is mid-instruction. The verifier keyed its asm re-read by instruction start and
therefore missed them.

Measured instance: `ISL69247-3e1f753a6279` reports `imm_ec_window_a20` at `0x3ac`; module image
byte at `0x3ac` is `0x20`, the pattern spans `0x3ac..0x3af`, and the enclosing instruction begins
at `0x3ab` (`b9 20 0a 00 00` = `mov ecx,0xa20`), which is asm address `0x543`. The baseline looked
at `0x544` and failed. Failure classes: 53 anchor-offset re-reads (23 `imm_ec_window_a20`,
7 `mov_dx_2e`, 6 `push_cfg_index_2e`, 4 `push_cfg_data_2f`, 4 `test_al_40`, 3 `out_imm_2e`,
2 `push_mbox_66`, 1 each `in_imm_2e`, `mov_al_87`, `mov_dx_2f`, `push_mbox_70`) plus 4 owned
EC-window immediates. A second class lies in decode gaps: at `DxeCore-2f1d8056b0da@0x13f85`
the image holds `6a 2f` while the pinned objdump text lists no covering instruction (nearest
listed start `0x13f7f`, one `0x00` byte).

Set-level checks of the same failing run already passed: asm-derived writer set, 14/14 anchor
census counts, unique whole-ROM occurrence of both writer images, helper entries and call sites.

## Correction

`changes.patch` adds one module-level helper `site_bytes()` and routes the two offset re-read sites
(anchor offsets, owned EC-window immediate) through it. The helper reads the pattern at its own
offset inside the instruction that covers the address; when no listed instruction covers the whole
pattern it falls back to the immutable module image and the verdict records the readback source in
`per_site_readback_sources`. No detector, anchor set, writer set or input changed.

Observed: `PASS 604/0`, `anchor_offset_entries_verified 200`,
`per_site_readback_sources {"asm": 185, "image": 19}` (204 entries = 200 anchor offsets + 4 owned
immediates). Of the 200 anchor offsets, 181 read from the covering instruction, 19 from the module
image (2 patterns crossing an instruction boundary, 17 in decode gaps).

The upstream final revision classifies the same 200 sites as
`{"aligned": 181, "cross-instruction": 2, "decode-gap": 0, "outside-code-section": 17}`. The two
independent fixes agree on 181 aligned sites and disagree only on the label boundary for 2
cross-instruction sites; no site disagrees on the bytes.

## Uncertainty and unrun checks

- `static-analysis` only: no hardware readback, no register access, no board contact.
- For the 17 decode-gap sites the pattern is re-read from the same module image the scanner used;
  that path is weaker than the asm text and is labelled per site in the verdict.
- Both verifier revisions classify sites by the pinned objdump text; whether those anchors sit in
  code or in data at run time is not resolved by either.
- No independent review by a different model family was performed for this recheck.
- The sibling task directory was written concurrently by another actor during this recheck; every
  claim here is pinned to the hashes recorded in `VERIFICATION.txt` and `SHA256SUMS.final`.

## Artifacts

- `evidence/firmware-audit/20260920-bc250-board-voltage-sources-recheck/` —
  `scan_vr_mailbox_writers.py` (sha256 `63ae081c…`), `verify_board_voltage_sources.py.orig`
  (baseline `a1551700…`), `verify_board_voltage_sources.py` (corrected `2dfe26ff…`),
  `changes.patch`, `VERIFICATION.txt`, `SHA256SUMS.final`, `ROLLBACK.sh`, `captures/`, `objdump/`.
- Sibling package (not modified by this recheck):
  `evidence/firmware-audit/20260920-bc250-board-voltage-sources/` and
  `docs/research/2026-09-20-bc250-board-voltage-sources.md`.
