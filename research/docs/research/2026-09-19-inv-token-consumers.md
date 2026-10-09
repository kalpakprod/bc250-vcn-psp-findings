# INV token requesters: bounded compiled caller inventory — 2026-09-19

## Result

**A second real generic INV reader exists: `AmdCcxVhAriDxe` RVA `5AC4`.** Its two identified callers request **1000 and 1001**, and their returned values reach MSR bit updates. The earlier Fabric reader `1D3C` still has exactly two identified direct callers, requesting **10FF and 1104**. None of these four requests supplies **1364/1363/11ED/1204/1331/1373/1374**.

**No supported BIOS parameter-to-actuator proof for those seven target tokens is established.** This is not a global-dead verdict. Direct call-site coverage for the two identified readers is closed within the declared static scope; arbitrary computed/indirect destinations and other reader implementations are not exhaustively solved. The full user acceptance criterion for every dynamic/indirect requester therefore remains **incomplete**, not silently passed. Assertions of "no stock consumer" must be strictly qualified to direct static call-sites.

Evidence classes: `observed-bytes`, `static-analysis`, and explicitly synthetic host controls. No firmware execution, board/network access, source/builder/candidate mutation, or voltage/frequency recommendation.

## Identity and reproducible scope

- Input: RetroWeb provenance `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, **16,777,216 bytes**, SHA-256 **ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8**; asserted freshly, independently hashed with `sha256sum`.
- Own evidence directory: `evidence/firmware-audit/20260919-inv-token-consumers/` (called `E/` below). Predecessor files were not edited or regenerated. Independent `sha256sum -c` verified **32/32** preceding manifest entries; preserved `E/predecessor-check.txt`.
- Reused unchanged `scripts/firmware_audit.py::Extractor`, including its FV selection, supported LZMA/section containers, depth limit 10 and top SECURITY_CORE handling. All **233 unique executable bodies** reproduce the predecessor's complete SHA identity multiset, not merely its count. These are supported PE32/TE bodies, not every executable architecture in the SPI image.
- Own Census removes the predecessor's PPI-GUID-only save gate. Every supported body is retained, with container identity, image base, machine and independent section mapping; filename includes digest to avoid UI-name collisions. TE raw section offsets subtract that image's `StrippedSize-40`; PE uses its own section table. All report addresses are hexadecimal **module RVA**, unless marked raw.
- All code/executable-flagged sections decoded using GNU objdump **2.47**, correct IA32/X64 mode, `-D -z --insn-width=16`: **4,041,184 section bytes**, **1,125,281 decoded/listing byte rows** checked against bodies. Linear decoding is not a whole-program CFG proof; padding/data can decode as instructions. Exact selected reader/argument windows and raw relative-call checks narrow the claim.
- Census: **42** bodies contain literal heap GUID `d97d161a-16cd-4ada-b9f6-aec3f9fccc2c`; **2** contain literal handle `4254564E`/`NVTB`; **8** contain `$INV`. Both NVTB bodies are among the 42. Seven INV-bearing PEIMs contain serializers; Fabric additionally contains a reader. CBS has no heap GUID.

## Caller coverage matrix

The complete **42-row per-module matrix** is retained in [`caller-matrix.md`](../../../evidence/evidence/firmware-audit/20260919-inv-token-consumers/caller-matrix.md). `E/coverage.json` additionally retains each GUID's raw/RVA location, decoded GUID references, every module-local indirect call/jump, target candidate classification, exact stored-pointer checks and raw rel32 incoming edges. `E/census.json` covers the remaining 191 identities too.

| Reader module / entry  | Argument source → exact call                                              | Effective u16 token | Result            | Indirect boundary                                                                                                          |
| ---------------------- | ------------------------------------------------------------------------- | ------------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------- |
| AmdFabricAriPei / 1D3C | `1EB0 68 FF 10 00 00` → `1EBD E8 7A FE FF FF`; output EDI points to stack | 10FF                | non-target lookup | 31 module-wide indirect call/jump sites inventoried, not exhaustively resolved                                             |
| AmdFabricAriPei / 1D3C | `1F8B 68 04 11 00 00` → `1F94 E8 A3 FD FF FF`                             | 1104                | non-target lookup | same boundary                                                                                                              |
| AmdCcxVhAriDxe / 5AC4  | `5CA0 B9 00 10 00 00` → `5CA5 E8 1A FE FF FF`; output RDX=`rsp+58`        | 1000                | C0011029 bit14    | 133 module-wide indirect call/jump sites inventoried; IDS handler edge below resolved, remainder not exhaustively resolved |
| AmdCcxVhAriDxe / 5AC4  | `5CEC B9 01 10 00 00` → `5CF1 E8 CE FD FF FF`                             | 1001                | C0011023 bit45    | same boundary                                                                                                              |

For each reader, all decoded direct calls/jumps into its **whole function range**, not just its entry, were enumerated: Fabric `[1D3C,1E8F)`, CCX `[5AC4,5C65)`. Exactly two external edges each, both at the entry. An independent **every-code-byte E8/E9 rel32** search into those ranges finds precisely the same four edges, all valid instruction boundaries; no additional overlapping E8/E9 candidate.

No exact stored preferred-VA/RVA entry pointer (32- or 64-bit), immediate entry materialization or RIP-relative entry materialization was found in either reader's own body. This is a bounded pointer check, **not proof of no indirect caller**: computed addresses, interior pointers, foreign-module pointers, runtime-installed interfaces or overlapping instruction streams outside the checked windows remain possible.

### Transformed/dynamic token handling

The token accepted by Fabric is caller stack u16; CCX executes `5ADC 44 0F B7 E1` (`movzx r12d,cx`). Every located direct request is sliced to its final argument definition. CCX's constant move immediately precedes the call. Fabric's intervening LEA/MOV instructions neither transform nor overwrite the top-of-stack argument. There are no decoded direct entries into these slices after the defining load. Thus no arithmetic, table, dynamic or upper-bit alias can turn **these four callsites** into one of the targets under the traced flow.

Host controls distinguish `[ebx+1364]` displacement, immediate `ecx=1364`, 16-bit `cx=1364`, arithmetic `1360+4`, and sign-extended `6A FE`. They are synthetic checks of the analysis discipline, **not firmware requester evidence**. Runtime/computed arguments at unresolved indirect destinations were not symbolically executed; no absence claim is made for them.

## New CCX reader and actual downstream edge

`AmdCcxVhAriDxe` body SHA-256 **d9bc6337e3d039922016e95ed8be1fda5d7fb3e0250e43a6058d9c0d305997f0**, preferred base zero, PE32+ X64. Selected code independently decoded by LLVM objdump: `E/ccx-independent-llvm.txt`, **167 instruction-byte rows** matched against the exact PE body.

Reader `5AC4` saves u16 CX in R12D and output pointer RDX in RBP. `5AE9 BE 4E 56 54 42` selects NVTB; `5AF7` calls heap lookup `3FB0`. Cache miss uses `79E0` twice for size/fill; `7A09 B9 FE FF FF FF` requests event FFFFFFFE through gateway `7950`. This DXE request's provider success is not assumed. The independently traced cache-hit route needs the existing migrated heap instead.

`5BBE 81 3B 24 49 4E 56` validates `$INV`; `5BD3` advances by20. Record flag low two bits select lengths **4/5/7/B**, loading **u8/u16/u32/u64** at record+3. `5C2E` stores a qword result; `5C32 66 44 39 23` compares record u16 with R12W; `5C3B` compares against FFFF terminator. This is code-equivalent format handling, not a GUID/name-based attribution. Like Fabric, the output slot may be overwritten while traversing nonmatching records; callers check status before applying it.

A compiled indirect handler chain is present, not merely an isolated helper: entry `2A0` calls initialization `2EC` and main `4FC`; main's `AEF` forms **event2** with `lea ecx,[rdx+2]` after `xor edx,edx`, then `AF2` calls IDS dispatcher `5A14`. `$IDS` header at7F58 points at7F38: **`{event2, handler5C68}`**, followed by FFFFFFFF sentinel. Dispatcher `5A73 FF 57 08` invokes the selected handler. `5C68` tests BSP via MSR1B bit8, then issues both non-target lookups. This resolves that **indirect handler** edge; it is not an indirect invocation of the generic reader.

For token1000, success and `value != FF` permit `5CBC` selecting **MSR C0011029**; shift14 and mask4000 merge **value bit0 into bit14**, then `5CE5 0F 30` writes the MSR. For token1001, success and `value != 3` permit **MSR C0011023**, shift2D and mask200000000000, writing **bit45** at `5D34`. No mV/MHz meaning, voltage rail or PLL/divider semantics is inferred from these unrelated tokens.

## HOB-to-DXE retention is now byte-backed

CCX constructor `39D -> 3D50` first locates a shared heap protocol. If absent, it initializes the list and calls HOB importer `3C90` at3DA9; otherwise it adopts the existing protocol's list. Importer `3C9D/3D2D` references the exact GUID at7D90 and walks matching HOBs. It uses HOB+18 as heap header, validates **HEAP** and active byte+0D==1, allocates a DXE node through3BA0, then `3D0D -> 35CC` copies **size=header+8** bytes from **HOB+28** to **DXE node+20**. The DXE node has list links before its 10-byte-hex heap header.

Finder `3F30` walks that list, matching handle at node+14 and HEAP at+10; lookup `3FB0` returns node+20. Therefore the PEI NVTB payload has a compiled cross-phase migration/discovery route to the CCX reader, conditional on successful constructors/services and surviving HOB contents. No actual memory dump or physical execution is claimed.

## Target constants: complete decoded candidate disposition

Across the 233 supported code-section listings, exact target-value candidates classify as:

| Category                               | Count | Disposition                                                                                                                  |
| -------------------------------------- | ----: | ---------------------------------------------------------------------------------------------------------------------------- |
| Non-control-flow decoded immediate     |    49 | Seven target IDs × seven PEI serializers; each exact `BA imm32; 8B 45 F8; 66 89 10` writes a record ID, not a lookup request |
| Memory displacement or address comment |    13 | Not a token argument                                                                                                         |
| Direct control-flow address            |    74 | Branch/call destination number, not a token argument                                                                         |

Serializer carriers: CbsBasePei, AmdFabricAriPei, AmdNbioGfxARIPei, AmdNbioBaseARIPei, AmdNbioPcieARIPei, AmdNbioSmuV10Pei, AmdSocBl5AriPei. For example CBS `E3C4` writes ID1363 and reads Setup+6E5; `E3F6` writes ID1364, flag2, then `E419` reads Setup+6E6 unchanged. No actuator follows from those writes. All 49 byte windows and the excluded displacement/control-flow candidates are preserved; raw bytes embedded inside an instruction are never promoted to token requests.

## Verification, limitations and next missing component

**PASS:** predecessor manifest32/32; pinned input; 233 identity multiset reconciliation; all extracted body hashes; section-listing byte reconciliation; **517 explicit verification checks**, including 49 serializer stores, four argument slices, reader/MSR/migration byte anchors, IDS table, raw E8/E9 inventory and LLVM167-row independent check. Initial producer/verifier failures are recorded in the action log: missing UI key and a false assumption of unique UI names; corrected using FFS fallback and complete SHA multiset/body identity checks. Final runs pass.

**INCOMPLETE:** exhaustive arbitrary computed GUID/handle discovery; classification of every generic heap client's dynamic handle; complete points-to analysis of indirect module interfaces/callbacks; nonliteral parser equivalents; unsupported containers/architectures and runtime-generated code. The 42-row matrix reports literal-marker scope, not 42 proven INV consumers. Full-machine emulation, hardware tests, independent model-family review and project build/lint suites are **unrun** (evidence-only producers/report, no production source change).

**Next missing component:** a byte-backed requester of **1364/1363 or the five clock IDs**, including a resolved indirect/computed path if present, followed through its return value to rail/units or clock programming. The new CCX migration path explains how the buffer can reach DXE; it does not supply that missing target requester. Next analysis should resolve generic heap-handle arguments and reader address escapes/interfaces, not reopen the already excluded DXE B000000A hook or infer global dead code from literal absence.

Reproduction from repository root (producers write beside themselves; copy to a new evidence directory to preserve this run):

```sh
python3 -B evidence/firmware-audit/20260919-inv-token-consumers/audit.py
python3 -B evidence/firmware-audit/20260919-inv-token-consumers/analyze.py
llvm-objdump -d --x86-asm-syntax=intel --start-address=0x5ac4 --stop-address=0x5d36 evidence/firmware-audit/20260919-inv-token-consumers/AmdCcxVhAriDxe-*.bin > evidence/firmware-audit/20260919-inv-token-consumers/ccx-independent-llvm.txt
python3 -B evidence/firmware-audit/20260919-inv-token-consumers/verify.py
sha256sum -c evidence/firmware-audit/20260919-inv-token-consumers/SHA256SUMS
```

Requested OpenAI Codex/high alias was logged before writes; effective model/effort cannot be independently certified through the available interface. No network model invocation was substituted.
