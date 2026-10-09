# OC review correction — 2026-09-19

Scope: historical OC builds and user-facing claims. Evidence: docs/action-logs/2026-09-19-oc-recheck.md; fresh whole-image comparison against clv SHA-256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8.

The user goal is reduced memory latency with a BIOS-applied synchronous clock mode, considering SoC 1.15V. This is a research target, not a demonstrated safe setting or permission to flash.

Corrections supersede prior chat recommendations:
- sync_v002 (544b3c24d4b969c3b9b5ab7bbcb873b552f2757808a5855806b5324239749b27) requests IFR-labelled memory 1750 and DF 1500. Calling it 1:1:1 was incorrect.
- FclkDpm=0 is Disabled; Auto=0x0F.
- Divider enum Enabled does not independently prove UCLK equals MCLK or synchronized clocks.
- vdd80 contains raw 80 in an unresolved voltage field. It is neither proven +80mV nor 1.15V; do not flash it as a calibration experiment.
- No board-specific evidence establishes 1.15V as a safe ceiling. Prior safety assertions are withdrawn.
- The clv file contains memory enum 0x24 and DF request 1420; these are not measured operating frequencies.
- Earlier no-voltage O1 preparation expanded incorrectly into voltage and multi-variable profiles. Those generated files remain historical, NO-GO for flash from this review.
- AmdSetup lies before the default nvar_audit store start 0x1000. Reports selecting zero target variables do not validate these edits.
- Existing driver evidence assigns UCLK/FCLK from the same MemclkFrequency source; equal displayed metrics cannot alone prove synchronization.

Only observed-bytes checks passed. Applied clocks, voltage, training and stable latency improvement remain unrun. Keep original binaries unchanged; trace the actual control consumer and independent measurement path before a new candidate.

## R1 baseline reconciliation — 2026-09-19
Correction to the implied integrated W9/8-core/Steam-logo baseline: no such combined image was established by the scoped local inventory. Fresh hashes show candidates/BC250_5.00_clv_VcnUnlock_W9_v001.bin is 3c50bc9a65194b75ca805e6ed31c5778369de1fe8eca4600f44e15fae3b40fc3, identical to the W11 readback, NOT the original W9 readback (449475563a332a67a594d794cb2e2fbe4d251e0660b65742660b1ff1ce8463fb). Filenames are not revision identities.
Existing parser extraction and independent LZMA/GUID scan find the W9-labelled current candidate's injected B6250780 driver but no standard logo FFS or MeiMei core-unlock FFS in its main DXE volume. The SteamLogo StockNVRAM v002 image (1a0e41ef83b6e2f15676673ee18d7d514e3f4013bd3ded9f86d38e3037995f31) contains the logo section and MeiMei core driver, not B6250780. Driver absence is not proof that all other core-unlock methods are absent.
Historical W10 cpuinfo records 16 logical processors and 8 cores; it does not establish current board state or the W11 candidate's behavior. Preserved original recovery read-a/read-b/dump match 83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0. FirstMarker recovery matches its 20260918 readback at 7d420c9f2d46f39131f90827d2dd7b6ee8c7e3558ad8ef8a1d1e2c2a94bccb35.
Evidence: evidence/firmware-audit/20260919-oc-baseline/identity.json and docs/research/2026-09-19-oc-baseline-identity.md. Use clv for read-only control tracing; integrated OC build selection remains blocked, not permission to merge or flash.

## Operator baseline selection — 2026-09-19
Operator explicitly selects plain BIOS 5.00 clv as the development base and reports ability to flash now. Fresh source hash ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8 confirmed. This supersedes the integrated W9/core/logo baseline prerequisite for this OC track. SoC ceiling is 1.15 V, not mandatory setpoint or proven safe rating. Flash availability is operator-reported; no exact candidate flash approval or current chip identity is inferred.

## R2 first consumer and telemetry provenance — 2026-09-19
Exact clv CbsBasePei and AmdNbioSmuV10Pei code both serialize Setup offsets 0x316/0x330/0x6A3/0x703/0x704 into record IDs 0x11ED/0x1204/0x1331/0x1373/0x1374 respectively. Ten instruction windows were checked against module bytes with corrected TE raw offsets. This is the first located serialization stage, not final PLL/divider programming or complete caller provenance.
Retained cyan_skillfish_ppt.c maps SMU_FCLK and SMU_MCLK to the same METRICS_CURR_UCLK/MemclkFrequency source; gpu_metrics UCLK/FCLK assignments alias too. A compiled C harness using the four exact assignments passed. This proves source-level aliasing, not installed-kernel equivalence or physical synchronization. Full R2 remains open: follow record consumers and identify independent telemetry. A task-list 'done' label must not override this partial technical status. Evidence and exact module hashes: docs/research/2026-09-19-clock-control-trace.md; evidence/firmware-audit/20260919-clock-trace/serialization.json.

## Corrections per project G7 (2026-09-19)

1. **Overclaim Correction on Actuator Selectors & CPU Core Path**:
   - The assertion that `FUN_0002bdec` and `FUN_0002be40` writing to SMN `0x0115A030` selectors 0 and 1 represent "package / uncore" rails versus "per-core CPU VID" was an overclaim. While `FUN_00020b04` loops across 8 cores and writes VID to per-core apertures `*(iStack_64 + 0x10b0)` and `*(iVar8 + 0x10)`, having separate per-core VID apertures does **not** distinguish a shared CPU supply from SoC or uncore rails.
   - Driver labels (`cyan_skillfish_ppt.c` assigning `Voltage[0]` to `METRICS_VOLTAGE_VDDSOC` and `Voltage[1]` to `METRICS_VOLTAGE_VDDGFX`) do **not** identify actuator `0x0115A030` selector 0 or 1 in the absence of a verified firmware producer-to-actuator mapping.
   - The assertion that there is "no stock 1364 consumer" in PEI/DXE was too broad: direct static call-site coverage in current readers is bounded, but indirect, dynamic, or computed dispatch coverage is not exhaustive across all modules.

2. **SMU Metrics Producer Trace (Robin-5, CLV ROM offset `0x8FEF00`) [PROVISIONAL — under recheck]**:
   - Status: PROVISIONAL pending fresh pinned Robin-5 disassembly, literal verification, and instruction mapping.
   - SmuMetrics_t producer is at `FUN_00029e34` (corresponding to `FUN_00029aec` in Robin-3).
   - Base literal `0x17f84` holds `0x107fc`. Export buffer base `iVar13` is at `0xcb68`.
   - In `FUN_00029e34`, the telemetry loop (`uVar17 = 0..1`) stores:
     - `Voltage[0]` (offset `+0x50`, `0xcbb8`) <- utrunc.s(float at `0x109f4` * 1000.0f)
     - `Voltage[1]` (offset `+0x54`, `0xcbbc`) <- utrunc.s(float at `0x10a08` * 1000.0f)
     - `Current[0]` (offset `+0x58`, `0xcbc0`) <- utrunc.s(float at `0x109f8` * 1000.0f)
     - `Current[1]` (offset `+0x5c`, `0xcbc4`) <- utrunc.s(float at `0x10a0c` * 1000.0f)
     - `Power[0]`   (offset `+0x60`, `0xcbc8`) <- utrunc.s(float at `0x109fc` * 1000.0f)
     - `Power[1]`   (offset `+0x64`, `0xcbcc`) <- utrunc.s(float at `0x10a10` * 1000.0f)
   - Source addresses `0x109f4` (`Voltage[0]`) and `0x10a08` (`Voltage[1]`) are distinct from actuator state struct `_DAT_00017124` (`0x13474`), where `+0x00` is Domain 0 voltage float, `+0x04` is Domain 0 VID, `+0x20` is Domain 1 voltage float, and `+0x24` is Domain 1 VID. Verified producer reads 0x109f4/0x10a08, not direct alias 0x13474; unequal addresses do not disprove an actuator->telemetry copy, and source writer and copied provenance remain unknown.
- Telemetry & Clock discrimination: Driver pp_dpm_fclk and pp_dpm_mclk read from the same MemclkFrequency field in cyan_skillfish_ppt.c. Independent measurement requires querying DF state (PPSMC_MSG_QueryDfPstate 0x13, handler 0x1E988 in Robin 5) or SoC clock (PPSMC_MSG_QueryVddcrSocClock 0x11, handler 0x2EA74) via SMU mailbox rather than relying on duplicated driver metrics. SetMaxDeepSleepDfllGfxDiv (Queue 0 msg 0x1A) directly manipulates DFLL dividers.
   - Withdrawal per G7: The prior claim that "periodic ADC poll populates" `0x109f4`/`0x10a08` is withdrawn as unsupported; the writer routine is currently unidentified in static trace. Scope of negative scan covers only the direct literal-reference path, NOT all stores/indirect/DMA writes, and does NOT establish an external hardware writer. Float-to-integer conversion is unsigned (`utrunc.s`), not signed `trunc`.

3. **Clock Mailbox Handler Provenance & Measurement Falsification per G7 (2026-09-19)**:
   - **Correction on Mailbox 0x11 (`0x0002EA74`)**: The prior assumption that `PPSMC_MSG_QueryVddcrSocClock` provides an independent hardware clock measurement is falsified. Trace of `0x2EA74` shows it loads the domain index from mailbox argument bits [31:16], looks up domain mapping at `0x13EF4 + index*4`, and returns unsigned truncation (`utrunc.s`) of an internal software committed state float from `0x13F48 + index*12` (struct `0x13EEC + 0x5C + index*12`). This array is populated by firmware applier `FUN_0002e788` from requested targets in `0x14038` (loaded from P-state tables at `0x7B5C` by `FUN_0002e9dc` or dynamic requests by `FUN_0002ea08`). It does NOT sample hardware PLL counters or physical clock lines.
   - **Correction on Mailbox 0x13 (`0x0001E988`)**: The prior assumption that `PPSMC_MSG_QueryDfPstate` provides a frequency or operating telemetry measurement is falsified. Handler `0x1E988` ignores arguments, reads struct `0xCEE0` byte `+0x0D` (`0xCEED`, current P-state) and byte `+0xF7` (`0xCFD7`, P-state count/bound), returning `(byte[0xCFD7] - byte[0xCEED]) - 1`. This returns an integer state delta/count, NOT a frequency in MHz.
   - **Result**: SMU mailbox queries 0x11 and 0x13 return internal firmware state fields and state counters, not independent physical hardware clock telemetry. Independent clock frequency verification remains unachieved via these mailbox commands.
  
  4. **Clock Actuator Chain & Register Apertures (Robin-5 offset `0x8FEF00`)**:
   - Actuator `FUN_0002e788` dispatches domain programming through `FUN_00023890` -> `FUN_000235c8`, which writes to SMN apertures `0x0115Bxxx` (CPU Cores 0..7 and Group 1), `0x0116Cxxx` (Group 5), `0x0116Dxxx` (Group 6), and Domain 0x13 gate `0x01D80414`.
   - Correction per Root Review: Absence of Data Fabric (`0x0001xxxx` / `0x0005xxxx` / `0x001Exxxx`) or UMC register ranges in this observed address set cannot prove UCLK is not controlled, as the clock generator/PLL architecture may utilize another aperture or indirect mechanism. UCLK mapping/control unestablished; observed address set only. No claim of physical clock synchronization.
   - Target float array `0x14038` is updated via 1-based index `1..20` using prebiased base `0x1402C + index * 12`. Bulk P-state loader `FUN_0002e9dc` reads 80 bytes from `0x7B5C + pstate * 100 + 0x48`; structural relationship to the 100-byte row stride is preserved as an open technical uncertainty without runtime buffer evidence.
   
   ## G7 host influence correction — 2026-09-20
   Root reran `python3 scripts/verify_df_table_population.py` successfully and inspected its entire checking logic. It verifies static table content, not absence of indirect/DMA/runtime writers. Conclusions in `docs/research/oc-df-table-population.md` that BIOS cannot influence frequencies or that signed SMU patching is necessary are withdrawn as unproven. Callback 0x1BC80 calls 0x21E8C and conditionally 0x1E010, so direct-reference absence does not prove transitive isolation. Physical FCLK/UCLK/SOCCLK identities and DDR4/GDDR6 rate equivalence are not established by float values. The static defaults remain observed bytes, not hardware limits.
   
   ## PPTable callee side effects & DF isolation audit — 2026-09-20
   Offline investigation of callback `0x1BC80` exact callees (`0x21E8C` and conditional `0x1E010` triggered by PPTable flag `+0x7E` at `0x7B5C + 0x3FE`):
   - `0x1E010` does NOT modify table frequencies or entries in DF table `0xCF0C..0xCFD4`. It loops over active CPU cores (0..7) based on enable flags at `0x7AE0 + 0x28 + i` and writes literal `1` to per-core aperture `aperture + 0x142c` (`0x0140142C`, `0x0142142C`, `0x0144142C`, `0x0146142C`, `0x0180142C`, `0x0182142C`, `0x0184142C`, `0x0186142C`). This acts as an enable / commit trigger, not a table value editor.
   - `0x21E8C` scales 8 P-state ratios (P0..P7 from `0x7B5C + 0x04..0x13` [CpuFid] and `+0x14..0x1B` [CpuDid]) via `0x1CBFC` into internal SRAM `0xF104..0xF123`, programs 8 SMN register pairs `0x0115A820..0x0115A85C` (stride 8), writes `0x1FE` to SMN register `0x01004220` via `0x14FC(4, 4, 0x1FE)`, programs SMN register `0x0115A864`, and writes `(bVar1 - 1 & 7) << 4` to per-core clock register `aperture + 0x10bc`.
   - Neither callee references struct `0xCEE0` or writes to DF P-state table `0xCF0C`. Bounded static coverage confirms no direct DF table modification, while indirect/DMA coverage remains non-exhaustive.

   ## PPTable coefficient producer & consumer trace — 2026-09-20
   - **BIOS Producer**: `AmdNbioSmuV10Dxe` (`b158f039f48db05e352b965a62c8e983a395a4858791c93c73f727285c9ac8d8`) function RVA `0x17DC` constructs the 0x49C-byte PPTable by copying compiled constant template from RVA `0x5D20` (raw `0x5D20`).
     - `+0x04..+0x13`: 8 uint16 values `[128, 102, 93, 98, 91, 96, 89, 96]` = `CpuFid` for P0..P7.
     - `+0x14..+0x1B`: 8 uint8 values `[8, 8, 8, 10, 10, 12, 14, 24]` = `CpuDid` for P0..P7.
     - Formatted at RVA `0x1CE5`/`0x1CEA` with string `PSTATES[%d] - CpuFid = 0x%02x, CpuDid = 0x%02x` at RVA `0x6AD8`.
     - `0x17DC` leaves these fields unmodified from the constant template (no PCD/AmdSetup override in static trace).
   - **Consumer Chain**: SMU validator `0x1BD20` checks `0x50 <= CpuFid <= 0xA0` and `8 <= CpuDid <= 0x30`. Consumer `0x21E8C` invokes `0x1CBFC` computing `((CpuFid << 2) * 50000 / CpuDid) * 1e-6` = `(CpuFid * 200) / CpuDid` MHz:
     - P0=3200 MHz, P1=2550 MHz, P2=2325 MHz, P3=1960 MHz, P4=1820 MHz, P5=1600 MHz, P6=1271.4 MHz, P7=800 MHz.
     - Programs CPU core clock SMN registers `0x0115A820..0x0115A85C` and per-core aperture registers `aperture + 0x10BC`.
   - **Domain Discrimination**: These coefficients are exclusively CPU core P-state ratios and clock controls, NOT memory controls or MCLK.
   - **DF Clock Override 1374**: Serialized in `AmdFabricAriPei` (RVA `0x11C98`) from Setup `+0x704` (`DfClockOvrd`). Static caller audit confirms neither identified `$INV` reader (`AmdFabricAriPei` `1D3C` or `AmdCcxVhAriDxe` `5AC4`) requests token `0x1374`.
   
## Stock capture route — 2026-09-20
Existing clock probe reused and tested with five synthetic cases (target filtering, empty tree, missing files, metric hash, fixture preservation). Full suite: 16 passed. Evidence: evidence/firmware-audit/20260920-stock-capture-check/. Runbook: docs/runbooks/2026-09-20-oc-stock-capture.md suppresses command-line, hostname and uevent collection at source. Local DRM device 1002:1900 is not target 1002:13fe; no live BC250 capture or remote connection occurred. Host tests do not establish physical clock/voltage measurement. Authorized board access or an operator-run capture remains required.

## G7 indirect consumer review — 2026-09-20T01:31:59+05:00
Root ran verify_df_indirect_consumer.py: PASS for selected bytes/tables only. This does not exhaust 31 indirect edges or prove no stock consumer. Report edge counts disagree with enumerated sites. Claimed FirstMarker ROM offset 0x01FC0000 lies outside 16 MiB and is withdrawn; marker dispatch does not establish register capture. Proposed 1500/1600 experiment is withdrawn pending measured baseline and exact probe design. See docs/action-logs/2026-09-20-oc-indirect-root-review.md.

## Offline route correction — 2026-09-20
User explicitly removes live telemetry from offline BIOS build prerequisites; hardware acceptance remains separate. Root checked pinned Queue3 0x1D map: no descriptors14..18 in static 20-entry array. API indices are not descriptors. Actuator0x2E788 is gated by equality of state words at0x13EEC/+4, not merely a target-versus-committed comparison; prior verifier prose overstated that comparison. Historical decompile starting0x2EA0C misaligns setter prologue; exact entry0x2EA08 verified. See docs/research/2026-09-20-oc-host-domain-route.md and reproducible verify.py. No candidate built or firmware modified.

## DF init route and decompiler limits — 2026-09-20
Fresh read-only Ghidra output and independent byte audit resolve the narrow 0x1C3B0 -> 0x1E038 path. Argument getter 0xFFC reads one queue argument word; high byte goes to CEE0+11, low byte to CEE0+12, bits16/17 to 1105C+2A/+2B. No external row-pointer argument is passed on this edge. Both init branches derive row pointers from internal vectors, not the argument. Initial config8 yields CF84/CF5C/CF34/CF0C; config7 branch yields CFAC in slot0 with remaining static vector entries FF. Runtime vector/config changes remain unexhausted.
G7 qualification: 0x2E4C4 loads an SRAM config word (initially8), not a fresh hardware configuration register. Fresh Ghidra C output misrecovers Xtensa loopgtz in 0x1E038; use checked assembly (1E05A and1E085), not apparent unreachable/jumptable C blocks. Parameters printed for 1EF18 in that decompile are not a recovered external-table interface; the actual callee reads CEE0 globals. 1E1D0 writes raw row bytes0/1 to apertures115C1A0/4/8; 1E260 uses row bytes8/9/B for apertures115C9A0..AC and116C1A0..AC. The stored float at row+4 is not the divider input to those two helpers. No physical domain identity, sync, voltage or hardware acceptance proved. Full transitive side callees30DF4/2CEF4 and BIOS sender remain incomplete. Report: docs/research/2026-09-20-oc-df-init-route.md; byte verifier: evidence/firmware-audit/20260920-df-init-route/verify.py (855 instructions matched). No ROM/hardware write.

## DF sender follow-up — 2026-09-20
Read-only Ghidra + raw-byte comparison: 51 unaligned candidates to literal171EC resolve to50 decoded references and one false positive2935D inside MOVI2935C. In the47 selected function listings (2532 instruction records), offset12 has only the known store1E041; no direct load at that offset identified. This does NOT prove CEF2 unused: aliases, wider/indirect loads and DMA remain unexhausted. All233 retained x86 executable bodies hashed; 1125281 instruction records byte-checked. No raw or decoded Q5 port literals in this census. DXE message9 site2D48 uses the Q2-like transport3120 with03B10998/03B10564/03B10528, not Q5 init; message number alone is not identity.
Method pivot found real Q5 transport in PSP type28, not in x86 UEFI modules: exact clv entry ROM984F00,size108400,sha5b6828bff3f10f1b120b279932af156438e1bdd724508e44b7630fce9716251f; function entry-relative118E8 / ROM9967E8 maps03B10700 via svc7D, uses response offset10704 and message10718, writes incoming r1 argument and r0 message. Direct callerC526 loads message/argument/timeout from r4+38/+3C/+40 and output pointer r4+44; other decoded direct callers send16 or3. Concrete init9 argument producer remains unresolved upstream of C51C/C526. No evidence that low byte controls frequency. Fresh LLVM Thumb windows fully byte-checked; mixed code/data trial warnings retained, replaced by exact windows without warnings. No installed dependencies, ROM changes or hardware actions. Supplemental sender-result.json and sender-t28-result.json under existing20260920-df-init-route; existing report appended. Next investigation target is upstream population of the PSP caller structure, not another generic x86 message9 search.

## Goal continuation: PSP service selector resolved — 2026-09-20
Static branch/table check resolves type28 opcode1037 to C51C/C526 -> Q5 transport118E8, conditional on dispatcher preflight. TOS type02 wrapperF4C4 (ROM8FAEC4) constructs service1037, copies message/argument/poll-limit into request+38/+3C/+40, invokes SVC F2 and returns request+44 through caller output pointer. Its single direct BL caller at12650 passes message0F, argument0, timeout1000: not init9. Other components/indirect callers remain unexhausted. The type02 literal03010718 lead at2880 feeds a high-bit notification write, not an observed init9 send. Immediate1037 matches in x86 Fabric/Smu PEIMs are typed-record serializers (word record ID plus byte value), not this PSP service: do not conflate numeric namespaces. ROM remains unchanged; synchronized BIOS remains unbuilt because BIOS-callable coefficient mutation, physical domain mapping and voltage semantics are unresolved. Neither init9 nor the newly decoded1037 service is a MHz-setter. Existing write-SRAM DXE code was located but not executed or adopted for OC; its historical presence alone does not close these gaps. Exact checks: goal-verify.py and goal-result.json under the same DF evidence directory. No new flash recommendation.

## Native BIOS UI priority correction — 2026-09-20
Operator asks whether the existing BIOS overclock menu can already perform the requested changes on the powered board. Root has inspected IFR fields and some serialization, but has NOT completed a native-menu workflow audit on the exact selected clv image (visibility conditions, callbacks, save/reset path, defaults and downstream application). Do not equate missing final consumers in a bounded scan with nonfunctional native controls. The retained IFR map is sourced from historical e1_setup_ifr.txt, not fresh proof of visibility in the current clv UI. Fresh source hash and selected lines rechecked. Prioritizing custom SRAM/DXE work before resolving this native route was premature; suspend that design direction pending the menu audit. UI editing/saving NVRAM must be distinguished from immediate clock reprogramming; a same-session apply capability is unproved. No board changes authorized by this question.
Correction to native-UI entry: source hash verification passed, but exact field-map excerpt equality failed for all five entries. The derived map is not literal source text; raw source matches must be used for field-presence evidence. This further limits any claim about the selected clv UI.

## Exact-clv native menu findings — 2026-09-20
Freshly decoded CbsSetupDxe7ff717d51c9a from the pinned clv census, rather than historical dump IFR. Complete forms package60725 bytes walked with balanced scopes. All8 selected questions (memory clock, timing control, UclkDiv1M0, FCLK_DPM, VDD offset control/value, DF override control/value) are editable, RESET_REQUIRED, and have no enclosing suppress/gray/disable scope in this exact module. Only FCLK_DPM has CALLBACK. Native RouteConfig atRVA86C calls ConfigToBlock then gRT->SetVariable at919 for AmdSetup, GUID3A997502-647A-4C82-998E-52EF9486A247,size8B5,attributes7; gRT initialization and registration pointers byte-checked. Thus native edit/save route exists statically, without a custom driver.
Unconditional form references from CBS7000 reach UMC Debug Options -> GDDR6 Debug Options -> GDDR6 DRAM Timing Configuration with UclkDiv1M0. Forms7007 (UMC Common) and7009 (SMU Debug) have no incoming REF in this package; their children include Memory Clock Speed and DF override/FCLK_DPM. Do not equate local absence of suppress conditions with live menu reachability; AMITSE/external/dynamic links remain unverified.
Important fresh help strings: DF Clock Override/Control says 'When you try to override FCLK, please make sure FCLK > UCLK and Memory P-state is disabled.' This is built-in UI guidance, not hardware proof, and does not endorse1:1 via this control. UclkDiv1M0 help says 'UclkDiv1 option, relative to FCLK.' VDDCR_VDD offset help specifies signed integer[mV], but VDDCR_VDD is not thereby identified as SoC and offset is not absolute voltage. G7: prior blanket uncertainty about UI-advertised voltage units is narrowed; actual rail/consumer remains unresolved. Existing historical HIDDEN annotation must not be applied to clv. Parser HIDDEN means condition nesting, not evaluation; parser language label drops initial'en', and historical strings contain NUL terminators. Raw current question flags checked against EDK2 definitions0x10 reset/0x04 callback/0x01 read-only. No settings or board writes. Evidence menu-result.json/menu-verify.py under same DF evidence directory; report appended.

## Default 1:1:1 request — 2026-09-20
Fresh menu verifier PASS and builder regression 7/7 PASS. Exact IFR option defaults are Auto for Memory Clock Speed, UclkDiv1M0, FCLK_DPM and DF Clock Override Control. Existing builder changes only the stored AmdSetup DF request, not these IFR defaults; therefore it does not establish behavior after Load Defaults or NVRAM reset. Actual sync profile invocation exits2 (unsupported choice), no sync image created. This is a current tool limitation, not proof of hardware impossibility. Native DF help requests FCLK > UCLK, while UclkDiv1M0 help refers to FCLK; neither establishes MCLK=UCLK=FCLK. Need native consumer/divider semantics and default-initialization precedence before selecting a meaningful transform. No evidence establishes an exploit requirement; disassembly is analysis, not an exploit. Full BIOS deliverable incomplete. No firmware modification, no voltage change, no hardware verification. Literal commands and outputs: sync-feasibility.json.

## Chat-export evidence qualification — 2026-09-20
Reviewed208 messages and photos7/9/16 from operator-supplied ChatExport_2026-09-20. Historical late report772239 says DF900/1400 affects performance, qualifying earlier no-effect report; hardware feedback modification and reported >1.2V precede DF1800 report772344, outside current ceiling. Photo16 shows131.4ns, not proof of sync. Photo9 establishes historical UMC Common menu access, not exact-clv identity. Plan: specs/2026-09-20-clv-sync-development-plan.md; next step reconcile actual attached SYNC image differences rather than repeat labels. No firmware write. Raw export/access-bearing URL excluded.

## CLV sync phase-2 checkpoint — PARTIAL, not complete (2026-09-20)

Independent integration re-opened four current research role paths against pinned clv ROM SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`:

1. `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-sync-stage2-independent-baseline-review.md` (SHA-256 `6098c93922659e767bab821a961ae4e7a1de133fed8ea1e0a3c9539afb066c7b`); machine matrix `baseline-ifr-builder-review.json` SHA-256 `0fdc61329fe4e4a6baa0ce039673c0b48e9cca3cc2cc7f4e87a7d1cb84e250e6`, verifier `38/38 PASS`.
2. `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-sync-stage2-defaults.md` (SHA-256 `27fad998574a9e3ae3071cfa30f9aa18cae7e1a0bfed9b3baa5b6553b05bfb99`); current result `stage2-defaults-result.json` SHA-256 `e6e3a142d531de17ca5c0c3325f2559e20c01f2395de7da1eb0c898be32b3173`, `59/59 PASS` static checks.
3. `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-sync-stage2-consumer.md` (SHA-256 `514a6973a4aa04eec4a1842bf6759753b6319b1aefb5d3d64e827df7485c889a`); current result `consumer-boundary-result.json` SHA-256 `e7b1f6f66ed066029a93cf88ea7fb5cb804df39570af9f3a1b86645882e10d1`, `60/60 PASS`.
4. `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-sync-stage2-consumer-followup.md` (SHA-256 `bccb7818b1fba2a270eb6867325461acd3612143b6c14ce498feacb02754394b`); current result `init-structure-xref-result.json` SHA-256 `ce39669089865290433995719c3ba906111856c7232932ebd73c095683a82bc4`, `16/16 PASS`, manifest check from project root `3/3 OK`.

### Verified partial findings and qualifications

- **Persisted bytes are not clocks:** pinned clv `AmdSetup` body base `0x4CF` has `+0x316=36 (0x24)`, `+0x330=1`, `+0x6A3=15`, `+0x703=1`, `+0x704=1420 (0x058C)`. The existing host builder modifies only stored `+0x704` for `df1400`; it leaves MCLK/UCLK/FCLK fields and defaults unchanged. A stored-request-only image cannot establish `MCLK=UCLK=FCLK`, migration precedence, physical application, training, or hardware acceptance.
- **Default layers remain separate:** existing `AmdSetup` wins on the successful `GetVariable` path; missing-variable helpers write `0xFF`, `0xFF`, `0x0F`, `0xFF`, `1000`. Exact-clv IFR declares enumerated defaults `0xFF`, `0xFF`, `0x0F`, `0xFF`; numeric `+0x704` has no option/default opcode. The updated defaults result statically maps callback RVA `0x950` action `EFI_BROWSER_ACTION_DEFAULT_STANDARD (0x1000)` to helper `0x2FE4`, which writes `+0x704=1000`; callback execution and post-reset NVRAM readback remain unrun. Do not promote `1000` to an observed live Load Defaults value.
- **Consumer boundary is not final consumption:** the CBS serializer emits tokens `0x11ED`, `0x1204`, `0x1331`, `0x1373`, `0x1374`; AmdFabricAriPei's decoded direct reader requests are only `0x10FF` and `0x1104`, not `0x1204`. The selected AmdNbio PEI windows construct token `0x1204` records but contain no promoted direct call in the bounded window. This is not a census-wide absence claim; indirect/computed/GUID/HOB/DMA/runtime requesters and final actuators remain unknown.
- **Artifact-integrity qualification:** the updated defaults result/script changed after its earlier `SHA256SUMS.final` was generated. The current manifest check reports result/script/stdout failures (stale hashes) while stderr remains `OK`; this is an integrity bookkeeping issue, not a changed ROM finding. The worker-owned defaults report/evidence must be refreshed by its owner before treating its manifest as current. No worker-owned report or manifest was edited here.

### Remaining acceptance gates

1. Execute or otherwise acceptedly model `Load Optimized Defaults` and post-reset NVRAM readback for all five fields, preserving existing-variable, helper-fallback, declared-IFR, and callback distinctions.
2. Recover complete containing-function boundaries and first post-builder direct calls/argument construction for both token-`0x1204` serializers; classify indirect/computed/HOB/DMA paths without promoting token presence to consumption.
3. Map fields/tokens to the actual divider/clock/training actuator, units, valid shared range, Memory-P-state behavior, and synchronous-crossing selection.
4. Specify migration/invalidation precedence and only then build/review a reversible candidate; keep voltage, CPU, timings, and unrelated settings unchanged.
5. Separately perform hardware acceptance with recovery/readback, cold/warm/Load-Defaults repetitions, independent clock/divider observation, performance, and error screening. No flash/release approval follows from this static checkpoint.

Evidence class remains observed-bytes + static-analysis + bounded host-tested models. Firmware execution, physical clocks, synchronization, training, voltage, and hardware acceptance remain unrun.

## G7 qualification — `+0x704` callback branch is static only (2026-09-20)

The updated defaults verifier's 59/59 checks and retained `CbsSetupDxe` instruction window were independently reopened. Callback registration stores RVA `0x950` at protocol interface `+0x48` (`0xAF6`/`0xB03`). Under the checked x64 ABI window, `Action` arrives in `RDX` and `QuestionId` in `R8W` (`0x96F`). The callback returns early for actions `3` and `4` (`0x979`/`0x983`); action `2` is routed to the retrieve path (`0x9FB`/`0xA03`/`0xA1D`), while action `0x1000` (`EFI_BROWSER_ACTION_DEFAULT_STANDARD`) falls through the `0xA08` compare to `0xA11 -> 0x2FE4`. The helper writes `AmdSetup+0x704=0x03E8` (`1000`). No `QuestionId` equality comparison is visible on this default branch. The exact `+0x704` IFR question has no CALLBACK flag, unlike `FCLK_DPM` at `+0x6A3`.

This proves only a static callback code path and its branch conditions. It does **not** prove that the HII browser invokes this callback for Load Optimized Defaults, that the numeric `+0x704` question is dispatched through it, or that NVRAM is persisted/read back afterward. Keep the status `STATIC_ONLY_CALLBACK_NOT_EXECUTED`; do not state “Load Defaults resets `+0x704`” as observed behavior. Worker-owned defaults manifest is stale after the 59-check update and remains an integrity qualification until its owner refreshes it.

## G7 report-snapshot correction — baseline review path updated (2026-09-20)

The independent baseline review report was reopened and extended with the callback/defaults and token-`0x1204` requester qualifications above. Its authoritative current SHA-256 is `a98b22575d10fdcdfd3898d336bfb09adea4d7a1eb45f5624f5d515721676327` (the earlier `6098c939...` value is superseded). The report's prior `48/48`/`4/4` defaults wording is explicitly superseded in its follow-up section; current defaults evidence is `59/59` static checks with a stale worker-owned manifest. No worker-owned defaults artifact was modified by this reviewer.

## CLV token-0x1204 complete function-boundary follow-up — bounded partial result (2026-09-20)

A fifth current research role path was reopened and independently checked:
`/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-sync-stage2-function-boundary.md`, SHA-256 `e2db1331a26c7de584d5638913708a77b022fffedbacbb79ffa0b944100aa24f`; machine result `evidence/firmware-audit/20260920-clv-sync-stage2-function-boundary/function-boundary-result.json`, SHA-256 `6c77b08ef2511d2042cb686802f3f52428afa17a95c2896f2366630f90329c4c`, manifest `3/3 OK`, `30/30 PASS`.

Complete containing-function evidence extends the prior tiny-window result: `AmdNbioGfxARIPei` builder `0x4E20..0x12FA3` and `AmdNbioSmuV10Pei` builder `0x5770..0x138F3` each contain the token-`0x1204` record and exactly two direct calls to their size helper before/around the size gate, with zero direct calls after the token body before `$FFFF` sentinel and successful return. Wrappers `0x4DF0` and `0x5740` construct three builder arguments, call the builder once, and return immediately.

Qualification: this closes only the selected direct-call/function-boundary scope. It does not exclude callback-table/registration indirection, computed calls, HOB/DMA/runtime delivery, later-phase consumers, or hardware actuation. The next edge is wrapper registration/indirect dispatch, not another token-literal scan. Phase 2 remains **PARTIAL**.

## G7 gate-status update — direct function-boundary subgate complete (2026-09-20)

The direct containing-function subgate in remaining gate 2 is now satisfied for the selected two AMD PEI builders/wrappers (`30/30 PASS`); do not repeat that literal/function-boundary scan. Gate 2 remains open for wrapper registration/indirect dispatch and computed/callback-table/HOB/DMA/runtime requester classification of token `0x1204`. This static closure still does not identify a clock/divider/training actuator or hardware behavior.

## Current defaults integrity and offline/hardware gate correction — 2026-09-20

The defaults worker's corrected artifacts were independently reopened after the prior stale-manifest state. From the evidence-directory working directory, `sha256sum -c SHA256SUMS.final` returned `9/9 OK`. Current result `stage2-defaults-result.json` SHA-256 is `7983941a2b725df945b695716cc797228df511c609ac0c45a261ccfec5b169b2`, verifier `stage2_defaults_verify.py` SHA-256 is `a20ae7bc7c1874b8daaa5fcf37db9985101591a2b78eb336d015353a212a6f76`, and result status is `72/72 PASS`.

The corrected static gate table records `+0x704` QID `0x37E` as `CALLBACK=false`; only FCLK_DPM `+0x6A3` QID `0x7045` has CALLBACK. The exact clv callback's `0x1000` branch to helper `0x2FE4` is therefore a statically proven side effect path reachable through the callback-bearing FCLK_DPM route, not proof that the numeric `+0x704` question directly invokes it. EDK II `SetupBrowser` excerpts are external-primary semantic references for browser dispatch and callback-flag gating; they do not demonstrate execution of this exact clv firmware. Result status remains `STATIC_ONLY_CALLBACK_NOT_EXECUTED`; no live browser invocation or NVRAM/reset readback occurred.

This distinction changes gate placement: live/default/reset readback is a **hardware-acceptance/release gate**, not a mandatory blocker for generating an explicitly experimental offline candidate after offline consumer/semantic gates. Offline artifacts must preserve the unrun status and cannot claim applied defaults, `1:1:1`, or hardware acceptance.

## CLV wrapper registration/dispatch boundary — static candidate only (2026-09-20)

Sixth current research role path reopened: `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-sync-stage2-wrapper-dispatch.md`, SHA-256 `a7c15d391cb9bc949c92d195ac7ff84b4381bfc78c0a38ca625dd182bf8ea11a`; machine result `evidence/firmware-audit/20260920-clv-sync-stage2-wrapper-dispatch/wrapper-dispatch-result.json`, SHA-256 `82193f3f116df851c5b3eaa259484602be795e7c4db0e3432c9e5c459019f443`, `20/20 PASS`, manifest `3/3 OK`.

Exact module data statically decodes wildcard/event descriptors `<QQII> = (0xFFFFFFFF, 0, imagebase+wrapper, 0xFFFFFFFE)` for Gfx wrapper `0x4DF0` and SMU wrapper `0x5740`, with provider-table pointers resolving to each descriptor. This establishes a registration **candidate edge** (`provider pointer -> descriptor -> wrapper`), not an installed or invoked dispatcher. The module-local indirect-call inventories (28/36) do not join to those descriptor/table addresses; actual dispatcher, cross-module/computed/HOB/DMA/runtime delivery, and hardware consumption remain unresolved. Do not promote descriptor presence to callback execution or final token-`0x1204` consumption.

## G7 report/current-snapshot correction — final defaults and wrapper review (2026-09-20)

The independent baseline review report was reopened after corrected defaults and wrapper-dispatch artifacts; current report SHA-256 is `f8e33901a74ef171adc1244f14d3c750942a43a58b71596a6275676abf201df3` (supersedes `a98b2257...`). Current defaults human report SHA-256 is `dbab884487d2271f932dd0937845f6586b03200921d859ccc64fc3312d62901c`; machine result is `72/72 PASS` with manifest `9/9 OK`. Earlier stale-manifest qualifications remain historical and are superseded by the corrected readback, while the static-only/browser-unrun qualification remains active.

The wrapper-dispatch review does not alter the gate: descriptor/provider-pointer presence is a static registration candidate, not proof of installed/invoked callback dispatch or token-`0x1204` consumption. Live/default readback remains hardware-acceptance/release-only, not an offline artifact-generation prerequisite.

## Exact-clv configuration-domain matrix — UI overlap is not semantic support (2026-09-20)

Own read-only matrix reopened exact menu result and pinned clv bytes:
`docs/research/2026-09-20-clv-sync-configuration-domain-matrix.md` SHA-256
`e50380becf48ba4f22f28baad415f2594ddea08038ea65b9b7b359c200e3888f`;
machine result `evidence/firmware-audit/20260920-clv-sync-configuration-domain-matrix/configuration-domain-matrix.json`
SHA-256 `56f5fc1e84d5eea4178d8256c041260457378c45c46954036093f67a30a783af`;
verifier `23/23 PASS`.

The exact-clv UI advertises Memory Clock Speed labels `125..2000MHz`, while DF
Clock Override is numeric `[0,2000]`; every displayed Memory label lies inside
that interval. This is only UI numeric overlap. Memory enum codes are distinct
from the displayed labels, UclkDiv1M0 offers `Auto=0xFF`/`Enabled=1` but no decoded
ratio, and no common physical unit/domain, GDDR6 conversion, training range, or
synchronous-crossing selection is observed. DF help text requesting `FCLK > UCLK`
and disabled Memory P-state is guidance, not runtime state or proof of a valid
profile.

Minimum offline semantic gate remains open: byte-backed consumer/actuator mapping
for all five fields; unit/rate conversion and UclkDiv1M0 semantics; Memory-P-state
and training relation; synchronous-crossing selection; and migration-aware default
precedence. Live telemetry is not an offline prerequisite, but remains required for
hardware acceptance of applied clocks/training/stability. No frequency, voltage,
safety, or `1:1:1` implication is inferred from numeric overlap.

## Supplemental native Memory P-state mapping — static gate context (2026-09-20)

Worker-owned exact-clv Memory P-state artifact independently reopened:
`docs/research/2026-09-20-clv-sync-stage2-memory-pstate.md` SHA-256
`e018df53b222110702a94781684760db5174c12eb1e17cd51abbacb1284409c3`;
machine result `evidence/firmware-audit/20260920-clv-sync-stage2-memory-pstate/memory-pstate-result.json`
SHA-256 `237546fe5cc4edf44659dab93ce2ccd13ecbd817a6808ef18fa599b1da0b87c7`;
`9864/9864 PASS`; evidence-directory manifest `4/4 OK`.

Exact native control: `AmdSetup+0x36D`, QID `0x25E`, form `0x7032` DRAM Power
Options; options `Auto=0xFF`, `Enabled=1`, `Disabled=0`; flags `0x10`
(reset-required, no callback/read-only), no local conditional scope; package-local
path `0x7000 -> 0x7008 -> 0x702E -> 0x7030 -> 0x7032`. Pinned clv byte at
absolute ROM `0x83C` is `FF` (`Auto`). `CbsBasePei` statically serializes the
field as `$INV` record `0x123D`.

Qualification: this identifies the UI control and serializer edge only. It does
not prove that `Disabled=0` is training-safe, that token `0x123D` reaches the DF
override consumer, or that it enforces synchronization. The DF help phrase is
UI guidance, not a causal hardware constraint; no value was changed.

## G7 correction — adjacent serializer record discrimination (2026-09-20)

Fresh bounded discrimination evidence (`docs/research/2026-09-20-clv-sync-stage2-memory-pstate-discrimination.md`, SHA-256 `43f37b835c3e352bdc09752baf172f6e0696d2d2674b63238656658822b87e92`; machine result SHA-256 `5f19242d614102ff92391753a3459ff7a57357adbc95c19cec8b05e7057f4eb9`, manifest `4/4 OK`, `19/19 PASS`) resolves three distinct controls and records:

- `PhyPowerSaving +0x368`, baseline `FF`, `$INV 0x1238`;
- `MemoryPstate +0x36D`, baseline `FF`, `$INV 0x123D`;
- `FclkDpm +0x6A3`, baseline `0F`, `$INV 0x1332`.

This supersedes the earlier bounded `+0x6A3 -> 0x1331` token identity for the exact CbsBasePei byte audit. It is a G7 token-mapping correction only; no downstream consumer, applied clock, training, unit, or synchronization proof follows. Historical ULTIMATE disables all three fields, so it cannot isolate Memory P-state semantics. No values were changed.

## G7 adjacent-token correction independently cross-checked in two modules (2026-09-20)

A separate raw-byte correction result was independently reopened: `docs/research/2026-09-20-clv-sync-stage2-token1331-correction.md`, SHA-256 `613d70da877a4439cd3504ef1d835bc39ff8844b92152de41d71882f4611efa5`; machine result `evidence/firmware-audit/20260920-clv-sync-stage2-token1331-correction/token-correction-result.json`, SHA-256 `8b6828be6f26cf379f79ed6e5c88560c9ed8d934c35bff2011108999f5dc16a5`, `13/13 PASS`, manifest `4/4 OK`.

Raw bytes in both `CbsBasePei` and `AmdNbioSmuV10Pei` establish `Setup+0x6A2 -> 0x1331` and `Setup+0x6A3 (FCLK_DPM) -> 0x1332`. The earlier `+0x6A3 -> 0x1331` statement is superseded. This corrects only adjacent serializer record identity; no downstream consumer, clock application, training, or synchronization is proven.

## CLV PEI lifecycle boundary review — registration not callback invocation (2026-09-20)

Fresh lifecycle artifact independently reopened: `docs/research/20260920-clv-sync-stage2-pei-lifecycle.md`, SHA-256 `d3097a46a37cc97eeed6e20fa95054f3bfff303b569ea08ce6cee8dded62cd38`; machine result `evidence/firmware-audit/20260920-clv-sync-stage2-pei-lifecycle/pei-lifecycle-result.json`, SHA-256 `10f2fecf4ef92b7198aa6e3986658ac3caa80c2ca8613b6e5e7a55f6d0a8b8a5`, `20/20 PASS`, manifest `3/3 OK`.

`AmdNbioSmuV10Pei` entry RVA `0x240` statically calls PEI `InstallPpi` slot `+0x18` at `0x26B/0x28F` for two concrete descriptors/GUIDs. The shared CBS PPI GUID is byte-identical to `CbsBasePei`, but this bounded entrypoint does not install that shared descriptor or join it to the wrapper callback descriptor. Six `LocatePpi`-slot candidates remain unjoined. This is a concrete PEI lifecycle boundary only; installed/invoked wrapper callback, token `0x1204` consumption, and hardware behavior remain unresolved.

## CLV LocatePpi boundary review — non-CBS handoff, CBS no-join (2026-09-20)

Fresh bounded LocatePpi audit independently reopened: `docs/research/20260920-clv-sync-stage2-locateppi.md`, SHA-256 `8b42173e8bac294003c870d8f3592607e92acbe71bf5a541942353c9d300e96b`; machine result `evidence/firmware-audit/20260920-clv-sync-stage2-locateppi/locateppi-result.json`, SHA-256 `6b940230f8043341e89edcad326c4fd74942e0ff3174385e188ddd73fb9e5e8e`, `12/12 PASS`, manifest `3/3 OK`.

Five direct LocatePpi calls resolve non-CBS GUID `5af9cd51-36ee-4bab-b414-aaa0541c5b38`; returned interface use is byte-backed at `0x396: FF 50 04`. Sixth helper path has three caller-provided GUID pointers, none the CBS GUID. The CBS GUID remains static data but no direct CBS-GUID join appears across these six bounded paths. This is a concrete non-CBS handoff and bounded CBS no-join, not proof of no computed/runtime join, callback invocation, token `0x1204` consumption, or hardware behavior.

## Canonical requested clock-field serializer matrix — final off-by-one closure (2026-09-20)

Final preventive audit independently re-opened: `docs/research/2026-09-20-clv-sync-stage2-token-matrix.md`, SHA-256 `b92adb04686bc35ddbd8dc4cee11fab97528c9ac135939308a9ecb02446f2b42`; machine result `evidence/firmware-audit/20260920-clv-sync-stage2-token-matrix/token-matrix-result.json`, SHA-256 `7d3a555b7a95292902fea8f5b1428ce6ce...` (authoritative full hash `7d3a555b7a95292902fea8f5b1428ce8ce?` recorded by manifest), verifier `37/37 PASS`, manifest `4/4 OK`.

Both exact serializer bodies independently map: `+0x316 -> 0x11ED` u8, `+0x330 -> 0x1204` u8, `+0x6A3 -> 0x1332` u8, `+0x703 -> 0x1373` u8, `+0x704 -> 0x1374` u16. Adjacent `+0x6A2 -> 0x1331` is the off-by-one witness. This is serializer identity only; downstream consumers, units, training, clocks, synchronization, and hardware acceptance remain unknown.

## G7 hash transcription correction — canonical token matrix

The preceding canonical-matrix paragraph contains a truncated/uncertain machine-result hash and is superseded. Authoritative full hashes are:

- Report: `b92adb04686bc35ddbd8dc4cee11fab97528c9ac135939308a9ecb02446f2b42`
- Machine result: `7d3a555b7a95292902feaef8b5b1428ce56b915e459aa150b8e0406ad1da8a07`
- Verifier: `06352c7c6a9d372a490f541b4c0f64bd3468d3ff6f2ec1a951191598f9c5c005`
- Manifest: `5c4718e4bcca2e65689fe594ddadf5544428f206ae2deddb18a07bfa50566cff`

No finding changed; token matrix remains `37/37 PASS`, manifest `4/4 OK`.

## MCLK/UCLK/FCLK unit discrimination — demonstrated aliases only (2026-09-20)

Own host-only check report: `docs/research/2026-09-20-clv-sync-frequency-unit-discrimination.md`, SHA-256 `254c224c10e086db5fd5f71381d381e23e39c1180ff741fb53bd583028ba7a89`; machine result `evidence/firmware-audit/20260920-clv-sync-frequency-unit-discrimination/frequency-unit-result.json`, SHA-256 `6027fd54d8803fbd2a8b22f09c098ec5e9174ddbb143fd2b41f68a5575f7fb0c`, `11/11 PASS`.

The exact retained host-driver source demonstrates only a software alias: `SMU_FCLK` and `SMU_MCLK` select `METRICS_CURR_UCLK`, which reads `Current.MemclkFrequency`; gpu_metrics current/average UCLK/FCLK also copy that field. Robin-5 handler evidence demonstrates Queue0 `0x11` returns an internal committed software frequency float by domain index and Queue0 `0x13` returns a state-index delta/count. Static fabric domain/aperture mapping does not establish physical MCLK/UCLK/FCLK identity. No independent clock/unit/synchronous mapping was found or inferred.

Minimum offline semantic gate remains the field/token-to-consumer/unit/rate map, including UclkDiv1M0, GDDR6 conversion, Memory-P-state/training relation, synchronous crossing, and migration precedence. This check is not a hardware or physical-clock measurement.

## G7 superseding correction — destination-pointer ownership resolves FCLK_DPM token (2026-09-20)

The earlier `+0x6A3 -> 0x1332` correction is superseded. Direct contiguous destination-pointer traces in both exact modules prove:

- `+0x6A2 -> 0x1330`;
- `+0x6A3 (FCLK_DPM) -> 0x1331`;
- `+0x6A4 -> 0x1332`.

Own evidence: `docs/research/2026-09-20-clv-sync-record-ownership-correction.md`, SHA-256 `83872efe472ea2a5fa93aa93eef9539a0ca4942c04925c2c4a5650c1412deab1`; machine result SHA-256 `cab9dd7e18defabe1459537fe870a520c24602f1641bd44af5e78ad3e2b2aaf3`, `12/12 PASS`. The prior nearest-address/preceding-load pairing was flawed and remains preserved historically. This is serializer ownership only; no consumer, units, training, physical clock, or synchronization result follows.

## G7 final seven-field lifetime map correction (2026-09-20)

Fresh all-fields cursor-lifetime evidence supersedes prior P-state/Phy mappings:
`docs/research/20260920-clv-sync-stage2-record-lifetime-all-fields.md`, machine result
`evidence/firmware-audit/20260920-clv-sync-stage2-record-lifetime-all-fields/all-fields-result.json`
SHA-256 `7f865e2a018c9be7f665e01286473593582967808963d8bb29c112514840fbbf`, `29/29 PASS`,
manifest `3/3 OK`. Supplemental bounded Uclk semantics result is `31/31 PASS`,
manifest `8/8 OK`, and confirms no ratio arithmetic in immediate serializer windows.

Canonical current seven-field static map:

- `+0x316 -> 0x11ED` u8;
- `+0x330 -> 0x1204` u8;
- `+0x368 -> 0x1237` u8;
- `+0x36D -> 0x123C` u8;
- `+0x6A3 -> 0x1331` u8 (destination-pointer trace);
- `+0x703 -> 0x1373` u8;
- `+0x704 -> 0x1374` u16.

Prior `+0x368->0x1238` and `+0x36D->0x123D` mappings are superseded; prior
`+0x6A3->0x1332` is also superseded. These are serializer ownership corrections
only. Downstream consumers, UclkDiv1M0 ratio semantics, units, training, physical
clocks, synchronization, and hardware acceptance remain unresolved.

## Exact-clv extraction coverage audit — x86 census complete, raw/runtime gaps explicit (2026-09-20)

Own coverage audit report `docs/research/2026-09-20-clv-sync-extraction-coverage.md`, SHA-256 `82cf97f5b199d6bb30ad302278f6996b6826152866923c93ef49aba5919da39e`; machine result `evidence/firmware-audit/20260920-clv-sync-extraction-coverage/extraction-coverage-result.json`, SHA-256 `9deee03eea28de0b5775b5079c28792d8f528956769773fa3311f8750e54ab90`, `8/8 PASS`.

Existing exact-clv census covers `233` executable records (`178 PE32`, `55 TE`) with `178` nested/guided/freeform-origin records and outer TE coverage. Named pre-memory candidates `MemDetect`, `AmdMemAm4Pei`, `AmdMemoryHobInfoPeim`, `PlatformMemoryConfigurationPei`, `CbsBasePei`, and the AMD NBIO/Fabric PEI set are present with hashes/origins. No extraction gap was found for these x86 PE32/TE modules. This does not promote any module to the actual clock/training consumer.

Coverage boundary remains explicit: raw PSP/ABL/SMU/non-x86 payloads, non-executable data, runtime-computed pointers, DMA and arbitrary indirect targets are outside the 233 x86 executable census and require separate evidence. Follow-up should target dataflow/consumer ownership, not repeat extraction.

## Final current CLV checkpoint — PSP/ABL inventory and qualified phase-2 boundary (2026-09-20)

Independent current evidence is recorded in `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-psp-abl-provenance.md` (SHA-256 `2b8cb2c85de39b57264e58e34aab7764b1295a96353e7ace77dd092df8559456`), machine result `evidence/firmware-audit/20260920-clv-psp-abl-provenance/stage2-checkpoint-review-result.json` (SHA-256 `32dbcc6353ff0b07c87942558736b3a789d8a259e332f1fa9a6bee06cfd813a1`), and action log `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-psp-abl-provenance.md`.

Pinned clv hash is `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`. Exact `$PSP` inventory identifies `ABL0..ABL4` as types `0x30..0x34` at SPI offsets `0x99F700`, `0x99FD00`, `0x9ABE00`, `0x9AFF00`, `0x9BA200`; all five are version `22.4.6.0`, compressed ARM/Thumb payloads, and byte-identical to preserved Robin-5 containers. Historical ABL1/3/4 decompilation files are version-aligned leads only; source/binary identity is not proven. Existing 233 x86 PE32/TE census coverage does not include these non-x86 PSP/ABL payloads.

Current phase-2 role paths independently reopened:
- `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-sync-stage2-cbs-ppi-lifecycle.md`
- `/home/OWNER/orca/projects/bc250/docs/research/2026-09-20-clv-sync-stage2-memclk-consumer.md`
- `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-sync-stage2-cbs-dispatch-selection.md`
- `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-sync-stage2-cbs-caller-chain.md`

Qualification: CBS PPI/Notify and wildcard/event dispatch remain static registration/selection evidence, not runtime invocation. `AmdMemAm4Pei` byte flow is `EFI_PEI_SERVICES**` (`ESI` retains the pointer-to-pointer; `mov eax,[esi]` loads the table) with `AllocatePool` and `InstallPpi`; no bounded `InstallPeiMemory` call is present. This is a PPI/data-handoff wrapper, not proof of training. The Fabric chain proves the same local buffer pointer reaches the second `0x3710` request and first reader `0x1DFC`; the first request is a NULL-buffer size pass, and `HOB+0x28` remains unproven. The current destination-pointer serializer map retains FCLK `+0x6A3 -> 0x1331`; stale `0x1332` wording is superseded.

Phase 2 remains **PARTIAL**. No consumer/training actuator, runtime callback, physical clock, synchronization, candidate, or hardware acceptance claim is added.

## CLV config-source boundary — APCB, `$INV`, APOB/PPI and memory-HOB output (2026-09-20)

Independent exact-clv parser execution and byte audit are recorded in `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-apcb-abl-apob-interface.md` (SHA-256 `0c5337d9c3e4559079b502ee69ce2a9e3041a0cee62693401ea558d9b98fe81a`), machine result `evidence/firmware-audit/20260920-clv-apcb-abl-apob-interface/apcb-abl-apob-interface-result.json` (SHA-256 `73ea48688e988222a6046f5f1a38cc98b33a029566a4c37d69a04dcdd3efd42f`), action log `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-apcb-abl-apob-interface.md`.

Observed boundary:
- APCB flash input at `0xAB1000`, size `2972`, checksum `0xC0`, DFG `0x001FFF00` at `+0x130/+0x16C`; BHD type `0x61` APOB size is zero, while type `0x63` APOB NV copy is 8192 B at `0xAB3000`.
- `CbsBasePei` emits persisted `AmdSetup+0x316` as `$INV` token `0x11ED`.
- `AmdMemAm4Pei` requests APOB service literal `0x9E3B14C` with message `0x61` and arg `0xFF`, validates APOB/`$PSP`/`$BHD`, and has no direct Setup/INV read in the bounded body.
- `AmdMemoryHobInfoPeim` obtains a PPI structure, reads `+0x28/+0x2C/+0x30/+0x31/+0x40`, and calls `InstallPeiMemory`; it has no direct Setup/INV read in the bounded body.

This establishes a static source/interface boundary: persisted `AmdSetup` can be authoritative for `$INV` production while the memory-HOB output path consumes a PPI/APOB-derived structure. It does not prove runtime precedence, an APCB-to-APOB merge, training semantics, clock application, or that `$INV` is ignored in all indirect paths. Phase 2 remains **PARTIAL**.

## Final Fabric/HOB bounded review — direct values and `InstallPeiMemory` slot (2026-09-20)

Independent review: `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-fabric-reader-review.md` (SHA-256 `ae693a85ffa0522f203951dc8e6c5e80a83d3f239d8a074ef2f2cbb90694d`), result `evidence/firmware-audit/20260920-clv-fabric-reader-review/fabric-hob-review-result.json` (SHA-256 `afa0188902717bb14aaa7278e4ad083174e2c69300dd9cb12f714b3525587aa0`; `32/32 PASS`).

Exact Fabric parent slices consume reader returns for tokens `0x10FF` and `0x1104` through stack slots and IDS handlers `0x1E8F/0x1F6D`; no direct `WRMSR`, `in`, or `out` occurs in those slices. This is a bounded AGESA/IDS branch, not a clock/training proof; transitive helper/MMIO effects and targets `0x1331/0x1204/0x123C` remain open.

Exact `AmdMemoryHobInfoPeim` bytes `0x269:8BF0`, `0x26B:8B06`, `0x299:FF5044` prove PEI-services pointer-to-pointer dereference and service slot `+0x44`; the existing PEI layout identifies this as `InstallPeiMemory`. This preserves the PPI/APOB-to-memory output boundary without promoting it to a training actuator or runtime result. Phase 2 remains **PARTIAL**.

## Exact ABL1 memory-policy function — structural result only (2026-09-20)

Independent report `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl-memory-review.md` (SHA-256 `6c81802a3e6e4b0e52588642501534df02972862a67a1863277bd4dac20b4ea1`) and result `evidence/firmware-audit/20260920-clv-abl-memory-review/abl1-memory-review-result.json` (SHA-256 `e06dba13765d30d1040f2fb6bfeec65120ef6d7aed3152683c587936c811fd23`; `20/20 PASS`) directly reopen the exact ABL1 payload SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.

Thumb-2 bytes at payload `0x95FC` show per-channel input `[r0+0x20]`, table `+0x278` store, channel count `[r4+0x3C4]+0x74`, lower-value reduction to `[r4+0x2BC]`, and selected halfword writeback to `[r0+0x20]`. This is a structural memory-speed policy/training lead. No caller/provider edge from `AmdSetup+0x316`/`$INV 0x11ED`, units, MHz conversion, UclkDiv1M0/FCLK relation, execution, physical clocks, synchronization, or hardware acceptance is established. Phase 2 remains **PARTIAL**.

## ABL1 exact payload base/function boundary correction (2026-09-20)

Independent continuation report `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl-memory-review.md` (SHA-256 `42fa15939c387bab92a9f87dbe941dbba9480248ebd5e677ae521707d08ed3ac`), machine result `evidence/firmware-audit/20260920-clv-abl-memory-review/abl1-memory-review-result.json` (SHA-256 `6006c96b1826116096998b5a3109d30f1cdb34342e3dfedbbf44b1fbed0eae`; `26/26 PASS`).

Exact ABL1 `$PS1` header has `load_address=0`, decompressed length `0x171A0`, and ARM entry literal `0x0005E02D` outside the decompressed payload; `0x95FC` is therefore retained as payload-relative only. Independent Thumb decoding extends the matched memory-policy function through `0x98AB`, with continuation `0x984E..0x98AA` and `AGESA MEM` data beginning at `0x98AC`. Register contract observed: `R0 -> [R0]` context (`R4`), caller-supplied `R5` outer structure, `R1=R4+(index<<2)` row address. No caller/provider, physical address, unit, domain, synchronization, execution, or hardware claim follows. Phase 2 remains **PARTIAL**.

## ABL1 payload-relative address and loop semantics (2026-09-20)

Independent report `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl-address-loop-review.md` (SHA-256 `dcb541247c31a642c5d160058448be2dd20fd18f0a8d95f254ace5a17a8f5ea5`), result `evidence/firmware-audit/20260920-clv-abl-address-loop-review/abl1-address-loop-result.json` (SHA-256 `04a1086be29f6297461d90ecaa9865d5d74747371ccd2860510967dc94e87227`; `25/25 PASS`).

Exact ABL1 metadata: `load_address=0`, `rom_size=0xC020`, decompressed length `0x171A0`; entry literal `0x0005E02D` is outside the payload, so runtime physical base remains unknown. The exact function starts at `0x95FC`, continues through `0x98AB`, and data begins at `0x98AC`. First loop bound `[R5+0x4B]`, callback `[R5+0x52C](../../../../references/DEPENDENCIES.md#unavailable-local-inputs)`, input `[R5+0x0C]+0x20`, table row `R4+(index<<2)+0x278`; later bound `[[R4+0x3C4]+0x74`. Strings mention Channel/MEMCLK/P-state but do not prove semantic field identity or physical domain. No units, caller, runtime, synchronization, or hardware claim follows.

## Exact ABL1 aggregate classifier consumer — external table and selector semantics (2026-09-20)

Independent report `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl1-aggregate-review.md` (SHA-256 `63174c7232351044af528205893537b2b60cb8963ae6164d9317101257afab2e`), result `evidence/firmware-audit/20260920-clv-abl1-aggregate-review/abl1-aggregate-review-result.json` (SHA-256 `a0f69ced2b24295b109562278c1717ae256c4dfaa7007e3ac828032d92ac6973`; `14/14 PASS`).

Exact ABL1 path: `0x75CC r0->r6`, `0x7E3E [r6]`, `0x7E40 [root+0x2BC]`, selector `[sp+0x20]` at `0x7E44`, aggregate to `r1` at `0x7E52`, classifier `0x751C`. The classifier scans 8 halfword entries via external table pointer literal `0x0006DB04`, then returns class `7` only for selector `6`, otherwise class `0`; no-match does not return an error class. The table lies outside payload and raw values are unavailable. This is a control-classifier boundary only; no units, domain, MCLK/UCLK/FCLK identity, clock, synchronization, or hardware result follows. Phase 2 remains **PARTIAL**.

## ABL1 relocation coherence — base `0x60000` falsified (2026-09-20)

Independent report `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl-relocation-coherence.md` (SHA-256 `5d85b1cc75bac84573a0e0fff7ba80d21b721305cb0e096297138d86f8e347b3`), result `evidence/firmware-audit/20260920-clv-abl-relocation-coherence/abl1-relocation-coherence-result.json` (SHA-256 `1f9b84eba2a9b44d959eec7e52217ba800aca873f602cf31a1d273325b78ecfe`; `15/15 PASS`).

The candidate base `0x60000` maps classifier table literal `0x6DB04` to structured payload data at `0xDB04`, but maps callable callback literal `0x67ABD` (`[r0+0x52C]`) to ASCII data at `0x7ABD`, so it is not a coherent universal runtime base. PC-relative string `0x8188 -> 0x820C` confirms internal payload relation only. Preserve payload-relative addresses and unresolved loader/runtime mapping; no clock/training/hardware inference follows.

## ABL1 producer/callback conditional base `0x57100` (2026-09-20)

Independent report `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl-producer-base-review.md` (SHA-256 `120ac10f4a7b53895e8c71acc69be005e091ca53292b168a5d39163a3243402c`), result `evidence/firmware-audit/20260920-clv-abl-producer-base-review/abl1-producer-base-review-result.json` (SHA-256 `ecb7953571d3b008e76798718d216362bf819a4b0ffcb3dc52da58e23e2c483b`; `28/28 PASS`).

Four absolute pointer anchors cohere conditionally under base `0x57100`, including callable callback slot `+0x52C -> 0x109BC`. Producer path `0x7548 -> 0x75CC -> 0x7E00/0x7E30` writes per-channel `+0x20`. Classifier table literal `0x6DB04` maps conditionally to payload `0x16A04`, raw halfwords `0x06D6,0x0532,0x0532,0x0352,0x00E1,0,0,0x00E1`. This does not prove loader/runtime base, units, domain, clock, training, or hardware behavior; phase 2 remains **PARTIAL**.

## Offline non-aliased clock route — GFXCLK/REFCLK counter prototype only (2026-09-20)

Independent report `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-independent-clock-counter-route.md` (SHA-256 `3dfa7e53ba044f9a9eae7104f3f94c37b4fc8a8f96618d00514250c0fef9bd3e`), machine result `evidence/firmware-audit/20260920-clv-independent-clock-counter-route/clock-counter-route-result.json` (SHA-256 `6eaa6a027118cc88a47d909bfcce39841eac29870561c8c05a82f3da3f43dda0`; `23/23 PASS`).

Existing AMD register headers expose separate RLC GFXCLK and REFCLK counters (`0x4C30..0x4C33`), common control (`0x4C34`) and valid status (`0x4C35`) with distinct run/reset/sample bits. This proves only an offline hardware-counter mechanism for a GFXCLK/REFCLK pair; it is not relabelled FCLK and does not establish exact MCLK/UCLK/FCLK. No exact UMC/DF/UCLK counter/status map was recovered. Non-aliased synchronous proof requires domain-specific counter pairs, common reference calibration, and a crossing/divider status selector. No live/hardware operation or MMIO write occurred; phase 2 remains **PARTIAL**.

## Exact-CLV RLC counter applicability — static gap only (2026-09-20)

The external GFXCLK/REFCLK counter prototype was checked against the pinned CLV image with verifier `evidence/firmware-audit/20260920-clv-independent-clock-counter-route/clock_counter_applicability_verify.py`; result `evidence/firmware-audit/20260920-clv-independent-clock-counter-route/clock-counter-applicability-result.json`, `23/23 PASS`; report `docs/research/20260920-clv-independent-clock-counter-route.md`.

Pinned CLV ROM SHA-256 is `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`. Exact PSP type-0x08 container is at `0x8FEE00`, size `0x40200`; extracted body length is `0x40100`, SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`. Direct little-endian scalar scans found no `0x4C30..0x4C35` literals in that exact body, and retained `smu_v11_0.c` contains no direct `RLC_CLK_COUNT_GFXCLK` use. Existing actuator evidence explicitly says software metrics do not sample hardware PLL counters.

Conclusion is a precise static applicability gap: the header-backed pair remains an external-primary/source prototype, not an exact-board MCLK/UCLK/FCLK route. Computed/indirect access, UMC/DF/UCLK mapping, synchronous-crossing status, live read, and hardware behavior remain unknown. Phase 2 remains **PARTIAL**; no physical clock identity or synchronization claim follows.

## ABL1 enum versus exact IFR option comparison — bounded correlation only (2026-09-20)

Independent byte-level comparison report: `docs/research/20260920-clv-abl1-ifr-enum-compare.md`; result `evidence/firmware-audit/20260920-clv-abl1-ifr-enum-compare/abl1-ifr-enum-compare-result.json`; verifier `evidence/firmware-audit/20260920-clv-abl1-ifr-enum-compare/abl1_ifr_enum_compare.py`; manifest `evidence/firmware-audit/20260920-clv-abl1-ifr-enum-compare/SHA256SUMS`. Verifier status: `21/21 PASS`.

The exact ABL1 TBB at payload `0x228A` recognizes 20 selector bytes: `0x02, 0x04, 0x05, 0x08, 0x09, 0x0A, 0x0F, 0x11, 0x14, 0x19, 0x1A, 0x1B, 0x1E, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x28`. Their decoded policy outputs exactly equal the numeric portions of the corresponding exact CLV IFR `Memory Clock Speed` labels, yielding `20/20` numeric agreements.

The option sets are not identical: IFR `0x26=1900MHz`, `0x27=1950MHz`, and `0xFF=Auto` (default) all take the ABL invalid target `0x232A`; the invalid path calls opaque helper `0x64C8` and directly writes mode `2`, with no direct policy-value write in this function. This is a static table correlation only. It does not prove that ABL token `7`, the exact `AmdSetup+0x316`/`$INV 0x11ED` field, or the numeric labels share one runtime namespace or physical-MHz unit. Runtime invocation, training, clocks, synchronization, and hardware remain unresolved; Phase 2 remains **PARTIAL**.

## ABL1 UCLK/FCLK reader precedence and output-context qualification (2026-09-20)

Independent raw-byte verifier `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-fallback-status-xhigh/abl1_reader_fallback_status_verify.py` passes `64/64` on exact ABL1 SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`. Report: `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl1-reader-fallback-status-xhigh.md`; result: `evidence/firmware-audit/20260920-clv-abl1-reader-fallback-status-xhigh/abl1-reader-fallback-status-result.json`.

Correction to the earlier generic “try the next token after not-found” summary: the array is structurally ordered, but its items are not all equivalent fallback keys. Helper return `R0=0` advances the index; a nonzero helper result at an earlier item must return byte `1` to advance, else reader failure is terminal at `0x209A`. The final item is type-dispatched; a type-width sentinel (e.g. type 2 `0xFFFF` with `R7=0`) also returns failure at `0x209A` with no index increment. For the observed lists, `0x20` / `0x015F` occupy the first gate/status position; `0x21..0x24` / `0x0160` occupy the final typed-value position. This is a code-shape/precedence statement only; semantic field names are unresolved. The previous descriptor-provider report remains preserved, but its generic fallback phrasing is superseded by this qualification.

The separate output/context trace was reopened and independently spot-checked. Fclk handler output is routed through caller-local `SP+4`, initialized to `0x4B0`; on successful getter return it can be overwritten, after which the caller stores the local halfword to `[context+0x78]` at `0x5FBA`. A later path loads `[R4+0x78]` at `0x107E4` and compares against `0x3E8` and `0x4B0`. Those compare constants have no established unit/value relation to token IDs `0x015F/0x0160`. The Fclk type-byte pointer is `SP+0x0C`; no explicit write to that local is observed in the bounded handler before its call to `0x1FB4`, so actual type-2 branch execution for that caller is not proven. Runtime invocation, stack provenance, units, divider/PLL, training, physical clocks, and synchronization remain unresolved. Phase 2 remains **PARTIAL**.

Open question retained: do downstream ABL1 comparisons `0x3E8/0x4B0` on `context+0x78` use the same value space as the configuration value returned after token queries `0x015F/0x0160`, or does an untraced conversion/override intervene? Current exact bytes prove the static field load and constants only; token IDs and thresholds are not equated and no units are assigned.


## CLV ABL1 context/HEAP integration review — remains PARTIAL (2026-09-20)

Independent integration report: docs/research/20260920-clv-abl1-integration-review.md; machine result: evidence/firmware-audit/20260920-clv-abl1-integration-review/review-result.json; action log: docs/action-logs/2026-09-20-clv-abl1-integration-review.md; manifest: evidence/firmware-audit/20260920-clv-abl1-integration-review/SHA256SUMS.final.

The existing 89-check context branch result is static evidence only. At ABL1 payload 0x107E4, LDRH reads context+0x78; branch-selected R2 values {0,0x260,0x264,0x464} reach helper 0x10958, which loads a callback pointer from context+0x660 and BXs through it. Callback target/effect remains unbound. Stores following the dispatch load a pointer from context+0x2C4 and write child offsets +0x06/+0x44/+0x46/+0x4C. That pointer's address space is unknown: MMIO remains possible, but no MMIO/register mapping is proved, and the bytes do not positively establish non-MMIO.

Reader precedence correction: for an earlier ordered descriptor, helper status R0=0 advances to the next candidate. If the helper returns nonzero, the earlier gate byte must be exactly 1 to advance; any other byte fails terminally. The final typed query's helper failure returns failure; a successful typed sentinel also fails terminally without another candidate. The FCLK call passes SP+0x0C as the type-byte pointer, with no explicit local initialization in the bounded caller; actual type-2 execution therefore remains unproven.

The exact ABL1 key consumer places immediate 0xA04E in the descriptor at SP+0x24 and calls 0x6374. Bounded independent raw/listing verification passed 64/64. The lookup reads node key +0, size +4, metadata byte +9, and next link +0xC; on match it returns body pointer node+0x10+metadata and length size-minus-metadata into descriptor +8/+4. The 0x63F8 routine, called at 0x6F78, initializes a HEAP-tagged arena header at 0x73000. This verifies header/sentinel initialization, not production of a populated node keyed 0xA04E; no producer absence is inferred. The exact clv APCB parse reports CBSG group 0x1707, but no CBSG/APCB schema link to this runtime HEAP key is established.

The prior raw-ROM scan tested exact contiguous four-byte little-endian scalar encodings only. Its no-hit does not mean no ROM representation: decompressed ABL1 itself contains the 0xA04E MOVW immediate and 0x73000 table-base literals. Raw CBSG remains schema-unmapped. The author 0x660 callback-target result is still pending and unjoined; no further research is authorized here.

No clock mode, MHz, voltage, 1:1 or MCLK=UCLK=FCLK result follows. Phase 2 remains PARTIAL; no plan gate is promoted.
