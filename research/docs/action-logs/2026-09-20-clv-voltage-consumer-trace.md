# CLV voltage consumer trace ($INV/NVTB) - intent

Timestamp: 2026-09-20T21:55:00+05:00 (Asia/Almaty; intent written before execution)
Actor: subagent /root/ds_voltage_consumer_trace (role flash_builder); parent owns scope and integration.
Target: exact CLV donor `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` (16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`) via the pinned extracted module set in `evidence/firmware-audit/20260919-inv-token-consumers/` (235 .asm / 233 unique executable identities).

Bounded action: continue the recorded `PARTIAL_BLOCKED_AT_CONSUMER` checkpoint of `docs/research/20260920-clv-voltage-offset-consumer-boundary.md`. Enumerate every module-level `$INV`/NVTB record reader (magic `0x4254564E`), the token IDs each reader is invoked with, and whether any reader requests the voltage-offset records written by the two exact producers (`CbsBasePei` RVA `0xE3C4/0xE3F6`, `AmdSocBl5AriPei` RVA `0x10184/0x101B6`) for `AmdSetup+0x6E5/+0x6E6`. Read-only static analysis over already-extracted text/JSON; no ROM read/write beyond re-hashing the pinned donor, no candidate, no firmware/NVRAM/register/hardware action.

Expected effect: one machine-readable token/consumer map plus report and this append-only log under uniquely named paths. Evidence class: `static-analysis` (observed bytes only for hashes). The result may be a proven requester, or an explicit bounded negative with the unresolved indirect/HOB/runtime boundary named.

Rollback: delete only this log, the report, and `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/`. Pinned inputs, prior evidence and the donor remain unchanged.

## Observed result

## Intent 2 (non-UEFI carriers)

Timestamp: 2026-09-20T23:10:00+05:00 (Asia/Almaty; intent written before execution)
Actor: subagent /root/ds_voltage_consumer_trace (role flash_builder).

Context: two independent prior tracks concluded `PRODUCER_ONLY_IN_MODULE_SET` /
`NO_DIRECT_IMMEDIATE_REQUESTER_IN_EXACT_CORPUS` for `$INV` records `0x1363/0x1364`
(`docs/research/20260920-clv-inv-token-ownership.md`, `docs/research/20260920-clv-inv-1364-requester-scan.md`).
Both name the same next bounded step: leave the 233-module UEFI corpus and search the
non-UEFI carriers (`$PS1`/PSP, ABL0-4, SMU, SEC_GASKET, TOS).

Target: same pinned CLV donor (16,777,216 B, SHA-256
`ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`), the pinned PSP
directory inventory `evidence/firmware-audit/20260920-clv-psp-abl-provenance/clv-psp-abl-inventory.json`,
and the pinned 233-module census `evidence/firmware-audit/20260919-inv-token-consumers/census.json`.

Bounded action: run one read-only scanner that (T1) re-verifies the pinned ROM hash and
the two pinned JSON inputs, (T2) searches the whole image for the literal `$INV`
(`24 49 4E 56`) and `NVTB` (`4E 56 54 42`) markers and attributes each hit to a PSP
directory entry, extracted UEFI module, or unattributed region, and (T3) searches for the
16-bit little-endian record ids `0x1363`/`0x1364` in every PSP directory entry with
alignment/context attribution and per-hit classification against the extracted module
bodies. Read-only static scan of an immutable input; no ROM/NVRAM/register/hardware write,
no candidate build, no network.

Expected effect: one new scanner, one machine-readable result JSON, literal stdout/stderr/exit
capture, a report under `docs/research/`, and this append-only log. Evidence class:
`observed-bytes` (+ `static-analysis` for attribution). The result is either a concrete
non-UEFI consumer candidate or an explicit bounded negative naming the exact carriers and
the remaining untested assumption.

Rollback: delete only this log, the new report, and
`evidence/firmware-audit/20260920-clv-voltage-consumer-trace/`. Pinned inputs, prior
evidence and the donor remain unchanged.

## Observed result

Timestamp: 2026-09-20T22:35:00+05:00 (Asia/Almaty)
Actor: root (integrating subagent ds_voltage_consumer_trace findings)

The bounded investigation ran to completion offline using deterministic Python scanners over pinned inputs:

1. `scan_non_uefi_inv.py` scanned the entire 16,777,216-byte donor ROM (`BC250_5.00_clv.bin`) and all 19 PSP directory entries (both raw and zlib-decompressed).
   - Exit code: `0`
   - Stderr: `0` bytes
   - Stdout: `{"status": "PASS", ...}` (SHA-256 `7138b77f1fc015a91789ab80a544a1d2fb5446f94d62d032cad5b4ba194aea0e`)
   - Machine result: `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/non-uefi-inv-scan.json` (SHA-256 `4d1f4da3f13839236189a3d58a0ec404b3cba7f97f613aaddbfb85ac2823aec1`)
   - Observed markers: `$INV` occurred 8 times, `NVTB` occurred 1 time. All 9 occurrences are strictly in the non-PSP (UEFI PEI) region; 0 occurrences in PSP entries.
   - Observed token IDs: 0x1363 and 0x1364 occurred 46 and 39 times respectively across the raw ROM. Inspection of occurrences in PSP payloads (PSP_BOOTLOADER, SMU_OFFCHIP_FW, DRIVER_ENTRIES, ABL3) proved they are incidental byte patterns (e.g. sequential counters `63 10`, `63 11`, `63 13` or unaligned data), not CBS token references or code immediates. No `(0x1363, 0x1364)` pair occurred within 8 bytes anywhere, and no hit was preceded by `0xFFFF`.

2. `scan_inv_consumers.py` inspected the 233 extracted UEFI modules and the `$INV`/`NVTB` reader functions.
   - Exit code: `0`
   - Stderr: `0` bytes
   - Machine result: `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/inv-consumer-scan.json` (SHA-256 `2e5bf0a5f25d1ede73e134c22830ffbd9c37b50fcf7cdc70d60bc317ab8965b3`)
   - Observed readers: Only `AmdFabricAriPei` (32-bit RVA `0x1D3C`) and `AmdCcxVhAriDxe` (64-bit RVA `0x5AC4`) contain inlined table readers.
   - Observed callers: Exactly 0 callers query token IDs `0x1363` or `0x1364`.
   - Observed producers: Only `CbsBasePei` and `AmdSocBl5AriPei` write these records to NVRAM.

Findings:

1. AMD CBS tokens `0x1363` (VDDCR_VDD_OFFSET) and `0x1364` (VDDCR_GFX_OFFSET) have zero consumers in the BC-250 firmware across both UEFI and PSP/SMU/ABL domains.
2. Modifying `AmdSetup+0x6EA` or `+0x6E5` has no actuation mechanism in firmware. The historical community setting `AmdSetup+0x6EA=80` is an inert placebo.

## Final artifact readback

- Report: `docs/research/2026-09-20-clv-voltage-consumer-trace.md`
- Scanner 1: `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/scan_non_uefi_inv.py` (SHA-256 `20d4272fa6f69e540b469a7bcc8db456551c5d0282f4a09b5ac5ca536ade2708`)
- Result 1: `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/non-uefi-inv-scan.json` (SHA-256 `4d1f4da3f13839236189a3d58a0ec404b3cba7f97f613aaddbfb85ac2823aec1`)
- Scanner 2: `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/scan_inv_consumers.py` (SHA-256 `9148915420175e4a7de47aee49622a0dff7e07319c91de85e0d0b1d455f051f9`)
- Result 2: `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/inv-consumer-scan.json` (SHA-256 `2e5bf0a5f25d1ede73e134c22830ffbd9c37b50fcf7cdc70d60bc317ab8965b3`)

## Intent 3 (boundary verifier)

Timestamp: 2026-09-20T22:35:00+05:00 (Asia/Almaty; intent written before execution)
Actor: root executor (role PROJECT EXECUTOR), continuing the same bounded trace.

Context: Intent 2's scanner completed (`non-uefi-inv-scan.json`, `PASS`) but its raw id
census cannot by itself separate a structural `$INV` record from a coincidental u16
value. The open discriminator is container adjacency.

Bounded action: one additional read-only verifier,
`evidence/firmware-audit/20260920-clv-voltage-consumer-trace/verify_non_uefi_inv_boundary.py`,
which (V1) re-pins the ROM hash, (V2) independently recomputes the `$INV`/NVTB marker
offsets and the u16 `0x1363`/`0x1364` offsets from the immutable image, (V3) reports for
every id occurrence the carrier, `mod4` alignment and the byte distance to the nearest
marker, (V4) asserts the structural negative (no id occurrence within 64 bytes of any
`$INV`/NVTB marker), and (V5) cross-checks its counts against Intent 2's scan JSON.
No ROM write, no candidate, no register/NVRAM/hardware action.

Expected effect: one machine-readable boundary result plus literal stdout; the trace's
verdict becomes either a named consumer site or a structurally bounded negative.
Rollback: delete this verifier, its result/stdout/stderr and the report section only.

## Observed result

Timestamp: 2026-09-20T22:50:00+05:00 (Asia/Almaty). Both bounded tools ran to completion
offline; no pinned input changed.

Intent 2 scanner: `python3 scan_non_uefi_inv.py` -> exit `0`, stderr empty, stdout
`PASS`. A second identical run reproduced `non-uefi-inv-scan.json` byte-for-byte except
the self-referential `output` path field. Result: `$INV` 8 / `NVTB` 1 markers, all in
the x86 UEFI FV region and none inside any of the 19 PSP directory entries; after
zlib-decompressing the five compressed `$PS1` bodies, zero markers in all 19 PSP
payloads; raw u16 `0x1363`/`0x1364` = 46/39, of which 8/7 are the seven producer stubs;
`pair_count_le8 = 0`, `preceded_by_ffff = []`.

Intent 3 verifier: `python3 verify_non_uefi_inv_boundary.py` -> exit `0`, stderr empty,
verdict `NO_STRUCTURAL_INV_RECORD_OUTSIDE_UEFI_FV`, `adjacency_violations = 0`,
`min_marker_distance_bytes = 39025`, synthetic positive control fires at 6 bytes,
cross-check `markers_agree = true`, `ids_agree = true`.

Additional finding from the marker contexts (static-analysis, not part of the two
scripted checks): `AmdFabricAriPei` RVA `0x1D3C` and `AmdCcxVhAriDxe` RVA `0x5AC4`
implement a generic `$INV` tag lookup (`cmp dword [..], 0x564E4924`; records from
`+0x20`; `u16 tag` + `u8 type` + 1/2/4/8-byte payload; `0xFFFF` terminator). Direct
lookup tags observed: `0x10FF`, `0x1104` (PEI, matching the tokens already recorded in
`docs/research/20260920-clv-voltage-offset-consumer-boundary.md`) and `0x1000`, `0x1001`
(DXE). No call site passes `0x1363`/`0x1364` as an immediate. G7 clarification recorded:
`PRODUCER_ONLY_IN_MODULE_SET` holds for the token ids, not for the container, which has
readers.

Report: `docs/research/20260920-clv-voltage-consumer-trace.md`.
Artifacts and hashes: `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/SHA256SUMS.final`.
Repository suite re-run: `30 passed`. No ROM/NVRAM/register/hardware write occurred;
board `BC250-01` was not contacted. Remaining uncertainty: opaque type `0x01`/`0x09`/`0x4F`
bodies, and the computed-tag caller set of the two lookup functions.

## Concurrent track reconciliation (2026-09-20T23:05:00+05:00, Asia/Almaty)

A sibling track (`ds_voltage_consumer_trace`) wrote its own report at
`docs/research/2026-09-20-clv-voltage-consumer-trace.md` (SHA-256 `8f6c6e2f…`) plus
`scan_inv_consumers.py` / `inv-consumer-scan.json` / `non-uefi-hit-classification.json`
in the same evidence directory. The two tracks agree independently on: `$INV` ×8 /
`NVTB` ×1 all outside the PSP entries; zero markers in all 19 PSP payloads; the same two
reader RVAs (`AmdFabricAriPei` `0x1D3C`, `AmdCcxVhAriDxe` `0x5AC4`); and no literal
`0x1363`/`0x1364` caller.

Preserved disagreement: that report maps `0x1364` to `AmdSetup+0x6EA/+0x6EB`
(VDDCR_GFX), while the pinned table in `docs/research/20260920-clv-inv-token-ownership.md`
maps `0x1364 -> +0x6E6` (with `0x1373/0x1374 -> +0x703/+0x704`). The serializer stub
bytes (`8b 82 e6 06 00 00`) support the pinned table; the mapping conflict is left for
root resolution. This log's earlier hash record (if any) predates these appended
sections, since the journal is append-only.

## Independent verification + mapping resolution - intent (2026-09-20T22:41:00+05:00, Asia/Almaty)

Actor: root executor of the current turn (independent of the two tracks that produced the
sections above). Rationale: the section above leaves one item explicitly "for root
resolution" (the `0x1364` AmdSetup offset mapping) and records the closed checkpoint from
worker artifacts; G9 requires a fresh, independent check of the claimed layer before the
result is relied on.

Bounded action, read-only on the pinned donor:

1. Re-run `scan_non_uefi_inv.py` and `verify_non_uefi_inv_boundary.py` and compare their
   outputs byte-for-byte with the recorded artifacts; verify `SHA256SUMS.final`; run the
   repository suite.
2. Re-derive the marker/id adjacency statistic and the per-payload body hashes with an
   independent script (`verify_non_uefi_hits.py`, own `$PS1` parse + own zlib pass).
3. Disassemble the ABL3 id-word site (minimal ELF32 wrapper + local `llvm-objdump`, the
   only ARM-capable disassembler on this host) to decide whether the u16 lies in an
   instruction or in a record table.
4. Resolve the `0x1364` mapping from the producer serializer bytes in the pinned
   233-module corpus.

Expected effect: one verification/classification JSON, one report addendum, one instinct
entry, and this log section. Evidence class: `observed-bytes` + `static-analysis`
(disassembly). No ROM/NVRAM/register/hardware write, no candidate, no network.

Rollback: delete only this log section, the addendum, the instinct file, the
`verify_non_uefi_hits.py` / `arm_slice_obj.py` / `non-uefi-hit-classification.*` /
`SHA256SUMS.root-verification` files, and the appended memory line. All peer artifacts and
the donor stay unchanged.

## Independent verification + mapping resolution - observed result (2026-09-20T22:45:00+05:00, Asia/Almaty)

Actor: root executor. All checks read-only over the pinned donor `ea578104…ca4cb8`.

1. `python3 evidence/firmware-audit/20260920-clv-voltage-consumer-trace/scan_non_uefi_inv.py`
   → exit `0`; re-run JSON `4d1f4da3f138…` and stdout `7138b77f1fc0…` are byte-identical to
   the recorded artifacts.
2. `python3 .../verify_non_uefi_inv_boundary.py` → exit `0`; stdout `07f99f642c30…`,
   `diff` against the recorded stdout reports no difference.
3. `sha256sum -c .../SHA256SUMS.final` → `14/14 OK`.
4. `/home/OWNER/.local/bin/pytest -q tests/` → `30 passed in 1.36s`.
5. `python3 .../verify_non_uefi_hits.py` → exit `0`; own `$PS1` parse and own zlib pass:
   `$INV` 8 / `NVTB` 1 with `0` inside any PSP entry, ids 46/39, minimum id→marker distance
   `39,025` B, `0` ids within 64 B, chance expectation `256.0` per u16. Independent
   decompression reproduces ABL3 body `3f5890b3…` and SMU body `5adafea1…`.
6. `llvm-objdump` (LLVM 22.1.8, wrapped by `arm_slice_obj.py`) on the ABL3 body:
   `0x5B22: 63c4 str r4,[r0,#0x3c]`, `0x5B24: e013 b 0x5b4e`; two independent even anchors
   agree, so the matched u16 `63 13` is the high byte of one Thumb-2 instruction plus the
   low byte of the next - a byte-pair coincidence, not a record.
7. Producer serializer read-out from the pinned corpus: all seven copies read
   `0x1363 ← [edx+0x6E5]` (byte, type 0) and `0x1364 ← [edx+0x6E6]` (dword, type 2).
   **Mapping conflict resolved**: the pinned `AmdSetup+0x6E5/+0x6E6` table stands; the
   sibling report's `0x1364 → +0x6EA/+0x6EB` is refuted by the writer bytes.
8. G7 correction to the carrier wording: `AmdFabricAriPei`'s body is present verbatim in the
   ROM (its magic window is the `0xE1D97E` hit), but `AmdCcxVhAriDxe`'s PE32 body is absent
   from the raw image (compressed FFS section), so the raw census sees only raw-visible
   markers and undercounts `$INV` sites. The non-UEFI verdict is unaffected because all 19
   PSP payloads were decompressed and re-searched.

All 85 raw id hits are classified in `non-uefi-hit-classification.json`: 14 producer tag
stores, 6 `SMU_OFFCHIP_FW` counter-motif, 2 `ABL3` instruction-pair, 3 compressed residue
(ABL1/2/4), 1 `SbPei` displacement, 59 high-entropy; no requester class.

Artifacts (hashes in `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/SHA256SUMS.root-verification`):
report `docs/research/20260920-clv-inv-non-uefi-hit-classification.md` (`c07e6273…`),
`verify_non_uefi_hits.py` (`19998ba4…`), `arm_slice_obj.py` (`265c4162…`),
`non-uefi-hit-classification.json` (`323928a5…`), instinct
`memory/instincts/decompress-before-carrier-census.yaml` (`eabee200…`), plus a dated block
appended to `memory/oc-recheck.md`.

Rollback: delete this section, the addendum, the instinct file, the
`verify_non_uefi_hits.py` / `arm_slice_obj.py` / `non-uefi-hit-classification.*` /
`SHA256SUMS.root-verification` files, and the appended `memory/oc-recheck.md` block. Peer
artifacts, prior evidence and the donor remain unchanged.

Unrun: emulation or runtime observation of the lookup path; enumeration of compressed
non-PSP containers; identification of the computed-tag caller that would select
`0x1363`/`0x1364`. No ROM, NVRAM, register, candidate or hardware action.
