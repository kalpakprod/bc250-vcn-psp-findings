# R2: clock controls reach a serialized configuration; telemetry aliases domains

## Scope and verdict

Static analysis on clv SHA-256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8, 16777216 bytes. No board access or ROM modification. R2 is PARTIAL: field-to-record serialization is located in two exact PEI modules; final record consumers, physical divider semantics and independent clock measurement remain unresolved.

## Stored requests and first consumer

NVAR body convention 0x4CF; raw bytes are requests, not measured frequencies. Historical IFR labels are reference semantics, not a freshly regenerated clv IFR proof.

| Field                  | Setup offset | clv value                      | Serialized record ID | CbsBasePei load RVA / file offset | AmdNbioSmuV10Pei load RVA / file offset |
| ---------------------- | ------------ | ------------------------------ | -------------------- | --------------------------------- | --------------------------------------- |
| MemoryClockSpeed       | 0x316        | 0x24 (historical IFR: 1800MHz) | 0x11ED               | 0x9857 / 0x96C7                   | 0xB8D7 / 0xB747                         |
| UclkDiv1M0             | 0x330        | 1 (Enabled label)              | 0x1204               | 0x9CE4 / 0x9B54                   | 0xBD64 / 0xBBD4                         |
| FclkDpm                | 0x6A3        | 0x0F (Auto label)              | 0x1331               | 0xDA00 / 0xD870                   | 0xFA80 / 0xF8F0                         |
| DfClockOverrideControl | 0x703        | 1 (Manual label)               | 0x1373               | 0xE726 / 0xE596                   | 0x107A6 / 0x10616                       |
| DfClockOvrd            | 0x704        | 1420                           | 0x1374               | 0xE75B / 0xE5CB                   | 0x107DB / 0x1064B                       |

Each observed sequence writes a u16 record identifier at destination+0, adjusts flag bits at +2, copies the source byte/word to +3, and advances the destination by 4/5 bytes. The five mappings agree across both modules. This establishes serialization, not that a specific SMU request or PLL register consumes the record. Source pointer provenance and complete call reachability are not yet established.

CbsSetupDxe also contains default writes: RVA 0x3C80 sets +0x316 to FF; 0x3D22 sets +0x330 to FF; 0x4561 sets +0x6A3 to 0F; 0x4741 sets +0x703 to FF; 0x4748/0x474D sets +0x704 to 1000. Defaults differ from stored clv overrides. These instructions do not prove when defaults run or explain a specific hardware reset of NVAR.

Exact module identities and evidence:

- CbsBasePei: 6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77.
- AmdNbioSmuV10Pei: 905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80.
- CbsSetupDxe: 7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8.
- evidence/firmware-audit/20260919-clock-trace/serialization.json records instruction bytes, file offsets and surrounding instructions; trace.json pins inputs and module hashes.

## Telemetry provenance: three labels are not three independent measurements

Retained source archives/imported/recon-evidence/legacy-tmp-bc250-recon/cyan_skillfish_ppt.c SHA-256 9259ad3ff6f660fe97ca7ea68f9b7e5f5d185982f0d3341180bd880442f030f1:

- Lines 157-158: METRICS_CURR_UCLK reads Current.MemclkFrequency.
- Lines 209-214: sensor GFX_MCLK uses that same member and multiplies by 100 for its sensor representation.
- Lines 271-274: SMU_FCLK and SMU_MCLK both select METRICS_CURR_UCLK.
- Lines 409-410 and 416-417: exported average/current UCLK and FCLK both copy the same Average/Current.MemclkFrequency fields.

A host C test uses the four exact copied assignments, with Current=1750 and Average=1333. Both current exports become 1750, both average exports become 1333. PASS proves software aliasing for this source, not actual frequency equality. Installed custom kernel identity and its equivalent code remain unverified. Reading additional aliases of this source cannot prove 1:1:1.

## Reproduction and verification

Existing firmware_audit.Extractor selected five named CBS/SMU modules; no independent full-firmware parser was invented. Disassembly used GNU objdump 2.47. For TE .text, raw start = PointerToRawData - (StrippedSize - 40); objdump binary i386 uses section VirtualAddress as adjust-vma. PE files use objdump -d -M intel. The TE offsets were reconciled directly against the extracted bytes. Linear-disassembly hits are scoped observations, not whole-program control-flow proof.
Host test: `cc -Wall -Wextra -Werror evidence/firmware-audit/20260919-clock-trace/telemetry-alias.c -o /tmp/bc250-clock-alias-test && /tmp/bc250-clock-alias-test` (choose an unused output path). Compiler in this run: GCC 16.2.1 20260810.
PASS: pinned ROM identity, module hashes, ten field-load byte checks, matching record IDs in two modules, compiled telemetry alias test. Capstone import failed (not installed); no dependency installed, GNU objdump used instead.
UNRUN: live clocks, full consumer call chain, independent physical clock readings, synchronization, latency/stability, firmware boot. No safe frequency or voltage recommendation follows.

## Next discriminating work

Trace records 0x11ED/0x1204/0x1331/0x1373/0x1374 from serializer callers to receiver dispatch and final hardware writers; do not search only for Setup offsets once data has been serialized. Establish MemclkFrequency's firmware producer and an independent DF/UCLK source on the exact installed version before any synchronous-mode claim. Keep R2 open for this continuation; R3 is separate.
