# DF initialization to register programming: bounded offline result

## Result and implementation decision

The inspected edge `0x1C3B0 -> 0x1E038` is NOT an external table-pointer or rate upload interface. The mailbox word supplies configuration bytes and two flags. Both row-pointer branches derive addresses from internal SMU vectors. Consequently, do not build a synchronized BIOS by passing a rate or pointer to this initialization handler. This is a negative result for this specific construction, not proof that BIOS cannot influence DF clocks.

The actual register path is now explicit: `0x1E448` loads a selected internal row and invokes `0x1E170`, `0x1E1D0`, `0x1E260`, conditional helpers and `0x1E2DC`. Raw row coefficients, not its displayed frequency float, feed the first two coefficient-writing helpers. A patch to reported floats alone would not change those arguments.

## Inputs and reproducibility

Root: `/home/OWNER/orca/projects/bc250`.

- ROM: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16777216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- SMU: `archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5`, 262400 bytes, SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`.
- Provenance: existing retroweb donor and preserved imported SMU; full SMU equals ROM slice at `0x8FEF00`. No new external source.
- Address convention: SMU file offset equals address in the retained flat analysis; little-endian integers and Xtensa instructions.
- Reused Ghidra 12.1.3 headless, existing `OCConsumer` project and `OcConsumerRead.java`, `-readOnly -noanalysis`. All loaded bytes checked by the existing script before analysis. No program save.
- Exact launch commands: `evidence/firmware-audit/20260920-df-init-route/command.txt` and `side-command.txt`; stdout, stderr and exit statuses beside them.
- Reproduce byte audit: `python3 evidence/firmware-audit/20260920-df-init-route/verify.py`.
- Baseline: `python3 scripts/verify_df_table_population.py` (existing bounded verifier, no new parser).

## F1 — all direct argument fields at 0x1C3B0

`0xFFC` loads one word from the queue descriptor's argument-register pointer; `param_1` is used to select the descriptor, not passed as a DF row pointer.

| Argument bits | Store / use                           | Evidence             |
| ------------- | ------------------------------------- | -------------------- |
| 31:24         | first init argument -> `0xCEE0+0x11`  | `0x1C3CC`, `0x1E03E` |
| 7:0           | second init argument -> `0xCEE0+0x12` | `0x1C3C3`, `0x1E041` |
| 16            | `0x1105C+0x2A` flag                   | `0x1C3BE`, `0x1C3C6` |
| 17            | `0x1105C+0x2B` flag                   | `0x1C3B8`, `0x1C3C9` |

Other argument bits do not participate in these direct extractions. High byte is used as an eight-bit destination mask by `0x1EF18` and `0x1E170`; do not call it a requested frequency. Low-byte physical semantics remain unresolved.
The handler then calls `0x30DF4`, and conditionally `0x2CEF4(0)`, finally returning status1 through `0xFA8`. These are real side-effecting routines, not a read-only query. Fresh listings include both; their transitive closure has NOT been proved free of DF effects. `0x30DF4` reads the +2A flag and contains register save/restore and wait loops. Do not use a negative claim about the narrow init edge to erase these effects.
Handler pointer at `0x79FC` equals `0x1C3B0`. Queue5/message09 naming is retained from prior dispatch work; BIOS-side sender and host reachability were not independently established in this pass.

## F2 — internal row pointers, both branches

`0x2E4C4` reads `*(0x15774+4)`, initial value8. This is an SRAM configuration word, NOT a live hardware register read.

- Config !=7: four-iteration `loopgtz` at `0x1E085`; indices from `0xCEE0+0xA0`; pointer = `0xCEE0+0x2C+40*index`.
- Config ==7: four-iteration `loopgtz` at `0x1E05A`; indices from `0xCEE0+0xF0`; pointer = `0xCEE0+0xCC+40*index`.
- `FF` skips a slot. Each selected row receives its slot number in row byte3; selected-row count goes to `0xCEE0+0xF7`.

Static vectors produce:

| Branch | Vector     | Row pointers                 |
| ------ | ---------- | ---------------------------- |
| !=7    | 3,2,1,0    | CF84,CF5C,CF34,CF0C          |
| ==7    | 0,FF,FF,FF | CFAC,skipped,skipped,skipped |

The arguments do not enter address arithmetic. Neither branch copies an external table. Runtime modification of the configuration, vectors or pointers remains outside this proof.

Ghidra warns about unreachable loop blocks and an unrecovered jumptable here. The assembly, not the malformed C loop reconstruction, establishes the iteration count. The apparent three arguments in decompiled `1EF18(...)` are not a table interface: its own listing shows global reads, not consumption of caller a2/a3/a4 as table parameters.

## F3 — initialization writes and actuation

`0x1EF18` loops over row slots and enabled mask bits. It sends row+0x1C to register addresses `0x50278` and `0x52278`, row+0x20 to `0x5027C` and `0x5227C`, each plus `slot*0x100 + mask_bit*0x100000`. Helper `0x2A74(0,address,value,2)` implements the windowed 32-bit write. Values originate in the selected internal row, not the mailbox low byte.

`0x1E448` bounds the selected state against byte `0xCFD7`, then loads a pointer from `0xCEFC+4*state`.

- Row byte3 -> `0x1E170`: selected-state bits in destination registers, governed by +0x11 mask.
- Row bytes0/1 -> `0x1E1D0`: direct writes to `0x0115C1A0`, `0x0115C1A4`, `0x0115C1A8`. Values are `0x80001`, `0x40005001 | ((byte1 & 0x7F)<<16)`, and `byte0 & 0x1FF`.
- Row bytes8..0xC are prepared by the caller for `0x1E260`. Inspected callee uses incoming a2/a3/a5 (row bytes8/9/B); incoming a4/a6 are not used as coefficients in its listing. Destinations derive from the eight-word array at `0x15130`: `0x0115C9A0..0x0115C9AC` and `0x0116C1A0..0x0116C1AC`, step4.
- Float row+4 is loaded separately and later used for software state update; it is not substituted for the raw arguments above.

These are firmware-visible aperture addresses, not an independently measured physical clock identity. No MHz-to-memory-rate equivalence or synchronization follows from them.

## Checks and limits

- PASS: original ROM/SMU hashes, sizes and full slice equality.
- PASS: both headless commands exit0; loaded program equals exact SMU.
- PASS: 380 main +475 side-listing instruction byte records match the SMU; standalone audit exit0.
- PASS: both static row-vector derivations and literal-resolved register addresses.
- INCONCLUSIVE: complete BIOS-to-DF frequency-control route, runtime writers, side-callee transitive effects, physical domain names and low-byte semantics.
- UNRUN: independent reviewer, CPU emulation, live mailbox access, boot, voltage, latency and stability.
- UNRUN: Procoder full gate. Known whole-tree/privacy issue remains; no imported-corpus security scan was launched. This pass adds only a bounded stdlib evidence checker, reusing the existing analysis engine. No new dependency or production parser.

## Next decisive offline work

Locate the BIOS producer of this exact initialization argument and its low-byte consumer (`CEE0+0x12`), then compare the producer inputs with the separate state-selection path. In parallel conceptually, resolve whether `30DF4`'s configuration flags reach raw coefficient writers; do not assume they do. Required positive evidence before a BIOS candidate: a BIOS-controlled value with a demonstrated path to the raw row/divider arguments above, not another recorded Setup token or telemetry float.

No candidate was built, no firmware bytes changed, no board connection or write occurred. Rollback for this research consists only of removing new output files; original firmware and prior evidence remain intact. Historical findings are superseded only by the explicit qualifications appended to memory.

## Follow-up: sender and low-byte consumer (2026-09-20)

### New result

**The generic Queue5 transport was located in PSP type28, not the x86 UEFI sender previously suspected. The specific producer of init command9 and its argument remains unresolved.** This changes the next investigation target to the request structure passed into the PSP-side caller.

### Low byte CEE0+12

Reused the existing Ghidra read-only script for47 entry leads containing DF-struct references. Fresh output `sender-smu.txt` contains2532 instruction records, each checked against the pinned SMU. Raw unaligned l32r search in code range1B000..39000 yields51 candidates for literal171EC;50 are decoded references. Candidate2935D is disproved by the covering instruction at2935C (`a2a1a3`, MOVI a10,0x1A3).
Within these listings, the only immediate-offset12 byte/halfword/word load or byte-store match is the known store at1E041. **No direct reader found in this bounded scope; not a proof that the field is unused.** Wider loads, propagated/interior pointers, indirect callees, computed offsets and DMA remain unresolved. No supported frequency semantics can be assigned to this byte.

### Excluding a misleading BIOS message9 match

Reopened and SHA-256 checked all233 supported executable bodies from the existing clv census. Verified1125281 stored instruction byte records against their module/section maps. No four-byte raw literals or decoded immediate references to Q5 port candidates03010700/704/718 or03B10700/704/718 were found. This excludes neither computed constants nor code outside the extracted UEFI executable census.
`AmdNbioSmuV10Dxe` contains message9 at RVA2D43 followed by call3120 at2D48. Transport3120 uses argument03B10998, response03B10564, message03B10528. The SMU queue2 tuple is03010998/03010564/03010528; queue5 is03010700/03010704/03010718. The host/SMU alias correspondence is a static inference; the offset tuples themselves are byte-proven. **Do not equate this DXE message9 with Queue5/init9.**

### Positive PSP-side transport finding

A full-ROM literal search produced two new non-SMU leads:

- ROM996898:03B10700, inside PSP directory type28 at ROM984F00, length108400, SHA-2565b6828bff3f10f1b120b279932af156438e1bdd724508e44b7630fce9716251f.
- ROM8EE280:03010718, inside type02 (location only; caller code not investigated here).

Reused the existing PSP directory layout/parser and independently checked the type28 directory descriptor in the supplemental verifier. Type28 addresses below are **relative to the complete directory entry**, not a guessed stripped-body or runtime address.

Installed LLVM decoded exact Thumb windows without warnings and every emitted instruction encoding matched ROM bytes. Function `type28+118E8` (ROM9967E8) does:

1. Save incoming r0/r1/r2/r3; preserve r2 as optional output pointer and r3 as polling limit.
2. Load literal03B10700 at instruction118FC, from pool11998, and invoke svc7D with length32. The returned address is stored in r7.
3. Form message pointer `(r7 & 0xFFF00000)+0x10718`, response pointer with offset10704. Poll response, clear it, write saved r1 to[r7], then saved r0 to message pointer.
4. Poll response again, expect1, optionally read back[r7], then call svc7E for the mapped region. SVC implementation itself was not analyzed or executed; mapping semantics are inferred from the address use.

Four direct Thumb BL sites resolve to118E8 and are independently decoded:

| Entry-relative caller | Message source | Argument source      |
| --------------------- | -------------- | -------------------- |
| C526                  | `[r4+0x38]`    | `[r4+0x3C]`          |
| FB58                  | constant0x10   | constant1            |
| FBA8                  | constant0x10   | constant0            |
| FC8A                  | constant3      | literal-loaded value |

At C51C..C526: `r0=r4+0x38; r2=r4+0x44; ldm r0,{r0,r1,r3}; bl118E8`. Therefore timeout comes from `[r4+0x40]` and return argument destination is `r4+0x44`. This is a concrete dynamic route to the correct mailbox. **No constant init9 producer was located; origin and allowed values of this request structure are still open.** Direct-call enumeration does not cover indirect/tail callers.

### Execution, verification and limits

- PASS: `python3 evidence/firmware-audit/20260920-df-init-route/sender-verify.py` (SMU byte audit, queue tables,233 modules and instruction census).
- PASS: `python3 evidence/firmware-audit/20260920-df-init-route/sender-t28.py` (pinned type28, exact LLVM windows, four BL targets).
- Existing `verify.py`, `result.json`, report, manifest and action journal remain the same role set; supplemental sender records extend them. Prior manifest preserved as `sender-prior-manifest.json` before report append.
- Tool availability attempts: current Python lacks pypcode/capstone; cutter venv lacks capstone. No installation. Reused Ghidra and installed LLVM instead.
- Initial mixed code/data LLVM window emitted warnings despite exit0; output retained, not accepted as clean analysis. Exact code-window rerun has empty stderr and complete byte coverage.
- INCONCLUSIVE: init9 producer and low-byte consumer; hardware control from BIOS remains unproved.
- UNRUN: independent review, emulation, board access, voltage/clock/latency tests, Procoder broad gate (unchanged privacy/scope blocker).
- No firmware modification: MODIFIED and firmware ROLLBACK behaviors are not applicable; original baseline verification and hashes are repeated, not substituted for a hardware test.

### Next discriminating target

Trace the enclosing PSP dispatcher and the producer of `r4+0x38/+0x3C/+0x40` at C51C. Determine whether any reachable caller supplies message9 and how it constructs the low/high argument bytes. This is a new concrete code path, not a repeat of negative UEFI literal scans. Leave CEF2 semantics unresolved until an actual load/dataflow is found.

## Full-goal continuation: resolve the request selector (2026-09-20)

The user explicitly reasserted the deliverable: a BIOS-applied synchronous memory/DF profile, not an endless sequence of reports. Current builder was reread: it implements only stored `DfClockOvrd` request1400, not the required actuation. Do not relabel its existing output as the requested BIOS.

### New checked edge

With dispatcher preflight successful, type28 service **0x1037** selects the generic Q5 request case:

- BC5C dispatcher takes the request pointer into r4.
- BCE8..BCF4 compares opcode to1030 and computes delta.
- BDA8 bounds the delta below61; BDAC branches to BDBE TBB.
- Delta7 selects table byte atBDC9, yielding branch stubBFB2.
- BFB2 branches toC51C; C526 calls118E8.
- Request+38/+3C/+40 are command/argument/poll-limit; request+44 receives returned argument.

This is a dispatcher reachability derivation, not proof that an arbitrary x86 BIOS caller is authorized or can invoke it. Preflight and SVC routing remain boundaries.

### Upstream TOS wrapper

PSP type02 entry ROM8EBA00, length78672, existing SHA-256cbc99cc0d1b25d97258d5db81959531ce791f0bec6b358be683ae0a6f2017527.
At entry-relativeF4C4 / ROM8FAEC4:

- Saves incoming r0(message), r1(argument), r2(optional returned-argument pointer), r3(limit).
- Constructs stack request with service1037 at+0 and value2 at+4.
- Copies saved message/argument/limit to+38/+3C/+40.
- Invokes `svc #0xF2` with r0=1,r1=request.
- On success, copies request+44 to the optional output pointer.
  The sole direct BL site found in this component,12650 / ROM8FE050, supplies command0F, argument0 and limit1000. It does not supply init9. Direct BL coverage does not include indirect/tail calls or different components.

### Rejected shortcuts

- Type02 literal03010718 at2880 belongs to a write of80000000 in the inspected notification path. It does not establish init9 production.
- UEFI immediate1037 matches are not proof of PSP-service invocation. The checked AmdFabricAriPei772F sequence stores a16-bit record ID, then source byte+98; analogous serializers exist in other PEIMs. Token namespace differs from PSP service namespace.
- `SmuWriteSram32` exists in the old VCN DXE source, but its presence is not proof that a proposed OC table edit has correct domain identities, execution timing, limits or readback. No such write was executed.
- No guessed voltage encoding, signed-SMU patch, generic init9 injection or cosmetic stored-request candidate was generated.

### Verification and decision

PASS: `python3 evidence/firmware-audit/20260920-df-init-route/goal-verify.py` checks exact dispatcher bytes and table branch, TOS wrapper/caller Thumb windows through installed LLVM, and the UEFI false lead against its pinned module. Code-only LLVM windows have empty stderr and contiguous byte coverage; mixed code/data trial output is retained separately and not used as a valid full-function decode. Previous sender-t28 checkpoint verifier was executed at turn start and passed.

The complete BIOS objective is **incomplete**. This pass removes the request-selector uncertainty but does not establish a BIOS-callable change to raw clock coefficients. The remaining build prerequisites are an actuation path with identified domains/rate semantics and, if voltage is changed, a verified rail/encoding. These are offline implementation gaps, not a demand for live telemetry. Hardware acceptance and independent review remain separate, UNRUN gates.

## Native BIOS menu audit on exact clv (2026-09-20)

### Conclusion

**The native edit-and-save mechanism exists in the selected clv firmware. A custom DXE is not justified merely to store these settings.** The relevant IFR questions require reset; immediate reprogramming of memory clocks while remaining in Setup is not established. A native menu is not itself proof that every setting reaches hardware, but neither is missing consumer coverage proof that it fails.

Inputs: exact clv hash unchanged; CbsSetupDxe SHA-2567ff717d51c9a... (full value in menu-result.json), Setup10cc728ae3f8...; both matched against the existing clv extraction census. Reused e1_ifr_dump.py functions, not its hardcoded Windows main. Forms package at moduleB2D4, length60725; UTF string package at1A024. Walked60721 IFR body bytes to exact end with balanced scopes. Existing string decoder retains terminal NULs and truncates the language label to'-US'; stripped only text terminators for reporting. Historical HIDDEN labels are not substituted for current visibility.

### Controls, flags and native help

| Control                          | AmdSetup offset | Choices/range                   | Current-clv IFR                     |
| -------------------------------- | --------------- | ------------------------------- | ----------------------------------- |
| Memory Clock Speed               | 316             | Auto and enumerated125..2000MHz | editable, reset required            |
| DRAM Timing User Controls        | 32F             | Auto / Manual                   | editable, reset required            |
| UclkDiv1M0                       | 330             | Auto / Enabled                  | editable, reset required            |
| FCLK_DPM                         | 6A3             | Disabled / Enabled / Auto       | editable, callback + reset required |
| DF Clock Override Control        | 703             | Auto / Manual                   | editable, reset required            |
| DF Clock Override                | 704             | 0..2000                         | editable, reset required            |
| VDDCR_VDD Voltage Offset Control | 6E5             | Auto / Manual                   | editable, reset required            |
| VDDCR_VDD Voltage Offset         | 6E6             | 32-bit value                    | editable, reset required            |

All8 selected questions have no enclosing SUPPRESS_IF, GRAY_OUT_IF or DISABLE_IF in this package. None is READ_ONLY. Flags independently matched to retained EDK2 UefiInternalFormRepresentation.h:0x10 RESET_REQUIRED,0x04 CALLBACK,0x01 READ_ONLY. Direct question-layout check reproduced flag and var offset from raw opcode bytes for8/8.

Exact current help text:

- DF override/control: **"When you try to override FCLK, please make sure FCLK > UCLK and Memory P-state is disabled."**
- UclkDiv1M0: "UclkDiv1 option, relative to FCLK."
- VDDCR_VDD offset: "Specify the voltage offset to apply to VDDCR_VDD -- signed integer [mV]".

This warns against assuming the DF override menu is a supported1:1 switch. It does not independently prove a hardware inequality constraint. The signed-mV description resolves UI-advertised units, not target-rail identity, absolute1.15V setting or board safety.

### Navigation: present versus reachable

Confirmed unconditional REF path within the CBS package:
`AMD CBS (7000) -> UMC Debug Options (7008) -> GDDR6 Debug Options (702E) -> GDDR6 DRAM Timing Configuration (702F)`.
This reaches timing control and UclkDiv1M0.

Other internal chains exist:

- `UMC Common Options (7007) -> GDDR6 Common Options (7028) -> DRAM Timing Configuration (702A) -> I Accept (702C)` contains Memory Clock Speed.
- `SMU Debug Options (7009) -> SMU Features (703E)` contains FCLK_DPM.
- `SMU Debug Options (7009) -> SMU Debug (703F)` contains DF override and voltage offset.

But7007 and7009 have no incoming REF in this package. Main AMITSE/external/dynamic form registration may expose them; that integration and the actual live screen are UNVERIFIED. Do not call these fully accessible merely because the individual questions lack suppress conditions. Existing Setup package separately includes Save Changes and Reset/Save Changes forms; its conditional tags were not evaluated for a live system.

### Native persistence, not custom SRAM programming

CbsSetupDxe instruction evidence:

- At2F7, load runtime services from SystemTable+58; at326, store to global40278.
- ConfigAccess registration: ExtractConfig588 at interface+0, RouteConfig86C at+8, Callback950 at+10 (instructionsAD1..B03).
- RouteConfig86C validates request header; at8E5 invokes config-routing method+20 (ConfigToBlock) for buffer size8B5.
- At8F1/8F8 prepares GUID atB180 and UTF16 name at3F028. GUID decodes to3A997502-647A-4C82-998E-52EF9486A247; name isAmdSetup.
- At90E supplies attributes7; at919 calls runtime method+58 (SetVariable), with data size8B5 and the configuration buffer.
  All selected instruction bytes checked against the module's section map. This is a positive static native save path, not a board execution test.

### Verification and result boundary

PASS: `python3 evidence/firmware-audit/20260920-df-init-route/menu-verify.py`; exact inputs, full IFR record boundaries/scopes, raw question fields, options, internal links and persistence instruction bytes.
PASS: independent fixed-offset question flag/var-offset read for8/8; retained EDK2 flag definitions checked.
UNRUN: live BIOS UI navigation, save/reset execution, post-reset settings readback, actual clocks, voltage, synchronization and latency. No hardware connection or setting change occurred.

Decision: use the native menu/configuration route first. Custom SRAM/DXE implementation remains deferred. Establish whether7007/7009 are reachable through current UI integration before proposing a minimal menu change; do not design a replacement clock controller based solely on incomplete UI investigation.

## Default 1:1:1 request — 2026-09-20

Fresh menu verifier PASS and builder regression 7/7 PASS. Exact IFR option defaults are Auto for Memory Clock Speed, UclkDiv1M0, FCLK_DPM and DF Clock Override Control. Existing builder changes only the stored AmdSetup DF request, not these IFR defaults; therefore it does not establish behavior after Load Defaults or NVRAM reset. Actual sync profile invocation exits2 (unsupported choice), no sync image created. This is a current tool limitation, not proof of hardware impossibility. Native DF help requests FCLK > UCLK, while UclkDiv1M0 help refers to FCLK; neither establishes MCLK=UCLK=FCLK. Need native consumer/divider semantics and default-initialization precedence before selecting a meaningful transform. No evidence establishes an exploit requirement; disassembly is analysis, not an exploit. Full BIOS deliverable incomplete. No firmware modification, no voltage change, no hardware verification. Literal commands and outputs: sync-feasibility.json.

## Chat-informed plan extension

See specs/2026-09-20-clv-sync-development-plan.md and chat-attachment-audit.json. Historical DF efficacy evidence is mixed and changes over time; later positive report does not prove1:1:1. Default initialization and real consumer semantics precede firmware implementation.
