# CLV `$INV`/NVTB non-UEFI carrier trace — bounded negative, container reader located

Scope clarification: `NO_NON_UEFI_CONSUMER_IN_CLV_IMAGE` below is the historical machine verdict for **visible `$INV`/NVTB structures in raw and decoded payloads examined here**. This report itself leaves opaque PSP bodies and computed tag flows unresolved; it cannot establish a global absence of voltage consumers.

## Current

The two prior offline tracks closed the _write_ side of the AmdSetup-to-`$INV` field
records and left the _read_ side open:

- `docs/research/20260920-clv-inv-token-ownership.md` — `PRODUCER_ONLY_IN_MODULE_SET`;
  the seven AmdSetup field records (`0x11ED`, `0x1204`, `0x1331`, `0x1363`, `0x1364`,
  `0x1373`, `0x1374`) are written by seven byte-identical inline serializer copies and
  are never requested by a literal id in the 233-module UEFI extraction.
- `docs/research/20260920-clv-inv-1364-requester-scan.md` —
  `NO_DIRECT_IMMEDIATE_REQUESTER_IN_EXACT_CORPUS`; the `0x1363 -> 0x1364` pair always
  occurs at delta `0x32`, i.e. always in the same emitter stub.

Both named the same next step: leave the 233-module UEFI corpus and search the non-UEFI
carriers (`$PS1`/PSP, ABL0-4, SMU, SEC_GASKET, TOS). This trace is that step. It answers
the carrier question and, as a by-product, locates the container reader that the
id-only scans could not see.

## Question

Does any non-UEFI carrier in the pinned CLV 5.00 image carry or read a `$INV`/NVTB
record container, and in particular the voltage-offset records `0x1363`
(`AmdSetup+0x6E5`, u8) and `0x1364` (`AmdSetup+0x6E6`, u32)?

## Method

Two read-only, deterministic tools over immutable pinned inputs; no ROM write, no
candidate build, no register/NVRAM/hardware action.

1. `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/scan_non_uefi_inv.py`
   — T1 pinned-input hashes, T2 whole-image `$INV` (`24 49 4E 56`) / `NVTB`
   (`4E 56 54 42`) marker census with PSP-entry / module / unattributed attribution,
   T3 whole-image u16 LE `0x1363`/`0x1364` census with alignment and context,
   T4 structural tests (id pair within 8 bytes; id preceded by the `0xFFFF` record
   terminator), T5 per PSP directory entry: locate the `$PS1` container, zlib-decompress
   the signed body when the container declares compression, and repeat the marker/id
   search inside the decompressed image.
2. `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/verify_non_uefi_inv_boundary.py`
   — V1 re-pin, V2 independent marker recomputation, V3 per-id carrier / `mod4` /
   distance to the nearest marker, V4 structural assertion, V5 cross-check against the
   T-scan result, plus a synthetic positive control and marker-context dump.

The discriminator is container adjacency: a structural `$INV` record cannot exist
without its `$INV` container magic, so a u16 id that is nowhere near a marker is a
coincidental value, not a record.

## Result

### R1 — bounded negative: no `$INV`/NVTB container outside the x86 UEFI FV region

`$INV` occurs 8 times and `NVTB` once in the whole 16 MiB image. All nine markers are
inside `0xE00000..0x1000000` (the x86 UEFI FV region); none is inside any of the 19 PSP
directory entries. Marker contexts are code-side _store_ forms of the producing PEIMs
(`c7 02 24 49 4E 56` = `mov dword [edx], 0x564E4924`, then
`24 49 4E 56 8b 45 f4 c7 40 04 01 00 00 00` = store magic + set the `+4` flag), not
container headers.

All five zlib-compressed `$PS1` bodies (ABL0-ABL4) were decompressed and re-searched,
and the eleven uncompressed `$PS1` bodies (TOS, SMU, SMU2, DEBUG_UNLOCK,
HARDWARE_IP_CONFIG, SEC_GASKET, DRIVER_ENTRIES, FW_XHCI, TOS_SECURITY_POLICY,
BL_PUBLIC_KEY, TOS_PUBLIC_KEY) were searched in place: **zero `$INV` and zero `NVTB`
markers in all 19 PSP payloads**.

The u16 encodings `0x1363`/`0x1364` occur 46 / 39 times raw. Only 8 / 7 of those are
inside the extracted module bodies (the seven producer stubs); the rest are
coincidental values in unrelated code, displacement bytes, or high-entropy data
(carriers: pre-PSP block `0x820000..0x8E0000` 3, `PSP_BOOTLOADER` 3,
`SMU_OFFCHIP_FW` 6, `DRIVER_ENTRIES` 2, `ABL1` 1, `ABL2` 1, `ABL3` 2, `ABL4` 1,
firmware region `0xAE0000..0xE00000` 49, UEFI FV region 17). The minimum distance from
any id occurrence to any `$INV`/NVTB marker is **39,025 bytes**; `0` occurrences lie
within 64 bytes of a marker. T4 found `0` id pairs within 8 bytes and `0` ids preceded
by a `0xFFFF` terminator. The synthetic positive control (`$INV` + u16 tag 6 bytes
apart) fires, so the adjacency test is not vacuous.

### R2 — the `$INV` container reader exists, and it is a generic tag lookup in the UEFI set

The marker census surfaced two modules that _test_ the container magic instead of
storing it. Reading the extracted module bodies and disassembly
(`evidence/firmware-audit/20260919-inv-token-consumers/`) gives the container reader:

| Module            | RVA      | Instruction                               | Role              |
| ----------------- | -------- | ----------------------------------------- | ----------------- |
| `AmdFabricAriPei` | `0x1D3C` | `cmp dword [esi], 0x564E4924` at `0x1DFC` | PEI reader/lookup |
| `AmdCcxVhAriDxe`  | `0x5AC4` | `cmp dword [rbx], 0x564E4924` at `0x5BBE` | DXE reader/lookup |

Both build an NVTB query (`mov ebx/esi, 0x4254564E` at `0x1D4D` / `0x5AE9`) and validate
a `0x55AA` sentinel at `+0x64` before checking the `$INV` magic. The decoded record
layout (static-analysis, from the shared control flow of both copies):

- container magic `$INV` at `+0x00`, records start at `+0x20`;
- record = `u16 tag` at `+0`, `u8 type` (low 2 bits) at `+2`, payload at `+3` of
  1 / 2 / 4 / 8 bytes for type 0 / 1 / 2 / 3;
- record size = `3 + payload` = `4 / 5 / 7 / 11` (the `push 4/5/7/0xb` size constants);
- the table ends at tag `0xFFFF` (`r13d = 0xffff`, `mov eax,0xffff`);
- the function compares each record tag with a caller-supplied tag and writes the
  decoded payload into the caller's buffer, returning `0` on match and `1` when the
  terminator is reached without a match.

Direct lookup call sites observed inside those two modules use tags `0x10FF` and
`0x1104` (`AmdFabricAriPei` `0x1EB0` / `0x1F8B` — the same two reader tokens already
recorded in `docs/research/20260920-clv-voltage-offset-consumer-boundary.md`) and
`0x1000` / `0x1001` (`AmdCcxVhAriDxe` `0x5CA0` / `0x5CEC`, in a function that also reads
MSR `0x1b` and `0xC0011029`). No call site anywhere in the image passes `0x1363` or
`0x1364` as an immediate.

A re-check of every u16 tag occurrence inside the 233 module bodies confirms that the
14 hits of `0x1363`/`0x1364` in the seven producer modules are all the byte-identical
stub `ba 63 13 00 00` / `ba 64 13 00 00` (`mov edx, imm32`) followed by
`8b 45 f8 66 89 10` (store the tag word into the record). The five remaining module
hits are RIP-relative displacement bytes or high-entropy data, not a tag table.

## Verdict

- `NO_NON_UEFI_CONSUMER_IN_CLV_IMAGE` — no **visible** `$INV`/NVTB container or
  structural `0x1363`/`0x1364` record was found outside the x86 UEFI FV region in the
  checked raw and decoded payloads. This excludes literal structures in those bytes,
  not an encrypted/opaque or computed consumer path.
- `CONTAINER_READER_LOCATED_IN_UEFI_SET` — the record consumer machinery is a generic
  tag lookup implemented in `AmdFabricAriPei` (PEI, RVA `0x1D3C`) and `AmdCcxVhAriDxe`
  (DXE, RVA `0x5AC4`).
- G7 clarification of the prior wording: `PRODUCER_ONLY_IN_MODULE_SET` is true for the
  _token ids_ (no literal requester exists), but it must not be read as "the container
  has no reader". The container does have readers; they address records by a
  caller-supplied tag, which is exactly why an immediate-id scan cannot find the
  voltage-offset record consumer. The consumer of `0x1363`/`0x1364` is a computed-tag
  caller and remains unlocated.

## Evidence class and limits

`observed-bytes` for the pinned hashes, marker/id offsets and decompressed payload
sizes; `static-analysis` for carrier attribution, the record layout and the reader
semantics. No hardware-verified claim is made; no voltage, rail, unit, clock,
synchronization or firmware-safety claim follows from this trace.

Untested / not excluded by this trace:

- `PSP_BOOTLOADER` (type `0x01`), `UNNAMED_TYPE_09` and `UNNAMED_RAW_TYPE_4F` are not
  `$PS1` containers, so their bodies were searched raw only; an encrypted or otherwise
  opaque body inside them cannot be excluded by a byte-level scan.
- Only the two reader modules' own call sites were enumerated. Callers reaching the
  lookup through a PPI/protocol, a computed tag, or a register-derived tag were not
  enumerated, and no data-side tag table was found for `0x1363`/`0x1364`.
- The reader semantics are inferred from control flow of the extracted modules; no
  emulation or runtime observation was performed.
- Board `BC250-01` was not contacted; the repository suite was re-run green
  (`30 passed`) and no firmware/NVRAM/register/hardware write occurred.

## Artifacts

- Scanner: `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/scan_non_uefi_inv.py`,
  result `non-uefi-inv-scan.json`, literal `non-uefi-inv-scan.stdout` / `.stderr`
  (empty), exit `0`. A deterministic re-run reproduced the result JSON identically
  (modulo the self-referential `output` path field).
- Boundary verifier:
  `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/verify_non_uefi_inv_boundary.py`,
  result `verify-non-uefi-inv-boundary.json`, stdout/stderr/exit captured.
- Action log: `docs/action-logs/2026-09-20-clv-voltage-consumer-trace.md`.
- Pinned inputs: donor `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
  (16,777,216 B, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`);
  PSP inventory `evidence/firmware-audit/20260920-clv-psp-abl-provenance/clv-psp-abl-inventory.json`
  (SHA-256 `7fab47054f8548c2bf5812ddc1ee649ec42a22184b4107fef75e210649c29f94`);
  233-module census `evidence/firmware-audit/20260919-inv-token-consumers/census.json`
  (SHA-256 `506b8eefd0ef3847782dddd88a458b95e32082f473346d7d645703dce6b60d39`).

## Next decisive step

Enumerate the callers of the two tag-lookup functions (`AmdFabricAriPei+0x1D3C`,
`AmdCcxVhAriDxe+0x5AC4`) across the image and classify each call argument: literal tag,
data-table tag, or computed/register-derived tag. A computed-tag caller that can reach
`0x1363`/`0x1364` is the last in-image candidate for the voltage-offset record consumer;
if none is found in that bounded caller set, the consumer edge remains unresolved;
opaque or other computed paths are not thereby excluded.

## Independent concurrent track — reconciliation

A sibling bounded track (`ds_voltage_consumer_trace`) answered the same question in
parallel and wrote `docs/research/2026-09-20-clv-voltage-consumer-trace.md`
(SHA-256 `8f6c6e2f…`, 5,219 B) plus `scan_inv_consumers.py`,
`inv-consumer-scan.json` and `non-uefi-hit-classification.json` in the same evidence
directory.

Agreement (independent method, independent code):

- Both tracks find `$INV` ×8 / `NVTB` ×1, all outside the PSP entries, and zero markers in
  all 19 PSP payloads including the decompressed ABL bodies.
- Both tracks identify the same two `$INV` reader RVAs (`AmdFabricAriPei` `0x1D3C`,
  `AmdCcxVhAriDxe` `0x5AC4`) and the same absence of a literal `0x1363`/`0x1364` caller.
- Both tracks find `0` `(0x1363, 0x1364)` pairs within 8 bytes and `0` ids preceded by
  `0xFFFF`.

Preserved disagreement — record-to-field mapping:

- The sibling report maps `0x1364` to `VDDCR_GFX_OFFSET` / `AmdSetup+0x6EA/+0x6EB`.
- The pinned prior table in `docs/research/20260920-clv-inv-token-ownership.md` maps
  `0x1363 -> +0x6E5`, `0x1364 -> +0x6E6`, `0x1373 -> +0x703`, `0x1374 -> +0x704`, and the
  serializer stub bytes (`8b 82 e6 06 00 00` = read `+0x6E6` next to the `0x1364` store)
  support the pinned table. This trace therefore keeps `0x1364 = AmdSetup+0x6E6` and does
  not adopt the `+0x6EA` mapping; the conflict needs a root-side check of the `0x6EA/+0x6EB`
  record id before either mapping is used in a recipe.

Scope note: the sibling report's stronger wording ("zero consumers", "inert placebo",
"no mechanism exists") is not adopted here. The static evidence bounds literal and
container-adjacent references only; a computed-tag caller of the two lookup functions and
the opaque type `0x01`/`0x09`/`0x4F` bodies remain untested, so the consumer edge is
`not located`, not `proven absent`.
