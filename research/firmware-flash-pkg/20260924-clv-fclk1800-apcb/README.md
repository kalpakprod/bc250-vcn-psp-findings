# Flash Package: 20260924-clv-fclk1800-apcb

## Artifacts
- `BC250_5.00_clv_FCLK1800_APCB_v001.bin`: 16,777,216 bytes, SHA-256 `3d6348c65a0c2ee500e13f3b1a5c9e9c64c57e36b570fbd1e85a19b9713871f8`
- `SHA256SUMS`: verification hashes

## Description

FCLK 1800 candidate on the clean clv 5.00 base
(`evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, sha256
`ea578104…`). The change vs the base is EXACTLY 3 bytes:
`0xAB1B9A/B` u16 `0x058C` -> `0x0708` (1420 -> 1800, the APCB FCLK
override record the ABL1 token reader consumes) and `0xAB1010`
APCB checksum `0xC0` -> `0x42`. Gate byte `0xAB1B99` = `0x01` untouched.
No NVRAM, AmdSetup, PSP entry table, $PS1, or BIOS-region changes.

Emulator validation (2026-09-24): the actual candidate bytes drive the
native ABL1 builder to FCLK service argument 1800 (control 1420,
gate-off 1200) —
`evidence/firmware-audit/20260923-abl95fc-next/emulate_pll_apcb_v001.py`,
result JSON in the same directory.

## Role in the validation sequence

ONE-VARIABLE image (FCLK only), on the clv 5.00 lineage — a DIFFERENT
BIOS base than the v003b VCN image. The two images are flashed
separately, v003b first. Flashing this one REPLACES the whole firmware
with clv 5.00 (no VCN driver, no 8-core change). The final combined
image is built only after both variables are proven on hardware.

## Runbook

Complete programmer procedure and safety gates:
`docs/guides/bc250-clv-fclk1800-programmer-flash-runbook.md`

## Evidence

- Build log: `docs/action-logs/2026-09-24-fclk1800-apcb.md`
- Builder: `scripts/build_clv_fclk1800_apcb.py`
- Mechanism: `docs/research/2026-09-23-abl-pll-service-boundary.md`,
  `.procoder/plans/clv500-overclock-result.md` (A3 checkpoints)
