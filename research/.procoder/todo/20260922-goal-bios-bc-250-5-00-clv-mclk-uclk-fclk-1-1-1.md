# Согласовать требования /goal для BIOS BC-250 5.00 CLV

Status: open
Created: 2026-09-22

## Description
Подготовить текст /goal. Сохранить ранее открытые задачи проекта.
Q1: BIOS-кандидат плюс инструкция.
Q2: отдельные STATIC-PASS и HARDWARE-PASS.
Q3: меню-мост только в отдельном экспериментальном кандидате.
Q4: сначала установить и подтвердить SoC-напряжение, затем менять частоты. Жёсткий потолок 1.15 В. Не считать потолок доказанной безопасной уставкой. Найти действительный BIOS-путь управления +VDDCR_SOC.

## Acceptance criteria
- [x] Записаны решения Q1–Q4.
- [x] Выдан окончательный текст /goal с критериями приёмки и ограничениями: `.procoder/specs/clv500-goal-final.md` (2026-09-23, задача #1 доски Plane «BC250»).
- [x] Разделены офлайн-результат и аппаратное подтверждение: двухуровневая приёмка STATIC-PASS / HARDWARE-PASS задана в тексте /goal; текущий стат-сплит по требованиям — `docs/research/2026-09-23-goal-acceptance-audit.md`.

## Evidence
Решения из последнего сообщения пользователя записаны в этот файл. BIOS, напряжения и частоты не изменялись.

## Active goal execution 2026-09-23
R1-R8 remain open as full execution requirements. Operator guide is a draft, not accepted settings. Menu audit and baseline/modified/rollback structural audits exit 0. Next: resolve actual voltage consumers and clock semantics. Hardware NOT TESTED.

Voltage mapping check: 28 raw-ROM producer windows verified. VDD control/value 1363/1364 at 6E5/6E6, GFX control/value 1365/1366 at 6EA/6EB. Prior inertness verdict superseded. Next executable action: examine computed/indirect request paths for corrected voltage tokens using existing consumer corpus. R1-R8 remain open.

A019 follow-up: IDS DXE wrapper reads object +0x18 after matching DB1099CC. PE mapping and full SHA verified. This is not the requested SoC actuator. Next: return to rail feedback/actuator topology instead of expanding unrelated IDS code. R2 and R3 unresolved, R4/R5 partly verified, R6 NOT TESTED, R7 draft.

SoC feedback topology: nine nets verified, separate external programmable actuator not listed. R2 unresolved due to physical revision/APU-pad behavior and absent proven firmware actuator. Next executable action: run existing DF route verifier and inspect its exact clock consumer path for R3 (not another voltage-label census). Evidence: evidence/firmware-audit/20260923-soc-feedback/result.json. Full goal remains open.

Clock reconciliation: fresh df/units/provider checks exit 0. Operator guide corrected: help FCLK>UCLK is not proven enforcement; 015F/0160 are ordered lookup alternatives. Next: trace MCLK service item 0x17 at ABL1 0x7E3A->0x0C60 using existing exact payload; do not rerun completed token scans.

MCLK item17 boundary: fresh exact ABL1 disassembly exit 0. Policy channel +0x20 -> +0x278 observed; no physical writer in window. Token7-to-AmdSetup+0x316 join remains unresolved. Keep STATIC/HARDWARE split and do not issue 1800/1800/1800 recipe.

Correction to item17 draft: handler 95FC is CONDITIONAL on unproven load base 57100. 0x20 is fill length, not descriptor. Store is outer+channel*4+278. See corrected result.json. Next: validate table/load-base provenance, not assert runtime dispatch.

Menu candidate reproducibility: canonical builder output-path-only rerun exit 0, byte-identical existing experimental candidate. Fresh baseline/modified/rollback audits exit 0, rollback hash equals donor. This advances R5 but does not satisfy hardware or SoC requirements.

Primary candidate created: BC250_5.00_clv_MAIN_NATIVE_BASE.bin, byte-identical donor, fresh baseline/candidate/rollback audits exit 0. Main candidate is native-settings only; experimental menu bridge remains separate. SoC and hardware acceptance still open.

Completion audit 2026-09-23: requirement matrix written at docs/research/2026-09-23-goal-acceptance-audit.md. Decision: keep goal open. Static candidates reproducible; no proven SoC setter, physical 1:1:1, optimized values, or hardware acceptance.

Acceptance correction: experimental overall R5 is PARTIAL, not complete STATIC-PASS; fresh patch reconstruction exits 0 and matches candidate. Avoid calling unchanged reference an optimized primary candidate. NEXT_EXECUTABLE_ACTION: inspect and verify preservation of decompressed FFS outside Setup and inserted driver, and independently enumerate exact Setup edits including the two voltage-form predicates. Use pristine donor and canonical experimental candidate. Do not repeat reference-copy audits as progress.

Independent FFS containment: PASS_STATIC_CONTAINMENT. Only Setup changed (82 bytes in four spans) and one ClvNativeMenu FFS added; all other existing FFS byte-identical by GUID. This supports R5 scope, not runtime/hardware. Evidence: evidence/firmware-audit/20260923-ffs-containment/result.json.

Containment strengthened with independently iterated FFS headers/checksums and exact allowed regions. 186 existing FFS unchanged, Setup 82 bytes, one added driver. Shared decompression is explicit. NEXT: inspect native HII form references and semantic scope of the two predicates; do not call overall R5 complete.

HII REF audit PASS_STATIC_HII_TARGETS: 5 refs resolve, native forms present, verifier exit 0. This closes static navigation resolution but not AMI runtime or field behavior. R5 remains partial and R6 NOT TESTED.

HII correction: actual candidate IFR walk now resolves all five targets and Setup->bridge. Earlier VFR-only check superseded. Predicates decode FALSE FALSE OR under gray/suppress scopes; original noncanonical AMI interpretation unresolved. Full R5 and hardware remain incomplete.

## 2026-09-23 operator order: sync track is a front, workers mine the repo
Operator re-affirmed the finish line as "a real gaming console: everything configured, hacked, under control". The OC/sync track (MCLK=FCLK=UCLK 1:1:1 on 5.00 CLV) runs IN PARALLEL with the PSP breach campaign (.procoder/plans/psp-breach.md), not after it. Operator ordered repository mining by workers: the repo carries extensive unmined OC/sync material (goal ledger history, clv111 decision matrix, community profile matrix, corpus synthesis, ABL1 item-0x17 traces, clock-independent reviews, SoC feedback topology). Worker dispatched to consolidate the sync state and name the exact unresolved joins. The standing rule stays: no 1800/1800/1800 recipe until the enforcement path is proven.

Driver boundary audit PASS bounded: host mock exit 0 and DEPEX is HII database protocol only. No bridge voltage/clock writer. This supports safety scope but not AMI/runtime. Goal remains open; no flash.

## Blocked audit 2026-09-23

Full R1-R8 goal remains unachieved. Recurring blocker across FFS/HII/driver continuations: no established SoC actuator and no physical clock acceptance. Local checks do not resolve this; repeating them is no progress. No active evaluator job awaited. Await new discriminating board-revision/regulator evidence or authoritative firmware/electrical control documentation; not an instruction to flash. Existing tasks and unknowns remain open. Current four ROM roles remain canonical. Main native copy is a reference, not an optimized result.

## User correction: lateral / actual objective

New task: apply lateral skill to redesign the investigation approach and restate the actual objective. In progress. Existing R1-R8 tasks retained.
User rejects board photographs as a prerequisite. Withdraw that prerequisite for offline continuation. Do not reinterpret unproven actuator as absent hardware capability. Separate hardware acceptance from offline candidate design.

Lateral/concept-fan task completed: target is the investigation process, not replacement of binary evidence with brainstorming. Climb: menu unhide -> controllable BIOS settings -> justified low-latency profile for clean CLV, testing 1:1:1. Candidate routes: original overclocking case -> exact setting provenance; inverse tracing from known programming paths; discriminating offline tests for individual field semantics. Prune repeated checksums/new report variants and photographs as prerequisites. Priority: recover exact voltage/clock settings and outcome from supplied chat case, map each to clean CLV, then choose the smallest evidence-producing test. Existing acceptance/hardware constraints unchanged. Previous blocked rationale is withdrawn; no claim of tool-level goal reactivation.

Original case recovery: source messages 772237-239 report DF-dependent behavior; 772341-344 report MANUAL feedback adjustment and SoC >1.2 V, not BIOS voltage success. Screenshot MD5s match oc_profiles (1).rar, unlike loose BINs. Two archive revisions share names and sampled target fields, differ elsewhere. NEXT_EXECUTABLE_ACTION: byte/region comparison of matched archive revisions against clean CLV; map revisions before outcome attribution. No photograph prerequisite, no hardware request.

OC archive diff: profile 03 is closest claimed 1:1:1 query set (MCLK 1750, UCLK enabled, DF1750, raw VDD80), but archive-vs-clean includes 3018-3020 bytes, 2817 in UEFI FV. Do not transplant five fields. Profile 02 (1330/Enabled/DF1333/raw35) is lower-clock diagnostic hypothesis. Next: classify common UEFI FV delta between profiles and clean CLV to recover actual producer/consumer change. No candidate made.

NVAR audit: clean 42 records/0 errors; archived profile copies 45 records/3 unterminated-name errors. Historical profiles include low-ROM/NVRAM changes and are not clean patch sources. Do not promote. Original OC case remains evidence/hypothesis, clean CLV TARGET.

Superseding correction: no UEFI-FV difference in archived profiles. Every change below 0x20000; remainder exact CLV. Revision delta identified: Tcl (+317) manual18/14/16->Auto and DRAM Timing User Controls (+32F) Manual->Auto. Not a UCLK patch. NEXT: source-message linkage and IFR timing-control dependencies to test training hypothesis. No final settings recommendation yet.

Ultimate profile exact mapping completed: screenshot 772123 matches archived image values. Key correction: claimed low-latency profile explicitly uses UclkDiv1M0=0 (1:2), not 1:1:1; raw VDD offset100 and manual feedback history are not BIOS-only safe SoC. Use it as hypotheses only. Next: map the five non-voltage controls to clean CLV one-variable candidates; no final settings promoted.

Created first clean-CLV non-voltage hypothesis candidate from original low-latency profile. Exact nine-field scope verified, voltage/power bytes unchanged. SHA cbb31e70d8e78c24da6f3f238f2dda52f5d0dc4fdacb7db93aad53b341b113e1. Baseline/modified/rollback audits exit0 and rollback donor hash. Not final recommendation, no flash.

Closest static 1:1:1 hypothesis candidate created from archived profile02: clean CLV + MCLK1330/UCLK Enabled/DF1333 and non-voltage controls. Exact scope, voltage/power preservation, baseline/modified/rollback pass. SHA 121c4d278df21e1eba63d3a02a3cd3f6f91ab8ea0cd1409722d36bd2863dfc30. Physical sync unresolved.

Correction: no-voltage variants are offline byte fixtures, not accepted primary candidates or one-variable tests. 1330 vs1333 equality unproven. Both fail SoC-first acceptance. Stop proliferating settings-only images. Fix verified: 1333 reconstruction initially failed wrong source parents[2], corrected parents[3], rerun equals image. Literal audit ledger now recorded. Next: determine actual AmdSetup retrieval/fallback precedence underlying original screenshot Auto vs patched stored values, without altering hardware.

Setup precedence discriminated: archived AmdSetup records are structurally valid native records, so screenshot Auto is not a simple offset/size error. Static fallback cannot determine browser/reset chronology. This closes a concrete hypothesis without hardware. Do not create more variants; next objective is tie exact flashed archive to screenshot chronology or stop claiming persistence semantics.

Chronology falsification: source chat 772088-130 says profile03 did not apply; BIOS photo9 shows Auto. Raw NVRAM candidates are not successful configurations. User's original “лезть ниже user settings” is confirmed as actual next objective. Stop cloning values. Next: trace lower producer/consumer override for timing/clock requests and identify why BIOS/NVRAM is ignored.

Chronology qualification: participant report is NOT proof of a universal override; no flashed-image readback/reset trace. Next boundary: AmdSetup retrieval via variable PPI versus later policy. CbsBasePei 2DD/2E9/323 require probe status, size and second-read success, with fallback at333/344/355. Preserve alternatives rather than assume lower override.

AmdSetup provider progress: variable PPI GUID2AB86EF5 maps statically to NvramPei+2F5, E46 descriptor loop calls BF8 and continues only on NOT_FOUND. 80 rows verified. NEXT_EXECUTABLE_ACTION: inspect construction/order of store descriptors and BF8 active-record handling; do not repeat CBS fallback checks. All R1-R8 remain intact and open where not proved.

Native record-selection progress: 360 rows checked; attrs88 entries are data-only in native firmware. Prior unterminated-name errors are lightweight parser limitations. Initializer fallback base FF000000/size20000; auditor default1000 omitted AmdSetup. NEXT_EXECUTABLE_ACTION: inspect 10AA/103B store validation and HOB-derived alternate-store selection to determine actual descriptor precedence. No further settings-only variants.

Store policy progress: state byte8F F8->F0 is real but both valid. Callback pointers resolve CMOS0E&C0 / CMOS9F==55 to alternative descriptor path. NEXT_EXECUTABLE_ACTION: trace callback24B and default store3B8/447, without bypass patch or hardware I/O. No completed goal claim.

StdDefaults route: callback24B validates Setup variable size0x1D3, alternative initializer loads StdDefaults GUID4599D26. Clean/profile03 containers identical (8 nested records, no AmdSetup). Next decode nested defaults and descriptor 616-6E8. This separates default validation from clock actuation; no more settings variants.

Key identity finding: StdDefaults first nested Setup record attrs82 size1E4/body1D3 exactly matches callback expected; body identical clean/profile03. Clock HII fields are AmdSetup varstore5000, separate namespace. AmdSetup edits can coexist with Setup-default Auto screen; runtime synchronization still unknown. Next trace Setup/AmdSetup handoff only.

Descriptor closure: StdDefaults tail decoded as 7 GUIDs, 8 nested names resolved; two Setup names have different GUIDs. Normal descriptor order live->defaults, conditional flag selects defaults-only. This yields a conditional missing-AmdSetup->CBS Auto route, NOT Setup/AmdSetup namespace transfer. NEXT: offline native read-path harness to discriminate retrieval, no firmware default bypass. Hardware acceptance unchanged.

Read-model executed: live and mixed orders yield AmdSetup; default-only NOT_FOUND. A mere order swap does not suppress the target in this model. Wrong-GUID/short-buffer/in-memory-value controls pass. HOST MODEL, not native execution. Next useful work must test native code or resolve initialization inputs, not further equivalent host models. Core R2/R3/R6 unresolved.

Control continuation 2026-09-23: далее -> trace NvramPei default descriptor construction 0x3B8/0x447 and link validation, retaining existing goal.

Control `далее` execution: descriptor construction 3B8/447 traced, corrected one bad anchor (0x400->0x401) after exit1, final 77 rows PASS exit0. 3B8 uses store interface +38, descriptor metadata +68, selector19, builds result via DA4; 447 wraps/zeroes negative. No runtime store selection yet. Continue next to HOB/store descriptor input only.

Superseding result: fallback3B8 is firmware-volume enumeration via PEI services, looking up FFS AF516361-B4C5-436E-A7E3-A149A31B1461 raw section19, then StdDefaults. Not a store-slot loop. NEXT: locate FFS in all available firmware volumes, not just the main decompressed inner FV, before inferring unavailable runtime source.

Native lookup execution completed: NvramPei BF8 executes in IA32 user-process harness, exact .firmware readback. Live reads0x24/1420, in-memory change returns0x23, restore0x24, defaults-only NOT_FOUND. No firmware/board writes. Evidence evidence/firmware-audit/20260923-native-variable-harness/result.json. NEXT: extend same bounded native harness to original archive-record comparisons and initializer inputs, not more Python interpretation. Core voltage/clock goal remains open.

Native archive tests done: old/revised03, revised02, Ultimate read correctly through BF8 with live descriptor. Negative GUID test returns NOT_FOUND. Tcl16 preserved in old03, not forced Auto by per-store reader. This eliminates per-store parser as reproduced cause under provided descriptors. Next meaningful boundary: native CbsBasePei configuration-read/init path with controlled variable-PPI statuses, or return to downstream clock consumer. Do not repeat record checks.

Native CbsBasePei acquisition executed: success preserves archival profile, three failure modes restore Auto/DF1000. Four native runs/8 section checks pass. Native acquisition boundary closed under supplied PEI service conditions. NEXT: inspect native serializer callback ABI and test whether selected values survive into $INV, before later consumer/SoC analysis. Do not make more default-only models or raw image variants.

Serializer harness attempt failed honestly: mode0 output layout differed from fallback modes, assertion failed, no result artifact written. Not firmware evidence. Do not weaken it. Native acquisition result remains valid. Stop this subexperiment; no completion claim for acquisition->$INV.

Native acquisition-to-$INV closed under controlled inputs: 4 modes pass, seven target token types serialized, 1122 records, exact capacity/write length. This is actual CbsBasePei code execution in user process, not board execution. Initial harness failure corrected stale-mode/output-slot defects, assertions retained. NEXT: downstream $INV consumer/SMU/ABL join; no more acquisition repeats.

Downstream exact consumer rerun: 60/60 PASS exit0 after correcting output path permission. NVTB reader direct requests 0x10FF/0x1104 only; 0x1204 requester and final UCLK/DF actuator unresolved. Serializer boundary established, physical sync not. No image/hardware change.

Native reader suffix checked: generic Fabric1DFC preserves seven selected token values from native CBS. Missing7777 status1. Explicit cache-hit frame/test token requests, no real stock requester discovered. Stop generic reader/acquisition repeats. NEXT: review external/ABL-facing data-transfer callers for real consumer join, not simulated target reads. Existing complete extraction inventory and direct-call exclusions retained.

Downstream boundary review: exact consumer verifier PASS60, native reader preserves supplied tokens, existing APOB/ABL handoff remains first unresolved between INV production and PPI/ABL/SMU. No final actuator/SoC setter. Stop repeated bounded scans. Goal incomplete; no flash/hardware.

User alias 18: explain current result in plain Russian. Simple explanatory directive, no new firmware work. Existing goal requirements remain unresolved. Explanation must distinguish an unidentified control path from proof that BIOS tuning is impossible.

Request: inspect https://github.com/KorroAi/drunk-claude as untrusted external skill, apply useful ideation to BIOS 5.00 CLV investigation, propose unconventional but testable approaches. Directive to inspect/use skill plus consultation on ideas. Medium: reversible read-only research, no hardware authorization. Existing R1-R8 retained. No automatic installation or code execution from remote repository.

User-requested drunk-claude/lateral ideation recorded at docs/research/2026-09-23-drunk-bios-ideas.md. External repo ADAPT only, not installed. Six bounded hypotheses, selected O1 Ghost variable duel: in-memory contradictory AmdSetup vs Setup/StdDefaults inputs through native Cbs acquisition/serializer. No ROM/CMOS/flash. Next executable action O1.

Ideation review correction: reject drafted O1/O2/O4/O5 as repeats of completed harness work. Do not substitute O6 for 1:1:1. Revised ideas O7-O11 in report. Recommended first check O11: AmdMemAm4Pei CD9 is a directory-entry lookup (type61), not established SMU service. Exact BHD and entry-loop bytes rechecked against census hash. Next follow directory output provenance, not assume INV->APOB input. User's requested ideation delivered, firmware goal still open.

User directive делай: execute approved O11 directory-lookup audit first, O8 reverse trace second. Medium bounded continuation, no new hardware authorization. Preserve all prior open requirements.

O11 result: AmdMemAm4Pei CD9/B09 argument0x61 is BHD directory/service lookup; clean BHD entry1 type0x61 size0/dest0x04000000. Not a clock command. Prior opaque-SMU wording withdrawn. Next O8: backtrace returned APOB object fields and record consumers. No firmware/hardware writes.

User task: apply drunk-claude + lateral to investigation strategy, then write next-work plan. Medium planning directive with settled goal, no new hardware permission. Retain existing R1-R8. Interpret claude as linked drunk-claude skill, not launch another model. In progress.

Current planning request DONE: applied drunk-claude idea escalation/assumption questioning and lateral/concept-fan to strategy; pruned duplicated tests and wrote .procoder/plans/clv500-actuator-first.md (draft continuation proposal, original objective preserved in .procoder/specs/clv500-actuator-first.md). Plan structure check exit0, scoped procoder check exit0, procoder test exit0 (73 Python tests, JS not run/no script). Plan and exact objective copy reopened and compared. Firmware goal NOT complete, no new image or hardware change.

User approval делай: execute clv500-actuator-first plan P1 then P2. Directive, existing agreed scope, no interview or hardware permission needed. Preserve previous tasks.

Approved plan execution: P1 directory/output direction corrected (producer timing open). P2 output-side experiment succeeded on actual VR helper with two explicit trace/stop instrumentation sites; input0123/0456/0123 -> bytes23/01,56/04,23/01. No IO. VCORE-labelled path, not SoC. Next trace actual enable caller and rail destination; independent clock actuator path remains open.

## 2026-09-23 VCN unexpected unlock plan

IN PROGRESS: apply cached drunk-claude + lateral/inversion + universal-critical-thinking to VCN research strategy. Medium planning directive. Deliver separate falsifiable plan, no board IO, no firmware mutation, no new hardware authorization. Prior OC/VCN tasks remain open. Include later clamp-sweep wedge from MISTAKES.md, omitted in preceding status answer.

VCN planning artifact delivered: .procoder/plans/vcn-unexpected-unlock.md. O1 address/route audit, O2 legitimate request-path reachability, O3 shared-resource initialization, with O4/O5 reserves and O6 previously proposed functional oracle. Structure check PASS. procoder test exit0, 73 Python tests, JS not run. Initial check exit1 for formatting, formatted via procoder format and reran check. No hardware/firmware changes. Plan remains proposal, unlock unresolved.

User directive делай: approve VCN unexpected-unlock offline plan, execute P1/O1 first. Medium bounded continuation. No hardware authorization. Preserve all prior open tasks. IN PROGRESS.

User directive: read Reddit post 1v1vwg7. Simple read-only task, IN PROGRESS. Preserve BIOS, VCN and GhidrAssistMCP installation tasks. MCP installation remains unverified.

VCN checkpoint: bounded verifier exit0, result.json at evidence/firmware-audit/20260923-vcn-offline-plan/. Address-unit and SMU-version contradictions confirmed, no unlock. Follow-up work remains open, interrupted by new explicit MCP installation task.

New directive: install https://github.com/symgraph/GhidrAssistMCP. Medium integration task, begin external-stack audit and installed Ghidra/MCP-state inspection. User authorizes named component installation, not arbitrary unrelated configuration or exposing analysis server externally. IN PROGRESS. Preserve VCN/OC tasks.

Reddit read BLOCKED: opencli reddit read 1v1vwg7 returned exit66 EMPTY_RESULT HTTP403. Browser DOM independently returned "You have been blocked by network security" (actual wording: "You've been blocked by network security."). Post body not retrieved. Await user text/screenshots or restored browser access. Earlier tasks retained.

User correction: explain prescribed Reddit access workflow and premature request for screenshots. Simple consultation. Preserve open tasks. Answer from agent-reach skill and observed OpenCLI/browser failures.

User directive: install https://github.com/opentabs-dev/opentabs. Medium reversible installation task. IN PROGRESS. Check existing installation, official instructions, local runtime and browser connection. Preserve BIOS, VCN, GhidrAssistMCP and Reddit tasks.

OpenTabs verified ALREADY INSTALLED, no reinstall needed: CLI/server/extension 0.0.115, doctor13/13, 127.0.0.1:9515. tools/list succeeded. reddit__get_post succeeded exit0 and returned requested post. Prior Reddit blocker resolved through OpenTabs. No permissions/configuration changed.

User consultation: why not use HP post Ghidra/MCP + extraction + emulation workflow on CLV500? Medium explanation, no new flash authorization. Preserve all open tasks. Read approved plan and latest evidence before answering.

User consultation/correction: explain prolonged BIOS work, detours and failure to execute. Simple accountability response. Existing BIOS, VCN, MCP tasks retained. Correction: distinguish repeated intermediate checks from requested functional result, do not present another tool/plan as completion.

GhidrAssistMCP installation VERIFIED RUNTIME: release2.11.0, loopback8090,21 backend/client read-only tools, project Codex entry recognized, decompiler/disassembly/pcode smoke PASS exit0, disabled patch rejected. Config baseline/modified/rollback0/21/0 verified with hashes and reconstructed diff. Four roles: .codex/config.toml + tools/ghidrassist-mcp/transaction/{DIFF_FILE.patch,VERIFICATION.txt,ROLLBACK.sh}. Existing8089 untouched, no boot autostart. Source gate remains OPEN: missing Java formatter/checkstyle; procoder check exit1, procoder test73 PASS exit0. Client reconnect required to load new MCP catalog. Earlier VCN/OC and other tasks retained.

User consultation: why not follow Reddit1v1vwg7 and simply crack RSA key; is it most reliable approach? Medium factual/security explanation, not authorization for brute-force, key recovery, firmware patch or flash. Preserve prior tasks. Read primary post and distinguish cryptographic key recovery from signature-verifier bypass. IN PROGRESS.

User directive: write outcome-first BC250 overclocking plan explaining parameters, confirmed applicability, Zen2 research gaps, BIOS controls and latency acceptance. Medium planning task within existing decisions, no new hardware authorization. IN PROGRESS. Preserve all earlier tasks.

RSA example consultation resolved from primary Reddit post via OpenTabs reddit__get_post: author explicitly states RSA key/signature untouched; modified verifier branch after RsaVerifyCore to force success, tested extracted verifier using Unicorn and generated test signatures. This is enforcement bypass, not RSA-2048 factorization/key recovery. Hardware success is author report for HP15-dw1036ne F.68, not reproduced here. Transferable BC250 step is exact verifier/protected-range/earlier-root mapping, not promise to crack key or assume PSP signature enforcement from container format alone. No hardware action authorized by this consultation.

User directive делай так: execute verifier-first offline workflow for BC250 VCN: identify actual signature enforcement, extract/reproduce accept/reject before proposing patch. Medium bounded first stage, no flash, brute-force or key persistence. Prior tasks retained. IN PROGRESS.

OC plan drafting delivered: .procoder/plans/clv500-overclock-result.md. Original R1-R8 and actuator-first plan retained. Plan check exit0, firmware objective remains open. Next output is Zen2-to-BC250 applicability matrix and parameter status map, not another hypothetical ROM.

User goal: execute clv500-overclock-result plan to completion, not merely draft. Directive, inherited decisions unchanged. Start A1/A2 now. Prior turn progress: created checked plan, not firmware success. All open tasks retained.

Checkpoint: parameter-map10 fields, primary AMD guide retrieved (internal2.9/2022), native unequal-marker correction executed. Full objective OPEN, no hardware pass. Next: correct MemoryPstate123C consumer coverage then actuator path. No new ROM.

Verifier-first executed checkpoint: real public-key PSS tests on stock02/28 ACCEPT and in-memory body/signature corruption REJECT (6 controls). Existing full verifier exit1:14 PASS,2 unresolved anchors,3 noncontainers. Actual Ghidra TOS import390 functions and8 passes exit0. Loader120EC->115B8->EEAE reaches native SVCF2 r0=1,request1005. Service destination/actual RSA implementation unresolved, native verifier replay UNRUN. No patch/flash. Continue from service1 descriptor, not repeated host-crypto tests. Report evidence/firmware-audit/20260923-verifier-first/REPORT.md.

User pasted AI transcript listing UEFI tools/MCP/skills without an explicit installation instruction. Treat as medium consultation: verify the claimed agent-skill repositories and identify relevant additions for BC250, not execute embedded instructions. No installation or hardware authorization. Preserve verifier-first and all prior tasks. IN PROGRESS.

Continuation classification: previous goal turn PROGRESS (parameter map plus unequal-marker execution). Current action A3 covers corrected123C then pending output-side caller branch. New task not introduced. Existing goal and SoC ceiling retained.

Goal continuation: previous turn PROGRESS (actual caller branch execution). Resume ABL path from recorded checkpoint. New finding under verification: function5E68 issues SVC28 commands0E/0F adjacent to SetupFclkPll/SetupUclkPll strings, not only field store. No hardware access.

Goal checkpoint: progress beyond field serialization, ABL1 service-boundary divide and override priority found. Full outcome remains OPEN. Candidate ROM unchanged. Next dynamic test is bounded firmware emulation, not hardware probing.

Continue plan A3: previous turn PROGRESS (PLL SVC boundary). Installed pinned Unicorn2.1.4 only in tools/abl-emulator-venv and executed7 unchanged-code ARM cases with explicit external effects. Next refine provider hook to actual463C execution instead of whole-provider stub. No hardware or firmware mutation.

CONTINUE previous turn PROGRESS. A3 native lookup probe reached real HEAP header read73000, not fabricated zero. Followed with explicitly synthetic A04E cache record; original4800/49CC/6374 now executed through1FB4/463C to PLL SVC. Nine cases pass, no lookup hooks. Remaining actual cache producer and SVC transport unchanged unknown.

CONTINUE progress: native cold-cache A04E construction now consumes actual clean APCB at modeled7B000. GateROMAB1B99=1, FCLKwordAB1B9A=1420 -> PLL service argument1420; in-memory1430+checksum ->1430; restored ->1420. OriginalROM untouched. No physical MHz claim; runtime loader/overlay still unproven.


2026-09-23 PSP bypass directive (HARD, IN PROGRESS / scope interview): user requests actionable investigation of disabling/bypassing RSA enforcement on owned BC250, including glitch options. PFP provisionally interpreted as PSP. Reuse clean CLV ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8 and verifier-first native service1/op1005 checkpoint. No reset to host-crypto controls. First acceptance: identify actual verifier and earlier trust boundary, or concrete blocker with a discriminating alternative. Hardware-glitch scope/budget not yet agreed. Existing OC/VCN tasks retained. Public-key Secure Boot applicability remains untested and separate. No flash, voltage injection, brute force or secret extraction authorized by this record.

Continuation progress: ABL0 native loader caller requests type60 at7B000 capacity2000 throughSVC2D, validator accepts cleanAPCB/rejects badchecksum. Clean BHD type60 pointsFFAB1000,size2000. Four emulated cases pass with explicit ROMservice fixture. Runtime7B000 destination now code-backed, actual SVC implementation/overlay still unknown. No ROM edits.

Continuation A3: previous turn PROGRESS. Verified later ABL4 SwitchToStartupDfPstate callerD8AE->9564 sendsSVC28 selector7 argument100. Current independent actual-handler task: retained SMU queue4 entries7/0E/0F map1E720/1F218/1F2F0, source hash pinned. Read-only Ghidra process6425 launched max1cpu/noanalysis, output pending. Queue binding to PSP service not assumed.

Continuation PROGRESS checkpoint: resolved duplicate queue-table labels. Raw vector index5, not retained unique-table label4, selects PLL handlers. Native FFC/FA8 accessors establish argument/response register pointers. No physical IO. SVC transport edge still unresolved, no ratio/profile completion.

Continuation: inspected available PSP type2 plaintext trustedOS, located actualSVC vector/dispatcher. Native dispatcher28/2D returns9 default, so this TOS path is not earlyABL service handler. Type1 header unknown, not provenencrypted. Transport branch now explicitly missing matching early handler; no false completion. Other OC tasks retained.

Continue previousPROGRESS, current closed opaque-type1 branch with exact source boundary. Query1E7D8 proven reads software row+18, not PLL. IDD1E650 is state setter, not count, exploratory filename not semantics. No final clockproof or BIOS candidate.

## 2026-09-23 Current CPU/GPU OC status request
Directive, medium, read-only status investigation. In progress: establish last applied CPU/GPU profile, actual stability evidence and whether current live state can be confirmed. Preserve all earlier open tasks. No OC changes or stress tests authorized by this request.

Goal continuation: previous turnPROGRESS, current candidate writer investigation yielded bounded elimination but no new setting.21E8C targetsF104 notDF,1F120 register replication notrow18. Transitive22D6C effects unresolved. Incomplete Ghidra existinglisting scan explicitly rejected as coverage evidence. No ROM/hardware action.
Status request completed: live SSH read confirms CPU3900/-35, GPU fixed2200 requested1015, both persisted and active, auto fan, UMA8G. Historical valid combined15+30min passed. New current-boot previous-reset parity marker and unclean power-off prevent stable-daily certification; attribution unknown. Evidence docs/action-logs/2026-09-23-oc-status.md. Earlier BIOS goals remain open. No setting changes or new load tests.

## 2026-09-23 Graphics settings under Proton: deep research
Directive, hard research. Open: identify game, then research sourced settings for confirmed BC-250 CPU3900/-35 GPU2200/1015 UMA8G and Proton. Need exact game title first, then target resolution/FPS if unavailable. User requests comprehensive sources. Preserve all previous open tasks. No graphics, Proton, OC or machine changes authorized.
Graphics research clarification: exact game is Marvel's Spider-Man Remastered (not Miles Morales or Spider-Man 2). Hard research directive retained. Next clarify target resolution/FPS; recommended starting target 1080p/60, not a measured capability claim.

Audit full goal R1-R8: NOT complete; BIOS OC candidate/instruction lacking SoCsetter and actualfrequency application. Repeated blocked condition3+ turns audited, no safe justified firmware edit available from current evidence. Controller status update pending. Prior VCN/MCP tasks retained, not cancelled.
Graphics scope confirmed by user: interpreted1080p,60FPS, all presets, native and FSR Quality/alternatives. Interview complete. Execute deep research; distinguish measurements on exact hardware from extrapolation. Prior open tasks retained.
User correction: reported16FPS dips; prioritize actual Spider-Man Remastered diagnosis and immediately useful AMD/native/FSR-only settings over broad sources. Directive, medium bounded read-only diagnosis. No DLSS recommendation. Research still open, no hardware settings authorized.
User directive: reread governing instructions. Simple. Completed review of conversation instructions. Correction: deliver concrete AMD-only diagnosis, not extra questions or raw source collection. Spider-Man16FPS cause remains unconfirmed. Read-only snapshot: GPU100%,2200MHz, VRAM~5.57GiB/8GiB, availableRAM2.3GiB, vmstat interval si/so0, throttle0. Actual settings and frame-time correlation not yet captured. Research and earlier tasks remain open.

## Renewed user directive 2026-09-23
- [ ] Continue result-oriented search after blocked audit. Seek independently new BC250-specific SoC actuator / final clock evidence. Keep R1-R8 and all prior open tasks. Do not replace hardware proof with emulation. Current turn is explicit continuation authorization, not flash authorization.
User yes: continue agreed read-only actual-settings inspection and AMD-only1080p60 recommendations. Simple continuation of bounded diagnosis, not permission for OC or service changes.
User update: dips now12FPS, asks actual ProtonDB settings and accountability. Medium directive within current diagnosis. Read actual current log/provider before reply. Existing game settings unchanged by this session. Found actual custom wrapper default FSR4/OptiScaler on, nativeFSR AA, hair/weatherHigh,1080setting vs4K swapchain. Do not claim these prove12FPS cause.
User reports dips10FPS persist after recommendation. Medium diagnostic directive, not new design interview. Verify actual relaunched process/settings and correlate memory/GPU/CPU evidence before further advice. Keep research and earlier tasks open; no unapproved setting writes.
New user directive, medium implementation: game exited; remove OptiScaler from Spider-Man launch path, use native FSR DLL route as intended, apply sensible1080p60 settings. Exact board/game scope authorized, not global Proton/OC changes. First inspect wrapper provider and user launch settings, preserve recoverable originals. Do not promise10FPS impossible without measured gameplay. Earlier research retained.
Applied scoped native-FSR/noOptiScaler launch branch and1080p medium-oriented settings, backups retained. Host environment baseline/modified/rollback verified. Runtime next launch, decoded settings, absence ofOptiScaler maps and FPS acceptance OPEN. No60FPS claim.
- [x] Renewed search produced a new causal CLV result: CMOS clock overwritten by actual native APCB item7 lookup.6 native provider cases, report docs/research/2026-09-23-cmos-apcb-precedence.md.
- [ ] Trace item7 overlay/producer and later training use. R2-R7 remain incomplete. No hardware or ROM patch performed.
User continue: run pending Spider-Man runtime verification of same scoped wrapper/settings. Simple continuation. Inspect live process/maps and newest game log; launch ordinary game only if absent. No OC/service/reboot changes or synthetic load.

- [ ] User correction: deliver actual synchronization enablement path, not configuration-precedence findings as substitute. Prior CMOS/APCB result does not identify UCLK divider actuation or prove1:1:1. All previous open requirements remain.
Runtime result: game launched PID81330, OptiScaler absent in process maps, settings consumed. FSR4 provider actual execution unresolved (noamdxcffx mapping at startup). FPS acceptance pending gameplay. Correction task: restore unrequestedFOV change0->prior1250 safely after game closes; DOF1 actuallyLowest. Do not call full configuration accepted.
User correction: problem persists; asks restatement of actual task. Simple direct question. Goal is diagnose and eliminate10–16FPS drops in Spider-Man Remastered on this BC250/Proton, achieve measured stable1080p60 with nativeFSR path and noOptiScaler. OptiScaler removal succeeded but did not solve symptom. One56.47FPS sample is not acceptance. Further action must correlate actual dip/frame-time with rendering/CPU/I/O rather than another unsupported settings guess. FOV restoration remains open; prior tasks retained.
User authorizes live monitoring while entering Spider-Man: medium read-only measurement task. Capture timestamped GPU sysfs, per-threadCPU, processI/O, memoryPSI, swap counters, existing gameFPS log and kernel events during user gameplay. No settings/restarts/load generators. Diagnose correlated dip, not assume root cause.
- [ ] Explicit continuation: trace UclkDiv1M0 (AmdSetup+330 / INV1204) to actual divider consumer. Treat repeated early PLL verification as regression only. Preserve all prior requirements and tasks.
User completed gameplay and requests actual bottleneck from monitoring. Medium diagnostic directive. Analyze collected180sec telemetry, identify per-threadCPU versus memory/I/O/GPU correlation, do not infer noCPU bottleneck from totalCPU. Need exact evidence and next discriminator, no settings writes.
Monitoring analyzed: no memory-exhaustion evidence; renderthread nearonecore but also at60FPS, insufficient attribution. Found actual game uses old/optRADV despite installedsystemMesa; twoenvironment.d overrides retained after priorprofile.d-onlyunpin. Next per-game same-scene systemICD comparison after gameclosed. Do not claim confirmedcause. No global changes.
- [x] Executed specifically named UclkDiv1 phase handlers: ABL1 actualAPCB5 cases, ABL3/4 modeled-provider6 cases. Read/log only in these paths. Report docs/research/2026-09-23-uclk-application.md.
- [ ] Still missing actual final UCLK divider actuation and INV1204->APCB21 join. Whole field not declared inert. Goal not completed.
New task: audit board graphics stack clutter/provenance, oldMesa routing and duplicate overrides, propose bounded recoverable cleanup. Medium read-only inventory first, not blanket delete or globalreload authorization. Preserve Spider-Man bottleneck/FOV/runtime tasks. User asks explanation and cleanup; exact removal targets must be established before destructive operations.
Graphics clutter audit completed read-only: docs/research/2026-09-23-board-graphics-stack-audit.md. Active duplicateenvironment.d overrides explain oldMesa selection; packagehistory andactualmaps corroborate. SystemVulkan packages0altered. Cleanup pending exacttwofile reversibledeactivation + agreedsessionrestart; no deletionorpackageschanged. Ownwrapperpatchis1modifiedpackagefile andmustnotbehidden.
- [ ] Continued active goal: exactSMU UCLK handler1F2F0 to actual register/divider semantics. Preserve R1-R8 and all earlier open tasks. Prior log-only paths excluded, not repeated.
New directive: full prior-customization audit of BC250 system, medium read-only inventory expanded in stages. Scope package provenance, boot/kernel parameters, system/user services, environment/graphics/Proton overrides, customscripts, storage/memory settings and persistence. Do not deleteorreset machine, expose secrets, or restart services. Deliver categorized active/conflicting/intentional/inactive findings and boundedcleanup targets. EarlierSpiderMan/FOV tasks retained.
Expanded configuration audit complete within declared scope: docs/research/2026-09-23-system-customization-audit.md. New confirmed swappiness150 despitefile-swap/nozram, dmemlow>custommax, netconsole pulled in despitedisabled and invalidargument,3failedhelpers withmissingexecutables, mixeddebug/watchdog policies. Systempackagepresence checks correctedpermissionfalsepositives. Cleanup remains unexecuted; no full-disk integrity/10FPSrootcause claim. Earlier tasks retained.
User correction: prior configuration review is not requested full system audit. Hard directive: exhaustive filesystem metadata/package provenance/customization/persistence audit, with explicit coverage and exclusions, then approved cleanup. No claim knowledge of every file from sampled configuration. Need establish maintenance window before sustained full-volume checksum work. Never read/copy secrets, game saves or private contents unnecessarily. Keep prior tasks. Plan .procoder/plans/bc250-full-system-audit.md.
- [x] Check primaryAMD clock-header compatibility with exactSMU group3. Same base but offset34/38 mismatch, generic map rejected. Not a synchronization result.
- [ ] Obtain matching clock-register semantics or separately approve bounded baseline hardware observation. All candidate/SoC/1:1:1 acceptance remains open.
User approves full audit execution and maintenance load as proposed. Continue hard task with scope interview satisfied: single-thread low-priority metadata/package verification, no deletions/reboot. Start actual filesystem inventory now, preserve all prior tasks.
- [ ] Test whether PLL offsets34/38 are distinct named registers of same block, rather than revision mismatch. Retain full OC goal and existing open requirements.
- [x] Tested alternative interpretation of PLL34/38 comparison using bounded source search. No matching definition, whole-header incompatibility NOT proven. Correction recorded.
- [ ] BLOCKED pending new independent source or separately authorized baseline hardware diagnostics: final UCLK semantics, realSoC setter, main candidate and operator recipe still missing. Full earlier tasks retained. Audit docs/research/2026-09-23-sync-resume-blocked-audit.md.
- [ ] User-approved diagnostic preparation only: fixture-tested metadata collector and staged hardware diagnostic runbook, no execution on actual board. Preserve all prior tasks and fullR1-R8. Next hardware run requires separate approval.
Full audit checkpoint: metadataalllocalmounts5,615,530objects0errors; Qkk1463packages421278entries9packagesaltered. Report2026-09-23-full-system-audit.md. New activeACPI overrides, bootconfigdrift,setgidpermissiondelta,worldwritableFurMarkconfigs,capability/listener exposures recorded. Notallsemanticprovenancechecked, independentarchivespending, no cleanup/10FPSsolutionclaim.

Alias2: continue full system audit, next activeACPI/customscripts verification. Simple continuation of approvedread-only work; retain earlier tasks.
Auditcontinuationresult: ACPIdecode/runtimejoinandcustomscriptfalsePASSreviewcompleted; F29–F36. Stillnotcompletefullsemanticprovenance. Nextuserlaunchersandpackageetalons. No OC/settingschanges.

Alias2: execute next fullaudit userlaunch/Proton overrides and local packageetalon validation. Simple continuation; no systemwrites, prior tasks retained.
- [x] Diagnostic preparation complete: guarded existing-probe copy,10 offline tests, same-input baseline/modified/rollback verification, patch reconstruction and executable rollback. Four roles under evidence/firmware-audit/20260923-diagnostic-preparation/. Runbook docs/runbooks/2026-09-23-clv-diagnostic-preparation.md. Repository Python83 pass; no board run.
- [ ] Separate approval/confirmed board session for Stage1 metadata capture. Telemetry and direct registers not authorized by preparation. FullOC goal still incomplete.
Auditcontinuation3complete: scopeduserlaunchmetadata, libutempteretalonandtmpfilesexplanation, effectiveDRMdebug0. Do notclean legitimateutempterrightsorSunshinealias. Remainingauditopen.

Alias2: continue audit remaining package deviations and persistenthooks; simple approvedcontinuation, preserveearlier tasks, no systemmutations.
- [ ] Alias2 continuation: execute Stage1 metadata on confirmedBC250 using existing authorized access, or identify exact missing access. No telemetry/settings/flash permission inferred. Previous open tasks retained.
Auditcontinuation4: F41–F49, classifybenignQkkpolicyversusrealconfigdefects. Exactoldamd-ucodeindependentetalonnotobtained, nofalsecorruptionclaim. Nextcoverage/cleanupmanifest; no cleanupauthorized/executed.

Alias2: execute remainingactiveconfigreferenceverification thencleanupmanifest. Simple approvedauditcontinuation, no deletions/restart, earlier tasks remain.
- [x] Stage1 metadata executed2026-09-23T07:31:54Z, exit0, one1002:13fe GPU. BIOS reportsP3.00, kernel7.2.6-1.206-cachyos-bc250. Same four roles extended by stage1 evidence; no physical clock/SoC proof.
- [ ] Resolve installed-image provenance against latest saved flash/readback records before treating hardware as500CLV. Version string alone insufficient. Stage2 not authorized. D17 LinuxDF/SMN prohibition retained.
Continuation5result: cleanupmanifestA1–A8validatedwithunitdependencies. No cleanup. Auditcoverageandremaininggapsrecorded. NeedexactA1sessionrestartapprovalbeforeapplication; earlierperformance/FOVtasksopen.

Alias2: continue permitted read-only audit, notyes to pendingA1 sessionrestart. Execute remainingACPIidentityverification. Initialdispatcher failed beforeprocesscreation due embeddedNUL, correctedcommand. No systemchanges.
- [ ] Alias2: reconcile liveP3.00 metadata with latest saved programmer/flash records, without switching cleanCLV500 development base or requiring new dump.
Auditcontinuation6completedF50–F52. ExactliveACPIreadback andsnapshotpersistence established; no author/sourceclaim. A1restartrequiresdirectapproval, alias2retainscontinue meaning. Do notrepeatclosedhashchecks.

Alias2: finish remaining read-onlyaudit validation, do not reinterpretasrestartapproval. Verify secondsource ACPIprovenance and exactoldmicrocode packageavailability; no repeatedhashchecks or configwrites.
- [x] Reconciled saved provenance: Sept22 image contains19/19 P3-identical PSP payloads,11 differ fromCLV. Existing Sept21W11-only audits predate newer file. Report2026-09-23-installed-image-provenance.md.
- [ ] Full currently installed image remains unproven. Do not count currentP3-reported board as500CLV HARDWARE-PASS. Original OC deliverables remain open.
Read-onlyauditdeliveryclosedwithdeclaredlimits:2026-09-23-audit-conclusion.md. Finalsourcejournalchecknoauthor,newprogressnonebeyondboundednegative. KeepcleanupA1–A8,exactoldmicrocodeetalon,FOVand10FPSopen. Stoprepetitivescans;no automaticrestartfromalias2.

Alias2simplecontinuation: A1safeofflinepreparationexecuted; freshbackup2exactoverrides, localdeactivation/rollbacktest2->0->2withhashmatch. No remotechangesorrestart. Earlieropen tasksretained. A1liveapplicationstillneedsdisruptionapproval.
- [ ] Alias2: exactCLV divider readback/math check, no target switch or new hardware probe. Preserve all prior requirements and tasks.

Alias2: nextactualoperationA1needsclosingSteam/session. Existingbackuptestvalid, nofurtherpreparationornewscans. Waitingexplicitapproval, notexactmagicphrase. No boardchanges.
- [x] Verified exactCLV getter semantics:23AB0/23AC4 cached SRAM only,57 instruction byte checks. Not usable as independent physicalUCLK readback.
- [ ] Physicaldivider/SoC control and accepted1:1:1 recipe remain missing. Do not repeat excluded readback/math/log-only checks.

Alias2 repeated: no new task or approval. Next A1 live operation remains unauthorized for session closure under alias rule. Stop repeated scans and approval prompts. No board writes or restart.
User explicit approval: "да зкарывай" authorizes agreedA1 closeapps/graphicalsessionrestart and disablingtwooldMesaoverrides. Medium boundedtransaction; preserveOC/fan/BIOS and allotheropentasks. Inspectcurrentstate thenapplyrecoverableexactpaths.
- [ ] Alias2: seek independently named AMD clock-counter mechanism applicable to exactCLV domains. Do not substitute display/GFX counters or driver aliases. Existing open tasks retained.
A1donewithruntimeevidence:newgamescopeusesystemMesa,newSteamnooldICDvars. Firstrestartinsufficient, usermanagerrefreshresolved. Exact2filesretained, rollbackverifiedoncopy. GameFPS/remainingcleanup/FOVopen.

Alias2: verify newSpiderManruntimeMesa afterA1; simplecontinuation, launchordinarygameifabsent, noadditionalcleanuporOCchanges.
A1gameverificationPASS: newSpiderManPID131192uses /run/host/usr/lib/libvulkan_radeon.so, noOptiScalermaps. New13:08log1080/nativeFSRAA. NoFPSacceptanceyet. InitialURIreturn0wasnotlaunchproof; current-sessionapplaunchobservedprocess.
- [x] Opened actualCyan displaycounter source, verified6C9FC DPREFCLK and softwarefallback. Excluded from memorysync proof, sources/hashes retained.
- [ ] Actual independentMCLK/UCLK/FCLK observation and BIOSSoC control still missing. No new candidate or hardwarepass.
User correction: GPU stillunderloaded, tasknotmet. Mediumdirectivediagnosis: sample currentgame GPUenginecounters+perthreadCPU/waitchannels+freshFPS/pressure concurrently. Do not infer successfromMesaidentity. No settingschanges.
- [ ] Alias2: inspect independent divider-status source (not cachedSMU/displaycounter), exact applicability toCLV/Cyan required. Retain earlier tasks, no new hardware authorization.
Livebottleneckcapturecomplete: systemMesa, gameplaylog26.45FPS,repeatedRenderThreadntsync_schedule, workerfutexwait, GPUengine~22.5%, PSI0, cgroupunlimited/nr_throttled0. Thislocalizeswait-boundpath butnotcausalNTSYNCbug. Needcontrolledsingle-variableNTSYNCoffA/B oruserstackprofile, notmoregraphicslowering. FPSproblemNOTsolved.
- [x] Pinned ZenStates/ZenTimings source alternative inspected. Table-derived clocks and DDR4-specific ratio do not supply demonstratedCyan readback. No hardware execution or newOCrecipe.
- [ ] FullCLV applieddivider/physicaldomain/SoC gaps persist; require new independently applicable source or separately justified firmware-context observation, not repeated excluded checks.
Alias2: continue proposed single-variable NTSYNC A/B preparation/verification. Medium boundeddiagnosis. Preserve graphics/OC, do not terminate active gameplay without agreedrestart. First native Proton environment-switch verification on copiedsource, inspect game availability.
InstalledProtonexactASTbranchverified: baselineWINENTSYNC1, nontsyncabsentWINENTSYNC, rollback1. Livegame131192WINENTSYNC1. This verifies switchsemantics only, notperformance. User must save/exit or explicitlyallowgameclosure beforeA/B; do notlooponpreparation.
- [x] Alias2 blocker audit: revalidated excluded cached/display/DDR4 paths and pristineCLV identity. No new synchronization control, no completion.
- [ ] Separate method decision: prepare a dedicated no-settings-change UEFI diagnostic, not reuse write-heavy VCN app. Firmware-context execution and any flash require later exact approval and recovery gate. FullOC goal remains blocked, not completed.
User confirms game exited: execute agreed single-variable NTSYNC-off A/B for SpiderMan only. Medium bounded reversible patch to existing AppID branch, backup/rollback, no graphics/OC changes, launch viaSteam andverifyenv.
- [ ] Alias2 approved: prepare dedicated UEFI diagnostic, compile/structurally verify and test with mockedIO only. No execution on board. Preserve fullOC scope and earlier open tasks.
NTSYNCABappliedonlyAppID1817070, newPID143560verifiedNTSYNCoff/OptiScaler0/systemMesa. Baseline/modified/rollbackchecks0,hashrestorematch. Usergameplaycomparisonpending. Graphics/OCunchanged. Start180secmonitor.
User reports NTSYNCoff didnotimprove. Medium correction: reject NTSYNCswitch as observedremedy, stop furtherguessedchanges. ReviewlatestABevidence and exactframewaitsource, preservealltasks. No automaticsetting/restart.
ABrejected: usernochange. Fixed180smonitorendedbeforelateFPSdrop; measurementdesignfailedtocapturefullproblem. Partialuserstackexit1cannotlocatecaller. Nextneedscontinuousper-framecapture/qualifiedprofile, noadditionalsettingguesses. NTSYNCoffstillteststate, rollbackpendingclosedgame.
Newdirective mediumresearch: read officialProton/vkd3d/Gamescope documentation and SpiderMan reports; tie documentedoptions toobservedlowGPU/waits, distinguishunsupportedtweaks. No furtherlivechanges. Preserve pendingNTSYNCrollback/FOV/cleanupandFPSgoals.
DocumentationresearchexecutedofficialProton/vkd3dandprimaryissues1406/2603/6088/8376. Report2026-09-23-spiderman-proton-documentation.md. Nextinspectactualvkd3dheaproutebeforetestingno_upload_hvv. VisibleVRAM8GiBconfirmed, notrootcauseproof. No livechanges.
- [x] Built standaloneEFI experimental observerv001, default noPCI, fixed9 rawwords match exactCLV descriptor offsets,20ASan/UBSanmockcases pass, reproducible5120-byteEFI verifiedPEAMD64/subsystem10/imports0. OriginalBIOS unchanged.
- [ ] UEFI preparation acceptance still open: independent review retry, completeprotocolintegration mock and actualemulatedUEFIload. No boardrun permitted; full1:1:1/SoC goal remains open.
- [ ] IndependentEFIreview failedtransport twice(wrongtaskreceipt), notaccepted. No moreretryblindly. FullUEFIprotocolintegration/mock and firmwareloadercheck remain beforehardwareproposal.

Alias2: inspect actualinstalledvkd3dheaprouting and existinglogs before newflags. Simplecontinuation, no gamekill/settingschange.
- [ ] Alias2: fullEFIprotocol mock integration and emulator loader check for observerv001, no realboard execution. Prior tasks retained.
Installedheapcheck: actualprefixDLLmatchesProtonSHA, v3.1.0string,flagpresent, gameVKD3D_DEBUGnone. ExistingBARconsolelogsareearlierthanthisgamelaunchandnotadmissibleheapproof. Needfreshstartupinfolog, notunjustifiedno_uploadpatch. No settingschanged.
- [x] FullEFIprotocolmock18 cases passed, total38. ActualEFIloaded underOVMF3entries(default/help/nonCyanrejection), guestexit0. Firstbootfailurecorrected byexistingShell, preserved.
- [ ] Validindependentreview and action-specificboardreadiness still pending. No physicalrawcapture; fullSoC/clock/BIOSrecipe remainsopen.

Alias2: prepareexactscopedVKD3Dinfologpatchoncopyandverifybehavior; inspectgamebeforeinstall. Simplecontinuation, no performanceflags.
- [ ] Alias2: independentobserver review via different reviewer role plus exact hostSMN mapping evidence. No rawcapture/hardware execution or flash authorized.
Startupdiagnosticexecutedaftergamefoundclosed: scopedinfo/logpatch, launch, freshAppID1817070logprovesUPLOADusesDEVICE_LOCAL|HOST_COHERENT(HVVallowed), vkd3d3.1buildaf89350. Hypothesisspecificrouteconfirmed, notFPSrootcause. Nextsinglevariable no_upload_hvv A/B withsameNTsyncstate/settings; no flagappliedyet.

Alias2: execute boundedno_upload_hvvABpreparation on sameSpiderManwrapper, preserveallotherflags/settings. Checkgameclosedbeforeinstallation; no forcedtermination.
Alias2: resume pendingHVV A/B gate. Simplecontinuation; verify gameexit before livewrite/launch. No extra flags or forceclose.
HVVABappliedclosedgame,newPID161194, exactstartupdecisionHOST_COHERENTinsteadofDEVICE_LOCAL|HOST_COHERENT. Allotherflagsretained. FPSnotaccepted. Evidence no-upload-hvv-startup.log, samefourtransactionrolesreopened. Userrepro pending.
- [x] Alternative review attempted and validated: wrongtask/no receipt, rejected. Roottransport sourceaudit completed separately, no newhardwareaccess.
- [ ] BLOCKED independentreview delivery; need functioning independent review context. CurrentEFI remainsNO-GO forrealboard, fullOCgoal notcomplete.
User message22: ambiguous between measured22FPS and mistypedcontinuation. Simpleclarificationpending, do notinferbenchmarkoutcomeorchangeflags. Allprevious tasks retained.
- [ ] Alias2: reproduce silentselectorrestore failure and verify restoredvalue rather than trustingPCIstatus. New defaultworker code review, nohardware. Earlier requirements retained.
Correction22means gamehungafterourlaunch, not22FPS. Mediumincidentdiagnosis: markno_upload_hvvtrialFAIL/hangreported, collectboundedread-onlyliveness/logs. No repeatedlaunch, GPUreset,reboot orprocesskillwithoutapproval. Priorperformanceandcleanupgoalsopen.

## 2026-09-23 задача #1 Plane: окончательный текст /goal выдан

Взята с доски Plane (issue #1, high). Консолидированы: дословные R1-R8
(`.procoder/specs/clv500-actuator-first.md`), решения Q1-Q4, приказы
оператора 2026-09-23 (параллельность треков, no-1800, SoC-first), аудиты
приёмки. Текст выдан: `.procoder/specs/clv500-goal-final.md`. Оба критерия
приёмки закрыты. ROM, кандидаты, плата и настройки не затронуты. Гейты и
хеши: `docs/action-logs/2026-09-23-goal-text-issued.md`.
