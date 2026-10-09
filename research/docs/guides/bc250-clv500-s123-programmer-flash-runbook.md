# Unified 5.00-CLV (S1+S2+S3) — programmer flash runbook

Status: STAGED, NOT flashed. Operator performs every step physically.
Package: `firmware-flash-pkg/20260922-clv500-s123/` (`SHA256SUMS`).
Method: **hardware programmer (CH347 + flashrom) ONLY**. No AFU, no
in-OS flash, no NVRAM direct edit is authorized by this runbook.

Build evidence: `docs/action-logs/2026-09-22-goal-s1.md`,
`2026-09-22-goal-s3.md`, `2026-09-22-goal-s4.md`, S2 records in
`candidates/s2-ocv/` (verdicts + provenance + structural report);
verdicts + structural report in `candidates/s3-drivers/`;
tests `tests/test_s3_drivers.py` (20/20) + `tests/test_clv_oc_builder.py`
(23/23), all re-run green by root 2026-09-22.

## 1. Package identity (verified this session)

| File | SHA-256 | Note |
|---|---|---|
| `BC250_5.00_clv_S3-DRV_v001.bin` | `26c0634da2fbda7125ebf284241917af58b6c30149d18cca434e55a6ded873ab` | 16,777,216 B; S1 NVRAM defaults + S2 empty voltage template + 6 DXE drivers + 57-byte Setup unhide |

Ladder (one variable per rung, all on CLV base `ea578104…`):

- S1 (`c5dc6424…`): H1330 1:1:1 request defaults — `0x7E5=0x1A`
  (`+0x316` MCLK 1330), `0xBD3=0x32` (`+0x704` DF value low byte;
  `0x7FF`/`0xBD2`/`0xBD4` already at target in donor, `0x83C`
  arbitrated `0xFF`). Request-only: no applied-clock claim.
- S2 (image == S1, `c5dc6424…`): voltage template NO-CHANGE +
  STAYS-0. No voltage byte is set; VDDCR_VDD stays request-only.
- S3 (`26c0634d…`): +6 MeiMeiDXEv3 DXE drivers (FFS 187→193,
  donor-exact blobs) + 57-byte Setup-IFR unhide transplant
  (byte-exact community edit, link target verified in S2's own
  CbsSetupDxe). Static-only: no dispatch/menu/clock/volt claim.

## 2. Why this ROM is contained (own bytes, root re-verified)

- PSP/BHD/APCB subtrees: identical S3 vs S2 (`firmware_audit.py`
  exit 0, re-run by root; E gate 24/24 ranges identical).
- Changed range vs S2: `0xae0088–0xc28e5f`, all inside
  `[0xAE0000,0xE00000)`; outside byte-identical (root `cmp` walk,
  ndiff=1341763).
- Boot block (last 512 KB) and `0xE00000+`: identical to CLV donor
  (root re-checked). Crisis recovery stays intact.
- Inner FV: `0x41C000`→`0x437000`, header checksum valid; all 193
  FFS header checksums valid; 186 pre-existing files untouched,
  6 added blobs donor-exact; 899407D7 same-size + 57/57 bytes.
- Independent rebuild (S3-D) byte-identical to S3-C (root `cmp`
  silent). Two builders, one hash.
- Residual risks: unhide is a static transplant (Setup may still
  hide the menu at runtime); DXE dispatch order/DEPEX is static
  reasoning (one intra-set GUID); 8-core + clocks + volts are
  UNPROVEN until the hardware acceptance below. No second-family
  independent review exists (marked INCOMPLETE, not substituted).

## 3. Preconditions (all mandatory, programmer discipline)

1. Board identity re-confirmed in Setup before touching the
   programmer. Record DMI BIOS version + date. Anything
   unexpected → STOP and re-plan (this image is CLV-lineage).
2. 8-pin PCIe power polarity verified; board FULLY unpowered
   (PSU out), CMOS battery REMOVED, capacitors discharged.
3. Programmer CH347 (native 3.3 V). NEVER a black-PCB CH341A.
4. Chip identification FIRST: `flashrom -p ch347_spi:spispeed=1.875M
   --flash-name` must report Winbond `W25Q128.V` 16 MiB.
   Any other ID → STOP, move clip/header.
5. Display path: direct DisplayPort for all observations.
   P0 oracle: LED green-blink = booted; red-static = halt;
   no LAN + no video + constant fans = silence (5-min wait).
6. Pinned flashrom identity recorded (`flashrom --version` +
   binary hash; project pin v1.8.0 — re-verify on flash host).

## 4. Procedure

1. Fresh pre-write capture ×2 to NEW files
   (`evidence/programmer/reads/<date>/pre-s123-read-a.bin`,
   `-b.bin`): `flashrom -p ch347_spi:spispeed=1.875M -r <file>`
   twice. Require byte-identical (`cmp` exit 0) + record both
   SHA-256. This capture is the primary recovery image.
   STOP on any mismatch.
2. Re-verify candidate hash from disk:
   `sha256sum -c firmware-flash-pkg/20260922-clv500-s123/SHA256SUMS`.
   Expect `26c0634d…ed873ab`. Abort on mismatch.
3. Exact operator approval (all brackets filled from the fresh
   capture; no flash without it):
   `Подтверждаю запись файла firmware-flash-pkg/20260922-clv500-s123/BC250_5.00_clv_S3-DRV_v001.bin SHA-256: 26c0634da2fbda7125ebf284241917af58b6c30149d18cca434e55a6ded873ab на плату [ID], чип W25Q128.V (ID-подтверждён). Pre-write дамп: [путь], SHA-256 [хеш], 16 MiB, два чтения совпали. Recovery: [путь pre-write копии + stock], route: programmer re-write + readback.`
4. Write: `flashrom -p ch347_spi:spispeed=1.875M -w
   firmware-flash-pkg/20260922-clv500-s123/BC250_5.00_clv_S3-DRV_v001.bin`.
   Require exit 0 + `VERIFIED`. Preserve the full log.
5. Independent full-chip readback to a NEW file; require SHA-256 ==
   `26c0634d…ed873ab` (`cmp` exit 0). STOP and do NOT boot on
   mismatch.
6. Remove programmer, reinstall battery, clear CMOS (60 s
   battery-out or 20 s jumper; verify by wrong clock in Setup).
7. Cold boot, observe P0 (LED/LAN/video/fans + 5-min wait +
   ping/SSH). Any red-static/silence → STOP, rollback §6.
8. Setup inspection (change nothing yet): photograph/transcribe
   CPU core count option, the six S1 clock fields (MCLK `0x1A`,
   UclkDiv `0x01`, DF `0x01/0x0532`, MemPstate `0xFF`), and the
   Chipset → GFX Configuration → NBIO submenu visibility.
9. Boot OS. Remote session re-reads: NVRAM body hash + the six
   fields, `nproc`, `pp_dpm_mclk/sclk/fclk`, VCN IP block state.

## 5. Hardware acceptance (claims allowed only from here)

| # | Check | Pass bar |
|---|---|---|
| H1 | POST + display + OS boot | P0 green, SSH up, 3 cold boots stable |
| H2 | Setup defaults | six S1 fields read back as §1 values |
| H3 | NVRAM readback | live body hash recorded, fields match |
| H4 | Menu visibility | NBIO/ChIPSET submenu present or `UNREACHABLE` recorded (no forcing) |
| H5 | Core count | `nproc` + Setup toggle state recorded |
| H6 | Training/stability | no training loop, no GPU reset, no MCE burst |
| H7 | Independent clock/volt measurement | domain counters / meter readings recorded; sync/volt claims ONLY from this row |

H7 is the only row that can ever promote "equal numbers" or
"stored bytes" into a sync/voltage claim. Until H7 passes, the
image is "boots with requested defaults", nothing more.

## 6. Stop / rollback

- STOP on: chip-ID mismatch, capture mismatch, candidate-hash
  mismatch, write not VERIFIED, readback mismatch, no POST /
  display / OS, red-static LED, training loop, thermal alarm,
  any voltage value changed unexpectedly.
- Rollback path A: programmer re-write of the step-1 pre-write
  capture + readback verify (separate exact approval).
- Rollback path B: programmer re-write of stock recovery
  (separate exact approval).
- Preserve the failure state and report before any further boot.

## 7. Honest boundary

- Static BUILD acceptance only (gates + tests + independent
  rebuild). No reviewer from a second model family was
  available; review is recorded INCOMPLETE.
- No statement in this package claims 1:1:1 sync, applied
  clocks, applied voltages, VCN enablement, or 8-core dispatch.
  Those need §5 rows, which are UNRUN.
- The unhide transplant is byte-exact community-proven on the
  3.00 lineage; its behavior on CLV Setup (TSE) is unobserved.
