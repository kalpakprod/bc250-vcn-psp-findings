# CLV APCB/ABL/APOB/INV interface provenance — action log

## Intent (before write)

- Timestamp: 2026-09-20 Asia/Almaty
- Actor: independent reviewer, continuation checkpoint
- Target: immutable clv ROM `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Scope: distinguish actual APCB, ABL/PSP/APOB, PPI, `$INV`, and `InstallPeiMemory` inputs/outputs using existing parser/extraction evidence and exact instruction records. Do not duplicate default semantics or generic ABL source correlation.
- Existing routes reused: `scripts/firmware_audit.py`, `scripts/apcb_detail.py`, exact-clv extracted module instruction records under `evidence/firmware-audit/20260919-inv-token-consumers/`, and stage-1 extraction metadata.
- Hypothesis to discriminate: persisted `AmdSetup`/`$INV` records may be serialized but the bounded memory-HOB path may instead select an APOB/PPI-provided structure before permanent-memory installation; a byte-backed input/output boundary can qualify why a stored setting might be ignored without claiming runtime precedence.
- Expected effect: create a machine-readable read-only interface report with exact hashes/offsets/instruction windows and a research report; no ROM, hardware, settings, shared MCP, or candidate write.
- Rollback: remove only newly created evidence/report files; immutable input and existing evidence remain unchanged.
  ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8 evidence/donor/retroweb-20260916/BC250_5.00_clv.bin

## Observed result after write

- Existing parsers executed on immutable clv: `firmware_audit.py` exit `0`; `apcb_detail.py` exit `0`.
- Interface checker exit `0`: `32/32 PASS`.
- Concrete boundary: APCB DFG/checksum parsed from flash; `CbsBasePei` emits `$INV 0x11ED`; `AmdMemAm4Pei` requests APOB service `0x9E3B14C/0x61/0xFF` and validates APOB/$PSP/$BHD; `AmdMemoryHobInfoPeim` consumes PPI fields and calls `InstallPeiMemory`.
- Qualification: no direct Setup/INV read in the bounded memory-HOB consumer; no APCB-to-APOB merge edge or runtime precedence claim.
- Worker review reopened: defaults static GetVariable precedence; ABL source-anchor mismatch means no direct source bind map; CCX reader is CPU MSR branch only.
- Readback hashes:
  0c5337d9c3e4559079b502ee69ce2a9e3041a0cee62693401ea558d9b98fe81a docs/research/20260920-clv-apcb-abl-apob-interface.md
  73ea48688e988222a6046f5f1a38cc98b33a029566a4c37d69a04dcdd3efd42f evidence/firmware-audit/20260920-clv-apcb-abl-apob-interface/apcb-abl-apob-interface-result.json
  1f2744f3e55ac31087a4c05f28ab3d95ca98d81b0bfa2906dcda956d15bff1f4 evidence/firmware-audit/20260920-clv-apcb-abl-apob-interface/apcb_abl_apob_interface_verify.py
- Remaining uncertainty: exact PPI GUID/provider identity, APOB service conversion, INV-to-APOB indirect path, memory-training actuator, runtime and hardware behavior.
- Rollback: remove only this owned report/evidence set; immutable clv and existing artifacts unchanged.

## Integration intent amendment (before shared writes)

- Targets: append-only sections in `specs/2026-09-20-clv-sync-development-plan.md` and `memory/oc-recheck.md`.
- Scope: record only the verified APCB/ABL/APOB/INV boundary and worker review; preserve phase-2 `PARTIAL` and all runtime/training gates.
- Required limits: no APCB-to-APOB merge claim, no runtime precedence, no training/clock claim, no source/binary ABL identity claim.
- Rollback: remove only the two appended sections.

## Integration observed result

- Shared plan and memory received append-only qualified config-source boundary sections.
- Phase 2 remains `PARTIAL`; no consumer/training/runtime/hardware gate was completed.
- Readback hashes after integration:
  eb9daecf430204c22f3b193b15f6dc7ccf2c5822208a148cf769dff9275da301 specs/2026-09-20-clv-sync-development-plan.md
  e7607c171194b21d405596ed75589c8f57df3b7ba9bbdc9b91dc93b47e20418e memory/oc-recheck.md
- Rollback: remove only the two appended sections; prior evidence and historical corrections remain.

## Fabric/HOB final review intent (before write)

- Scope: independently reopen the exact Fabric reader result and direct instruction bytes, and recheck `AmdMemoryHobInfoPeim` IA32 PEI service pointer/slot `+0x44` against the existing EDK II service layout. Review return-value use/IDS ownership only; do not infer transitive clock or MMIO effects.
- Expected result: preserve the Fabric `0x10FF/0x1104` CPU/config boundary and the APOB/PPI `InstallPeiMemory` distinction; current targets `0x1331/0x1204/0x123C` remain unresolved.
- No ROM, hardware, settings, shared MCP, plan, memory, or candidate modification is intended by this bounded review.

## Fabric/HOB final review observed result

- Reran worker Fabric verifier: `19/19 PASS`; independent reviewer checker: `32/32 PASS`.
- Verified return-value use for tokens `0x10FF/0x1104` and IDS mapping `0x20000003 -> 0x1E8F`, `0x20000004 -> 0x1F6D`; no direct WRMSR/in/out in complete checked parent slices.
- Reopened `AmdMemoryHobInfoPeim`: `0x269 ESI=EAX`, `0x26B EAX=[ESI]`, `0x299 call [EAX+0x44]`; source slot layout confirms `+0x44=InstallPeiMemory`.
- Transitive AGESA/IDS helper MMIO and current targets `0x1331/0x1204/0x123C` remain unresolved.

## Fabric/HOB integration intent (before shared writes)

- Append only the bounded Fabric return-value and PEI slot correction to the shared plan/memory. Preserve phase-2 `PARTIAL`; do not claim hardware, training, or clock semantics.
- Rollback: remove only the two appended sections.

## Exact ABL1 function review intent (before write)

- Scope: independently re-run exact ABL1 payload hash and Thumb-2 decoding for the memory-speed function, verify little-endian raw prologue/dataflow/minimum/writeback bytes, and preserve the distinction between structural memory policy and MCLK/UCLK/FCLK synchronization.
- Input: exact decompressed ABL1 payload SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Expected effect: create a bounded independent review artifact; no ROM, hardware, settings, shared MCP, plan, or memory change during byte verification.
- Limits: do not reuse historical source addresses as a flat map; do not infer MHz units or 1:1:1 behavior.

## Exact ABL1 memory-function review observed result

- Reran worker ABL function verifier: `27/27 PASS`.
- Independent raw/Thumb review: `20/20 PASS`; payload hash `af8cf5626a113afe72bc0687ca6f1a3b44ec34312cf385b0be011e063b1aa691`? (see correction below).
- Correct exact payload SHA-256: `af8cf5626a113afe72bc0687ca6f1a3b44ec34312cf385b0be011e063b1aa691` is historical worker mismatch? No: exact current ABL1 payload SHA-256 is `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`; the owned review checked this value.
- Raw prologue/dataflow checks confirm Thumb-2 prologue, per-channel input/store, lower-value reduction, and writeback. No AmdSetup/INV input edge, MHz unit, UCLK/FCLK relation, or 1:1:1 claim.
- Readback report/result/action log completed; no ROM/hardware/settings change.

## ABL1 review integration intent (before shared writes)

- Append only the verified structural ABL1 memory-policy result to shared plan/memory. Preserve all unresolved caller/provider/unit/training/hardware gates.
- Rollback: remove only the two appended sections.

## G7 correction to ABL1 review log

- The previous result bullet contained a mistaken historical hash in explanatory text. It is superseded by the immediately following exact value and by the machine result: the checked payload SHA-256 is `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.

## Final ABL1 integration observed result

- Shared plan/memory append-only integration completed; phase-2 `PARTIAL` preserved.
- ABL1 review remains structural only; no caller/provider, unit, synchronization, training, or hardware gate completed.
- Readback hashes after integration:
  36061dce485f0a91b77d4c5c7028b70a39a636ca8e55bd24dff8a924b8dd1a49 specs/2026-09-20-clv-sync-development-plan.md
  dbf409d11fa93786f74c39b0ff7d693f5f5b317b2f0ca6c84b6c5ea6078d3514 memory/oc-recheck.md
- Rollback: remove only the appended ABL1 review sections.

## ABL1 function-boundary correction intent (before write)

- The worker disassembly window stops at `0x9870`; independent decoding shows code continuation through `0x98AA` and a code-to-data transition at `0x98AC` (`"AGESA MEM..."`).
- Extend the owned review only to verify this exact boundary and preserve branch/dataflow semantics. No broader ABL search or physical-domain inference.

## ABL1 function-boundary review observed result

- Independent payload/header check: exact container `95ae7826a69ea56b8c52ac703b85f181d45bdc309de334c2b7f9f4130376d515`, decompressed payload `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`, header `load_address=0`, length `0x171A0`.
- ARM entry at payload `0x0` loads literal target `0x0005E02D` and `BLX`es outside the decompressed payload; no physical runtime address is inferred.
- Independent Thumb decode extends the function to `0x98AB`; raw string data begins `0x98AC`. The worker's `0x9870` window is incomplete but its internal match remains valid.
- Register contract observed: `R0 -> [R0]` context (`R4`), caller-supplied `R5` outer structure, per-channel table row via `R1=R4+(index<<2)`. No caller/provider or physical domain inferred.
- Independent checker: `26/26 PASS`.
- Correction: prior log hash text is superseded by current owned report/result hashes below.
  42fa15939c387bab92a9f87dbe941dbba9480248ebd5e677ae521707d08ed3ac docs/research/20260920-clv-abl-memory-review.md
  6006c96b182611609ed6998b5a3109d30f1cdb34342e3dfedbbf44b1fbed0eae evidence/firmware-audit/20260920-clv-abl-memory-review/abl1-memory-review-result.json
  5bc21719736ca81e46517281f6013be556b758a14255949a1fd6a13fbbdba66b evidence/firmware-audit/20260920-clv-abl-memory-review/abl1_memory_review_verify.py

## ABL1 boundary integration observed result

- Shared plan/memory append-only integration completed; phase 2 remains `PARTIAL`.
- Exact payload-relative base/function boundary and external entry trampoline qualification recorded.
- No consumer/training/clock/hardware gate completed.
- Readback hashes after integration:
  baf2ef1dc53602cb011762f46763e3c8aae072cea9fbbe175ef413144f641f3e specs/2026-09-20-clv-sync-development-plan.md
  47bf138a56f456efa38d3d11f51ae87401310864513674bcb3e865d58eeeea6d memory/oc-recheck.md

## ABL1 address/loop review observed result

- Independent exact header/entry/Thumb checker: `25/25 PASS`.
- ABL1 `$PS1 load_address=0`, `rom_size=0xC020`, decompressed length `0x171A0`; ARM entry literal `0x0005E02D` is outside payload, so physical runtime base is not inferred.
- Function code extension: `0x95FC..0x98AB`; data begins at `0x98AC`. Outer bound is `[R5+0x4B]`; callback `[R5+0x52C] (R5,index)` precedes `[R5+0x0C]+0x20`; later bound `[[R4+0x3C4]+0x74]` drives reduction/writeback loops.
- Strings mention Channel/MEMCLK/P-state but do not establish field semantics or physical domain.

## ABL1 address/loop integration intent (before shared writes)

- Append only the verified payload-relative entry/function-boundary and loop-semantic qualification to plan/memory; no runtime-base, channel/P-state, unit, or physical-domain claim.
- Rollback: remove only the appended sections.

## ABL1 address/loop integration observed result

- Shared plan/memory append-only integration completed; phase 2 remains `PARTIAL`.
- No runtime base, channel/P-state semantic, clock, training, or hardware gate completed.
- Final readback hashes:
  dcb541247c31a642c5d160058448be2dd20fd18f0a8d95f254ace5a17a8f5ea5 docs/research/20260920-clv-abl-address-loop-review.md
  04a1086be29f6297461d90ecaa9865d5d74747371ccd2860510967dc94e87227 evidence/firmware-audit/20260920-clv-abl-address-loop-review/abl1-address-loop-result.json
  c6362cfa6eba7920aed116e1c32630ac6a4b08b92009e73db645a56b9295c69c docs/action-logs/2026-09-20-clv-apcb-abl-apob-interface.md
  edb53915c92ed6975baa9dfc8a640a5577855c63dfa96774efbd2b0bb43e1617 specs/2026-09-20-clv-sync-development-plan.md
  dfaed049291e4d68402326352efb6963f4ac40af3ee87e37a656daf898e69a55 memory/oc-recheck.md

## ABL1 aggregate-consumer classifier review intent (before write)

- Scope: independently verify aggregate root provenance, selector flow, classifier full semantics, eight-entry loop/no-match behavior, and table pointer/raw availability. Do not infer units or physical clock identity.
- No ROM, hardware, settings, shared MCP, plan, memory, or candidate modification is intended by this bounded review.

## ABL1 aggregate classifier review observed result

- Worker downstream verifier rerun: `16/16 PASS`.
- Independent classifier/root review: `14/14 PASS`.
- Aggregate provenance: `0x75CC r0->r6`, `0x7E3E [r6]`, `0x7E40 [root+0x2BC]`, selector `[sp+0x20]` at `0x7E44`, aggregate passed as `r1` at `0x7E52`.
- Classifier `0x751C` scans exactly 8 external halfword entries, converges match/no-match to selector branch, returns class 7 iff selector is 6, otherwise class 0; table pointer literal `0x6DB04` is outside payload, so raw table values are unavailable.
- No units, physical domain, clock, synchronization, or hardware claim.

## ABL1 aggregate integration intent (before shared writes)

- Append only the verified classifier semantics and external-table limitation to shared plan/memory; preserve phase-2 `PARTIAL`.
- Rollback: remove only the appended sections.

## ABL1 aggregate integration observed result

- Shared plan/memory append-only integration completed; phase 2 remains `PARTIAL`.
- No clock/unit/synchronization/training/hardware gate completed.
- Final readback hashes:
  63174c7232351044af528205893537b2b60cb8963ae6164d9317101257afab2e docs/research/20260920-clv-abl1-aggregate-review.md
  a0f69ced2b24295b109562278c1717ae256c4dfaa7007e3ac828032d92ac6973 evidence/firmware-audit/20260920-clv-abl1-aggregate-review/abl1-aggregate-review-result.json
  4ffa1945d5adb4fcbb12c565eb729336eadf451e8352f7c30f2e7c3ee79825a8 docs/action-logs/2026-09-20-clv-apcb-abl-apob-interface.md
  28be8fdb0c17135c4a82be1654f2c28fc2189510d285a1e8df75183d924bce71 specs/2026-09-20-clv-sync-development-plan.md
  1adce5ca4a194aff3543653d42eb77695d93dfb071b90c38cdc472a32fc7fa1e memory/oc-recheck.md

## ABL1 relocation-coherence review intent (before write)

- Scope: test bounded candidate load base `0x60000` against three independent PC-relative literal/string/pointer anchors and the exact `$PS1` header, without promoting any base from one hit.
- Required qualification: table pointer `0x6DB04` may map to payload `0xDB04`, but callback pointer `0x67ABD` must also map to callable code; if it maps to data, reject `0x60000` as universal base. Preserve payload-relative offsets.
- No firmware, hardware, settings, shared MCP, plan, memory, or candidate modification is intended.

## ABL1 relocation-coherence observed result

- Independent candidate test: `15/15 PASS`.
- Candidate base `0x60000` maps table literal `0x6DB04` to payload `0xDB04` with 8 structured halfwords, but maps callable callback literal `0x67ABD` to payload `0x7ABD` ASCII data (`lock Speed...`); universal base is falsified.
- PC-relative string anchor `0x8188 -> 0x820C` confirms internal payload relationship only; actual runtime/loader base remains unknown.
- No units, clock, synchronization, training, or hardware claim.

## ABL1 relocation-coherence integration intent (before shared writes)

- Append only the verified falsification of candidate base `0x60000` and provisional table limitation. Preserve payload-relative addresses and unresolved loader mapping.
- Rollback: remove only the appended sections.

## ABL1 relocation-coherence integration observed result

- Shared plan/memory append-only integration completed; phase 2 remains `PARTIAL`.
- No runtime base, channel/P-state, clock, training, or hardware gate completed.
- Final readback hashes:
  5d85b1cc75bac84573a0e0fff7ba80d21b721305cb0e096297138d86f8e347b3 docs/research/20260920-clv-abl-relocation-coherence.md
  1f9b84eba2a9b44d959eec7e52217ba800aca873f602cf31a1d273325b78ecfe evidence/firmware-audit/20260920-clv-abl-relocation-coherence/abl1-relocation-coherence-result.json
  250bd63b903fadf1f922eb9d800f0c87ccedabdc16d930817ed9e9e0712730e2 docs/action-logs/2026-09-20-clv-apcb-abl-apob-interface.md
  cc59b76199692fecec5ebadc5ba0e4458cdb205c6696f34e6ab01cf5c5887587 specs/2026-09-20-clv-sync-development-plan.md
  74662d424e00b7b25f30709ec03d59ca81ac9a5b8dddaa0caa679e627cc07d36 memory/oc-recheck.md

## ABL1 producer/base-57100 review intent (before write)

- Scope: independently verify the updated producer's four absolute callback anchors, conditional base `0x57100`, callback `+0x52C` path, producer writes, and classifier table relocation to `0x16A04`.
- Required limits: base `0x57100` remains conditional static mapping, not loader/runtime proof; table values remain raw values without unit/clock inference.
- No ROM, hardware, settings, shared MCP, plan, memory, or candidate modification is intended.

## ABL1 producer base-57100 review observed result

- Reran updated producer verifier: `32/32 PASS`.
- Independent producer/base review: `28/28 PASS`.
- Four absolute pointer anchors map under conditional base `0x57100` to local Thumb code; callback +0x52C resolves conditionally to `0x109BC`.
- Classifier table literal `0x6DB04` maps conditionally to payload `0x16A04`; raw halfwords: `0x06D6,0x0532,0x0532,0x0352,0x00E1,0,0,0x00E1`.
- Producer path writes per-channel `+0x20`; no loader/runtime base proof, units, clock, training, or hardware claim.

## ABL1 producer base-57100 integration intent (before shared writes)

- Append only conditional static mapping and raw table values; preserve loader/runtime uncertainty and phase-2 `PARTIAL`.
- Rollback: remove only appended sections.

## ABL1 producer base-57100 integration observed result

- Shared plan/memory append-only integration completed; phase 2 remains `PARTIAL`.
- No loader/runtime base, unit, clock, training, synchronization, or hardware gate completed.
- Final readback hashes:
  120ac10f4a7b53895e8c71acc69be005e091ca53292b168a5d39163a3243402c docs/research/20260920-clv-abl-producer-base-review.md
  ecb7953571d3b008e76798718d216362bf819a4b0ffcb3dc52da58e23e2c483b evidence/firmware-audit/20260920-clv-abl-producer-base-review/abl1-producer-base-review-result.json
  d6480332e6bd484757274a8a13f267956e880e92c5f20854880ed3c4284bf2e4 docs/action-logs/2026-09-20-clv-apcb-abl-apob-interface.md
  dcc86e08a1935f1f389f011556afdba3b1c50d8bf18d039db4f88e892ea193d2 specs/2026-09-20-clv-sync-development-plan.md
  0be459c2c62b975cedaaf7b4003d524f2fe5ef1a4e41eb21ff503bfb1d4a235f memory/oc-recheck.md
