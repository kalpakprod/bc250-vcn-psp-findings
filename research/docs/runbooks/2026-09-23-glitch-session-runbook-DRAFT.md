# Glitch session runbook — patched BIOS + spoof + EMFI (DRAFT)

Date: 2026-09-23. Operator strategy this implements: "патченный BIOS с глитчем, со
спуфом, и только тогда можно писать в систему" (the lock is boot-time; runtime-only is
closed by field experience). DRAFT until the operator approves the physical session.

## The package (all offline-verified, nothing flashed yet)

| item        | value                                                                                                                                                                                                             |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| image       | `candidates/BC250_5.00_clv_VcnUnlock_GlitchSigned_v001.bin`                                                                                                                                                       |
| sha256      | `91de01eb7cb8e97014294adc8692eb8be66c3f95ce8481c234805544c0ddd517`                                                                                                                                                |
| base        | stock 5.00 CLV `ea578104…` (14,009 B changed, `0x8E0004..0x9E4707`)                                                                                                                                               |
| spoof       | KDB t50 slot0 key entry replaced: AMD `39bfc192…` -> OURS `b36ad5af…` (RSA-2048, e 65537)                                                                                                                         |
| unlock      | type `0x24` SEC_GASKET + type `0x45` TOS_SECURITY_POLICY rebuilt with donor values (`0x3E810<-6`, `0x3A2011C<-0x107FF`, `0x3A20124<-0x10FFF`, `0x3E814<-0x2544C382`) + 56-record VCN bank appended to TOS `0x280` |
| signing     | RSA-PSS / MGF1-SHA256 / salt 32 over `header(0x100)\|\|body`, kid at `header+0x38` — verified by `psp_ps1_verify.py` (2026-09-19)                                                                                 |
| staged copy | `firmware-flash-pkg/20260923-glitchsigned-vcn/` + SHA256SUMS                                                                                                                                                      |

The ONLY gate this image cannot pass by itself: the on-die PSP ROM hash check over the
KDB/root key (anchor is in ROM, not in SPI). The EMFI step exists to pass exactly that
one check ("our key entry accepted"). Everything after it is legitimately signed — by us.

## Prerequisites (hard, per project rules)

1. Board restored to a booting state (current state: silent on `af531026`; programmer
   recovery proven, stock rollback `83c4e420` preserved).
2. Observation channel before first shot: J5 UART/POST pad located and wired
   (standopen question that flips ranking); fallback: port-80 POST card + LAN presence.
3. Fresh full readback dump before any write; cold-boot + readback check after.
4. EMFI go from the operator (coil, no soldering — allowed by the standing rule only
   with separate approval; this runbook is the approval target).

## EMFI step (no soldering)

Reference: amd-sp-glitch (CCS'21, in `import/…/amd-sp-glitch/`) — their ROM-key-check
glitch is our exact target class (Zen 2 family confirmed in the paper). Adapted to
no-solder: EMFI coil over the PSP die, no board taps.

1. Trigger alignment: reset deassert -> PSP ROM reads KDB/root from SPI
   (`0x93F000` root blob / `0x9CB200` KDB). Use the reset button as trigger; the
   check happens in the first milliseconds of PSP boot.
2. Parameter sweep (from their `ParameterDetermination.md` procedure): delay and
   pulse duration in a grid; expect a 2D sweep of a few hundred shots.
3. Kill criterion (from the breach plan): ~200 shots across the delay/duration window
   without a state change -> stop, re-target (the check may sit inside a tight window
   that needs the UART to localize).
4. Success criterion: board proceeds past PSP with OUR key accepted — visible as:
   normal boot of a "tampered" image (stock PSP would park it), then VCN alive in OS.

## Outcome matrix

| observation                               | reading                                                | next                        |
| ----------------------------------------- | ------------------------------------------------------ | --------------------------- |
| boots, VCN works (`vainfo` encode+decode) | root check glitched through; spoof accepted            | F2 reached; package for F5  |
| boots, VCN still gated                    | root accepted but second gate (thelamer T2) holds      | V5/T2 gate-clearing session |
| parks exactly like stock                  | glitch missed / wrong window                           | widen sweep, add UART first |
| no signs of life                          | flash/verify problem first (readback!), THEN re-glitch | programmer recovery         |

## Session order (one sitting)

1. Restore board (programmer, stock `83c4e420`), verify boot + readback hash.
2. Locate UART/POST pad; capture stock boot log (baseline).
3. Flash `91de01eb…` (programmer, not in-system flasher), readback-verify hash.
4. Cold boot WITHOUT glitch: expect park (this is the clean negative baseline).
5. Engage EMFI sweep per above; log every shot (delay, duration, result) to
   `evidence/firmware-audit/<date>-emfi-session/`.
6. On success: OS bring-up per T2 debug setup (blacklist amdgpu, SSH, `dmesg -wH`,
   patched amdgpu, `vainfo`).

## Status

DRAFT — blocked on: board restore + operator EMFI go + UART pad location. The offline
preparation is complete except the UART pad (open question in the breach plan).
