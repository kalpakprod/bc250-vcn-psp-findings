# 2026-09-24 — Software bypass-track closure session

Operator directive: execute every not-yet-done bypass that is software-only
(no hardware intervention, no soldering, no voltage glitch), close every track.

Scope: PSP/KDB key attack, UCLK PSP-breach patch, type-9 tail / root-swap,
gasket consumer hunt, ZD-1 SMU forged-record delivery, v2000a/spoof remainder.
No firmware image flashed this session. All changes are repo files only.

## Per-track verdicts

| Track                                | Verdict                                                                      | Key evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ------------------------------------ | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R2 KDB RSA audit (deep)              | CLOSED, negative: keys healthy                                               | `evidence/firmware-audit/20260924-kdb-deep-audit/result.json` — 13 images, 15 unique moduli, trial/Fermat/Wiener/ROCA/rho/batch-GCD/cross-image all negative; `scripts/kdb_rsa_deep_audit.py`                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| R4 UCLK PSP-breach                   | BUILT + EMULATOR-PROVEN, glitch-gated (same class as VCN glitch image)       | patch ABL1+0x5F32 `0x54→0x04` (LSR.W→LSL.W#0 ≡ MOV): UCLK service arg = input (1800→1800, 1750→1750); `evidence/firmware-audit/20260923-abl95fc-next/emulate_pll_apcb_uclkpatch.py` + result JSON; candidate `candidates/BC250_5.00_clv_UCLK_MOV_GlitchSigned_v001.bin` sha256 b5fff267472bd8ae80d1a87a82f760cd388740305feb46847be04cd57854e799, `psp_ps1_verify.py` 14/14 PASS (re-signed $PS1 under kid d9cc642a, container relocated 0x99FD00→0x9E0000, $KDB t50 slot 0, $PSP repoint+Fletcher32); `evidence/firmware-audit/20260924-uclk-lsr/build-report.json`                                                                               |
| Type-9 tail / ROOTKEY swap           | CLOSED: not software-forgeable                                               | 64-byte tail @0x93F400 is per-build protected material (differs clv 5.00 vs shared 3.00/2.00/FD tail), high-entropy, not sha256(blob) prefix; root-swap artifacts `evidence/firmware-audit/20260923-psp-root-swap/*` remain static-only                                                                                                                                                                                                                                                                                                                                                                                                           |
| Gasket consumer hunt (absence route) | CLOSED, indeterminate                                                        | DF window/mailbox/VCN-bank literals exist only inside the 0x24/0x45 carrier bodies; the applier is a generic ROM loop with no literals in readable TOS/SMU bodies; type-1 blob encrypted (no strings/$PSP refs) — directory consumer not solvable statically                                                                                                                                                                                                                                                                                                                                                                                      |
| R3 ZD-1 SMU forged record            | Transport + plan READY for robin-5; live-board run BLOCKED (version + wedge) | plan `evidence/firmware-audit/20260923-smu-forged-record-plan/plan-result.json` (robin-5 = 58.7.1 = the clv 5.00 type-08 body); tool `scripts/probe4l8_ring_forgery.py` deployed to board, version-gated (refuses non-58.7.1). Live board: SMU 0x00580600 (58.6.0, 3.00-lineage) — geometry differs (robin-1 literal scan: ring literal 0xDAC @0x181B0 confirmed, Q0-table-slot literal = 0x13E88 @0x1818C, NOT base+0x580 → needs its own decompile, no slot analogy). Board SMU queue-3 wedged by a code-address read via Q3 0x2A (read trap) — cold cycle required before any mailbox work; no ring appends were ever sent (gate + abort held) |
| v2000a / spoof remainder             | CLOSED (prior evidence, re-cited)                                            | `docs/research/2026-09-17-c3-v2000a-8c-rung.md` (driver path needs SMU-side PowerUpVcn = NULL on BC250); `docs/research/2026-09-23-v2000a-apcb-vcn-tokens.md` §5 (APCB-only cannot enable VCN; gasket config rides signed carriers)                                                                                                                                                                                                                                                                                                                                                                                                               |
| R1 PSP/$PS1 signatures               | CLOSED (prior)                                                               | `docs/research/2026-09-19-psp-signature-scheme-solved.md`: RSA-PSS over header‖body, KID@+0x38; anchor 39bfc192 is a platform constant in silicon ROM (cross-image test) — KDB-edit-only bypass impossible; re-sign works only under a ROM-accepted key (glitch class)                                                                                                                                                                                                                                                                                                                                                                            |
| R5 glitch track                      | EXCLUDED by operator (hardware)                                              | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |

## Board state (needs operator action)

SMU queue 3 wedged at 2026-09-24 by a read-only geometry probe (Q3 0x2A on a
code address 0x1000 — the read service traps there). Q0/Q2 responded before;
nothing was written to SRAM, no ring append was ever sent. A cold power cycle
restores the mailbox. Until then: no further mailbox probes.

## New files

- `scripts/kdb_rsa_deep_audit.py` + `evidence/firmware-audit/20260924-kdb-deep-audit/result.json`
- `evidence/firmware-audit/20260923-abl95fc-next/emulate_pll_apcb_uclkpatch.py` (+ result JSON)
- `scripts/build_clv_uclk_lsr_candidate.py`
- `candidates/BC250_5.00_clv_UCLK_MOV_GlitchSigned_v001.bin` (sha above)
- `evidence/firmware-audit/20260924-uclk-lsr/build-report.json`
- `scripts/probe4l8_ring_forgery.py` (deployed to board as `/home/OWNER/vcn_unlock/probe4l8_ring_forgery.py`)

## Candidate inventory after this session

| Image                                         | Base     | sha256                                                                | Gate                                                   |
| --------------------------------------------- | -------- | --------------------------------------------------------------------- | ------------------------------------------------------ |
| BC250_3.00_v003b_RouteB_VCN_v001.bin          | FD 3.00  | 3a7fcf85… (package: `firmware-flash-pkg/20260924-v003b-route-b-vcn/`) | flash approval (operator)                              |
| BC250_5.00_clv_FCLK1800_APCB_v001.bin         | clv 5.00 | 3d6348c6… (package: `firmware-flash-pkg/20260924-clv-fclk1800-apcb/`) | flash after v003b decision                             |
| BC250_5.00_clv_UCLK_MOV_GlitchSigned_v001.bin | clv 5.00 | b5fff267…                                                             | glitch key-acceptance (hardware) — not flashable as-is |

## Outstanding operator decisions

1. Cold power cycle the board (restores SMU mailbox).
2. Flash approval for v003b (exact name+sha above), then the FCLK image.
3. D1: SoC voltage decision for the OC case.
4. ZD-1 runtime probe: run after the clv-base flash (robin-5 live, plan valid
   as-is), or commission the robin-1 (58.6.0) decompile if staying on a
   3.00-family base.
