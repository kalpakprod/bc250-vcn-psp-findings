# CLV `$INV` non-UEFI hits — independent verification, hit classification, mapping resolution

## Current

`docs/research/20260920-clv-voltage-consumer-trace.md` closed the non-UEFI carrier question
for the pinned CLV 5.00 donor and named two residuals: a `0x1364` AmdSetup offset conflict
with the sibling report `docs/research/2026-09-20-clv-voltage-consumer-trace.md`
(`+0x6E6` vs `+0x6EA/+0x6EB`, left "for root resolution"), and the fact that a literal-id
scan cannot see a computed-tag caller. This addendum is the independent check of that
closed result plus the mapping resolution. It adds evidence the two prior tools did not
produce: disassembly of an id-word site, producer-side serializer displacements, and a
carrier-visibility test for the raw byte census.

## Method

Read-only over the immutable pinned donor (`ea578104…ca4cb8`, 16,777,216 B). Three
independent reproductions plus two new checks, all in
`evidence/firmware-audit/20260920-clv-voltage-consumer-trace/`:

1. Re-run of `scan_non_uefi_inv.py` and `verify_non_uefi_inv_boundary.py`; comparison of
   the outputs with the recorded artifacts; `sha256sum -c SHA256SUMS.final`; repository
   suite.
2. `verify_non_uefi_hits.py` — own `$PS1` parse, own zlib pass, own marker/id adjacency
   statistic, own per-payload body hashes, per-hit classification of all 85 raw id hits.
3. `arm_slice_obj.py` + local `llvm-objdump` (LLVM 22.1.8, the only ARM-capable
   disassembler on this host; GNU objdump here has no ARM target) for the ABL3 site.
4. Producer serializer read-out from the pinned 233-module corpus
   (`evidence/firmware-audit/20260919-inv-token-consumers/*.instructions.json`).

## Result

### V1 — the recorded result reproduces byte-for-byte

| Check                                                       | Result                                                                            |
| ----------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `scan_non_uefi_inv.py` re-run vs recorded JSON / stdout     | identical, `4d1f4da3…` / `7138b77f…`                                              |
| `verify_non_uefi_inv_boundary.py` re-run vs recorded stdout | identical, `07f99f64…`                                                            |
| `sha256sum -c SHA256SUMS.final` (14 entries)                | 14/14 OK                                                                          |
| `/home/OWNER/.local/bin/pytest -q tests/`                | `30 passed in 1.36s`                                                              |
| marker census, own implementation                           | `$INV` 8, `NVTB` 1, 0 inside any PSP entry                                        |
| id census, own implementation                               | `0x1363` 46, `0x1364` 39                                                          |
| min id→marker distance / ids within 64 B                    | 39,025 B / 0                                                                      |
| independent zlib re-decompression                           | ABL3 body `3f5890b3…` and SMU body `5adafea1…`, both equal to the recorded values |

The 85 observed u16 hits sit below the 256-per-u16 chance expectation for a 16 MiB image,
which is consistent with coincidence rather than a deliberate id table.

### V2 — every non-producer id hit is classified, and none is a record

`per_hit_classification` in `non-uefi-hit-classification.json` (85 entries):

| Class              | Count | Basis                                                                                                             |
| ------------------ | ----- | ----------------------------------------------------------------------------------------------------------------- |
| producer-stub      | 14    | `ba 63 13 00 00` / `ba 64 13 00 00` (`mov edx,imm32` tag store) in the 7 serializer copies — writers, not readers |
| module-code        | 1     | `SbPei` `0xE1405D`, displacement bytes                                                                            |
| counter-motif      | 6     | `SMU_OFFCHIP_FW` stride-6 motif (below)                                                                           |
| instruction-pair   | 2     | `ABL3` site (below)                                                                                               |
| compressed-residue | 3     | `ABL1`/`ABL2`/`ABL4`: present in the compressed bytes, absent from the decompressed body                          |
| high-entropy       | 59    | local entropy ≈ 6.5–6.6 bits/byte, no marker within 39,025 B                                                      |

Two cases are now decided by disassembly rather than by inference:

- **ABL3 `0x5B23`.** The decompressed body is Thumb-2 entered through an A32 veneer
  (`10 40 2d e9 04 20 9f e5 32 ff 2f e1 10 80 bd e8` = `push {r4,lr}; ldr r2,[pc,#4];
blx r2; pop {r4,pc}`, literal `0x00060D91` = Thumb entry). Decoding from two independent
  even anchors gives the same boundaries at the site:
  `0x5B22: 63c4 str r4,[r0,#0x3c]` and `0x5B24: e013 b 0x5b4e`. The matched u16 `63 13`
  is the high byte of one instruction plus the low byte of the next — a byte-pair
  coincidence across an instruction boundary, not a record field.
- **SMU `0x2BFE…0x2C28` / `0x2E28…0x2E40`.** 17 occurrences of the 3-byte motif
  `03 22 63` in the decompressed `SMU_OFFCHIP_FW` body, running at stride 6, with the byte
  after the constant `0x63` incrementing (0x10, 0x11, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18,
  then 0x13, 0x16, 0x17, 0x18, 0x14, 0x2b, 0x2c). The scanner's `63 13` is one step of that
  counter read at the offset that happens to reproduce the record id. Note the byte-order
  trap: the motif key read big-endian is `0x6313`, the byte swap of the LE record id
  `0x1363`. The second SMU payload (`SMU_OFF_CHIP_FW_2`) has a different body
  (`6ee019e3…`) and contains no motif, which is why only the first copy produced hits.

### V3 — `0x1363` → `AmdSetup+0x6E5`, `0x1364` → `AmdSetup+0x6E6` (mapping conflict resolved)

All seven byte-identical serializer copies in the pinned corpus agree:

| Token    | Source read                                 | Store             | Type                               |
| -------- | ------------------------------------------- | ----------------- | ---------------------------------- |
| `0x1363` | `8a 82 e5 06 00 00` = `mov al,[edx+0x6E5]`  | `mov [ecx+3],al`  | 1-byte payload (type bits cleared) |
| `0x1364` | `8b 82 e6 06 00 00` = `mov eax,[edx+0x6E6]` | `mov [ecx+3],eax` | `or dl,0x2` → 4-byte payload       |

Sites: `AmdFabricAriPei` `0x11924`/`0x11956`, `AmdNbioBaseARIPei` `0x12734`/`0x12766`,
`AmdNbioGfxARIPei` `0xFAF4`/`0xFB26`, `AmdNbioPcieARIPei` `0x13244`/`0x13276`,
`AmdNbioSmuV10Pei` `0x10444`/`0x10476`, `AmdSocBl5AriPei` `0x10184`/`0x101B6`,
`CbsBasePei` `0xE3C4`/`0xE3F6`.

Therefore the pinned mapping is correct and the sibling report's `0x1364 → AmdSetup+0x6EA/
+0x6EB` is refuted by the writer bytes: the 4-byte payload is read from `+0x6E6` and covers
`+0x6E6..+0x6E9`, so it cannot be `+0x6EA`. `AmdSetup+0x6EA` is a different field that this
serializer does not copy.

The producer also corroborates the container reader layout independently inferred in
`20260920-clv-voltage-consumer-trace.md` (tag `u16` at `+0`, type in the low two bits at
`+2`, payload at `+3`): the writers store exactly that shape, with `type 0` for the 1-byte
`0x1363` and `type 2` for the 4-byte `0x1364`.

### V4 — carrier-visibility caveat on the raw byte census

The raw census counts only bytes that exist in the image. `AmdFabricAriPei`'s PE32 body is
present verbatim in the ROM (its magic window is the hit at `0xE1D97E`), but
`AmdCcxVhAriDxe`'s PE32 body is **not** present raw (neither its first 64 bytes nor the
48-byte window around its `cmp [rbx],'$INV'` at RVA `0x5BBE` occurs anywhere in the
16 MiB image) — its FFS section is stored compressed and only exists after decompression.

Consequence for the wording of the closed result: "all nine markers are inside the x86
UEFI FV region" is a statement about _raw-visible_ markers and does not bound the number of
`$INV`/NVTB sites in the image. The non-UEFI verdict itself is unaffected, because all 19
PSP payloads were decompressed and re-searched (V1); what remains unenumerated is any
_compressed non-PSP_ container, e.g. inside `0xAE0000..0xE00000` (49 raw id hits) or the
pre-PSP block `0x820000..0x8E0000`.

## Evidence class and limits

`observed-bytes` for hashes, offsets, decompressed bodies and the raw census;
`static-analysis` for the disassembly, the motif structure and the serializer mapping.
No hardware, emulation or runtime claim. Unrun here: emulation of the reader/lookup path;
enumeration of compressed non-PSP containers (V4); any identification of which caller
supplies the computed tag that would select `0x1363`/`0x1364`.

## Artifacts

- `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/verify_non_uefi_hits.py`
- `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/arm_slice_obj.py`
- `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/non-uefi-hit-classification.json`
- `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/non-uefi-hit-classification.{stdout,stderr}`
- `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/SHA256SUMS.root-verification`
