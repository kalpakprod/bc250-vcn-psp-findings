# PEI $INV buffer lifetime: live compiled request, HOB destination, bounded reader — 2026-09-19

## Result

**The CbsBasePei serializer is not a stub or an orphaned callback.** A stock compiled chain in `AmdFabricAriPei` requests event `FFFFFFFE` using **`6A FE` (push sign-extended imm8 -2)**, first for size and then for serialization. Its output is a heap payload inside a GUID HOB, not the DXE PPTable. The same Fabric module immediately parses that `$INV` buffer. Its two identified lookup callers request **10FF and 1104**, not 1364. No actual caller requesting 1364, nor a voltage/clock actuator edge for that token, is established.

This is conditional static reachability through normal PEI services, successful PPI installation/lookup and allocation—not a hardware run or dynamic memory capture. The previously closed DXE B000000A path was not retraced.

## Identity, addresses and evidence

- Input: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes; freshly asserted SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- `CbsBasePei`: SHA-256 `6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77`, preferred image base `09EBA08C`; inspected TE mapping **raw = RVA - 190**. Fresh body equals the existing clock-trace body byte-for-byte.
- `AmdFabricAriPei`: SHA-256 `c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78`, base `09E1BB80`; its TE mapping is **raw = RVA - 198**, not 190. Each module's stripped-header adjustment is decoded independently. Addresses below are module-local RVAs unless explicitly called VA/raw.
- Own artifacts: `evidence/firmware-audit/20260919-inv-buffer-lifetime/`. `census.json` retains all 233 executable identities/container contexts, section mappings and extractor hash; `lifetime-windows.txt` preserves selected branch/caller/reader byte listings; `caller-windows.txt` preserves interface wrapper callers. Full relevant listings and module bodies are retained with `SHA256SUMS`.

## Installer, method and wildcard event branch

CbsBasePei entry `240 -> 610`; at `614`, descriptor VA `09ECDF60` is passed to PEI Services **InstallPpi**, service slot `+18`, called at `625`. This is a PEI PPI, not DXE InstallProtocolInterface.

```text
raw 13D44: 10000080 2cdeec09 4cdfec09
             flags   GUID VA interface VA
raw 13C10: 856c12044e5c8f45abc129f1f7da365e
             GUID 04126c85-5c4e-458f-abc1-29f1f7da365e
raw 13D30: dca2eb09   -> method VA09EBA2DC = RVA250
raw 13C90: ffffffff00000000 0000000000000000 4cdeec09
             wildcard CPU, reserved, nested table VA09ECDE4C
raw 13C30: ffffffff00000000 0000000000000000 4cd7eb09 feffffff
             wildcard CPU, reserved, callback RVA36C0, eventFFFFFFFE
```

Method `250` obtains Setup into its **stack** buffer `[ebp-8C8]`, falling back to defaults on the shown variable-service errors. Its outer stride is `14`, inner stride `18`; this is not the DXE qword event layout. Event dword comparison is `42B..431`; outer/inner predicates explicitly admit wildcard `00000000FFFFFFFF`, so the serialization row is not blocked by a nonmatching CPU class. At `47D..495` it calls `36C0(PeiServices, event_descriptor, Setup)`.

Callback `36C4..36DE` evaluates `D = event_descriptor->field4`, then calls `36F0(Setup, D->buffer, D->size_pointer)`. The provider does not allocate the output. Serializer `3701: cmp [ecx],eax; 3703: jae 3719` checks required size **1605 = helper11880(15E5)+20**. Insufficient size writes 1605 through the size pointer and returns without touching the output. Sufficient size writes `$INV`, version 1 and records at `buffer+20`.

Sources: existing clock-trace CBS listing `:112` (outer table), `:141` (event comparison), `:300` (installer), `:3040` (descriptor forwarding), `:3065` (size branch); exact raw assertions are in `lifetime-test.py`.

## Actual stock caller, including sign extension

The positive chain is in **AmdFabricAriPei**, not AmdNbioSmuV10Pei:

```text
entry240 -> entry253 -> call3B6 -> 3FE
  420 pushes 20000003; 425 calls local IDS wrapper1D13
  1D13 -> local dispatcher1C8F -> table-selected handler1E8F
  1EB0 pushes token10FF; 1EBD calls lookup1D3C
  lookup cache miss: 1D72 calls request3710(NULL, &size)
                    1DCC calls request3710(buffer, &size)
  3710: local D={buffer,size_pointer}
  3722..3728: push &D; push 0; push -2
  3728 bytes 6A FE; 372A calls gateway36C0
  36C0: local event_descriptor={0,&D}; calls wrapper3B60 at36E6
  3B60: LocatePpi GUID04126c85... via service+20 at3B8C
  3B9A..3BAB: method0(PeiServices,&event_descriptor,FFFFFFFE)
  CBS250 -> CBS36C0 -> CBS36F0
```

Fabric `$IDS` header VA `09E328F4` has signature/version `$IDS`/1 and table pointer at `09E32914`. Raw table `16BC4` contains exactly active entries `20000003 -> 1E8F`, `20000004 -> 1F6D`, then `FFFFFFFF` sentinel. Event `20000004` is also requested at `56D/572`; its handler calls the same lookup with token `1104` at `1F8B/1F94`. This proves a compiled entry-to-request chain, rather than merely an uncalled request helper.

Six GUID-bearing clients were reverse-traced through their argument-forwarding gateways: Fabric `3B60/36C0`, Gfx `1D30/1920`, NbioBase `4970/4500`, Pcie `5470/5060`, Smu `2680/2270`, Soc `23B0/1AD0`. Decoded immediates, imm8 sign extension, arithmetic candidates and caller argument construction were considered; no claim relies on searching only `FE FF FF FF`. Computed -2 equivalents (`~1`, `0-2`) are accounted for as the same 32-bit event in host controls, but arbitrary computed aliases across the whole firmware were **not** exhaustively symbolically executed. The actual located request needs no such inference: `6A FE` is decisive.

## Outgoing buffer and next reader

Fabric lookup `1D3C` first asks heap lookup `33E0` for handle **4254564E**, bytes `NVTB`. On hit (`1D62`) it reuses the buffer and jumps to `1DFC`. On miss:

1. `1D68..1D85` sets size=0 and queries the serializer with buffer=NULL. If the size stays zero (e.g. PPI unavailable), it returns failure. CBS returns size1605 without a NULL output write.
2. `1D8A` requests size+68 from allocator3290, handle NVTB, persistence byte7. Allocator builds a 10-byte-hex heap header: `HEAP` signature, handle, requested size, persistence at +C, active byte1 at +D.
3. `3311 -> 2698 -> 266F`: **CreateHob**, PEI service `+34` at `2685`, type4. GUID copied by `26AC..26C0` is **d97d161a-16cd-4ada-b9f6-aec3f9fccc2c**. HOB GUID header size18; heap header size10; INV starts at **HOB+28**. Requested HOB size before service alignment is **1695 = 1605+68+10+18**.
4. `332B` publishes `heap_header+10` in allocation descriptor+9; `333E` vicinity zeroes the requested payload through helperDEB. In lookup this output is `[ebp-17]`. `1DC1` writes sentinel55AA at INV+size+64, i.e. INV+1669.
5. `1DCC` serializes into that payload. `1DE8` checks the sentinel. `1DFC` is the next content reader: compares `[esi]` with `$INV`, then `1E11` advances to first record at +20. Assertion branches call diagnostic helperB4D; do not mistake them for guaranteed aborts.

Reader `1E16..1E89` switches on record flag low two bits; record lengths are 4/5/7/B for 1/2/4/8-byte values. For flag2, `1E47` loads the u32 payload, clears output high dword at `1E4A`, and advances by7 on nonmatch. Token comparison `1E67..1E6E` is against caller-supplied u16 `[ebp+8]`; FFFF terminates. Output uses caller-provided **EDI**, an internal calling convention. The two direct callers supply stack result slots and tokens10FF/1104. This is a real generic INV reader, **not a token1364 lookup request**.

The event descriptors and CBS Setup are stack-lived; INV is HOB-backed and remains discoverable through GUID+HEAP/NVTB after those calls return. Heap finder3360 checks GUID HOBs, handle, HEAP signature and active byte; lookup33E0 returns header+10. No freeing occurs in this traced path. Absolute runtime address, actual contents, PEI migration and later DXE/SMM retention were not captured offline.

## Token1364, related clocks and precise remaining boundary

CBS still copies Setup+6E6 unchanged into record1364 (u32, flag2). The established clock serialization records remain 11ED/1204/1331/1373/1374 for Setup+316/+330/+6A3/+703/+704. All are serialized if the fill path executes; this does not mean a consumer requests them.

Within Fabric, both direct callsites of generic lookup1D3C are fully identified (10FF and1104); no stored preferred-VA pointer to that reader was found. These early-token lookups stop before1364; they do not establish its value reaching an actuator. In the seven interface-bearing modules, identified immediate1364 uses are serializer writes, not requested lookups. Synthetic reader tests prove only that the decoded generic format **could** return1364 if requested, not that compiled firmware does request it.

**Next exact unresolved interface:** additional consumers of GUID HOB `d97d161a-16cd-4ada-b9f6-aec3f9fccc2c`, heap handle **4254564E/NVTB**, especially a lookup1364 caller and the use of its returned value. The bounded census identifies **42 heap-GUID-bearing executable bodies** (including AmdNbioSmuV10Dxe, CbsSetupDxe and AMD PEI/DXE/SMM heap-library users); their heap operations have not all been classified by handle. GUID presence alone is not INV readership. Neither a missing caller nor “no reader anywhere” is claimed: the Fabric reader is positively resolved; the voltage-specific requester/actuator remains missing. Reopening the ruled-out DXE hook is not the next step.

## Coverage, verification and reproduction

PASS: pinned ROM hash; seven literal-PPI-GUID bodies out of **233 unique supported executable bodies**; all **189,694** instruction/continuation listing byte-lines match their bodies; 15 exact instruction-window assertions; provider descriptor, wildcard table and Fabric IDS table assertions; existing CBS body equality; six host dispatch controls; seven **synthetic** width/token/terminator reader controls. PASS: predecessor `scaling-SHA256SUMS`, 11 files; preserved output `predecessor-check.txt`. Tool versions/hashes and all relevant module hashes are retained in JSON and manifest.

Scope is unchanged `scripts/firmware_audit.py` extraction (supported containers/FV selection, depth10), literal interface GUID census and six clients' direct wrapper chains plus Fabric heap/reader chain. It excludes runtime-built GUIDs, protocol replacement, arbitrary indirect/computed aliases, unsupported containers and complete cross-phase HOB consumer classification. No full-machine emulation, hardware verification or actual buffer dump. No build/lint suite applies to evidence-only Python producers/Markdown. Existing extractor and GNU objdump were reused; prior final-consumer evidence was verified, and no Ghidra project needed modification.

From repository root, producers write only their own evidence directory; copy the producer scripts into a new output directory to preserve a previous run:

```sh
python3 -B evidence/firmware-audit/20260919-inv-buffer-lifetime/audit.py
python3 -B evidence/firmware-audit/20260919-inv-buffer-lifetime/verify.py
python3 -B evidence/firmware-audit/20260919-inv-buffer-lifetime/lifetime-test.py
sha256sum -c evidence/firmware-audit/20260919-inv-buffer-lifetime/SHA256SUMS
sha256sum -c evidence/firmware-audit/20260919-oc-final-consumer-pass/scaling-SHA256SUMS
```

Intent precedes continuation writes in the requested action log. Writes are own evidence/report/log and two bounded report cross-references only. No hardware/network/source/builder/candidate/firmware changes, provider patch or voltage recommendation. Requested OpenAI Codex high via alias could not be independently selected/certified through this tool interface; no network CLI invocation was used.
