# CLV `$INV` record `0x1364` token ownership — producer-only in the UEFI module set

Scope correction: “producer-only” below means no **literal immediate requester for these token IDs** in the checked 233-module corpus. The later [container trace](20260920-clv-voltage-consumer-trace.md) located generic `$INV` readers, and the [2026-09-23 correction](2026-09-23-clv-voltage-token-correction.md) explicitly leaves computed/indirect paths open. Do not read the historical “no UEFI code path consumes” sentence as a global absence proof.

## Current

The newest action log left one offline item open: the consumer of `$INV` record
`0x1364` (`AmdSetup+0x6E6`, paired with control record `0x1363` / `AmdSetup+0x6E5`)
was unresolved after a bounded single-body caller inventory. This trace answers the
ownership question at corpus and image level.

## Result

**PRODUCER_ONLY_IN_MODULE_SET.** In the pinned CLV 5.00 image
(`ea578104…ca4cb8`), every one of the seven AmdSetup-to-`$INV` field records is
written by seven byte-identical inline serializer copies and has no direct literal
request, argument, or comparison in the checked 233-module UEFI extraction.

### Producer census (instruction rows, 233 modules)

All seven field records share the same seven producer modules, one site each:

| `$INV` record | `AmdSetup` field |
| ------------- | ---------------- |
| `0x11ED`      | `+0x316`         |
| `0x1204`      | `+0x330`         |
| `0x1331`      | `+0x6A3`         |
| `0x1363`      | `+0x6E5`         |
| `0x1364`      | `+0x6E6`         |
| `0x1373`      | `+0x703`         |
| `0x1374`      | `+0x704`         |

Producer modules and `0x1364` sites (RVA):

```text
AmdFabricAriPei   0x11956        AmdNbioBaseARIPei 0x12766
AmdNbioGfxARIPei  0xFB26         AmdNbioPcieARIPei 0x13276
AmdNbioSmuV10Pei  0x10476        AmdSocBl5AriPei   0x101B6
CbsBasePei        0xE3F6
```

`0x1363` sites are the same seven modules 0x32 bytes earlier
(`AmdFabricAriPei 0x11924`, `CbsBasePei 0xE3C4`, …).

Every site is the store form `mov edx,<token>`; each `0x1364` site is followed by
`66 89 10` (store the token word into the record), `80 ca 02` (low payload flag
`2` = 4-byte payload), `8b 82 e6 06 00 00` (copy `AmdSetup+0x6E6`), and each
`0x1363` site by the paired `8a 82 e5 06 00 00` read of `AmdSetup+0x6E5`.

This corrects the earlier wording "both exact serializers": there are **seven**
inline copies of the same serializer — the six AMD Fabric/NBIO PEIMs plus
`CbsBasePei` — not two.

### Request census (negative plus positive control)

Across all 233 modules: **0** immediate token-argument sites (`push <token>`) and
**0** `cmp`/`test` immediate sites for the seven field records. The same detector
finds request sites for other tokens, so the negative is an absence of checked literal requesters,
not a broken detector:

```text
push 0x1000 x14   push 0x1388 x11   push 0x10FF x1   push 0x1104 x1
```

The remaining textual mentions of these values (e.g. 47 mentions of `0x1364`) are
RIP-relative displacements and branch/call targets — address coincidences, not
token references (`call 0x1364`, `lea rdx,[rip+0x1364]`, `jne 0x1364`).

### Raw image census

The 32-bit little-endian encodings of `0x1363` and `0x1364` each occur **exactly
seven times** in the whole 16 MiB image, all with the identical producer
prefix/suffix (`83 c1 04 89 4d f8 ba` … `8b 45 f8`), and each occurrence
attributes to exactly one producer module:

```text
0xE2D4D7 AmdFabricAriPei    0xE671BF AmdNbioBaseARIPei   0xE99453 AmdNbioSmuV10Pei
0xE4C75B AmdNbioGfxARIPei   0xE818AB AmdNbioPcieARIPei   0xEB20AB AmdSocBl5AriPei
0xEC8483 CbsBasePei
```

No other literal occurrence exists in the image, so no data table holds these
records and no second code site references them.

## Verdict and consequences

`AmdSetup+0x6E5/+0x6E6` are serialized into `$INV` records `0x1363/0x1364` by seven
inline serializer copies and have no direct literal requester in the checked UEFI modules.
Combined with the earlier clock-field findings, the checked native Setup → `$INV`
field tokens are producer-only **at the literal-requester boundary**. Generic readers
exist, and a computed/indirect UEFI caller or a later runtime path remains possible;
the applied step has not been located.

Therefore:

- Do **not** describe a BIOS setting change of these fields as an applied voltage,
  clock, or rail target.
- Do **not** interpret `+150` as `1.15 V` (unchanged from the prior verdict).
- No candidate build, ROM write, or hardware action follows from this trace.

## Fresh bounded execution

```text
cd evidence/firmware-audit/20260920-clv-inv-token-ownership
PYTHONDONTWRITEBYTECODE=1 python3 -B verify_inv_token_ownership.py
```

Observed: exit `0`, stderr empty (`0` bytes), stdout `83347` bytes, 644 internal
checks passed. Independent cross-check on the text path (`grep` over the 235 exact
`.asm` texts, not the JSON rows) reproduces 7 producer modules / 0 request sites /
0 compare sites per token. Repository suite re-run:
`/home/OWNER/.local/bin/pytest -q tests/` → `30 passed`.

Input integrity note: the archive manifest verifies `952 OK / 1 FAILED`; the one
failure is the documentation entry `docs/research/2026-09-19-inv-token-consumers.md`
(edited 2026-09-19 19:21, after the manifest), not an extraction input. All 233
module bodies match `census.json`.

Evidence class: `observed-bytes` + `static-analysis`. No execution of firmware; no
ROM, NVRAM, register, hardware, source-input or candidate mutation.

## Limits

- A computed/indirect consumer or a 16-bit-encoded token use is not excluded by
  this trace; only immediate operands and literal 32-bit occurrences are.
- PSP/`$PS1`, ABL1, SMU/TOS and host-visible runtime paths were not searched.
- Record ownership says nothing about voltage semantics, rails, units, training,
  clock application or hardware behaviour.
- The per-module attribution of ROM occurrences uses FFS offsets from the existing
  census; no independent FFS walk was re-run.

## Inputs and hashes

- ROM `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes,
  SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Extraction `evidence/firmware-audit/20260919-inv-token-consumers/`:
  `census.json` (233 records), per-module `*.bin` and `*.instructions.json`,
  manifest `SHA256SUMS`.

## Artifacts

- Verifier: `evidence/firmware-audit/20260920-clv-inv-token-ownership/verify_inv_token_ownership.py`
  (SHA-256 `004bd876ad04eec1200daf4d7f34c6432011370321b7fc23f0087bfa48607531`).
- Machine result and literal stdout: `inv-token-ownership-result.json`,
  `verifier.stdout` (identical, SHA-256
  `262c9f3cd414e8da313a9a78c9517056b95932669812fc4942723335d17a2b31`),
  `verifier.stderr` (empty), `verifier.exit`.
- Action log: `docs/action-logs/2026-09-20-clv-inv-token-ownership.md`.

## Next decisive step

Search the non-UEFI carriers for the same token, starting with the ABL1
decompressed image and the `$PS1`/PSP black boxes, and treat a computed token load
(register/total-table derived) as the remaining in-UEFI alternative. Ground
compatibility with `1.15 V` remains a hardware gate on board `BC250-01`.

## Independent concurrent track — reconciliation

A sibling bounded track ran the same question in parallel through a different
method (`evidence/firmware-audit/20260920-clv-inv-1364-requester-scan/`, log
`docs/action-logs/2026-09-20-clv-inv-1364-requester-scan.md`) and reached the
same conclusion from the opposite direction: `NO_DIRECT_IMMEDIATE_REQUESTER_IN_EXACT_CORPUS`
— 14 immediate hits equal seven identical write-side emitter stubs at the same
RVAs this trace records, four RIP-relative `# 0x1364` address mentions, 47
branch-target mentions, `0x1363 -> 0x1364` pairs always at delta `0x32`, and no
data/table pair. No disagreement was found between the two routes.

That track additionally censused the _field-offset_ displacement form
(`[reg+0x6e5]` / `[reg+0x6e6]`): 32 sites in 9 modules, with `CbsBaseDxe` and the
same PEIMs zero-initializing the pair and `CbsSetupDxe` storing register values at
`rva 0x46cd`/`0x46d4`. That is Setup-structure field copying; it does not create a
reader of `$INV` record `0x1364` and does not change this verdict.

Consequence for routing: a repeated literal/immediate scan of the same UEFI corpus
is now exhausted by two independent methods. The next bounded step must leave that
corpus.
