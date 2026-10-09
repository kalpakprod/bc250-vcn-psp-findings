# BC250 clv 5.00 + FCLK-1800 APCB — Programmer Flash Runbook

> Audit 2026-09-27: historical staged experiment, not a current flash instruction. The 1800 value is a stored request, not a measured physical clock. The ratio 1800:1800:900 below is a hypothesis, not verified operation. No SoC voltage or 1:1:1 claim follows. See `docs/research/2026-09-27-clock-oc-status-audit.md`.


Status: STAGED, NOT flashed. Physical execution requires operator
approval of the exact image name + SHA-256.
Package: `firmware-flash-pkg/20260924-clv-fclk1800-apcb/` (`SHA256SUMS`).
Method: **Hardware programmer (CH347 + flashrom) ONLY**. No AFU, no in-OS flash.

This runbook inherits the hardware procedure from
`docs/guides/bc250-v003-community-vcn-programmer-flash-runbook.md`
(same chip `W25Q128.V`, same CH347 method, same preconditions, same
power isolation, same double-read backup, same rollback structure).
Sections below state only what differs. Read the v003 runbook first.

---

## 1. Package Identity

| File | SHA-256 | Size |
|---|---|---|
| `BC250_5.00_clv_FCLK1800_APCB_v001.bin` | `3d6348c65a0c2ee500e13f3b1a5c9e9c64c57e36b570fbd1e85a19b9713871f8` | 16,777,216 B |

- Base: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
  (sha256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`).
- Diff vs base: EXACTLY 3 bytes — `0xAB1B9A/B` (u16 1420 -> 1800) and
  `0xAB1010` (APCB checksum `0xC0` -> `0x42`). Verified by full-image
  `cmp`-style diff and independent APCB re-parse (`scripts/apcb_detail.py`).
- No recompression, no FV changes: every region except those 3 bytes is
  byte-identical to the clean clv donor, including the signed PSP/$PS1
  subtrees.

## 2. What This Image Is and Is Not

- It IS the clv 5.00 BIOS with the FCLK override record set to 1800
  instead of the stock 1420. The ABL1 boot reader (token pair
  0x015F gate / 0x0160 value) reads this record and passes the value as
  the FCLK PLL service argument — proven on the native ABL1 code in
  Unicorn with these exact bytes (2026-09-24).
- It is NOT the final combined BIOS: no VCN driver (that is the v003b
  image on the 3.00 base), no 8-core change, no UCLK change. UCLK on
  this path remains the input/2 division (LSR#1 at ABL1 `0x5F30`); with
  MCLK 1800 the expectation is UCLK 900, so this image alone gives
  1800:1800:900, NOT 1:1:1. The 1:1:1 fabric goal still needs the
  UCLK track (PSP-breach class, separately gated).
- Flash ORDER (agreed): v003b first, evaluate, return the board to a
  known state, then this one. One variable per flash.

## 3. Preconditions

Identical to the v003 runbook (power isolation, CR2032 out, CH347
only, `--flash-name` -> `W25Q128.V`, DP + LAN attached, P0 LED oracle).

## 4. Procedure

Identical to the v003 runbook steps 1-6, with the clv names:

1. Double read backup: `pre-fclk-read-a.bin` / `pre-fclk-read-b.bin`,
   `cmp` must match, hash recorded.
2. `sha256sum -c SHA256SUMS` in the package dir -> `OK`
   (`3d6348c6…`).
3. Operator approval template (filled):
```text
Подтверждаю запись файла firmware-flash-pkg/20260924-clv-fclk1800-apcb/BC250_5.00_clv_FCLK1800_APCB_v001.bin
SHA-256: 3d6348c65a0c2ee500e13f3b1a5c9e9c64c57e36b570fbd1e85a19b9713871f8
на плату BC-250-01, чип W25Q128.V.
Pre-write дамп: pre-fclk-read-a.bin, SHA-256 [хеш], 16 MiB, два чтения совпали.
Recovery: pre-fclk-read-a.bin + evidence/donor/retroweb-20260916/BC250_5.00_clv.bin.
Route: programmer re-write + readback.
```
4. `flashrom -p ch347_spi:spispeed=1.875M -w BC250_5.00_clv_FCLK1800_APCB_v001.bin` -> rc 0 + `VERIFIED`.
5. Readback `post-fclk-readback.bin`, `cmp` against the candidate -> `FLASH VERIFIED EXACT`.
6. Bring-up: clip off, battery in, 12V in, power on, observe P0 LED + DP.

## 5. Hardware Acceptance Gates

| Gate | Check | Pass Criteria |
|---|---|---|
| **C1** | POST & Display | LED green activity, DP video, UEFI visible (clv 5.00 splash) |
| **C2** | APCB accepted | No APCB checksum fatal (the ABL0 validator rejects bad sum8 with fatal 16 — our sum is valid) |
| **C3** | OS Boot | Linux to login/SSH |
| **C4** | FCLK measured | fabric clock reads 1800 (zentimings/dmesg/clock probe), was 1420-class on the clv base |
| **C5** | UCLK unchanged | UCLK reads ~900 with MCLK 1800 (the LSR division; unchanged by this image) |
| **C6** | Stability soak | 15 min memory-sensitive load without MCE/edac errors |

C4 is the direct before/after evidence pair. Note honestly: the
emulator proved the FCLK service ARGUMENT becomes 1800; the physical
frequency depends on the SVC28 transport semantics (selector 0x0E) that
are not emulator-proven. A C4 mismatch is a transport finding, not a
checksum or boot failure — the board stays recoverable.

If C1/C2 fail (no POST / APCB fatal): rollback immediately (Path A/B
below). A bad APCB sum would fatal EARLY (ABL0 validator), but our sum
is verified valid twice (builder + independent parse) and by the
emulator's native reader path.

## 6. Rollback

- Path A: re-write `pre-fclk-read-a.bin` + readback verify.
- Path B: re-write the clean clv donor base
  `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (sha256
  `ea578104…`) — full return to stock clv 5.00.

## 7. Honest Assessment

- 3-byte change, twice-verified checksum, emulator-validated service
  argument on the native reader — the smallest-change image in the
  project so far.
- Not proven: SVC28 transport to physical FCLK, the loader copy of APCB
  to runtime 0x7B000 (modeled from ABL0 SVC2D evidence), and the
  post-training DF P-state behavior (early init vs steady state).
- One-variable image on the clv lineage; the final combined BIOS is a
  separate build after both variables pass their gates.
