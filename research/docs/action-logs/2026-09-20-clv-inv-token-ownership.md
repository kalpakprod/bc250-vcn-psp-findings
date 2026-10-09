# $INV record 0x1364 token ownership census — intent

Timestamp: 2026-09-20 (Asia/Almaty). Actor: root.

Trigger: continuation turn with no new operator instruction. The newest recorded
action log (`docs/action-logs/2026-09-20-clv-fd-drivers-reverify.md`) closed the
candidate-verification and repository-pytest items and left exactly one offline
item open: "The consumer of `$INV` record `0x1364` remains unresolved from the
prior bounded static trace." The board item in the same log (`BC250-01`
unreachable) stays a hardware gate.

Bound object (TARGET): pinned CLV donor ROM
`evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
(SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`)
and the existing exact 233-module UEFI extraction plus per-instruction rows under
`evidence/firmware-audit/20260919-inv-token-consumers/`.

Hypothesis: `$INV` record `0x1364` (AmdSetup+0x6E6) is producer-only in the UEFI
module set. If so, no immediate token reference other than the producer stores
exists anywhere in the pinned image, and the applied consumer must be outside the
UEFI extraction (PSP/ABL1/SMU/runtime) or use a computed token.

Method class change (G6): the prior bounded trace inventoried immediate callers of
one generic `$INV` reader inside a single module body. This trace instead runs a
corpus-wide instruction-row census over all 233 exact modules plus a 16 MiB
raw-byte census of the pinned ROM, with an explicit positive control (tokens that
do have request sites).

Bounded acceptance:

1. Pinned-input re-verification: ROM size/hash; 233 module body digests; presence
   of the per-module instruction rows.
2. Producer census for the seven AmdSetup field records
   `0x11ED 0x1204 0x1331 0x1363 0x1364 0x1373 0x1374`: exact module set, exact
   RVA per site, and the producer store structure for `0x1363`/`0x1364`.
3. Request census: immediate token arguments (`push <token>` call sites) across
   all 233 modules; positive control on tokens known to be requested.
4. Raw ROM census: occurrences of the 32-bit little-endian token encodings, with
   per-FFS attribution for every occurrence.
5. Stop at indirect/computed token use. No new parser framework, no module-wide
   semantic hunt, no ROM/NVRAM/register/hardware/candidate mutation.

Expected result: `PRODUCER_ONLY_IN_MODULE_SET` with an exact occurrence map, or an
exact located consumer. No voltage, rail, clock, unit or hardware claim.

Rollback: remove only this action log, the unique
`evidence/firmware-audit/20260920-clv-inv-token-ownership/` directory, and the
matching research report; archive inputs stay untouched.

## Observed result

Timestamp: 2026-09-20 (Asia/Almaty). Verifier execution exited `0`; stderr empty
(`0` bytes); stdout `83347` bytes, identical to the written result JSON.

Status: `PRODUCER_ONLY_IN_MODULE_SET`; 644 internal checks passed.

- Pinned inputs re-verified: ROM `16777216` bytes /
  `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; all 233
  module body digests match `census.json`; the archive manifest
  `evidence/firmware-audit/20260919-inv-token-consumers/SHA256SUMS` verifies
  `952 OK / 1 FAILED`, and the single failure is a documentation entry
  (`docs/research/2026-09-19-inv-token-consumers.md`, edited 19:21 on 2026-09-19,
  after the 19:00 manifest), not an extraction input. No module body failed.
- Producer census: for every one of the seven AmdSetup field records
  (`0x11ED→+0x316`, `0x1204→+0x330`, `0x1331→+0x6A3`, `0x1363→+0x6E5`,
  `0x1364→+0x6E6`, `0x1373→+0x703`, `0x1374→+0x704`) the token appears as a bare
  immediate in exactly the same seven modules, one site each:
  `AmdFabricAriPei`, `AmdNbioBaseARIPei`, `AmdNbioGfxARIPei`, `AmdNbioPcieARIPei`,
  `AmdNbioSmuV10Pei`, `AmdSocBl5AriPei`, `CbsBasePei`. Each site is the
  `mov edx,<token>` store form; the `0x1364` sites additionally carry the exact
  producer sequence `66 89 10` (store token word), `80 ca 02` (4-byte payload
  flag), `8b 82 e6 06 00 00` (copy `AmdSetup+0x6E6`), and the `0x1363` sites the
  paired `8a 82 e5 06 00 00` read of `AmdSetup+0x6E5`.
  G7 correction to the prior wording: the trace recorded "both exact
  serializers"; there are seven byte-identical inline copies of this serializer
  in the pinned image, not two.
- Request census over all 233 modules: zero immediate token-argument sites
  (`push <token>`) and zero `cmp`/`test` immediate sites for all seven field
  records. Positive control on the same detector: `push 0x1000` ×14,
  `push 0x1388` ×11, `push 0x10FF` ×1, `push 0x1104` ×1.
- Raw ROM census: the 32-bit little-endian encodings of `0x1363` and `0x1364`
  each occur exactly 7 times in the whole 16 MiB image, all carrying the
  identical producer prefix/suffix (`83 c1 04 89 4d f8 ba` … `8b 45 f8`), and each
  occurrence attributes to exactly one of the seven producer modules
  (`0xE2D4D7`→`AmdFabricAriPei`, `0xE4C75B`→`AmdNbioGfxARIPei`,
  `0xE671BF`→`AmdNbioBaseARIPei`, `0xE818AB`→`AmdNbioPcieARIPei`,
  `0xE99453`→`AmdNbioSmuV10Pei`, `0xEB20AB`→`AmdSocBl5AriPei`,
  `0xEC8483`→`CbsBasePei`). No other literal occurrence exists.
- Independent cross-check (text path, not the JSON rows): `grep` over the 235
  exact `.asm` texts gives 7 producer modules, 0 request sites and 0 compare
  sites for each of the seven tokens.
- Repository suite re-run: `/home/OWNER/.local/bin/pytest -q tests/` →
  `30 passed in 1.70s` (exit `0`).

Boundary: no UEFI consumer or requester of `$INV` record `0x1364` exists in the
exact clv UEFI extraction, and no other literal `0x1364`/`0x1363` reference exists
anywhere in the pinned image. A computed/indirect or 16-bit-encoded consumer is
not excluded, and PSP/`$PS1`, ABL1 and SMU/TOS were not searched. No voltage,
rail, unit, clock, synchronization or hardware claim follows.

## Final artifact readback

Report: `docs/research/20260920-clv-inv-token-ownership.md`.
Verifier: `evidence/firmware-audit/20260920-clv-inv-token-ownership/verify_inv_token_ownership.py`,
SHA-256 `004bd876ad04eec1200daf4d7f34c6432011370321b7fc23f0087bfa48607531`.
Machine result / literal stdout:
`evidence/firmware-audit/20260920-clv-inv-token-ownership/inv-token-ownership-result.json`
and `verifier.stdout`, both SHA-256
`262c9f3cd414e8da313a9a78c9517056b95932669812fc4942723335d17a2b31`.
Literal stderr SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`;
exit file SHA-256 `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`.

Final status `PRODUCER_ONLY_IN_MODULE_SET`. No ROM, NVRAM, register, hardware,
source-input or candidate mutation occurred.

Supplemental readback: report `docs/research/20260920-clv-inv-token-ownership.md`,
SHA-256 `cb222cb9440fb3ae2c61e37cf7bffcd60ba542fb240af32350b3a78ed400cff5`.
Interpretation note: the non-immediate occurrences of these values in unrelated
modules are RIP-relative displacements and branch/call targets (for example
`AmiApcbLibInterface 0xF16: mov rax,QWORD PTR [rip+0x1363] # 0x2280`,
`EbcDxe: jne 0x1364`); they are recorded as address coincidences, not token reads.

Reconciliation with an independent concurrent track: the sibling bounded scan
`evidence/firmware-audit/20260920-clv-inv-1364-requester-scan/`
(`NO_DIRECT_IMMEDIATE_REQUESTER_IN_EXACT_CORPUS`) reached the same conclusion as
this census from a different method — its 14 immediate hits are the same seven
write-side emitter stubs at these RVAs, and its field-offset census
(`[reg+0x6e5]`/`[reg+0x6e6]`, 32 sites in 9 modules) covers Setup-structure field
copying, not a reader of `$INV` record `0x1364`. No disagreement; two independent
routes agree that the same-corpus literal scan is exhausted.

Final readback supersedes the earlier report hash line: the report gained the
reconciliation section, so its current SHA-256 is
`4fa011cee72be6537d88aa7025ca15c70833d5f8c71fa13613e526a0bf247675`
(`docs/research/20260920-clv-inv-token-ownership.md`). Verifier
`004bd876ad04eec1200daf4d7f34c6432011370321b7fc23f0087bfa48607531`, machine result
and literal stdout `262c9f3cd414e8da313a9a78c9517056b95932669812fc4942723335d17a2b31`
(byte-identical from a second run started in `/tmp`), stderr empty, exit `0`. This
journal file is not self-pinned.
