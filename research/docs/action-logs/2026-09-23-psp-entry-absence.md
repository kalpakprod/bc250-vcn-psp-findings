# $PSP entry-absence candidate (lane D) — 2026-09-23

## Intent (before any write)

Operator ordered the attack track ("патчинг, обход, взлом — всё это нужно"), no soldering,
offline-only until a separate hardware approval. Lane D from the plan: what does PSP do
when the two VCN-lock carriers (0x24 SEC_GASKET, 0x45 TOS_SECURITY_POLICY) are REMOVED
from the $PSP directory entirely. Never tested; D3/D3-B2 tested modified/stale-signed
carriers, not absence.

Build target (new files only, source untouched):

- `candidates/BC250_5.00_clv_PSP-entry-absence_0x24-0x45_v001.bin`
- base: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
  sha256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- builder: `scripts/build_psp_entry_absence_candidate.py`
- report: `evidence/firmware-audit/20260923-psp-entry-absence/build-report.json`

No flash. Flash requires the operator's exact approval with this hash.

## Result

- Gate PASS: entries 7 (0x24) and 15 (0x45) replaced with the image's own empty-entry
  convention (16x 0xFF); fletcher32 `0x17AA38B9` -> `0x2CC838E9` over
  `0x8E0008..0x8E0140`; 33 changed bytes, all confined to the directory table + checksum
  word; 17 live entries remain; lock types absent from the directory.
- Independent verifier `psp_ps1_verify.py` on the candidate: remaining referenced
  containers verify, 0 failed (the removed carriers are unreferenced; their bytes stay
  in place, untouched).
- Structural audit `firmware_audit.py`: stored fletcher32 == calculated `0x2CC838E9`,
  `checksum_match: true`, 19 directory entries (17 live + 2 empty), 4 FVs.
- Candidate sha256 `02d6e33f3c8a99db27a003b1da8d093163ad4583181e958a5cda214c19e3127c`.
- Claim boundary: static only. What PSP does at boot with absent carriers
  (boot unlocked / boot parked / boot with VCN locked by defaults) is UNRUN.
  The decisive discriminator is one controlled programmer flash + cold boot,
  which needs the operator's exact approval for this hash.
