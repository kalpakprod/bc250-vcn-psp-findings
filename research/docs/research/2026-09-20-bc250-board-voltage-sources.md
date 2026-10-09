# BC-250 board voltage sources — firmware-visible inventory (CLV 5.00)

Date: 2026-09-20. Evidence class: `static-analysis` over `observed-bytes`.
Task log: `docs/action-logs/2026-09-20-bc250-board-voltage-sources.md`.
Evidence: `evidence/firmware-audit/20260920-bc250-board-voltage-sources/`.

## Question

Which modules in the pinned CLV 5.00 firmware corpus can drive a voltage-regulator
register through the shared Super-I/O/EC window, and which modules only touch that
window (or carry the same literal bytes) without a VR mailbox transaction?

## Inputs (immutable, hashes re-read)

| Input         | Identity                                                                                                                    |
| ------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Donor ROM     | `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 B, SHA-256 `ea578104…ca4cb8`                              |
| Pinned corpus | `evidence/firmware-audit/20260919-inv-token-consumers/`, 233 PE32/TE module images, `census.json` SHA-256 `506b8eef…b60d39` |

No ROM, NVRAM, register, candidate, board or network action occurred.

## Method

One conjunctive literal-byte detector over all 233 module images. Fourteen anchors were
defined; the **strong set** of ten must all be present in the same module:

`push 0x2e`, `push 0x2f`, `mov al,0x87`, immediate `0x00000a20`, `push 0x65`,
`push 0x66`, `push 0x70`, `push 0x63`, `push 0x60`, `test al,0x40`.

For every matching module the scanner enumerates the EC-window write helpers (function
entry, owned `0x0a20` immediate, owned unlock byte), the call sites with their pushed
register index, and the staged value where it is a literal immediate. Each matching
module image is then re-extracted from the immutable ROM through the FFS-relative `VZ`
TE signature scan and re-hashed.

An independently written verifier re-derives the match set from the pinned objdump text
with its own three-group anchor conjunction, re-locates each writer image in the ROM by
whole-image content search, recomputes the corpus-wide anchor module census, and re-reads
all 200 recorded anchor offsets as raw bytes plus (where disassembled) as instruction
bytes.

## Result

**Exactly two of the 233 modules implement the complete EC-window VR mailbox writer.**

| Module     | File GUID                              | TE image in ROM                                 | Size    | SHA-256 (image)   |
| ---------- | -------------------------------------- | ----------------------------------------------- | ------- | ----------------- |
| `ISL69247` | `6E6D2018-28D0-4AD3-BEB3-B48E4981707D` | `0xed2c74` (FFS file `0xed2c30`, FV `0xe02000`) | 4,264 B | `3e1f753a…421e34` |
| `ISL95712` | `02544BE0-2CB9-4B75-8111-CD8CDC07B837` | `0xed3d8c` (FFS file `0xed3d48`, FV `0xe02000`) | 3,624 B | `c0cc17d2…5d43a9` |

Transport implemented by both (observed bytes):

- Super-I/O/EC configuration window unlocked with `0x87,0x87` on port `0x2E`, index via
  `0x2E` / data via `0x2F`;
- EC data window base `0xA20` (`0xA20` command, `0xA21` data, `0xA22` status);
- mailbox staging registers `0x65` (transaction class `0xC0`), `0x66` (target register
  index), `0x70`/`0x71` (2-byte little-endian value), `0x63` (transfer count), `0x60`
  (trigger `0xC0`), followed by a status poll on bit `0x40` (`test al,0x40`).

Helper instances and call sites: `ISL69247` — 2 full-transport helpers (entries at RVA
`0x4f5`, `0x565`), 28 call sites; `ISL95712` — 2 helpers (RVA `0x313`, `0x383`),
18 call sites. The call sites enumerated by this scanner are calls to the two EC
primitives, so the indices they resolve are the mailbox staging registers (`0x61`,
`0x62`, `0x63`, `0x65`, `0x66`, `0x70`, `0x71`) together with the staged value, which is
recorded as an immediate, a resolved register, or explicitly unresolved. One literal
target is visible at this level: `ISL95712` stages `0xde` into mailbox register `0x66`
(two sites) — the VR target register index.

The VR-level register indices written through this transport (VCORE mV -> `0x21`,
loadline -> `0x28`, plus `0x23`, `0xc5`, `0xc7`, and MEMIO -> `0xdf`) are recorded by the
earlier fixed-voltage Setup consumer trace
(`docs/research/2026-09-20-clv-fixed-voltage-consumer.md`, independently re-run) and are
not re-derived by this inventory.

This is the same transport and the same two modules that the earlier fixed-voltage Setup
consumer trace identified as the readers of the fixed VCORE/GFX/MEMIO Setup fields
(`docs/research/2026-09-20-clv-fixed-voltage-consumer.md`); the cross-check in the
machine result reports `agree: true`.

## Bounded negative — "EC window only" bucket

28 modules carry at least one strong anchor but not the full conjunction; they are listed
with their per-anchor offsets in `vr-mailbox-writers-result.json`
(`ec_window_only_modules`). The two meaningful subsets are:

- 16 modules contain `push 0x2e` or `push 0x2f` (they touch the Super-I/O/EC configuration
  port): `DxeCore`, `SbDxe`, `PciRootBridge`, `NvramSmm`, `StatusCodeDxe`,
  `RealtekUefiDriver`, `AmdCcxVhAriPei`, `AmdFabricAriPei`, `AmdNbioGfxARIPei`,
  `AmdNbioBaseARIPei`, `AmdNbioPcieARIPei`, `AmdNbioSmuV10Pei`, `AmdSocBl5AriPei`,
  `CbsBasePei`, `FanTuningPei`, `OEMBOARDPei`;
- 9 modules contain the 4-byte `0x00000a20` immediate: `Setup`, `FanTuningDxe`,
  `AmdNbioGfxARIPei`, `AmdNbioBaseARIPei`, `AmdNbioPcieARIPei`, `AmdNbioSmuV10Pei`,
  `AmdSocBl5AriPei`, `FanTuningPei`, `OEMBOARDPei`.

Corpus-wide anchor module census (from `anchor_hit_table`, recomputed independently by
the verifier and found equal): `push 0x2e` 7, `push 0x2f` 16, `mov al,0x87` 9,
`0x00000a20` 44, `push 0x65` 3, `push 0x66` 12, `push 0x70` 25, `push 0x63` 16,
`push 0x60` 15, `test al,0x40` 36, `out 0x2e,al` 3, `in 0x2e,al` 1, `mov dx,0x2e` 8,
`mov dx,0x2f` 3.

No module in this bucket carries the `0x65`/`0x66`/`0x70`/`0x63`/`0x60` staging sequence
together with the `0xA20` window and the `0x2E`/`0x2F` unlock, so none can stage a VR
register write through this window on the evidence available. The two literal-anchor hits
that are not instruction-aligned (HiiDatabase, `A0327FE0-…`) are weak-bucket
coincidences and are named in `VERIFICATION.txt`.

## Independent verification

`verify_board_voltage_sources.py` → `status PASS`, 604 checks, 0 failed, stderr empty,
exit 0. It reproduces the two-writer set from a different evidence path, confirms each
writer image occurs exactly once in the ROM inside the reported FFS file, and re-reads
all 200 recorded anchor offsets (181 instruction-aligned, 2 spanning an instruction
boundary, 17 outside the disassembled code section, 0 decode gaps).

The two cross-instruction hits are literal-anchor false positives and are named in
`VERIFICATION.txt`; both are in the weak bucket, not in a writer.

## Limits

- Static analysis only. PEI dispatch, mailbox chip identity, PMBus/register semantics,
  physical rail identity and any applied voltage remain unverified.
- The anchor set is literal-byte and calibrated on two known positives; a module
  implementing the same protocol with different encodings would be missed.
- Register indices are inferred from the pushed arguments of the transport helper;
  register-valued arguments are recorded as unresolved, not guessed.
- The ROM re-extraction path uses the FFS-relative `VZ` TE scan; modules inside
  compressed firmware volumes are not covered by that path (neither writer is affected).
- No voltage value is recommended.

## Rollback

`evidence/firmware-audit/20260920-bc250-board-voltage-sources/ROLLBACK.sh` removes this
task's evidence directory and this report (and, with `--purge-log`, the task log).
It never touches the donor ROM, the pinned corpus or earlier evidence.
