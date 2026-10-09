# CLV `$INV` 0x1363/0x1364 requester scan — exact corpus (bounded)

## Current

Exact-corpus scan over `evidence/firmware-audit/20260919-inv-token-consumers/` (233 PE32
modules + pinned clv ROM) resolved the write side completely and left the read side open:
all 14 immediate operand occurrences of `0x1363`/`0x1364` are the same write-side emitter
stub, so no **direct immediate** reader/requester of record `0x1364` was found in this corpus. The consumer
edge stays computed/indirect/HOB/runtime.

## Question

The superseded bounded result
(`docs/research/20260920-clv-voltage-offset-consumer-boundary.md`, SHA-256
`be7a4eeb40e5bd4a0afe84c79fa75731e7e370216fece5b6d4679802eb03d845`) established that
`AmdSetup+0x6E5` is serialized as `$INV` record `0x1363` (u8) and `AmdSetup+0x6E6` as
`$INV` record `0x1364` (u32, 4-byte payload). It bounded the reader inventory to
`AmdFabricAriPei` only. This scan asks the corpus-wide question: does any module carry a
direct immediate requester of `0x1364` / `0x1363`?

## Method

`evidence/firmware-audit/20260920-clv-inv-1364-requester-scan/scan_inv_1364_requesters.py`
(read-only, deterministic, no firmware/NVRAM/register/hardware write):

- **T1 pinned inputs** — clv ROM SHA-256 pin, plus the corpus `SHA256SUMS` manifest
  (951 corpus-local entries verified).
- **T2 instruction scan** — every instruction operand in all 233 `.instructions.json`
  files, full-token regex `(?<![0-9a-fA-F])0x1363|0x1364\b`, classified
  immediate / memory-reference / branch-or-call, cross-checked against the `.asm`
  text as an independent surface (asserted equal for the immediate class).
- **T3 adjacent constants** — alignment-free search for u16 LE `0x1363` followed
  within 64 bytes by u16 LE `0x1364` (forward and reverse).
- **T4 config-offset scan** — operand occurrences of `0x6e5`/`0x6e6`, classified into
  config-displacement (register+offset, read vs write), rip-relative address, branch target.

## Result

- **T2** — `14` immediate hits, forming `7` identical emitter stubs, each shaped
  `mov DWORD PTR [ebp-0x8],ecx` / `mov edx,<id>` / `mov eax,DWORD PTR [ebp-0x8]`:
  `AmdFabricAriPei` `rva 0x11924`/`0x11956`, `AmdNbioBaseARIPei` `0x12734`/`0x12766`,
  `AmdNbioGfxARIPei` `0xfaf4`/`0xfb26`, `AmdNbioPcieARIPei` `0x13244`/`0x13276`,
  `AmdNbioSmuV10Pei` `0x10444`/`0x10476`, `AmdSocBl5AriPei` `0x10184`/`0x101b6`,
  `CbsBasePei` `0xe3c4`/`0xe3f6` (first `rva` = `0x1363`, second = `0x1364`).
  The `4` memory-reference hits are rip-relative address references
  (`AmdCpmInitDxe`, `AmiApcbLibInterface` ×2, `RuntimeDxe`) whose comments merely read
  `# 0x1364`; the `47` branch-or-call hits are branch targets such as `call 0x13641`.
  No direct literal compare/read of the token id appears in the checked instruction corpus; computed and indirect uses were not excluded.
- **T3** — `7` forward pairs inside the pinned ROM and exactly `1` forward pair in each of
  the same 7 modules; every pair delta is `50 (0x32)` bytes; zero reverse pairs, zero
  data/table pairs. The ROM hits are the same seven code stubs, not a separate table.
- **T4** — `32` config-displacement hits in `9` modules. `CbsBasePei` and the six `Amd*`
  PEIMs read the source pair (`mov al,BYTE PTR [edx+0x6e5]`, `mov eax,DWORD PTR [edx+0x6e6]`)
  inside the same emitter stubs that carry the immediates. `CbsBaseDxe` and those same
  modules also zero-initialize `+0x6e5`/`+0x6e6` (`mov BYTE PTR [...+0x6e5],0x0`,
  `mov DWORD PTR [...+0x6e6],0x0`). `CbsSetupDxe` writes register values into the pair
  (`mov BYTE PTR [rcx+0x6e5],r8b`, `mov DWORD PTR [rcx+0x6e6],r8d`) at `rva 0x46cd`/`0x46d4`.
  The remaining `15` offset hits are branch targets or rip-relative addresses.

## Verdict

`NO_DIRECT_IMMEDIATE_REQUESTER_IN_EXACT_CORPUS`. Every occurrence of `0x1363`/`0x1364` in
this 233-module corpus is write-side: an `$INV` record emitter that reads the
`AmdSetup+0x6E5/+0x6E6` pair. No module tests, compares, or indexes the record id through a checked direct literal operand.
The value/consumer edge may involve a computed, indirect, HOB or later runtime
path; this scan does not locate it.

Refinement of the superseded report (not a contradiction of its serializer bytes): the
identical emitter shape exists in seven modules, and the config pair at `+0x6E5`/`+0x6E6`
is present in nine modules, so the pair is a shared AmdCpm-style record, not a
`CbsBasePei`-only artifact. No consumption of the emitted record is visible in the corpus.

The signed-offset interpretation is still limited to: "a hidden native Setup u32 request
serialized unchanged as `$INV 0x1364`, paired with control `0x1363`". Physical rail identity,
numeric conversion, SoC target voltage, and applied hardware effect remain unestablished.
No `+150 => 1.15 V` mapping, no rail identity, no hardware or firmware mutation.

## Fresh bounded execution

- `python3 evidence/firmware-audit/20260920-clv-inv-1364-requester-scan/scan_inv_1364_requesters.py`
  → exit `0`; stdout SHA-256 `5e87d374b6080ddfe32d781565a624e97e053150ed144251845f60eef27a24b2`;
  stderr empty (SHA-256 `e3b0c442...`). Re-run produced byte-identical stdout
  (`scan.rerun.stdout`), so the scan is deterministic.
- Pinned prior verifier re-run as a reproducibility check:
  `python3 evidence/firmware-audit/20260920-clv-voltage-offset-consumer-boundary/verify_voltage_offset_boundary.py`
  → exit `0`, stderr empty, stdout SHA-256 `4026f8cebb814fc11fddb58eb5f5fd4e1e41fc878dbba3d3745161ddb7667bd3`,
  and `voltage-offset-boundary-result.json` unchanged (byte-identical, SHA-256
  `4026f8cebb814fc11fddb58eb5f5fd4e1e41fc878dbba3d3745161ddb7667bd3`).

## Inputs and hashes

- `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` — 16777216 bytes, SHA-256
  `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- `evidence/firmware-audit/20260919-inv-token-consumers/` — 233 `.bin` +
  233 `.instructions.json` + `.asm`; 951 corpus-local `SHA256SUMS` entries verified.
- Observed manifest drift, recorded not resolved: `SHA256SUMS` line for
  `docs/research/2026-09-19-inv-token-consumers.md` expects
  `d531226fb248bf4bdef9ce7392d0a7a8d1a302d577f7a3681733cf60e2ef1289`, file on disk hashes
  `5e3e50fb6aa9f72514b2674562c45839874ba9d7c305f110ffeff30dd091d6e4`. Outside this scan's
  scope; does not affect module-corpus pins.

## Artifacts

- Verifier: `evidence/firmware-audit/20260920-clv-inv-1364-requester-scan/scan_inv_1364_requesters.py`
- Machine result: `evidence/firmware-audit/20260920-clv-inv-1364-requester-scan/requester-scan-result.json`
- Literal stdout/stderr/exit: `scan.stdout` / `scan.stderr` / `scan.exit`, determinism pair
  `scan.rerun.stdout` / `scan.rerun.exit`, prior-verifier rerun
  `pinned-verifier-rerun.stdout` / `.stderr` / `.exit`
- Hash pin: `evidence/firmware-audit/20260920-clv-inv-1364-requester-scan/SHA256SUMS.final`
- Action log: `docs/action-logs/2026-09-20-clv-inv-1364-requester-scan.md`

## Open question

Q1: Where is `$INV` record `0x1364` consumed at runtime? The corpus holds only the emitter.
The next bounded step is a HOB/APCB/runtime-side search (for example the DF/APCB consumer
path or the ABL/SMU side), not a repeated x86 literal scan of the same corpus.
