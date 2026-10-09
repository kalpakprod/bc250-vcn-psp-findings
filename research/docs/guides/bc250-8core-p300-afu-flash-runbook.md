# 8-core unlock in BIOS — programmer flash runbook (BC250-01, P3.00 lineage)

Status: STAGED, NOT flashed. Operator performs every step physically.
Package: `firmware-flash-pkg/20260922-8core-p300-afu/` (`SHA256SUMS`).
Method: **hardware programmer (CH347 + flashrom)** — the only flash method
this project has ever used successfully (11+ verified writes, zero bricks).
AFU/USB is the community-standard alternative and is NOT the primary path
here; see §5 for why.

## Package identity (verified this session)

| File | SHA-256 | Note |
|---|---|---|
| `8_cores_steam.rom` | `c99cbca1…50449` | 16,777,216 B; NVRAM + DXE-region mod on P3.00 lineage |
| `AfuEfix64.efi` | `a21bab5c…120d9a` | AMI AFU EFI 5.16.01.0109 (kept as alternative only) |
| `BOOTX64.efi` | `8204279f…010ee` | EDK2 UEFI Shell (kept as alternative only) |
| `startup.nsh` | `e2c42a21…0f6a4` | 30 B, no auto-flash |

Provenance: public Drive folder from video ARFOKLBi_Tc description,
retrieved 2026-09-22. No author-published hash; single-source file
(unlike multi-source `BC250_3.00_CHIPSETMENU.ROM` `48fbe5d3…`).

## Why this ROM is lower-risk than the project's failed rungs (own bytes)

Checked directly against RetroWeb stock P3.00 (`07595ca3…`, community-hash
MATCH) and the board's own stock `read-a.bin` (`83c4e420…`):

- PSP zone `0x8E0000–0xAB0000`: byte-identical to BOTH. The #1 historical
  killer (foreign-PSP silent halt, M0–M6) does not apply.
- APCB `0xAB1000+0xB70`: identical. No APCB risk.
- Boot block (last 512 KB): identical. Crisis recovery stays intact.
- Diffs: 64 KB blocks 0–1 (NVRAM) + 174–194 (`0xAE0000–0xC2FFFF`, DXE FV).
  Same shape as the community 3.00-lineage pattern (NVRAM + varstore/DXE).
- Unlock module `Bc250CoreUnlockDxe` (`7d22d802…`, repo-analyzed: SMN
  read + SMU msg 0x98 + warm reset) present in DXE FV (FV-level audit).
- Residual risks: single-source file; DXE-region mods on this board have a
  mixed record (E1 inconclusive due to display miswiring, af531026 failed
  but was a cross-drop graft — different class); community boot proof is
  participant video evidence only.

## Preconditions (all mandatory, project programmer discipline)

1. Board = `BC250-01`; re-confirm current DMI in Setup before touching the
   programmer (expect P3.00; anything else → STOP and re-plan).
2. 8-pin PCIe power polarity verified; board FULLY unpowered (PSU out),
   CMOS battery REMOVED, capacitors discharged.
3. Programmer CH347 (native 3.3 V). NEVER a black-PCB CH341A (5 V trap).
4. Chip identification FIRST: `flashrom -p ch347_spi:spispeed=1.875M
   --flash-name` must report Winbond `W25Q128.V` 16 MiB on `BIOS_A1`.
   `MX25L4005` 512 KB = WRONG CHIP (`SIO1_R`) → STOP, move clip/header.
5. Display path: direct DisplayPort for all observations (HDMI adapters
   caused the 09-11 false no-video series). P0 oracle: LED green-blink =
   booted; red-static = halt; no LAN + no video + constant fans = silence.
6. Pinned flashrom identity recorded (`flashrom --version` + binary hash;
   project pin: v1.8.0, bin `5ee0b2e4…` — re-verify on the flash host).

## Procedure

1. Fresh pre-write capture ×2 to NEW files
   (`evidence/programmer/reads/20260922/pre-8core-read-a.bin`, `-b.bin`):
   `flashrom -p ch347_spi:spispeed=1.875M -r <file>` twice. Require
   byte-identical (`cmp` exit 0) + record both SHA-256. This capture is
   the primary recovery image. STOP on any mismatch.
2. Re-verify candidate hash `c99cbca1…50449` fresh from disk. Abort on
   mismatch.
3. Exact operator approval (contract form, all brackets filled from the
   fresh capture):
   `Подтверждаю запись файла firmware-flash-pkg/20260922-8core-p300-afu/8_cores_steam.rom SHA-256: c99cbca14a2e24224c0b152f18918c7f0e78edd7d94674df79a1ac904f550449 на плату BC250-01, чип W25Q128.V (ID-подтверждён). Pre-write дамп: [путь], SHA-256 [хеш], 16 MiB, два чтения совпали. Recovery: [путь pre-write копии + stock 83c4e420], route: programmer re-write + readback.`
4. Write: `flashrom -p ch347_spi:spispeed=1.875M -w
   firmware-flash-pkg/20260922-8core-p300-afu/8_cores_steam.rom`.
   Require exit 0 + `VERIFIED`. Preserve the full log.
5. Independent full-chip readback to a NEW file; require SHA-256 ==
   `c99cbca1…50449` (`cmp` exit 0). STOP and do NOT boot on mismatch.
6. Remove programmer, reinstall battery, clear CMOS (60 s battery-out per
   community doc or 20 s jumper; verify by wrong clock in Setup).
7. Cold boot, observe P0 (LED/LAN/video/fans + 5-min wait + ping/SSH).
   Enter Setup → CPU Configuration → `Unlock CPU Cores = Enabled`;
   re-apply recorded fan curve + VRAM 512 MB; save, boot OS.
8. Verify: `nproc` = 16; remote session re-reads NVRAM mask + clocks.

## Stop / rollback

- STOP on: chip-ID mismatch, capture mismatch, candidate-hash mismatch,
  write not VERIFIED, readback mismatch, no POST/display, red-static LED,
  missing unlock menu after CMOS reset.
- Rollback path A: programmer re-write of the step-1 pre-write capture +
  readback verify (separate exact approval).
- Rollback path B: programmer re-write of stock `83c4e420…` (separate
  exact approval).
- 8→6 cores without reflash: `Unlock CPU Cores = Disabled` + full power
  off + CMOS reset (per author).

## Why not AFU-first (correction record)

An earlier revision of this runbook proposed AFU/USB as primary. That was
wrong for this project: all 11+ project writes used the programmer with
the capture/verify/readback discipline above; AFU was never used here, has
no pre-write ×2 capture, unknown Secure Flash/ROMID behavior on this
board, and any AFU failure ends at the programmer anyway. AFU remains a
valid community-standard alternative (files kept in package) but only with
its own backup-first procedure and the same CMOS/P0/rollback discipline.
G7: method must follow project evidence, not video convenience.

## Honest boundary

- P3.00-based mod, NOT 5.00/CLV: delivers the BIOS core toggle, not the
  CLV OC menu surface.
- Community beta, single-source bytes; boot proof is participant video.
  No voltage change is part of this runbook.
